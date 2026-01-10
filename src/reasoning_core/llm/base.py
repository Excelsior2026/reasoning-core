"""Base LLM service interface."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from reasoning_core.extractors.concept_extractor import Concept
from reasoning_core.extractors.relationship_mapper import Relationship


class LLMService(ABC):
    """Base interface for LLM services."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if LLM service is available.
        
        Returns:
            True if service is available, False otherwise
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass
