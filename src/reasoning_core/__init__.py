"""Reasoning Core - Universal reasoning extraction engine.

This library provides domain-agnostic tools for:
- Extracting concepts from text/transcripts
- Identifying relationships between concepts
- Building knowledge graphs
- Generating reasoning chains
- Cross-referencing knowledge

Designed to be extended with domain-specific plugins.
"""

__version__ = "0.1.0"
__author__ = "Excelsior2026"

from reasoning_core.extractors.concept_extractor import ConceptExtractor
from reasoning_core.extractors.relationship_mapper import RelationshipMapper
from reasoning_core.graph.knowledge_graph import KnowledgeGraph
from reasoning_core.chains.reasoning_chain import ReasoningChain
from reasoning_core.domains.base_domain import BaseDomain

__all__ = [
    "ConceptExtractor",
    "RelationshipMapper",
    "KnowledgeGraph",
    "ReasoningChain",
    "BaseDomain",
]
