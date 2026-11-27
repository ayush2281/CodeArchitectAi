import networkx as nx

def is_private_function(function_name: str) -> bool:
    """Return True when the function name starts with an underscore."""
    name = function_name.rsplit(".", 1)[-1]
    return name.startswith("_")
def find_potentially_unreferenced_functions(
    call_graph: nx.DiGraph,
    entry_points: set[str] | None = None,
) -> list[dict]:
    """Find functions with no detected internal callers."""
    if not entry_points or not any(
        entry_point in call_graph
        for entry_point in entry_points
    ):
        return []
    
    unreferenced = []

    reachable = set()

    for entry_point in entry_points:
        if entry_point in call_graph:
            reachable.add(entry_point)
            reachable.update(nx.descendants(call_graph, entry_point))

    for function in call_graph.nodes:
       if function not in reachable:
           if is_private_function(function):
             reason = (
                     "Private function is not reachable from configured entry points; "
                     "may be unused."
            )
           else:
                reason = (
                   "Public function is not reachable from configured entry points; "
                   "may be unused or intended for external use."
                )

           classification = (
                "potentially_unused_private"
                if is_private_function(function)
                else "potentially_unused_public"
            )

           unreferenced.append({
                "function": function,
                "classification": classification,
                "reason": reason,
           })           

    return sorted(unreferenced, key=lambda item: item["function"])