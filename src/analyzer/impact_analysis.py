import networkx as nx


def find_affected_modules(
    graph: nx.DiGraph,
    changed_module: str,
) -> dict[str, list[str]]:
    """Find directly and indirectly affected modules."""
    if changed_module not in graph:
        raise ValueError(f"Module not found in graph: {changed_module}")

    affected = nx.ancestors(graph, changed_module)

    direct = [
        module
        for module in graph.predecessors(changed_module)
    ]

    indirect = sorted(affected - set(direct))

    return {
        "direct": sorted(direct),
        "indirect": indirect,
    }
def explain_impact(
    graph: nx.DiGraph,
    changed_module: str,
) -> dict[str, list[dict]]:
    """Explain why modules are directly or indirectly affected."""

    if changed_module not in graph:
        raise ValueError(f"Module not found in graph: {changed_module}")

    direct = sorted(graph.predecessors(changed_module))

    indirect = sorted(
        nx.ancestors(graph, changed_module) - set(direct)
    )

    result = {
        "direct": [],
        "indirect": [],
    }

    for module in direct:
        result["direct"].append({
            "module": module,
            "path": [module, changed_module],
            "reason": f"{module} directly depends on {changed_module}.",
        })

    for module in indirect:
        paths = list(
            nx.all_simple_paths(
                graph,
                module,
                changed_module,
            )
        )

        shortest_path = min(paths, key=len)

        result["indirect"].append({
            "module": module,
            "path": shortest_path,
            "reason": (
                f"{module} is indirectly affected through "
                f"{' → '.join(shortest_path)}."
            ),
        })
    result["summary"] = {
        "direct_count": len(result["direct"]),
        "indirect_count": len(result["indirect"]),
        "total_affected": len(result["direct"]) + len(result["indirect"]),
    }
    return result