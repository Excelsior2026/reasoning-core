"""Build reasoning chains from concepts and relationships."""

from typing import List, Dict, Optional
from dataclasses import dataclass
from reasoning_core.extractors.concept_extractor import Concept
from reasoning_core.extractors.relationship_mapper import Relationship


@dataclass
class ReasoningStep:
    """A single step in a reasoning chain."""

    concept: Concept
    action: str  # e.g., "observe", "diagnose", "treat", "analyze"
    rationale: str  # Why this step follows the previous


@dataclass
class ReasoningChain:
    """A complete reasoning chain."""

    type: str  # e.g., "diagnostic", "therapeutic", "analytical"
    steps: List[ReasoningStep]
    confidence: float
    domain: str


class ReasoningChainBuilder:
    """Build reasoning chains from concepts and relationships."""

    def __init__(self, domain=None):
        """Initialize reasoning chain builder.

        Args:
            domain: Domain plugin for domain-specific patterns
        """
        self.domain = domain

    def build_chains(
        self, concepts: List[Concept], relationships: List[Relationship], domain_hints: Optional[Dict] = None
    ) -> List[ReasoningChain]:
        """Build reasoning chains from concepts and relationships.

        Args:
            concepts: List of extracted concepts
            relationships: List of relationships
            domain_hints: Optional domain-specific hints

        Returns:
            List of reasoning chains
        """
        chains = []

        # Use domain-specific chain building if available
        if self.domain:
            domain_chains = self.domain.build_reasoning_chains(concepts, relationships)
            chains.extend(domain_chains)

        # Generic chain building
        if not chains:
            chains = self._generic_chain_building(concepts, relationships)

        return chains

    def _generic_chain_building(
        self, concepts: List[Concept], relationships: List[Relationship]
    ) -> List[ReasoningChain]:
        """Generic reasoning chain construction.

        Args:
            concepts: List of concepts
            relationships: List of relationships

        Returns:
            List of reasoning chains
        """
        chains = []

        # Build graph of relationships
        graph = self._build_relationship_graph(relationships)

        # Find chains (paths through the graph)
        for start_concept in concepts:
            paths = self._find_paths(start_concept, graph, max_depth=5)
            for path in paths:
                chain = self._path_to_chain(path)
                if chain and len(chain.steps) >= 2:  # At least 2 steps
                    chains.append(chain)

        return chains

    def _build_relationship_graph(self, relationships: List[Relationship]) -> Dict:
        """Build a graph structure from relationships.

        Args:
            relationships: List of relationships

        Returns:
            Graph as adjacency list
        """
        graph = {}
        for rel in relationships:
            source_key = rel.source.text
            if source_key not in graph:
                graph[source_key] = []
            graph[source_key].append((rel.target, rel.type, rel.confidence))
        return graph

    def _find_paths(self, start: Concept, graph: Dict, max_depth: int = 5) -> List[List[Concept]]:
        """Find all paths from a starting concept.

        Args:
            start: Starting concept
            graph: Relationship graph
            max_depth: Maximum path length

        Returns:
            List of paths (each path is a list of concepts)
        """
        paths = []
        visited = set()

        def dfs(current: Concept, path: List[Concept], depth: int):
            if depth > max_depth:
                return

            current_key = current.text
            if current_key in visited:
                return

            visited.add(current_key)
            path.append(current)

            if len(path) >= 2:
                paths.append(path.copy())

            if current_key in graph:
                for next_concept, rel_type, confidence in graph[current_key]:
                    dfs(next_concept, path, depth + 1)

            path.pop()
            visited.remove(current_key)

        dfs(start, [], 0)
        return paths

    def _path_to_chain(self, path: List[Concept]) -> Optional[ReasoningChain]:
        """Convert a path to a reasoning chain.

        Args:
            path: List of concepts forming a path

        Returns:
            ReasoningChain or None
        """
        if len(path) < 2:
            return None

        steps = []
        for i, concept in enumerate(path):
            action = self._infer_action(concept, i, len(path))
            rationale = self._generate_rationale(path, i)
            steps.append(ReasoningStep(concept=concept, action=action, rationale=rationale))

        return ReasoningChain(type="generic", steps=steps, confidence=0.7, domain="unknown")

    def _infer_action(self, concept: Concept, position: int, total: int) -> str:
        """Infer the action for a reasoning step.

        Args:
            concept: The concept
            position: Position in the chain
            total: Total steps in chain

        Returns:
            Action string
        """
        if position == 0:
            return "observe"
        elif position == total - 1:
            return "conclude"
        else:
            return "analyze"

    def _generate_rationale(self, path: List[Concept], position: int) -> str:
        """Generate rationale for a step.

        Args:
            path: Full path
            position: Current position

        Returns:
            Rationale string
        """
        if position == 0:
            return "Starting point"
        prev_concept = path[position - 1]
        current_concept = path[position]
        return f"Based on {prev_concept.text}, consider {current_concept.text}"
