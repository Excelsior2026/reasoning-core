"""Tests for the high-level reasoning API."""

import pytest
from reasoning_core.api.reasoning_api import ReasoningAPI
from reasoning_core.plugins.medical_domain import MedicalDomain
from reasoning_core.plugins.business_domain import BusinessDomain


class TestReasoningAPI:
    """Test the high-level reasoning API."""

    def test_api_initialization(self):
        """Test API initialization."""
        api = ReasoningAPI()
        assert api is not None
        assert api.domain is None

        # With domain
        api_with_domain = ReasoningAPI(domain=MedicalDomain())
        assert api_with_domain.domain is not None

    def test_process_medical_text(self, sample_medical_text):
        """Test processing medical text through full pipeline."""
        api = ReasoningAPI(domain=MedicalDomain())
        result = api.process_text(sample_medical_text)

        # Check structure
        assert "concepts" in result
        assert "relationships" in result
        assert "reasoning_chains" in result
        assert "knowledge_graph" in result
        assert "questions" in result

        # Check content
        assert len(result["concepts"]) > 0
        assert isinstance(result["knowledge_graph"], dict)
        assert isinstance(result["questions"], list)

    def test_process_business_text(self, sample_business_text):
        """Test processing business text through full pipeline."""
        api = ReasoningAPI(domain=BusinessDomain())
        result = api.process_text(sample_business_text)

        assert "concepts" in result
        assert len(result["concepts"]) > 0
        assert "questions" in result

    def test_process_without_graph(self, sample_medical_text):
        """Test processing without building knowledge graph."""
        api = ReasoningAPI(domain=MedicalDomain())
        result = api.process_text(sample_medical_text, include_graph=False)

        assert "concepts" in result
        assert "knowledge_graph" not in result

    def test_domain_switching(self, sample_medical_text, sample_business_text):
        """Test switching domains dynamically."""
        api = ReasoningAPI()

        # Process with medical domain
        api.set_domain(MedicalDomain())
        medical_result = api.process_text(sample_medical_text)
        assert len(medical_result["concepts"]) > 0

        # Switch to business domain
        api.set_domain(BusinessDomain())
        business_result = api.process_text(sample_business_text)
        assert len(business_result["concepts"]) > 0

    def test_get_domain_info(self):
        """Test getting domain information."""
        api = ReasoningAPI(domain=MedicalDomain())
        info = api.get_domain_info()

        assert "name" in info
        assert "patterns" in info
        assert "terminology" in info
        assert info["name"] == "medical"

    def test_generic_processing(self, sample_generic_text):
        """Test processing without domain (generic)."""
        api = ReasoningAPI()
        result = api.process_text(sample_generic_text)

        assert "concepts" in result
        assert "relationships" in result
        # No questions without domain
        assert "questions" not in result or len(result["questions"]) == 0

    def test_empty_text(self):
        """Test processing empty text."""
        api = ReasoningAPI(domain=MedicalDomain())
        result = api.process_text("")

        assert "concepts" in result
        assert len(result["concepts"]) == 0
