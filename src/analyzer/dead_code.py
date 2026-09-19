import networkx as nx


def find_potentially_unused_functions(
    call_graph: nx.DiGraph,
    entry_points: set[str] | None = None,
) -> list[str]:
    """Find functions with no detected callers that are not entry points."""
    if entry_points is None:
        entry_points = {
           "src.analyzer.analyze_project.analyze_project",
        }
    unused = []

    for function in call_graph.nodes:
        if (
            call_graph.in_degree(function) == 0
            and function not in entry_points
        ):
            unused.append(function)

    return sorted(unused)