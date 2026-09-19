import json

from src.analyzer.llm_client import generate_response


def generate_architecture_report(
    issues: list[dict],
    analysis: dict,
) -> str:
    """Generate an architecture report using the local LLM."""
    prompt = f"""
You are a software architecture analyst.

Analyze the following static-analysis results from a Python codebase.

Architecture issues:
{json.dumps(issues, indent=2)}

Dependency analysis:
{json.dumps(analysis, indent=2)}

Provide a concise report with these sections:

1. Architecture Overview
2. Detected Problems
3. Why They Matter
4. Recommended Improvements

Only discuss problems supported by the supplied analysis.
Do not invent files, dependencies, or problems.
"""

    return generate_response(prompt)