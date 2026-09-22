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

Dependency analysis:
{json.dumps(analysis, indent=2)}

Call graph:

{json.dumps(call_graph or {}, indent=2)}

Potentially unreferenced functions:

{json.dumps(unreferenced_functions or [], indent=2)}

Change impact analysis:

{json.dumps(impact_analysis or {}, indent=2)}

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
Do not infer the purpose, role, or type of any module.
Do not invent files, dependencies, usage, or architectural intent.
If the supplied analysis does not establish a fact, do not state it as fact.
"""

    return generate_response(prompt)