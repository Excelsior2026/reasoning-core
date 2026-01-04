"""Integration tests for full reasoning extraction pipeline."""

import pytest
from reasoning_core.api.reasoning_api import ReasoningAPI
from reasoning_core.plugins.medical_domain import MedicalDomain
from reasoning_core.plugins.business_domain import BusinessDomain


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_medical_diagnostic_workflow(self):
        """Test complete medical diagnostic reasoning extraction."""
        text = """
        A 65-year-old male presents to the emergency department with acute onset 
        chest pain radiating to the left arm, accompanied by dyspnea and diaphoresis.
        Vital signs show tachycardia and hypertension.
        ECG reveals ST-segment elevation in leads II, III, and aVF.
        Troponin levels are significantly elevated at 5.2 ng/mL.
        Diagnosis: Acute inferior wall myocardial infarction.
        Immediate treatment initiated with aspirin 325mg, clopidogrel, 
        unfractionated heparin, and prepared for emergent cardiac catheterization.
        """

        api = ReasoningAPI(domain=MedicalDomain())
        result = api.process_text(text)

        # Verify all components extracted
        assert len(result["concepts"]) >= 5, "Should extract multiple medical concepts"
        assert len(result["relationships"]) > 0, "Should identify relationships"
        assert len(result["reasoning_chains"]) > 0, "Should build reasoning chains"
        assert result["knowledge_graph"]["nodes"], "Should create knowledge graph"
        assert len(result["questions"]) > 0, "Should generate questions"

        # Verify medical-specific extraction
        concept_types = [c["type"] for c in result["concepts"]]
        assert any(t in ["symptoms", "tests", "diseases", "treatments"] for t in concept_types)

    def test_business_sales_workflow(self):
        """Test complete business sales reasoning extraction."""
        text = """
        The prospect's primary pain point is inefficiency in their current 
        lead qualification process, resulting in a low conversion rate of 12%.
        Our solution addresses this through automated lead scoring using 
        the MEDDIC framework, improving their sales team's productivity.
        Expected outcomes include a 40% increase in conversion rate and 
        improved ROI on marketing spend. We'll track success through 
        metrics including CAC, LTV, and pipeline velocity.
        """

        api = ReasoningAPI(domain=BusinessDomain())
        result = api.process_text(text)

        # Verify extraction
        assert len(result["concepts"]) >= 3, "Should extract business concepts"
        assert len(result["relationships"]) > 0, "Should identify relationships"

        # Verify business-specific extraction
        concept_types = [c["type"] for c in result["concepts"]]
        assert any(t in ["pain_points", "strategies", "metrics", "frameworks"] for t in concept_types)

    def test_cross_domain_processing(self):
        """Test processing different domains with same API instance."""
        api = ReasoningAPI()

        # Medical text
        medical_text = "Patient has fever and cough. Diagnosis: pneumonia. Treatment: antibiotics."
        api.set_domain(MedicalDomain())
        medical_result = api.process_text(medical_text)

        # Business text
        business_text = "Customer pain: high costs. Strategy: upselling. Metric: ROI improvement."
        api.set_domain(BusinessDomain())
        business_result = api.process_text(business_text)

        # Both should produce results
        assert len(medical_result["concepts"]) > 0
        assert len(business_result["concepts"]) > 0

        # Results should be different
        assert medical_result["concepts"] != business_result["concepts"]

    def test_knowledge_graph_construction(self):
        """Test that knowledge graphs are properly constructed."""
        text = "Symptom: chest pain. Test: ECG shows abnormality. Diagnosis: MI. Treatment: aspirin."

        api = ReasoningAPI(domain=MedicalDomain())
        result = api.process_text(text, include_graph=True)

        graph = result["knowledge_graph"]
        assert len(graph["nodes"]) > 0
        assert len(graph["edges"]) > 0

        # Verify graph structure
        assert all("id" in node for node in graph["nodes"])
        assert all("source_id" in edge and "target_id" in edge for edge in graph["edges"])

    def test_question_generation_quality(self):
        """Test quality of generated questions."""
        text = "Hypertension is treated with ACE inhibitors and beta blockers."

        api = ReasoningAPI(domain=MedicalDomain())
        result = api.process_text(text)

        questions = result.get("questions", [])
        if questions:
            # Questions should be complete sentences
            assert all("?" in q for q in questions)
            # Questions should reference extracted concepts
            assert any("hypertension" in q.lower() for q in questions)
