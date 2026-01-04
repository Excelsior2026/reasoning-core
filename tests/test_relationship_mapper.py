"""Tests for relationship mapping."""

import pytest
from reasoning_core.extractors.relationship_mapper import RelationshipMapper, Relationship
from reasoning_core.plugins.medical_domain import MedicalDomain
from reasoning_core.plugins.business_domain import BusinessDomain


class TestRelationshipMapper:
    """Test relationship mapping functionality."""

    def test_generic_relationship_detection(self, sample_concepts, sample_generic_text):
        """Test generic relationship detection."""
        mapper = RelationshipMapper()
        relationships = mapper.map_relationships(sample_concepts, sample_generic_text)

        assert isinstance(relationships, list)
        assert all(isinstance(r, Relationship) for r in relationships)

    def test_medical_relationships(self, sample_concepts, sample_medical_text, medical_domain):
        """Test medical-specific relationship mapping."""
        mapper = RelationshipMapper(domain=medical_domain)
        relationships = mapper.map_relationships(sample_concepts, sample_medical_text)

        assert len(relationships) > 0

        # Check relationship types
        rel_types = [r.type for r in relationships]
        # Should have medical-specific relationships
        assert any(rt in ["indicates", "treats", "diagnosed_by", "confirms"] for rt in rel_types)

    def test_business_relationships(self, business_domain):
        """Test business-specific relationship mapping."""
        from reasoning_core.extractors.concept_extractor import Concept

        concepts = [
            Concept(text="inefficiency", type="pain_points", confidence=0.8, context="main pain point", position=10),
            Concept(text="upselling", type="strategies", confidence=0.8, context="upselling strategy", position=50),
            Concept(text="ROI", type="metrics", confidence=0.9, context="improve ROI", position=90),
        ]

        mapper = RelationshipMapper(domain=business_domain)
        relationships = mapper.map_relationships(concepts, "pain point addressed by strategy measured by ROI")

        assert len(relationships) > 0

        # Check for business relationship types
        rel_types = [r.type for r in relationships]
        assert any(rt in ["addressed_by", "measured_by", "impacts"] for rt in rel_types)

    def test_confidence_scoring(self, sample_concepts, sample_medical_text, medical_domain):
        """Test that relationships have confidence scores."""
        mapper = RelationshipMapper(domain=medical_domain)
        relationships = mapper.map_relationships(sample_concepts, sample_medical_text)

        assert all(0 <= r.confidence <= 1 for r in relationships)

    def test_evidence_extraction(self, sample_concepts, sample_medical_text, medical_domain):
        """Test that evidence is extracted for relationships."""
        mapper = RelationshipMapper(domain=medical_domain)
        relationships = mapper.map_relationships(sample_concepts, sample_medical_text)

        assert all(r.evidence for r in relationships)
        assert all(isinstance(r.evidence, str) for r in relationships)

    def test_empty_concepts(self, sample_medical_text, medical_domain):
        """Test with empty concept list."""
        mapper = RelationshipMapper(domain=medical_domain)
        relationships = mapper.map_relationships([], sample_medical_text)

        assert relationships == []

    def test_single_concept(self, medical_domain):
        """Test with only one concept."""
        from reasoning_core.extractors.concept_extractor import Concept

        concepts = [Concept(text="fever", type="symptom", confidence=0.9, context="has fever", position=10)]
        mapper = RelationshipMapper(domain=medical_domain)
        relationships = mapper.map_relationships(concepts, "patient has fever")

        assert relationships == []
