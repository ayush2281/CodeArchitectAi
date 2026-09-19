import networkx as nx


def detect_architecture_issues(
    graph: nx.DiGraph,
    analysis: dict,
) -> list[dict]:
    """Detect basic architecture issues from dependency relationships."""
    issues = []

    # Circular dependencies
    cycles = list(nx.simple_cycles(graph))

    for cycle in cycles:
        issues.append({
            "type": "circular_dependency",
            "severity": "high",
            "modules": cycle,
            "message": "Circular dependency detected between project modules.",
        })

    # Highly connected modules
    for module, metrics in analysis.items():
        if metrics["total_connections"] >= 3:
            issues.append({
                "type": "high_coupling",
                "severity": "medium",
                "module": module,
                "message": "Module has a high number of dependency connections.",
            })

    return issues

def summarize_architecture_issues(issues: list[dict]) -> dict:
    """Summarize architecture issues by severity."""
    summary = {
        "total": len(issues),
        "high": 0,
        "medium": 0,
        "low": 0,
    }

    for issue in issues:
        severity = issue.get("severity")

        if severity in summary:
            summary[severity] += 1

    return summary