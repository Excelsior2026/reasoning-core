"""Custom domain builder functionality."""

import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from reasoning_core.plugins.base_domain import BaseDomain
try:
    from reasoning_core.extractors.concept_extractor import Concept
except ImportError:
    # Fallback if Concept not directly importable
    from dataclasses import dataclass
    from typing import Optional
    
    @dataclass
    class Concept:
        text: str
        type: str
        confidence: float = 0.5
        context: Optional[str] = None
        position: int = 0


class CustomDomain(BaseDomain):
    """Custom domain created by user."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize custom domain from configuration.

        Args:
            config: Domain configuration dictionary
        """
        self.config = config
        self.name = config.get('name', 'custom')
        self.description = config.get('description', '')
        
        # Concept types
        self.concept_types = config.get('concept_types', [])
        
        # Patterns
        self.concept_patterns = config.get('concept_patterns', {})
        self.relationship_patterns = config.get('relationship_patterns', {})
        
        # Rules
        self.rules = config.get('rules', [])

    def get_concept_types(self) -> List[str]:
        """Get list of concept types for this domain.

        Returns:
            List of concept type strings
        """
        return self.concept_types

    def get_concept_patterns(self, concept_type: str) -> List[str]:
        """Get extraction patterns for a concept type.

        Args:
            concept_type: Type of concept

        Returns:
            List of regex patterns
        """
        return self.concept_patterns.get(concept_type, [])

    def get_relationship_patterns(self) -> List[Dict[str, Any]]:
        """Get relationship extraction patterns.

        Returns:
            List of relationship pattern dictionaries
        """
        return self.relationship_patterns

    def validate_concept(self, concept: Concept) -> bool:
        """Validate if concept belongs to this domain.

        Args:
            concept: Concept to validate

        Returns:
            True if concept is valid for this domain
        """
        return concept.type in self.concept_types

    def get_name(self) -> str:
        """Get domain name."""
        return self.name

    # Implement required BaseDomain abstract methods
    def extract_concepts(self, text: str) -> List:
        """Extract concepts using domain patterns."""
        from reasoning_core.extractors.concept_extractor import ConceptExtractor
        extractor = ConceptExtractor(domain=self)
        return extractor.extract(text)

    def identify_relationships(self, concepts: List, text: str) -> List:
        """Identify relationships using domain patterns."""
        from reasoning_core.extractors.relationship_mapper import RelationshipMapper
        mapper = RelationshipMapper(domain=self)
        return mapper.map_relationships(concepts, text)

    def build_reasoning_chains(self, concepts: List, relationships: List) -> List:
        """Build reasoning chains."""
        from reasoning_core.extractors.reasoning_chain_builder import ReasoningChainBuilder
        builder = ReasoningChainBuilder(domain=self)
        return builder.build_chains(concepts, relationships)

    def generate_questions(self, content: Dict) -> List[str]:
        """Generate questions from content."""
        # Simple question generation based on concepts
        questions = []
        concepts = content.get('concepts', [])
        
        if concepts:
            # Generate questions about key concepts
            for concept in concepts[:5]:  # Limit to first 5
                concept_text = concept.text if hasattr(concept, 'text') else concept.get('text', '')
                questions.append(f"What is the significance of {concept_text}?")
        
        return questions

    def get_terminology_mapping(self) -> Dict:
        """Get terminology mapping."""
        # Build terminology from concept patterns
        terminology = {}
        for concept_type, patterns in self.concept_patterns.items():
            # Extract terms from patterns (simplified)
            terms = []
            for pattern in patterns:
                # Try to extract literal terms from regex patterns
                # This is simplified - in practice would parse regex better
                import re
                # Remove regex anchors and special chars, keep word chars
                terms.extend(re.findall(r'\b\w+\b', pattern))
            terminology[concept_type] = list(set(terms))
        
        return terminology


