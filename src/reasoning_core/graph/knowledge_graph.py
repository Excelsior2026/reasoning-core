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

        Raises:
            ValueError: If source or target node doesn't exist
        """
        if edge.source_id not in self.nodes:
            raise ValueError(f"Source node '{edge.source_id}' not found in graph")
        if edge.target_id not in self.nodes:
            raise ValueError(f"Target node '{edge.target_id}' not found in graph")

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

        if start_id == end_id:
            return [start_id]

        visited: Set[str] = set()
        path: List[str] = []

        def dfs(current_id: str, depth: int) -> bool:
            if depth > max_depth:
                return False

            if current_id == end_id:
                path.append(current_id)
                return True

            visited.add(current_id)
            path.append(current_id)

            for neighbor_id in self.get_neighbors(current_id):
                if neighbor_id not in visited:
                    if dfs(neighbor_id, depth + 1):
                        return True

            # Backtrack: remove from path and visited when backtracking
            path.pop()
            visited.remove(current_id)
            return False

        if dfs(start_id, 0):
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

    def to_dot(self) -> str:
        """Convert graph to Graphviz DOT format.

        Returns:
            DOT format string for visualization
        """
        lines = ["digraph KnowledgeGraph {"]
        lines.append("  rankdir=LR;")
        lines.append("  node [shape=box];")

        # Add nodes
        for node in self.nodes.values():
            label = node.label.replace('"', '\\"')
            node_attrs = f'label="{label}"'
            if node.confidence < 1.0:
                node_attrs += f', style="dashed", color="gray{int((1-node.confidence)*100)}"'
            lines.append(f'  "{node.id}" [{node_attrs}];')

        # Add edges
        for edge in self.edges:
            edge_attrs = f'label="{edge.type}"'
            if edge.confidence < 1.0:
                edge_attrs += f', style="dashed", color="gray{int((1-edge.confidence)*100)}"'
            lines.append(f'  "{edge.source_id}" -> "{edge.target_id}" [{edge_attrs}];')

        lines.append("}")
        return "\n".join(lines)

    def to_graphml(self) -> str:
        """Convert graph to GraphML format.

        Returns:
            GraphML XML string for visualization tools
        """
        import xml.etree.ElementTree as ET

        root = ET.Element("graphml")
        root.set("xmlns", "http://graphml.graphdrawing.org/xmlns")

        # Define attributes
        key_id = ET.SubElement(root, "key")
        key_id.set("id", "label")
        key_id.set("for", "node")
        key_id.set("attr.name", "label")
        key_id.set("attr.type", "string")

        key_confidence = ET.SubElement(root, "key")
        key_confidence.set("id", "confidence")
        key_confidence.set("for", "node")
        key_confidence.set("attr.name", "confidence")
        key_confidence.set("attr.type", "double")

        key_type = ET.SubElement(root, "key")
        key_type.set("id", "type")
        key_type.set("for", "edge")
        key_type.set("attr.name", "type")
        key_type.set("attr.type", "string")

        graph = ET.SubElement(root, "graph")
        graph.set("id", "KnowledgeGraph")
        graph.set("edgedefault", "directed")

        # Add nodes
        for node in self.nodes.values():
            node_elem = ET.SubElement(graph, "node")
            node_elem.set("id", node.id)

            data_label = ET.SubElement(node_elem, "data")
            data_label.set("key", "label")
            data_label.text = node.label

            data_conf = ET.SubElement(node_elem, "data")
            data_conf.set("key", "confidence")
            data_conf.text = str(node.confidence)

        # Add edges
        for i, edge in enumerate(self.edges):
            edge_elem = ET.SubElement(graph, "edge")
            edge_elem.set("id", f"e{i}")
            edge_elem.set("source", edge.source_id)
            edge_elem.set("target", edge.target_id)

            data_type = ET.SubElement(edge_elem, "data")
            data_type.set("key", "type")
            data_type.text = edge.type

        return ET.tostring(root, encoding="unicode", method="xml")

    def to_cytoscape(self) -> Dict:
        """Convert graph to Cytoscape.js JSON format.

        Returns:
            Dictionary in Cytoscape.js format for web visualization
        """
        elements = {"nodes": [], "edges": []}

        # Add nodes
        for node in self.nodes.values():
            elements["nodes"].append(
                {
                    "data": {
                        "id": node.id,
                        "label": node.label,
                        "type": node.type,
                        "confidence": node.confidence,
                        **node.properties,
                    }
                }
            )

        # Add edges
        for i, edge in enumerate(self.edges):
            elements["edges"].append(
                {
                    "data": {
                        "id": f"e{i}",
                        "source": edge.source_id,
                        "target": edge.target_id,
                        "type": edge.type,
                        "confidence": edge.confidence,
                        **edge.properties,
                    }
                }
            )

        return elements

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
        if not self.nodes:
            return {
                "num_nodes": 0,
                "num_edges": 0,
                "node_types": [],
                "edge_types": [],
                "avg_degree": 0.0,
            }

        # Calculate average degree correctly (sum of degrees / number of nodes)
        # For directed graph: sum all outgoing edges per node
        total_degree = sum(len(self.get_neighbors(node_id)) for node_id in self.nodes.keys())

        return {
            "num_nodes": len(self.nodes),
            "num_edges": len(self.edges),
            "node_types": list(set(node.type for node in self.nodes.values())),
            "edge_types": list(set(edge.type for edge in self.edges)),
            "avg_degree": total_degree / len(self.nodes),
        }
