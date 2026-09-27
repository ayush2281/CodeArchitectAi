from pathlib import Path

import networkx as nx
from pyvis.network import Network


def create_dependency_graph(
    nodes: list[str],
    edges: list[tuple[str, str]],
) -> nx.DiGraph:
    """Create a directed dependency graph from analysis results."""
    graph = nx.DiGraph()

    graph.add_nodes_from(nodes)
    graph.add_edges_from(edges)

    return graph


def get_graph_statistics(graph: nx.DiGraph) -> dict:
    """Return basic statistics for a dependency graph."""
    return {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "density": nx.density(graph),
        "is_directed": graph.is_directed(),
    }


def save_dependency_graph(
    graph: nx.DiGraph,
    output_path: str = "dependency_graph.html",
) -> None:
    """Create an interactive HTML visualization of the dependency graph."""
    network = Network(
        height="700px",
        width="100%",
        directed=True,
        neighborhood_highlight=True,
    ) 
    network.barnes_hut(
        gravity=-8000,
        central_gravity=0.3,
        spring_length=140,
        spring_strength=0.04,
        damping=0.09,
        overlap=0,
    )

    for node in graph.nodes:
        network.add_node(
            node,
            label=node.split(".")[-1],
            title=node,
        )

    for source, target in graph.edges:
        network.add_edge(
            source,
            target,
        )

    network.write_html(
        str(Path(output_path)),
        open_browser=False,
    )
    
def save_call_graph(
    graph: nx.DiGraph,
    output_path: str = "call_graph.html",
) -> None:
    """Create an interactive HTML visualization of the call graph."""
    network = Network(
        height="700px",
        width="100%",
        directed=True,
        neighborhood_highlight=True,
    )
    network.barnes_hut(
        gravity=-8000,
        central_gravity=0.3,
        spring_length=170,
        spring_strength=0.04,
        damping=0.09,
        overlap=1,
    )

    for node in graph.nodes:
        network.add_node(
            node,
            label=node.split(".")[-1],
            font={"size": 14},
            title=node,
        )

    for source, target in graph.edges:
        network.add_edge(
            source,
            target,
        )

    network.write_html(
        str(Path(output_path)),
        open_browser=False,
    )    