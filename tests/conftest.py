"""Shared test fixtures for reasoning-core tests."""

import pytest
from reasoning_core.extractors.concept_extractor import Concept
from reasoning_core.extractors.relationship_mapper import Relationship
from reasoning_core.plugins.medical_domain import MedicalDomain
from reasoning_core.plugins.business_domain import BusinessDomain


@pytest.fixture
def sample_medical_text():
    """Sample medical text for testing."""
    return """
    Patient presents with chest pain and shortness of breath.
    ECG shows ST elevation. Troponin is elevated.
    Diagnosis: Myocardial infarction.
    Treatment: Aspirin, heparin, and catheterization.
    """


@pytest.fixture
def sample_business_text():
    """Sample business text for testing."""
    return """
    The customer's main pain point is inefficiency in their current process.
    We can address this with our upselling strategy.
    This should improve their conversion rate and ROI.
    We'll measure success using NPS and revenue metrics.
    """


@pytest.fixture
def sample_generic_text():
    """Sample generic text for testing."""
    return """
    The Theory of Relativity describes the relationship between space and time.
    Einstein published this work in 1915.
    It has important implications for Physics and Astronomy.
    """


@pytest.fixture
def sample_concepts():
    """Sample concept objects for testing."""
    return [
        Concept(text="chest pain", type="symptom", confidence=0.9, context="Patient presents with chest pain", position=20),
        Concept(text="ECG", type="test", confidence=0.95, context="ECG shows ST elevation", position=60),
        Concept(text="myocardial infarction", type="disease", confidence=0.9, context="Diagnosis: MI", position=100),
        Concept(text="aspirin", type="treatment", confidence=0.85, context="Treatment: Aspirin", position=140),
    ]


@pytest.fixture
def sample_relationships(sample_concepts):
    """Sample relationship objects for testing."""
    return [
        Relationship(
            source=sample_concepts[0],
            target=sample_concepts[2],
            type="indicates",
            confidence=0.8,
            evidence="chest pain indicates MI",
        ),
        Relationship(
            source=sample_concepts[1],
            target=sample_concepts[2],
            type="confirms",
            confidence=0.9,
            evidence="ECG confirms MI",
        ),
        Relationship(
            source=sample_concepts[3],
            target=sample_concepts[2],
            type="treats",
            confidence=0.85,
            evidence="aspirin treats MI",
        ),
    ]


@pytest.fixture
def medical_domain():
    """Medical domain plugin instance."""
    return MedicalDomain()


@pytest.fixture
def business_domain():
    """Business domain plugin instance."""
    return BusinessDomain()
