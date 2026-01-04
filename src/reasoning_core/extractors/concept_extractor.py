"""Extract domain-specific concepts from text."""

from typing import List, Dict, Optional
import re
from dataclasses import dataclass


@dataclass
class Concept:
    """Represents an extracted concept."""

    text: str
    type: str  # e.g., "symptom", "disease", "treatment", "strategy", "metric"
    confidence: float
    context: str  # Surrounding text
    position: int  # Character position in text


class ConceptExtractor:
    """Extract concepts from text using domain-specific patterns."""

    def __init__(self, domain=None):
        """Initialize concept extractor.

        Args:
            domain: Domain plugin for domain-specific extraction
        """
        self.domain = domain

    def extract(self, text: str, domain_hints: Optional[Dict] = None) -> List[Concept]:
        """Extract concepts from text.

        Args:
            text: Input text to analyze
            domain_hints: Optional domain-specific hints

        Returns:
            List of extracted concepts
        """
        concepts = []

        # Use domain-specific extraction if available
        if self.domain:
            domain_concepts = self.domain.extract_concepts(text)
            concepts.extend(domain_concepts)

        # Generic extraction (fallback)
        if not concepts:
            concepts = self._generic_extraction(text)

        return concepts

    def _generic_extraction(self, text: str) -> List[Concept]:
        """Generic concept extraction using basic NLP.

        Args:
            text: Input text

        Returns:
            List of concepts
        """
        concepts = []

        # Extract capitalized phrases (potential concepts)
        pattern = r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b"
        matches = re.finditer(pattern, text)

        for match in matches:
            concept_text = match.group()
            # Skip common words
            if concept_text.lower() not in {"the", "a", "an", "this", "that"}:
                concepts.append(
                    Concept(
                        text=concept_text,
                        type="unknown",
                        confidence=0.5,
                        context=self._get_context(text, match.start(), match.end()),
                        position=match.start(),
                    )
                )

        return concepts

    def _get_context(self, text: str, start: int, end: int, window: int = 50) -> str:
        """Get surrounding context for a concept.

        Args:
            text: Full text
            start: Start position of concept
            end: End position of concept
            window: Context window size

        Returns:
            Context string
        """
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end]

    def extract_with_llm(self, text: str, llm_service) -> List[Concept]:
        """Extract concepts using LLM.

        Args:
            text: Input text
            llm_service: LLM service for extraction

        Returns:
            List of extracted concepts
        """
        # Placeholder for LLM-based extraction
        # This would integrate with Ollama or other LLM services
        prompt = f"""
Extract key concepts from the following text. For each concept, identify:
- The concept text
- Its type (e.g., symptom, disease, strategy, metric)
- Context

Text:
{text}

Respond in JSON format.
"""
        # TODO: Implement LLM call
        return self.extract(text)
