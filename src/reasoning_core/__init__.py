"""Reasoning Core - Universal reasoning extraction engine.

Transform expertise into intelligent knowledge graphs.
"""

__version__ = "0.1.0"
__author__ = "Excelsior2026"
__license__ = "MIT"

from reasoning_core.api.reasoning_api import ReasoningAPI
from reasoning_core.api.async_reasoning_api import AsyncReasoningAPI
from reasoning_core.extractors.concept_extractor import ConceptExtractor
from reasoning_core.extractors.relationship_mapper import RelationshipMapper
from reasoning_core.extractors.reasoning_chain_builder import ReasoningChainBuilder
from reasoning_core.graph.knowledge_graph import KnowledgeGraph
from reasoning_core.plugins.base_domain import BaseDomain
from reasoning_core.plugins.medical_domain import MedicalDomain
from reasoning_core.plugins.business_domain import BusinessDomain
from reasoning_core.plugins.meeting_domain import MeetingDomain

__all__ = [
    "ReasoningAPI",
    "AsyncReasoningAPI",
    "ConceptExtractor",
    "RelationshipMapper",
    "ReasoningChainBuilder",
    "KnowledgeGraph",
    "BaseDomain",
    "MedicalDomain",
    "BusinessDomain",
    "MeetingDomain",
]
