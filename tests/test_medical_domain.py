"""Tests for medical domain plugin."""

import pytest
from reasoning_core.plugins.medical_domain import MedicalDomain


class TestMedicalDomain:
    """Test medical domain functionality."""

    def test_domain_name(self, medical_domain):
        """Test domain name retrieval."""
        assert medical_domain.get_name() == "medical"

    def test_terminology_mapping(self, medical_domain):
        """Test medical terminology mapping."""
        terminology = medical_domain.get_terminology_mapping()

        assert "symptoms" in terminology
        assert "diseases" in terminology
        assert "treatments" in terminology
        assert "tests" in terminology

        # Check some specific terms
        assert "pain" in terminology["symptoms"]
        assert "aspirin" in terminology["treatments"]

    def test_reasoning_patterns(self, medical_domain):
        """Test medical reasoning patterns."""
        patterns = medical_domain.get_reasoning_patterns()

        assert len(patterns) > 0
        assert "symptom_to_differential" in patterns
        assert "diagnosis_to_treatment" in patterns

    def test_concept_extraction(self, sample_medical_text, medical_domain):
        """Test medical concept extraction."""
        concepts = medical_domain.extract_concepts(sample_medical_text)

        assert len(concepts) > 0
        concept_types = {c.type for c in concepts}
        # Should extract medical-specific types
        assert len(concept_types.intersection({"symptoms", "diseases", "treatments", "tests"})) > 0

    def test_relationship_identification(self, medical_domain):
        """Test medical relationship identification."""
        from reasoning_core.extractors.concept_extractor import Concept

        concepts = [
            Concept(text="fever", type="symptoms", confidence=0.9, context="has fever", position=0),
            Concept(text="infection", type="diseases", confidence=0.9, context="diagnosed infection", position=20),
        ]

        text = "Patient has fever which indicates infection"
        relationships = medical_domain.identify_relationships(concepts, text)

        assert len(relationships) > 0
        assert any(r.type == "indicates" for r in relationships)

    def test_question_generation(self, medical_domain):
        """Test medical question generation."""
        content = {"diseases": ["pneumonia", "COPD"]}

        questions = medical_domain.generate_questions(content)

        assert len(questions) > 0
        assert any("pneumonia" in q for q in questions)
        assert any("symptoms" in q.lower() or "treatment" in q.lower() for q in questions)
