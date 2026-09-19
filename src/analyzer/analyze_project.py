from pathlib import Path
from src.analyzer.impact_analysis import explain_impact  
from src.analyzer.repository_scanner import find_python_files
from src.analyzer.dependency_graph import build_dependency_graph
from src.analyzer.architecture_analysis import (
    analyze_dependencies,
    find_circular_dependencies,
)
from src.analyzer.call_graph import build_call_graph
from src.analyzer.dead_code import find_potentially_unused_functions
from src.analyzer.architecture_issues import detect_architecture_issues


def analyze_project(
    repo_path: str,
    changed_module: str | None = None,
) -> dict:
    """Run the complete static analysis pipeline."""

    project_root = Path(repo_path).resolve()

    # 1. Find Python files
    python_files = find_python_files(str(project_root))

    # 2. Build dependency graph
    dependency_graph = build_dependency_graph(
        python_files,
        project_root,
    )

    # 3. Analyze dependencies
    dependency_analysis = analyze_dependencies(
        dependency_graph
    )

    # 4. Detect circular dependencies
    circular_dependencies = find_circular_dependencies(
        dependency_graph
    )

    # 5. Detect architecture issues
    architecture_issues = detect_architecture_issues(
        dependency_graph,
        dependency_analysis,
    )

    # 6. Build call graph
    call_graph = build_call_graph(
        python_files,
        project_root,
    )

    # 7. Find potentially unused functions
    unused_functions = find_potentially_unused_functions(
        call_graph
    )
    # 8. Analyze change impact if a module was specified
    impact_analysis = None

    if changed_module:
        try:
             impact_analysis = explain_impact(
                 dependency_graph,
                 changed_module,
             )
        except ValueError as error:
            impact_analysis = {
              "error": str(error),
            }
    return {
        "files": [str(path) for path in python_files],
        "dependency_analysis": dependency_analysis,
        "circular_dependencies": circular_dependencies,
        "architecture_issues": architecture_issues,
        "call_graph_nodes": list(call_graph.nodes),
        "call_graph_edges": list(call_graph.edges),
        "potentially_unused_functions": unused_functions,
        "impact_analysis": impact_analysis,
    }