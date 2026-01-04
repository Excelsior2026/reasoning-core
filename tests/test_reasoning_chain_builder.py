"""Tests for reasoning chain building."""

import pytest
from reasoning_core.extractors.reasoning_chain_builder import ReasoningChainBuilder, ReasoningChain
from reasoning_core.plugins.medical_domain import MedicalDomain
from reasoning_core.plugins.business_domain import BusinessDomain


class TestReasoningChainBuilder:
    """Test reasoning chain building functionality."""

    def test_generic_chain_building(self, sample_concepts, sample_relationships):
        """Test generic chain building."""
        builder = ReasoningChainBuilder()
        chains = builder.build_chains(sample_concepts, sample_relationships)

        assert isinstance(chains, list)
        assert all(isinstance(c, ReasoningChain) for c in chains)

    def test_medical_diagnostic_chain(self, medical_domain):
        """Test medical diagnostic chain building."""
        from reasoning_core.extractors.concept_extractor import Concept
        from reasoning_core.extractors.relationship_mapper import Relationship

        concepts = [
            Concept(text="chest pain", type="symptoms", confidence=0.9, context="has chest pain", position=0),
            Concept(text="ECG", type="tests", confidence=0.95, context="ECG ordered", position=20),
            Concept(text="MI", type="diseases", confidence=0.9, context="diagnosed MI", position=40),
            Concept(text="aspirin", type="treatments", confidence=0.85, context="given aspirin", position=60),
        ]

        relationships = [
            Relationship(source=concepts[0], target=concepts[2], type="indicates", confidence=0.8, evidence="pain indicates MI"),
            Relationship(source=concepts[1], target=concepts[2], type="confirms", confidence=0.9, evidence="ECG confirms MI"),
            Relationship(source=concepts[3], target=concepts[2], type="treats", confidence=0.85, evidence="aspirin treats MI"),
        ]

        builder = ReasoningChainBuilder(domain=medical_domain)
        chains = builder.build_chains(concepts, relationships)

        assert len(chains) > 0
        # Should have diagnostic chain
        diagnostic_chains = [c for c in chains if c.type == "diagnostic"]
        assert len(diagnostic_chains) > 0

        # Check chain structure
        chain = diagnostic_chains[0]
        assert len(chain.steps) >= 2
        assert chain.domain == "medical"

    def test_business_sales_chain(self, business_domain):
        """Test business sales chain building."""
        from reasoning_core.extractors.concept_extractor import Concept
        from reasoning_core.extractors.relationship_mapper import Relationship

        concepts = [
            Concept(text="inefficiency", type="pain_points", confidence=0.8, context="pain point", position=0),
            Concept(text="upselling", type="strategies", confidence=0.8, context="strategy", position=20),
            Concept(text="ROI", type="metrics", confidence=0.9, context="measure ROI", position=40),
        ]

        relationships = [
            Relationship(source=concepts[0], target=concepts[1], type="addressed_by", confidence=0.8, evidence="pain addressed by strategy"),
            Relationship(source=concepts[1], target=concepts[2], type="measured_by", confidence=0.85, evidence="strategy measured by ROI"),
        ]

        builder = ReasoningChainBuilder(domain=business_domain)
        chains = builder.build_chains(concepts, relationships)

        assert len(chains) > 0
        # Should have sales chain
        sales_chains = [c for c in chains if c.type == "sales"]
        assert len(sales_chains) > 0

    def test_chain_confidence(self, sample_concepts, sample_relationships, medical_domain):
        """Test that chains have confidence scores."""
        builder = ReasoningChainBuilder(domain=medical_domain)
        chains = builder.build_chains(sample_concepts, sample_relationships)

        if chains:
            assert all(0 <= c.confidence <= 1 for c in chains)

    def test_empty_concepts(self, medical_domain):
        """Test with empty concept list."""
        builder = ReasoningChainBuilder(domain=medical_domain)
        chains = builder.build_chains([], [])

        assert chains == []

    def test_no_relationships(self, sample_concepts, medical_domain):
        """Test with concepts but no relationships."""
        builder = ReasoningChainBuilder(domain=medical_domain)
        chains = builder.build_chains(sample_concepts, [])

        # May or may not produce chains depending on domain logic
        assert isinstance(chains, list)
