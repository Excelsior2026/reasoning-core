"""Base domain interface for reasoning extraction.

All domain plugins must implement this interface.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class Concept:
    """Represents a domain concept."""
    
    name: str
    type: str  # e.g., "disease", "symptom", "treatment", "strategy", etc.
    context: str
    confidence: float = 1.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Relationship:
    """Represents a relationship between concepts."""
    
    source: Concept
    target: Concept
    relationship_type: str  # e.g., "causes", "treats", "requires", etc.
    strength: float = 1.0
    bidirectional: bool = False
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ReasoningPattern:
    """Represents a domain-specific reasoning pattern."""
    
    name: str
    description: str
    steps: List[str]
    example: Optional[str] = None


class BaseDomain(ABC):
    """Abstract base class for domain-specific reasoning.
    
    Each domain (medical, business, legal, etc.) implements this interface
    to provide domain-specific reasoning extraction capabilities.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize domain with optional configuration."""
        self.config = config or {}
        self.terminology = self.get_terminology_mapping()
        self.patterns = self.get_reasoning_patterns()
    
    @abstractmethod
    def get_domain_name(self) -> str:
        """Return the domain name (e.g., 'medical', 'business')."""
        pass
    
    @abstractmethod
    def extract_concepts(self, text: str) -> List[Concept]:
        """Extract domain-specific concepts from text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of extracted concepts with metadata
        """
        pass
    
    @abstractmethod
    def identify_relationships(self, concepts: List[Concept]) -> List[Relationship]:
        """Identify relationships between concepts.
        
        Args:
            concepts: List of concepts to analyze
            
        Returns:
            List of relationships between concepts
        """
        pass
    
    @abstractmethod
    def build_reasoning_chains(
        self,
        concepts: List[Concept],
        relationships: List[Relationship]
    ) -> List[Dict[str, Any]]:
        """Build domain-specific reasoning chains.
        
        Args:
            concepts: Extracted concepts
            relationships: Identified relationships
            
        Returns:
            List of reasoning chains (ordered concept sequences)
        """
        pass
    
    @abstractmethod
    def generate_questions(
        self,
        concepts: List[Concept],
        chains: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate domain-appropriate questions.
        
        Args:
            concepts: Extracted concepts
            chains: Reasoning chains
            
        Returns:
            List of generated questions
        """
        pass
    
    @abstractmethod
    def get_terminology_mapping(self) -> Dict[str, List[str]]:
        """Return domain-specific terminology.
        
        Returns:
            Dictionary mapping concept types to terms
        """
        pass
    
    @abstractmethod
    def get_reasoning_patterns(self) -> List[ReasoningPattern]:
        """Return domain-specific reasoning patterns.
        
        Returns:
            List of reasoning patterns for this domain
        """
        pass
    
    def validate_concept(self, concept: Concept) -> bool:
        """Validate if a concept belongs to this domain.
        
        Args:
            concept: Concept to validate
            
        Returns:
            True if concept is valid for this domain
        """
        return concept.type in self.terminology
    
    def get_concept_type_priority(self) -> List[str]:
        """Return priority order for concept types.
        
        Used for organizing and presenting concepts.
        
        Returns:
            Ordered list of concept types by priority
        """
        return list(self.terminology.keys())
