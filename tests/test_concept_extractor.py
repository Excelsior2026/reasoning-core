"""Tests for concept extraction."""

import pytest
from reasoning_core.extractors.concept_extractor import ConceptExtractor, Concept
from reasoning_core.plugins.medical_domain import MedicalDomain
from reasoning_core.plugins.business_domain import BusinessDomain


class TestConceptExtractor:
    """Test concept extraction functionality."""

    def test_generic_extraction(self, sample_generic_text):
        """Test generic concept extraction without domain."""
        extractor = ConceptExtractor()
        concepts = extractor.extract(sample_generic_text)

        assert len(concepts) > 0
        assert all(isinstance(c, Concept) for c in concepts)
        # Should extract capitalized phrases
        concept_texts = [c.text for c in concepts]
        assert any("Theory" in text or "Relativity" in text for text in concept_texts)

    def test_medical_extraction(self, sample_medical_text, medical_domain):
        """Test medical concept extraction."""
        extractor = ConceptExtractor(domain=medical_domain)
        concepts = extractor.extract(sample_medical_text)

        assert len(concepts) > 0

        # Check for medical concepts
        concept_texts = [c.text.lower() for c in concepts]
        assert any("pain" in text for text in concept_texts)
        assert any("ecg" in text for text in concept_texts)

        # Check concept types
        concept_types = [c.type for c in concepts]
        assert "symptoms" in concept_types or "tests" in concept_types

    def test_business_extraction(self, sample_business_text, business_domain):
        """Test business concept extraction."""
        extractor = ConceptExtractor(domain=business_domain)
        concepts = extractor.extract(sample_business_text)

        assert len(concepts) > 0

        # Check for business concepts
        concept_texts = [c.text.lower() for c in concepts]
        assert any("roi" in text or "nps" in text for text in concept_texts)

        # Check concept types
        concept_types = [c.type for c in concepts]
        assert "metrics" in concept_types or "strategies" in concept_types or "pain_points" in concept_types

    def test_confidence_scoring(self, sample_medical_text, medical_domain):
        """Test that concepts have confidence scores."""
        extractor = ConceptExtractor(domain=medical_domain)
        concepts = extractor.extract(sample_medical_text)

        assert all(0 <= c.confidence <= 1 for c in concepts)
        assert all(c.confidence > 0 for c in concepts)

    def test_context_extraction(self, sample_medical_text, medical_domain):
        """Test that context is captured for concepts."""
        extractor = ConceptExtractor(domain=medical_domain)
        concepts = extractor.extract(sample_medical_text)

        assert all(c.context for c in concepts)
        assert all(len(c.context) > 0 for c in concepts)

    def test_position_tracking(self, sample_medical_text, medical_domain):
        """Test that concept positions are tracked."""
        extractor = ConceptExtractor(domain=medical_domain)
        concepts = extractor.extract(sample_medical_text)

        assert all(c.position >= 0 for c in concepts)

    def test_empty_text(self, medical_domain):
        """Test extraction with empty text."""
        extractor = ConceptExtractor(domain=medical_domain)
        concepts = extractor.extract("")

        assert concepts == []

    def test_no_domain(self):
        """Test extraction without domain plugin."""
        extractor = ConceptExtractor()
        concepts = extractor.extract("The Patient has Fever and Cough.")

        # Should still extract using generic method
        assert len(concepts) > 0
