"""Tests for knowledge graph operations."""

import pytest
import json
from reasoning_core.graph.knowledge_graph import KnowledgeGraph, Node, Edge


class TestKnowledgeGraph:
    """Test knowledge graph functionality."""

    def test_graph_creation(self):
        """Test creating an empty graph."""
        graph = KnowledgeGraph()
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0

    def test_add_node(self):
        """Test adding nodes to graph."""
        graph = KnowledgeGraph()
        node = Node(id="test1", type="concept", label="Test Node")
        graph.add_node(node)

        assert len(graph.nodes) == 1
        assert graph.get_node("test1") == node

    def test_add_edge(self):
        """Test adding edges to graph."""
        graph = KnowledgeGraph()
        node1 = Node(id="node1", type="concept", label="Node 1")
        node2 = Node(id="node2", type="concept", label="Node 2")
        graph.add_node(node1)
        graph.add_node(node2)

        edge = Edge(source_id="node1", target_id="node2", type="relates_to")
        graph.add_edge(edge)

        assert len(graph.edges) == 1
        assert "node2" in graph.get_neighbors("node1")

    def test_get_neighbors(self):
        """Test getting neighboring nodes."""
        graph = KnowledgeGraph()
        node1 = Node(id="node1", type="concept", label="Node 1")
        node2 = Node(id="node2", type="concept", label="Node 2")
        node3 = Node(id="node3", type="concept", label="Node 3")
        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_node(node3)

        graph.add_edge(Edge(source_id="node1", target_id="node2", type="relates_to"))
        graph.add_edge(Edge(source_id="node1", target_id="node3", type="relates_to"))

        neighbors = graph.get_neighbors("node1")
        assert len(neighbors) == 2
        assert "node2" in neighbors
        assert "node3" in neighbors

    def test_find_path(self):
        """Test finding paths between nodes."""
        graph = KnowledgeGraph()
        for i in range(4):
            graph.add_node(Node(id=f"node{i}", type="concept", label=f"Node {i}"))

        graph.add_edge(Edge(source_id="node0", target_id="node1", type="relates_to"))
        graph.add_edge(Edge(source_id="node1", target_id="node2", type="relates_to"))
        graph.add_edge(Edge(source_id="node2", target_id="node3", type="relates_to"))

        path = graph.find_path("node0", "node3")
        assert path is not None
        assert path[0] == "node0"
        assert path[-1] == "node3"

    def test_find_path_no_connection(self):
        """Test path finding with disconnected nodes."""
        graph = KnowledgeGraph()
        graph.add_node(Node(id="node1", type="concept", label="Node 1"))
        graph.add_node(Node(id="node2", type="concept", label="Node 2"))

        path = graph.find_path("node1", "node2")
        assert path is None

    def test_subgraph_extraction(self):
        """Test extracting subgraphs."""
        graph = KnowledgeGraph()
        for i in range(5):
            graph.add_node(Node(id=f"node{i}", type="concept", label=f"Node {i}"))

        graph.add_edge(Edge(source_id="node0", target_id="node1", type="relates_to"))
        graph.add_edge(Edge(source_id="node1", target_id="node2", type="relates_to"))
        graph.add_edge(Edge(source_id="node3", target_id="node4", type="relates_to"))

        subgraph = graph.get_subgraph(["node0", "node1", "node2"])
        assert len(subgraph.nodes) == 3
        assert len(subgraph.edges) == 2

    def test_serialization(self):
        """Test graph serialization to dict/JSON."""
        graph = KnowledgeGraph()
        node = Node(id="test", type="concept", label="Test", confidence=0.9)
        graph.add_node(node)

        # Test to_dict
        graph_dict = graph.to_dict()
        assert "nodes" in graph_dict
        assert "edges" in graph_dict
        assert len(graph_dict["nodes"]) == 1

        # Test to_json
        graph_json = graph.to_json()
        assert isinstance(graph_json, str)
        parsed = json.loads(graph_json)
        assert "nodes" in parsed

    def test_deserialization(self):
        """Test creating graph from dictionary."""
        data = {
            "nodes": [{"id": "node1", "type": "concept", "label": "Node 1", "properties": {}, "confidence": 1.0}],
            "edges": [{"source_id": "node1", "target_id": "node2", "type": "relates_to", "properties": {}, "confidence": 1.0}],
        }

        graph = KnowledgeGraph.from_dict(data)
        assert len(graph.nodes) == 1
        assert graph.get_node("node1") is not None

    def test_merge_graphs(self):
        """Test merging two graphs."""
        graph1 = KnowledgeGraph()
        graph1.add_node(Node(id="node1", type="concept", label="Node 1"))

        graph2 = KnowledgeGraph()
        graph2.add_node(Node(id="node2", type="concept", label="Node 2"))

        graph1.merge(graph2)
        assert len(graph1.nodes) == 2

    def test_graph_stats(self):
        """Test getting graph statistics."""
        graph = KnowledgeGraph()
        graph.add_node(Node(id="node1", type="symptom", label="Fever"))
        graph.add_node(Node(id="node2", type="disease", label="Infection"))
        graph.add_edge(Edge(source_id="node1", target_id="node2", type="indicates"))

        stats = graph.get_stats()
        assert stats["num_nodes"] == 2
        assert stats["num_edges"] == 1
        assert "symptom" in stats["node_types"]
        assert "indicates" in stats["edge_types"]
