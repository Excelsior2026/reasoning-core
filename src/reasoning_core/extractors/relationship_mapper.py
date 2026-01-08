"""Map relationships between concepts."""

from typing import List, Dict, Tuple, Optional, TYPE_CHECKING
from dataclasses import dataclass
from reasoning_core.extractors.concept_extractor import Concept

if TYPE_CHECKING:
    from reasoning_core.plugins.base_domain import BaseDomain


@dataclass
class Relationship:
    """Represents a relationship between concepts."""

    source: Concept
    target: Concept
    type: str  # e.g., "causes", "treats", "leads_to", "requires"
    confidence: float
    evidence: str  # Text supporting this relationship


class RelationshipMapper:
    """Map relationships between extracted concepts."""

    def __init__(self, domain: Optional["BaseDomain"] = None):
        """Initialize relationship mapper.

        Args:
            domain: Domain plugin for domain-specific relationships
        """
        self.domain = domain

    def map_relationships(
        self, concepts: List[Concept], text: str, domain_hints: Optional[Dict] = None
    ) -> List[Relationship]:
        """Identify relationships between concepts.

        Args:
            concepts: List of extracted concepts
            text: Original text for context
            domain_hints: Optional domain-specific hints (currently unused)

        Returns:
            List of relationships

        Raises:
            TypeError: If concepts is not a list or text is not a string
            ValueError: If text is empty
        """
        if not isinstance(concepts, list):
            raise TypeError(f"concepts must be a list, got {type(concepts)}")
        if not isinstance(text, str):
            raise TypeError(f"text must be a string, got {type(text)}")

        relationships: List[Relationship] = []

        if not concepts:
            return relationships  # Return empty list if no concepts

        try:
            # Use domain-specific relationship mapping if available
            if self.domain:
                domain_relationships = self.domain.identify_relationships(concepts, text)
                if domain_relationships:
                    relationships.extend(domain_relationships)
        except Exception:
            # If domain mapping fails, fall back to generic detection
            relationships = []

        # Generic relationship detection (fallback if no domain or domain mapping failed)
        if not relationships:
            relationships = self._generic_relationship_detection(concepts, text)

        return relationships

    def _generic_relationship_detection(
        self, concepts: List[Concept], text: str
    ) -> List[Relationship]:
        """Generic relationship detection using patterns.

        Args:
            concepts: List of concepts
            text: Original text

        Returns:
            List of relationships
        """
        relationships = []

        # Common relationship indicators
        causal_indicators = ["causes", "leads to", "results in", "triggers"]
        treatment_indicators = ["treats", "cures", "alleviates", "manages"]
        requirement_indicators = ["requires", "needs", "depends on"]

        # Check for relationships between concept pairs
        for i, source in enumerate(concepts):
            for target in concepts[i + 1 :]:
                # Check if concepts appear near each other
                if self._concepts_are_related(source, target, text):
                    rel_type = self._determine_relationship_type(
                        source, target, text, causal_indicators, treatment_indicators, requirement_indicators
                    )
                    if rel_type:
                        relationships.append(
                            Relationship(
                                source=source,
                                target=target,
                                type=rel_type,
                                confidence=0.6,
                                evidence=self._get_evidence(source, target, text),
                            )
                        )

        return relationships

    def _concepts_are_related(self, concept1: Concept, concept2: Concept, text: str, max_distance: int = 100) -> bool:
        """Check if two concepts are related based on proximity.

        Args:
            concept1: First concept
            concept2: Second concept
            text: Original text
            max_distance: Maximum character distance

        Returns:
            True if concepts are likely related
        """
        distance = abs(concept1.position - concept2.position)
        return distance <= max_distance

    def _determine_relationship_type(
        self,
        source: Concept,
        target: Concept,
        text: str,
        causal_indicators: List[str],
        treatment_indicators: List[str],
        requirement_indicators: List[str],
    ) -> Optional[str]:
        """Determine the type of relationship between concepts.

        Args:
            source: Source concept
            target: Target concept
            text: Original text
            causal_indicators: List of causal relationship words
            treatment_indicators: List of treatment relationship words
            requirement_indicators: List of requirement relationship words

        Returns:
            Relationship type or None
        """
        # Get text between concepts
        start = min(source.position, target.position)
        end = max(source.position + len(source.text), target.position + len(target.text))
        between_text = text[start:end].lower()

        # Check for relationship indicators
        for indicator in causal_indicators:
            if indicator in between_text:
                return "causes"

        for indicator in treatment_indicators:
            if indicator in between_text:
                return "treats"

        for indicator in requirement_indicators:
            if indicator in between_text:
                return "requires"

        # Default relationship
        return "relates_to"

    def _get_evidence(self, source: Concept, target: Concept, text: str) -> str:
        """Extract evidence text supporting the relationship.

        Args:
            source: Source concept
            target: Target concept
            text: Original text

        Returns:
            Evidence text
        """
        start = min(source.position, target.position)
        end = max(source.position + len(source.text), target.position + len(target.text))
        return text[max(0, start - 20) : min(len(text), end + 20)]
