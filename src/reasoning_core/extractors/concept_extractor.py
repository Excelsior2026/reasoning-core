"""Extract domain-specific concepts from text."""

from typing import List, Dict, Optional, TYPE_CHECKING
import re
from dataclasses import dataclass

if TYPE_CHECKING:
    from reasoning_core.plugins.base_domain import BaseDomain


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

    def __init__(self, domain: Optional["BaseDomain"] = None):
        """Initialize concept extractor.

        Args:
            domain: Domain plugin for domain-specific extraction
        """
        self.domain = domain

    def extract(self, text: str, domain_hints: Optional[Dict] = None) -> List[Concept]:
        """Extract concepts from text.

        Args:
            text: Input text to analyze
            domain_hints: Optional domain-specific hints (currently unused)

        Returns:
            List of extracted concepts

        Raises:
            TypeError: If text is not a string
            ValueError: If text is empty
        """
        if not isinstance(text, str):
            raise TypeError(f"text must be a string, got {type(text)}")
        if not text.strip():
            return []  # Return empty list for empty text

        concepts: List[Concept] = []

        try:
            # Use domain-specific extraction if available
            if self.domain:
                domain_concepts = self.domain.extract_concepts(text)
                if domain_concepts:
                    concepts.extend(domain_concepts)
        except Exception:
            # If domain extraction fails, fall back to generic extraction
            concepts = []

        # Generic extraction (fallback if no domain or domain extraction failed)
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

    def extract_with_llm(self, text: str, llm_service: Optional[object] = None) -> List[Concept]:
        """Extract concepts using LLM (not yet implemented).

        This method is a placeholder for future LLM-based extraction.
        Currently falls back to standard extraction.

        Args:
            text: Input text
            llm_service: LLM service for extraction (not yet used)

        Returns:
            List of extracted concepts (using standard extraction for now)

        Note:
            This method will be implemented in a future release to integrate
            with Ollama or other LLM services for enhanced concept extraction.
        """
        # TODO: Implement LLM-based extraction
        # This will integrate with Ollama or other LLM services
        # For now, use standard extraction
        return self.extract(text)
