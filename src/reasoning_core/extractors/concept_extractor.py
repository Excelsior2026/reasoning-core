"""Extract domain-specific concepts from text."""

from typing import List, Dict, Optional, TYPE_CHECKING
import re
import logging
from dataclasses import dataclass

if TYPE_CHECKING:
    from reasoning_core.plugins.base_domain import BaseDomain
    from reasoning_core.llm.base import LLMService

logger = logging.getLogger(__name__)


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

    def __init__(
        self,
        domain: Optional["BaseDomain"] = None,
        llm_service: Optional["LLMService"] = None,
        use_llm: bool = False,
    ):
        """Initialize concept extractor.

        Args:
            domain: Domain plugin for domain-specific extraction
            llm_service: Optional LLM service for enhanced extraction
            use_llm: Whether to use LLM enhancement (default: False)
        """
        self.domain = domain
        self.llm_service = llm_service
        self.use_llm = use_llm and llm_service is not None

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

        # LLM enhancement (hybrid approach)
        if self.use_llm and self.llm_service and self.llm_service.is_available():
            try:
                domain_name = self.domain.get_name() if self.domain else "generic"
                llm_concepts = self.llm_service.extract_concepts(text, domain_name, concepts)
                
                if llm_concepts:
                    # Merge and deduplicate concepts
                    concepts = self._merge_concepts(concepts, llm_concepts)
                    
            except Exception as e:
                logger.warning(f"LLM enhancement failed: {e}, using pattern-based results only")

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

    def _merge_concepts(self, pattern_concepts: List[Concept], llm_concepts: List[Concept]) -> List[Concept]:
        """Merge pattern-based and LLM concepts, removing duplicates.

        Args:
            pattern_concepts: Concepts from pattern extraction
            llm_concepts: Concepts from LLM extraction

        Returns:
            Merged list of unique concepts
        """
        # Create a set of existing concept keys (text, type, position)
        existing_keys = {
            (c.text.lower(), c.type, c.position)
            for c in pattern_concepts
        }
        
        merged = list(pattern_concepts)
        
        # Add LLM concepts that aren't duplicates
        for llm_concept in llm_concepts:
            key = (llm_concept.text.lower(), llm_concept.type, llm_concept.position)
            
            # Check for near-duplicates (similar text)
            is_duplicate = False
            for existing in merged:
                if (llm_concept.text.lower() == existing.text.lower() and 
                    llm_concept.type == existing.type):
                    # Update confidence if LLM is higher
                    if llm_concept.confidence > existing.confidence:
                        existing.confidence = llm_concept.confidence
                        existing.context = llm_concept.context
                    is_duplicate = True
                    break
                
                # Fuzzy match for similar concepts
                if (llm_concept.text.lower() in existing.text.lower() or 
                    existing.text.lower() in llm_concept.text.lower()):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                merged.append(llm_concept)
        
        return merged

    def extract_with_llm(self, text: str, llm_service: Optional["LLMService"] = None) -> List[Concept]:
        """Extract concepts using LLM.

        Args:
            text: Input text
            llm_service: LLM service for extraction

        Returns:
            List of extracted concepts
        """
        if llm_service and llm_service.is_available():
            old_llm = self.llm_service
            old_use_llm = self.use_llm
            self.llm_service = llm_service
            self.use_llm = True
            try:
                result = self.extract(text)
            finally:
                self.llm_service = old_llm
                self.use_llm = old_use_llm
            return result
        return self.extract(text)
