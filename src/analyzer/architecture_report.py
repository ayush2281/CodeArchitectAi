import json

from src.analyzer.llm_client import generate_response


def generate_architecture_report(
    issues: list[dict],
    analysis: dict,
    call_graph: dict | None = None,
    unreferenced_functions: list[dict] | None = None,
    impact_analysis: dict | None = None,
    graph_statistics: dict | None = None,
) -> str:
    """Generate an architecture report using the local LLM."""
    prompt = f"""
You are a software architecture analyst.

Analyze the following static-analysis results from a Python codebase.

Architecture issues:
{json.dumps(issues, indent=2)}

Dependency analysis summary:
- Modules analyzed: {len(analysis)}
- Top connected modules:
{json.dumps(
    sorted(
        analysis.items(),
        key=lambda item: item[1]["total_connections"],
        reverse=True,
    )[:8],
    indent=2,
)}

Call graph summary:
- Functions: {len((call_graph or {}).get("nodes", []))}
- Call relationships: {len((call_graph or {}).get("edges", []))}

Architecture issue summary:
{json.dumps({
    "total": (len(issues)),
    "high": sum(1 for issue in issues if issue.get("severity") == "high"),
    "medium": sum(1 for issue in issues if issue.get("severity") == "medium"),
}, indent=2)}

High-connectivity module count: {len([
    module
    for module, metrics in analysis.items()
    if metrics["total_connections"] >= 3
])}



Potentially unreferenced functions:
- Count: {len(unreferenced_functions or [])}
- Functions:
{json.dumps(
    [
        item.get("function")
        for item in (unreferenced_functions or [])[:20]
    ],
    indent=2,
)}

Change impact summary:
{json.dumps({
    "summary": (impact_analysis or {}).get("summary", {}),
    "direct_modules": [
        item.get("module")
        for item in (impact_analysis or {}).get("direct", [])[:20]
    ],
    "indirect_modules": [
        item.get("module")
        for item in (impact_analysis or {}).get("indirect", [])[:20]
    ],
    "function_impact": (impact_analysis or {}).get("function_impact", {}),
}, indent=2)}

Graph statistics:

{json.dumps(graph_statistics or {}, indent=2)}

Return only the final report. Do not explain your reasoning or repeat the input. Use exactly these 4 sections and keep each section to 1–2 sentences:
1. Architecture Overview
2. Detected Problems
3. Why They Matter
4. Recommended Improvements

Only discuss facts and problems directly supported by the supplied analysis.
Interpret fan-in as the number of project modules that depend on a module.
Interpret fan-out as the number of project modules that the module depends on.
Do not infer failure propagation, bottlenecks, criticality, or runtime impact from fan-in/fan-out alone.

Do not infer effects on module loading, testing, runtime behavior, stability, or system behavior from the detected dependency cycle or fan-in/fan-out values. Recommendations must be limited to inspecting or restructuring the explicitly detected dependency relationships; do not assume that dependencies should be unidirectional unless the analysis establishes that requirement.
Do not infer maintenance difficulty, rigidity, change impact, or architectural quality from fan-in/fan-out alone.
Do not describe high fan-in/fan-out as tight integration, interlocking boundaries, or similar qualitative architectural characteristics. Do not recommend rebalancing fan-in or fan-out unless the analysis explicitly establishes that as a goal.
Do not infer the purpose, role, or type of any module.
Never describe any module as core, central, foundational, critical, important, or similar unless the supplied analysis explicitly establishes that classification.
Do not claim that a dependency violates architectural principles unless the supplied analysis explicitly defines and checks such a principle.
Do not invent files, dependencies, usage, or architectural intent.
If the supplied analysis does not establish a fact, do not state it as fact.
When describing high coupling, use only the explicitly supplied high-coupling modules and their configured threshold results. Do not infer that modules in a circular dependency group are also high-coupling modules. Do not state a high-coupling count unless it matches the supplied analysis.
For circular dependencies, distinguish direct dependencies from reachability through dependency paths. Do not state that every module in a circular dependency group directly depends on every other module.
"""

    return generate_response(prompt)