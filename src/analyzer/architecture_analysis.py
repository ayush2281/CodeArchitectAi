import networkx as nx


def analyze_dependencies(graph: nx.DiGraph) -> dict:
    """Analyze dependency relationships between project modules."""
    analysis = {}

    for module in graph.nodes:
        fan_in = graph.in_degree(module)
        fan_out = graph.out_degree(module)

        analysis[module] = {
            "fan_in": fan_in,
            "fan_out": fan_out,
            "total_connections": fan_in + fan_out,
        }

    return analysis


def find_circular_dependencies(graph: nx.DiGraph) -> list[list[str]]:
    """Find circular dependency chains in the project."""
    return list(nx.simple_cycles(graph))


def find_high_connectivity_modules(
    analysis: dict,
    threshold: int = 3,
) -> list[str]:
    """Find modules with many incoming and outgoing connections."""
    return [
        module
        for module, metrics in analysis.items()
        if metrics["total_connections"] >= threshold
    ]
