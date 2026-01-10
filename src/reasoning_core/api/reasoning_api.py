"""REST API for reasoning extraction."""

from typing import Dict, Optional
from dataclasses import asdict
from reasoning_core.extractors.concept_extractor import ConceptExtractor
from reasoning_core.extractors.relationship_mapper import RelationshipMapper
from reasoning_core.extractors.reasoning_chain_builder import ReasoningChainBuilder
from reasoning_core.graph.knowledge_graph import KnowledgeGraph, Node, Edge
from reasoning_core.plugins.base_domain import BaseDomain
from reasoning_core.llm import OllamaService
from reasoning_core.web.config import (
    LLM_ENABLED,
    LLM_MODEL,
    LLM_BASE_URL,
    LLM_USE_GPU,
    LLM_TIMEOUT,
)


class ProcessingError(Exception):
    """Exception raised when processing fails."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class ReasoningAPI:
    """High-level API for reasoning extraction."""

    def __init__(
        self,
        domain: Optional[BaseDomain] = None,
        use_llm: Optional[bool] = None,
        llm_service: Optional[OllamaService] = None,
    ):
        """Initialize reasoning API.

        Args:
            domain: Domain plugin for specialized extraction
            use_llm: Whether to use LLM enhancement (defaults to LLM_ENABLED config)
            llm_service: Optional LLM service instance (creates one if use_llm=True)

        Raises:
            TypeError: If domain is not None and not a BaseDomain instance
        """
        if domain is not None and not isinstance(domain, BaseDomain):
            raise TypeError(f"domain must be an instance of BaseDomain, got {type(domain)}")

        self.domain = domain
        
        # Initialize LLM service if enabled
        self.use_llm = use_llm if use_llm is not None else LLM_ENABLED
        self.llm_service = llm_service
        
        if self.use_llm and self.llm_service is None:
            try:
                self.llm_service = OllamaService(
                    model=LLM_MODEL,
                    base_url=LLM_BASE_URL,
                    use_gpu=LLM_USE_GPU,
                    timeout=LLM_TIMEOUT,
                )
                # Check availability
                if not self.llm_service.is_available():
                    self.use_llm = False
                    self.llm_service = None
            except Exception:
                # LLM not available, fallback to pattern-based
                self.use_llm = False
                self.llm_service = None
        
        # Initialize extractors with LLM support
        self.concept_extractor = ConceptExtractor(
            domain=domain,
            llm_service=self.llm_service,
            use_llm=self.use_llm,
        )
        self.relationship_mapper = RelationshipMapper(
            domain=domain,
            llm_service=self.llm_service,
            use_llm=self.use_llm,
        )
        self.chain_builder = ReasoningChainBuilder(domain=domain)

    def process_text(self, text: str, include_graph: bool = True, use_llm: Optional[bool] = None) -> Dict:
        """Process text and extract reasoning.

        Args:
            text: Input text to process
            include_graph: Whether to build knowledge graph
            use_llm: Override LLM usage for this request (None = use instance default)

        Returns:
            Dictionary containing extracted reasoning

        Raises:
            TypeError: If text is not a string
            ValueError: If text is empty
            ProcessingError: If processing fails at any stage
        """
        # Input validation
        if not isinstance(text, str):
            raise TypeError(f"text must be a string, got {type(text)}")
        if not text.strip():
            raise ValueError("text cannot be empty")

        try:
            # Temporarily override LLM usage if specified
            if use_llm is not None:
                old_use_llm = self.concept_extractor.use_llm
                old_use_llm_rel = self.relationship_mapper.use_llm
                self.concept_extractor.use_llm = use_llm and self.llm_service is not None
                self.relationship_mapper.use_llm = use_llm and self.llm_service is not None
            
            # Extract concepts
            concepts = self.concept_extractor.extract(text)

            # Map relationships
            relationships = self.relationship_mapper.map_relationships(concepts, text)

            # Build reasoning chains
            chains = self.chain_builder.build_chains(concepts, relationships)

            # Restore LLM usage if temporarily overridden
            if use_llm is not None:
                self.concept_extractor.use_llm = old_use_llm
                self.relationship_mapper.use_llm = old_use_llm_rel
            
            # Use asdict instead of vars for better dataclass support
            result = {
                "concepts": [asdict(c) for c in concepts],
                "relationships": [asdict(r) for r in relationships],
                "reasoning_chains": [asdict(c) for c in chains],
                "llm_enhanced": use_llm if use_llm is not None else self.use_llm,
            }

            # Build knowledge graph if requested
            if include_graph:
                try:
                    graph = self._build_knowledge_graph(concepts, relationships)
                    result["knowledge_graph"] = graph.to_dict()
                except Exception as e:
                    # Log error but don't fail entire processing
                    # Graph building is optional
                    result["knowledge_graph"] = None
                    result["graph_error"] = str(e)

            # Generate questions if domain supports it
            if self.domain:
                try:
                    content_dict = self._prepare_content_for_questions(concepts)
                    questions = self.domain.generate_questions(content_dict)
                    result["questions"] = questions
                except Exception as e:
                    # Log error but don't fail entire processing
                    # Questions are optional
                    result["questions"] = []
                    result["questions_error"] = str(e)

            return result

        except (TypeError, ValueError) as e:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            # Wrap other exceptions
            raise ProcessingError(f"Failed to process text: {e}", original_error=e) from e

    def _build_knowledge_graph(self, concepts, relationships) -> KnowledgeGraph:
        """Build knowledge graph from concepts and relationships.

        Args:
            concepts: List of Concept objects
            relationships: List of Relationship objects

        Returns:
            KnowledgeGraph instance

        Raises:
            ProcessingError: If graph building fails
        """
        import uuid
        from collections import Counter

        graph = KnowledgeGraph()
        # Track concept positions to generate unique IDs
        position_counter: Counter = Counter()

        # Add nodes with unique IDs
        node_map: Dict[tuple, str] = {}  # Maps (concept.text, concept.position) to node_id
        for concept in concepts:
            # Create unique ID using type, position, and counter to avoid collisions
            key = (concept.text, concept.position, concept.type)
            if key in node_map:
                # If duplicate exists, use existing node
                continue

            # Generate unique ID: use counter to handle same type+position
            pos_key = (concept.type, concept.position)
            position_counter[pos_key] += 1
            node_id = f"{concept.type}_{concept.position}_{position_counter[pos_key]}"

            node = Node(
                id=node_id,
                type=concept.type,
                label=concept.text,
                properties={"context": concept.context},
                confidence=concept.confidence,
            )
            graph.add_node(node)
            node_map[key] = node_id

        # Add edges - use node_map to find correct IDs
        for rel in relationships:
            source_key = (rel.source.text, rel.source.position, rel.source.type)
            target_key = (rel.target.text, rel.target.position, rel.target.type)

            source_id = node_map.get(source_key)
            target_id = node_map.get(target_key)

            # Only add edge if both nodes exist
            if source_id and target_id:
                edge = Edge(
                    source_id=source_id,
                    target_id=target_id,
                    type=rel.type,
                    properties={"evidence": rel.evidence},
                    confidence=rel.confidence,
                )
                try:
                    graph.add_edge(edge)
                except ValueError as e:
                    # Skip invalid edges (nodes not found) but continue processing
                    continue

        return graph

    def _prepare_content_for_questions(self, concepts) -> Dict:
        """Prepare content dictionary for question generation.

        Args:
            concepts: List of Concept objects

        Returns:
            Dictionary organized by concept type
        """
        content = {}
        for concept in concepts:
            if concept.type not in content:
                content[concept.type] = []
            content[concept.type].append(concept.text)
        return content

    def set_domain(self, domain: BaseDomain) -> None:
        """Change the active domain.

        Args:
            domain: New domain plugin

        Raises:
            TypeError: If domain is not a BaseDomain instance
        """
        if not isinstance(domain, BaseDomain):
            raise TypeError(f"domain must be an instance of BaseDomain, got {type(domain)}")

        self.domain = domain
        self.concept_extractor.domain = domain
        self.relationship_mapper.domain = domain
        self.chain_builder.domain = domain

    def get_domain_info(self) -> Dict:
        """Get information about the current domain.

        Returns:
            Dictionary with domain information
        """
        if not self.domain:
            return {"name": "generic", "patterns": [], "terminology": {}}

        return {
            "name": self.domain.get_name(),
            "patterns": self.domain.get_reasoning_patterns(),
            "terminology": self.domain.get_terminology_mapping(),
        }
