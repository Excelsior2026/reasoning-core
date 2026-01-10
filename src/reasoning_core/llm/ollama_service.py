"""Ollama LLM service integration."""

import os
import json
import logging
from typing import List, Optional, Dict
import requests
from reasoning_core.llm.base import LLMService
from reasoning_core.extractors.concept_extractor import Concept
from reasoning_core.extractors.relationship_mapper import Relationship

logger = logging.getLogger(__name__)


class OllamaService(LLMService):
    """Ollama-based LLM service for enhanced extraction."""

    def __init__(
        self,
        model: str = "llama3.2:3b",
        base_url: str = "http://localhost:11434",
        use_gpu: bool = True,
        timeout: int = 120,
    ):
        """Initialize Ollama service.

        Args:
            model: Model name to use (e.g., "llama3.2:3b")
            base_url: Ollama API base URL
            use_gpu: Whether to use GPU (Ollama uses GPU by default if available)
            timeout: Request timeout in seconds
        """
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.use_gpu = use_gpu
        self.timeout = timeout
        self._available = None

    def is_available(self) -> bool:
        """Check if Ollama is available and model is loaded."""
        if self._available is not None:
            return self._available

        try:
            # Check if Ollama is running
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                self._available = False
                return False

            # Check if model is available
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            
            # Check for exact match or compatible version
            available = any(
                self.model in name or name.startswith(self.model.split(":")[0])
                for name in model_names
            )
            
            self._available = available
            return available

        except Exception as e:
            logger.debug(f"Ollama not available: {e}")
            self._available = False
            return False

    def _call_ollama(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Call Ollama API with prompt.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt

        Returns:
            Response text from model

        Raises:
            Exception: If API call fails
        """
        if not self.is_available():
            raise Exception("Ollama service not available")

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,  # Lower temperature for more deterministic results
                "top_p": 0.9,
                # GPU settings - Ollama automatically uses GPU if available
                # But we can set num_gpu to prefer GPU
                "num_gpu": -1 if self.use_gpu else 0,  # -1 means use all available GPUs
            },
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "").strip()

        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API error: {e}")
            raise Exception(f"Failed to call Ollama: {e}")

    def extract_concepts(
        self, text: str, domain: str, existing_concepts: Optional[List[Concept]] = None
    ) -> List[Concept]:
        """Extract concepts using LLM.

        Args:
            text: Input text to analyze
            domain: Domain name for context
            existing_concepts: Optional list of concepts from pattern extraction

        Returns:
            List of extracted concepts
        """
        system_prompt = f"""You are an expert at extracting key concepts from {domain} text.
Extract all important concepts, including:
- Explicit concepts mentioned in the text
- Implicit concepts that are implied
- Synonyms and variations of concepts
- Abbreviations and their full forms

Return a JSON array of concepts with this format:
[
  {{
    "text": "concept name",
    "type": "concept type (e.g., symptom, disease, treatment, strategy, metric)",
    "confidence": 0.0-1.0,
    "context": "relevant context from text"
  }}
]

Only return valid JSON, no other text."""

        user_prompt = f"""Extract all key concepts from this {domain} text:

{text[:3000]}"""  # Limit text length for API

        if existing_concepts:
            existing_text = ", ".join([c.text for c in existing_concepts[:10]])
            user_prompt += f"\n\nNote: These concepts were already found: {existing_text}. Add any additional concepts not in this list."

        try:
            response = self._call_ollama(user_prompt, system_prompt)
            
            # Parse JSON response
            # Sometimes model returns markdown code blocks
            response = response.strip()
            if response.startswith("```"):
                # Extract JSON from code block
                lines = response.split("\n")
                json_lines = [l for l in lines if not l.startswith("```")]
                response = "\n".join(json_lines)
            elif response.startswith("```json"):
                lines = response.split("\n")
                json_lines = [l for l in lines[1:] if not l.startswith("```")]
                response = "\n".join(json_lines)

            concepts_data = json.loads(response)
            
            # Convert to Concept objects
            concepts = []
            for item in concepts_data:
                if isinstance(item, dict):
                    # Find position in original text
                    text_lower = text.lower()
                    concept_text_lower = item.get("text", "").lower()
                    position = text_lower.find(concept_text_lower)
                    if position == -1:
                        position = 0
                    
                    # Get context
                    context_start = max(0, position - 50)
                    context_end = min(len(text), position + len(item.get("text", "")) + 50)
                    context = text[context_start:context_end]
                    
                    concepts.append(
                        Concept(
                            text=item.get("text", ""),
                            type=item.get("type", "unknown"),
                            confidence=float(item.get("confidence", 0.7)),
                            context=context,
                            position=position,
                        )
                    )

            return concepts

        except Exception as e:
            logger.warning(f"LLM concept extraction failed: {e}, falling back to pattern extraction")
            return existing_concepts or []

    def infer_relationships(
        self,
        concepts: List[Concept],
        text: str,
        domain: str,
        existing_relationships: Optional[List[Relationship]] = None,
    ) -> List[Relationship]:
        """Infer relationships using LLM.

        Args:
            concepts: List of concepts
            text: Original text
            domain: Domain name for context
            existing_relationships: Optional list of relationships from pattern matching

        Returns:
            List of inferred relationships
        """
        if not concepts or len(concepts) < 2:
            return existing_relationships or []

        system_prompt = f"""You are an expert at identifying relationships between concepts in {domain} text.
Identify relationships including:
- Explicit relationships stated in the text
- Implicit relationships that can be inferred from context
- Causal relationships (causes, leads_to, results_in)
- Treatment relationships (treats, manages, alleviates)
- Requirement relationships (requires, needs, depends_on)
- General relationships (relates_to, associated_with)

Return a JSON array of relationships with this format:
[
  {{
    "source": "source concept text",
    "target": "target concept text",
    "type": "relationship type",
    "confidence": 0.0-1.0,
    "evidence": "text evidence supporting this relationship"
  }}
]

Only return valid JSON, no other text."""

        # Create concept list for prompt
        concept_list = [f"- {c.text} ({c.type})" for c in concepts[:20]]  # Limit for prompt size
        concepts_text = "\n".join(concept_list)

        user_prompt = f"""Given these concepts from {domain} text:
{concepts_text}

And the original text:
{text[:2000]}

Identify all relationships between these concepts. Include both explicit and implicit relationships.

Return relationships as JSON array."""

        try:
            response = self._call_ollama(user_prompt, system_prompt)
            
            # Parse JSON response
            response = response.strip()
            if response.startswith("```"):
                lines = response.split("\n")
                json_lines = [l for l in lines if not l.startswith("```")]
                response = "\n".join(json_lines)

            relationships_data = json.loads(response)
            
            # Convert to Relationship objects
            relationships = []
            concept_map = {c.text.lower(): c for c in concepts}
            
            for item in relationships_data:
                if isinstance(item, dict):
                    source_text = item.get("source", "")
                    target_text = item.get("target", "")
                    
                    source_concept = concept_map.get(source_text.lower())
                    target_concept = concept_map.get(target_text.lower())
                    
                    # Try fuzzy matching if exact match fails
                    if not source_concept:
                        for c in concepts:
                            if c.text.lower() in source_text.lower() or source_text.lower() in c.text.lower():
                                source_concept = c
                                break
                    
                    if not target_concept:
                        for c in concepts:
                            if c.text.lower() in target_text.lower() or target_text.lower() in c.text.lower():
                                target_concept = c
                                break
                    
                    if source_concept and target_concept and source_concept != target_concept:
                        relationships.append(
                            Relationship(
                                source=source_concept,
                                target=target_concept,
                                type=item.get("type", "relates_to"),
                                confidence=float(item.get("confidence", 0.7)),
                                evidence=item.get("evidence", ""),
                            )
                        )

            # Merge with existing relationships, removing duplicates
            if existing_relationships:
                existing_set = {
                    (r.source.text.lower(), r.target.text.lower(), r.type)
                    for r in existing_relationships
                }
                new_relationships = [
                    r
                    for r in relationships
                    if (r.source.text.lower(), r.target.text.lower(), r.type) not in existing_set
                ]
                relationships = existing_relationships + new_relationships

            return relationships

        except Exception as e:
            logger.warning(f"LLM relationship inference failed: {e}, using existing relationships")
            return existing_relationships or []

    def enhance_reasoning_chain(
        self, concepts: List[Concept], relationships: List[Relationship], text: str, domain: str
    ) -> Dict:
        """Enhance reasoning chains using LLM.

        Args:
            concepts: List of concepts
            relationships: List of relationships
            text: Original text
            domain: Domain name for context

        Returns:
            Dictionary with enhanced reasoning chain information
        """
        # This can be used to improve rationale generation
        # For now, return empty dict as enhancement can happen in chain builder
        return {}
