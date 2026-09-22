import networkx as nx


def detect_architecture_issues(
    graph: nx.DiGraph,
    analysis: dict,
    cycles: list[list[str]],
    highly_connected_modules: list[str],
) -> list[dict]:
    """Detect basic architecture issues from dependency relationships."""
    issues = []


    for cycle in cycles:
        issues.append({
            "type": "circular_dependency",
            "severity": "high",
            "modules": cycle,
            "message": "Circular dependency detected between project modules.",
        })
    for module in highly_connected_modules:
        issues.append({
          "type": "highly_connected_module",
          "severity": "medium",
          "module": module,
          "message": (
               f"Module has high connectivity "
               f"(fan-in: {analysis[module]['fan_in']}, "
               f"fan-out: {analysis[module]['fan_out']})."
           ),
        })
    # Highly connected modules
    for module, metrics in analysis.items():
        if metrics["fan_in"] >= 3 and metrics["fan_out"] >= 3:
            issues.append({
                "type": "high_coupling",
                "severity": "medium",
                "module": module,
                "message": (
                    f"Module has high coupling "
                    f"(fan-in: {metrics['fan_in']}, "
                    f"fan-out: {metrics['fan_out']})."
                ),                
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