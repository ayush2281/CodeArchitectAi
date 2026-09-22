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


def find_affected_functions(
    call_graph: nx.DiGraph,
    changed_function: str,
) -> dict:
    """Find functions directly and indirectly affected by a changed function."""

    if changed_function not in call_graph:
        raise ValueError(
            f"Function not found in call graph: {changed_function}"
        )

    direct = sorted(call_graph.predecessors(changed_function))

    indirect = sorted(
        nx.ancestors(call_graph, changed_function) - set(direct)
    )

    result = {
        "direct": [],
        "indirect": [],
    }

    for function in direct:
        result["direct"].append({
            "function": function,
            "path": [function, changed_function],
            "reason": f"{function} directly calls {changed_function}.",
        })

    for function in indirect:
        paths = list(
            nx.all_simple_paths(
                call_graph,
                function,
                changed_function,
            )
        )

        shortest_path = min(paths, key=len)

        result["indirect"].append({
            "function": function,
            "path": shortest_path,
            "reason": (
                f"{function} is indirectly affected through "
                f"{' → '.join(shortest_path)}."
            ),
        })

    return result


def explain_impact(
    graph: nx.DiGraph,
    changed_module: str,
    call_graph: nx.DiGraph | None = None,
    changed_function: str | None = None,
) -> dict:
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

    if call_graph is not None and changed_function is not None:
        result["function_impact"] = find_affected_functions(
            call_graph,
            changed_function,
        )

    result["summary"] = {
        "direct_count": len(result["direct"]),
        "indirect_count": len(result["indirect"]),
        "total_affected": len(result["direct"]) + len(result["indirect"]),
    }

    return result
