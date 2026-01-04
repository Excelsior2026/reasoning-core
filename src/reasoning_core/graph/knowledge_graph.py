"""Knowledge graph data structure and operations."""

from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
import json


@dataclass
class Node:
    """A node in the knowledge graph."""

    id: str
    type: str  # concept type
    label: str  # display text
    properties: Dict = field(default_factory=dict)
    confidence: float = 1.0


@dataclass
class Edge:
    """An edge in the knowledge graph."""

    source_id: str
    target_id: str
    type: str  # relationship type
    properties: Dict = field(default_factory=dict)
    confidence: float = 1.0


class KnowledgeGraph:
    """Knowledge graph for representing domain knowledge."""

    def __init__(self):
        """Initialize empty knowledge graph."""
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self.adjacency: Dict[str, List[str]] = {}  # For efficient traversal

    def add_node(self, node: Node) -> None:
        """Add a node to the graph.

        Args:
            node: Node to add
        """
        self.nodes[node.id] = node
        if node.id not in self.adjacency:
            self.adjacency[node.id] = []

    def add_edge(self, edge: Edge) -> None:
        """Add an edge to the graph.

        Args:
            edge: Edge to add
        """
        self.edges.append(edge)
        if edge.source_id in self.adjacency:
            self.adjacency[edge.source_id].append(edge.target_id)
        else:
            self.adjacency[edge.source_id] = [edge.target_id]

    def get_node(self, node_id: str) -> Optional[Node]:
        """Get a node by ID.

        Args:
            node_id: Node identifier

        Returns:
            Node or None if not found
        """
        return self.nodes.get(node_id)

    def get_neighbors(self, node_id: str) -> List[str]:
        """Get neighboring node IDs.

        Args:
            node_id: Node identifier

        Returns:
            List of neighbor IDs
        """
        return self.adjacency.get(node_id, [])

    def get_edges_from(self, node_id: str) -> List[Edge]:
        """Get all edges starting from a node.

        Args:
            node_id: Source node ID

        Returns:
            List of edges
        """
        return [edge for edge in self.edges if edge.source_id == node_id]

    def get_edges_to(self, node_id: str) -> List[Edge]:
        """Get all edges pointing to a node.

        Args:
            node_id: Target node ID

        Returns:
            List of edges
        """
        return [edge for edge in self.edges if edge.target_id == node_id]

    def find_path(self, start_id: str, end_id: str, max_depth: int = 5) -> Optional[List[str]]:
        """Find a path between two nodes.

        Args:
            start_id: Starting node ID
            end_id: Target node ID
            max_depth: Maximum path length

        Returns:
            List of node IDs forming the path, or None
        """
        if start_id not in self.nodes or end_id not in self.nodes:
            return None

        visited: Set[str] = set()
        path: List[str] = []

        def dfs(current_id: str, depth: int) -> bool:
            if depth > max_depth:
                return False

            if current_id == end_id:
                return True

            visited.add(current_id)
            path.append(current_id)

            for neighbor_id in self.get_neighbors(current_id):
                if neighbor_id not in visited:
                    if dfs(neighbor_id, depth + 1):
                        return True

            path.pop()
            return False

        if dfs(start_id, 0):
            path.append(end_id)
            return path
        return None

    def get_subgraph(self, node_ids: List[str], include_connections: bool = True) -> "KnowledgeGraph":
        """Extract a subgraph containing specific nodes.

        Args:
            node_ids: List of node IDs to include
            include_connections: Whether to include edges between these nodes

        Returns:
            New KnowledgeGraph containing the subgraph
        """
        subgraph = KnowledgeGraph()

        # Add nodes
        for node_id in node_ids:
            if node_id in self.nodes:
                subgraph.add_node(self.nodes[node_id])

        # Add edges if requested
        if include_connections:
            for edge in self.edges:
                if edge.source_id in node_ids and edge.target_id in node_ids:
                    subgraph.add_edge(edge)

        return subgraph

    def to_dict(self) -> Dict:
        """Convert graph to dictionary representation.

        Returns:
            Dictionary representation of the graph
        """
        return {
            "nodes": [vars(node) for node in self.nodes.values()],
            "edges": [vars(edge) for edge in self.edges],
        }

    def to_json(self) -> str:
        """Convert graph to JSON string.

        Returns:
            JSON representation of the graph
        """
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict) -> "KnowledgeGraph":
        """Create graph from dictionary.

        Args:
            data: Dictionary containing nodes and edges

        Returns:
            KnowledgeGraph instance
        """
        graph = cls()
        for node_data in data.get("nodes", []):
            graph.add_node(Node(**node_data))
        for edge_data in data.get("edges", []):
            graph.add_edge(Edge(**edge_data))
        return graph

    def merge(self, other: "KnowledgeGraph") -> None:
        """Merge another graph into this one.

        Args:
            other: Another KnowledgeGraph to merge
        """
        for node in other.nodes.values():
            if node.id not in self.nodes:
                self.add_node(node)
        for edge in other.edges:
            self.add_edge(edge)

    def get_stats(self) -> Dict:
        """Get graph statistics.

        Returns:
            Dictionary of statistics
        """
        return {
            "num_nodes": len(self.nodes),
            "num_edges": len(self.edges),
            "node_types": list(set(node.type for node in self.nodes.values())),
            "edge_types": list(set(edge.type for edge in self.edges)),
            "avg_degree": len(self.edges) / max(len(self.nodes), 1),
        }
