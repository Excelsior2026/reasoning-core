"""REST API for reasoning extraction."""

from typing import Dict, Optional
from reasoning_core.extractors.concept_extractor import ConceptExtractor
from reasoning_core.extractors.relationship_mapper import RelationshipMapper
from reasoning_core.extractors.reasoning_chain_builder import ReasoningChainBuilder
from reasoning_core.graph.knowledge_graph import KnowledgeGraph, Node, Edge
from reasoning_core.plugins.base_domain import BaseDomain


class ReasoningAPI:
    """High-level API for reasoning extraction."""

    def __init__(self, domain: Optional[BaseDomain] = None):
        """Initialize reasoning API.

        Args:
            domain: Domain plugin for specialized extraction
        """
        self.domain = domain
        self.concept_extractor = ConceptExtractor(domain=domain)
        self.relationship_mapper = RelationshipMapper(domain=domain)
        self.chain_builder = ReasoningChainBuilder(domain=domain)

    def process_text(self, text: str, include_graph: bool = True) -> Dict:
        """Process text and extract reasoning.

        Args:
            text: Input text to process
            include_graph: Whether to build knowledge graph

        Returns:
            Dictionary containing extracted reasoning
        """
        # Extract concepts
        concepts = self.concept_extractor.extract(text)

        # Map relationships
        relationships = self.relationship_mapper.map_relationships(concepts, text)

        # Build reasoning chains
        chains = self.chain_builder.build_chains(concepts, relationships)

        result = {
            "concepts": [vars(c) for c in concepts],
            "relationships": [vars(r) for r in relationships],
            "reasoning_chains": [vars(c) for c in chains],
        }

        # Build knowledge graph if requested
        if include_graph:
            graph = self._build_knowledge_graph(concepts, relationships)
            result["knowledge_graph"] = graph.to_dict()

        # Generate questions if domain supports it
        if self.domain:
            content_dict = self._prepare_content_for_questions(concepts)
            questions = self.domain.generate_questions(content_dict)
            result["questions"] = questions

        return result

    def _build_knowledge_graph(self, concepts, relationships) -> KnowledgeGraph:
        """Build knowledge graph from concepts and relationships.

        Args:
            concepts: List of Concept objects
            relationships: List of Relationship objects

        Returns:
            KnowledgeGraph instance
        """
        graph = KnowledgeGraph()

        # Add nodes
        for concept in concepts:
            node = Node(
                id=f"{concept.type}_{concept.position}",
                type=concept.type,
                label=concept.text,
                properties={"context": concept.context},
                confidence=concept.confidence,
            )
            graph.add_node(node)

        # Add edges
        for rel in relationships:
            edge = Edge(
                source_id=f"{rel.source.type}_{rel.source.position}",
                target_id=f"{rel.target.type}_{rel.target.position}",
                type=rel.type,
                properties={"evidence": rel.evidence},
                confidence=rel.confidence,
            )
            graph.add_edge(edge)

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
        """
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
