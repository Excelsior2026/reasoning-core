"""Tests for business domain plugin."""

import pytest
from reasoning_core.plugins.business_domain import BusinessDomain


class TestBusinessDomain:
    """Test business domain functionality."""

    def test_domain_name(self, business_domain):
        """Test domain name retrieval."""
        assert business_domain.get_name() == "business"

    def test_terminology_mapping(self, business_domain):
        """Test business terminology mapping."""
        terminology = business_domain.get_terminology_mapping()

        assert "strategies" in terminology
        assert "metrics" in terminology
        assert "frameworks" in terminology
        assert "pain_points" in terminology

        # Check some specific terms
        assert "ROI" in terminology["metrics"]
        assert "upselling" in terminology["strategies"]

    def test_reasoning_patterns(self, business_domain):
        """Test business reasoning patterns."""
        patterns = business_domain.get_reasoning_patterns()

        assert len(patterns) > 0
        assert "problem_to_solution" in patterns
        assert "pain_to_value" in patterns

    def test_concept_extraction(self, sample_business_text, business_domain):
        """Test business concept extraction."""
        concepts = business_domain.extract_concepts(sample_business_text)

        assert len(concepts) > 0
        concept_types = {c.type for c in concepts}
        # Should extract business-specific types
        assert len(concept_types.intersection({"strategies", "metrics", "pain_points"})) > 0

    def test_question_generation(self, business_domain):
        """Test business question generation."""
        content = {"strategies": ["upselling", "cross-selling"]}

        questions = business_domain.generate_questions(content)

        assert len(questions) > 0
        assert any("upselling" in q for q in questions)
        assert any("when" in q.lower() or "metrics" in q.lower() for q in questions)