class DomainBuilder:
    """Builder for creating custom domains."""

    def __init__(self, domains_dir: Optional[Path] = None):
        """Initialize domain builder.

        Args:
            domains_dir: Directory to store custom domains
        """
        if domains_dir is None:
            # Default to user's home directory
            domains_dir = Path.home() / '.reasoning-core' / 'domains'
        
        self.domains_dir = Path(domains_dir)
        self.domains_dir.mkdir(parents=True, exist_ok=True)

    def save_domain(self, config: Dict[str, Any]) -> str:
        """Save custom domain configuration.

        Args:
            config: Domain configuration

        Returns:
            Domain ID
        """
        domain_id = config.get('id') or self._generate_domain_id(config.get('name', 'custom'))
        
        # Validate configuration
        self._validate_config(config)
        
        # Save to file
        domain_file = self.domains_dir / f"{domain_id}.json"
        with open(domain_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        return domain_id

    def load_domain(self, domain_id: str) -> Optional[Dict[str, Any]]:
        """Load domain configuration.

        Args:
            domain_id: Domain identifier

        Returns:
            Domain configuration or None
        """
        domain_file = self.domains_dir / f"{domain_id}.json"
        
        if not domain_file.exists():
            return None
        
        with open(domain_file, 'r') as f:
            return json.load(f)

    def list_domains(self) -> List[Dict[str, Any]]:
        """List all custom domains.

        Returns:
            List of domain metadata
        """
        domains = []
        
        for domain_file in self.domains_dir.glob('*.json'):
            try:
                with open(domain_file, 'r') as f:
                    config = json.load(f)
                    domains.append({
                        'id': domain_file.stem,
                        'name': config.get('name', 'Unknown'),
                        'description': config.get('description', ''),
                        'concept_types': len(config.get('concept_types', [])),
                        'created_at': config.get('created_at', ''),
                        'updated_at': config.get('updated_at', ''),
                    })
            except Exception:
                continue
        
        return domains

    def delete_domain(self, domain_id: str) -> bool:
        """Delete custom domain.

        Args:
            domain_id: Domain identifier

        Returns:
            True if deleted successfully
        """
        domain_file = self.domains_dir / f"{domain_id}.json"
        
        if domain_file.exists():
            domain_file.unlink()
            return True
        
        return False

    def create_custom_domain(self, config: Dict[str, Any]) -> CustomDomain:
        """Create CustomDomain instance from configuration.

        Args:
            config: Domain configuration

        Returns:
            CustomDomain instance
        """
        return CustomDomain(config)

    def _generate_domain_id(self, name: str) -> str:
        """Generate unique domain ID from name.

        Args:
            name: Domain name

        Returns:
            Domain ID
        """
        import time
        import hashlib
        
        timestamp = str(int(time.time()))
        name_hash = hashlib.md5(name.encode()).hexdigest()[:8]
        return f"{name.lower().replace(' ', '_')}_{name_hash}_{timestamp}"

    def _validate_config(self, config: Dict[str, Any]) -> None:
        """Validate domain configuration.

        Args:
            config: Configuration to validate

        Raises:
            ValueError: If configuration is invalid
        """
        required_fields = ['name', 'concept_types']
        
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field: {field}")
        
        if not isinstance(config['concept_types'], list):
            raise ValueError("concept_types must be a list")
        
        if not config['concept_types']:
            raise ValueError("concept_types cannot be empty")
        
        # Validate concept patterns
        if 'concept_patterns' in config:
            if not isinstance(config['concept_patterns'], dict):
                raise ValueError("concept_patterns must be a dictionary")
        
        # Validate relationship patterns
        if 'relationship_patterns' in config:
            if not isinstance(config['relationship_patterns'], list):
                raise ValueError("relationship_patterns must be a list")


# Global domain builder instance
_domain_builder = None


def get_domain_builder() -> DomainBuilder:
    """Get global domain builder instance.

    Returns:
        DomainBuilder instance
    """
    global _domain_builder
    if _domain_builder is None:
        _domain_builder = DomainBuilder()
    return _domain_builder
