"""Base domain interface for reasoning extraction."""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class BaseDomain(ABC):
    """Abstract base class for domain-specific reasoning."""

    @abstractmethod
    def get_name(self) -> str:
        """Get domain name.

        Returns:
            Domain name string
        """
        pass

    @abstractmethod
    def extract_concepts(self, text: str) -> List:
        """Extract domain-specific concepts from text.

        Args:
            text: Input text to analyze

        Returns:
            List of extracted Concept objects
        """
        pass

    @abstractmethod
    def identify_relationships(self, concepts: List, text: str) -> List:
        """Identify domain-specific relationships between concepts.

        Args:
            concepts: List of Concept objects
            text: Original text for context

        Returns:
            List of Relationship objects
        """
        pass

    @abstractmethod
    def build_reasoning_chains(self, concepts: List, relationships: List) -> List:
        """Build domain-specific reasoning chains.

        Args:
            concepts: List of Concept objects
            relationships: List of Relationship objects

        Returns:
            List of ReasoningChain objects
        """
        pass

    @abstractmethod
    def generate_questions(self, content: Dict) -> List[str]:
        """Generate domain-appropriate questions from content.

        Args:
            content: Processed content dictionary

        Returns:
            List of question strings
        """
        pass

    @abstractmethod
    def get_terminology_mapping(self) -> Dict:
        """Get domain-specific terminology mapping.

        Returns:
            Dictionary mapping term types to term lists
        """
        pass

    def get_reasoning_patterns(self) -> List[str]:
        """Get common reasoning patterns for this domain.

        Returns:
            List of reasoning pattern names
        """
        return []

    def customize_extraction(self, config: Dict) -> None:
        """Customize extraction behavior.

        Args:
            config: Configuration dictionary
        """
        pass

    def validate_reasoning_chain(self, chain) -> bool:
        """Validate a reasoning chain for domain correctness.

        Args:
            chain: ReasoningChain object

        Returns:
            True if valid for this domain
        """
        return True
