from pathlib import Path
from src.analyzer.impact_analysis import explain_impact  
from src.analyzer.architecture_report import generate_architecture_report
from src.analyzer.repository_scanner import find_python_files
from src.analyzer.dependency_graph import build_dependency_graph
from src.analyzer.architecture_analysis import (
    analyze_dependencies,
    find_circular_dependencies,
    find_high_connectivity_modules,
)
from src.analyzer.call_graph import build_call_graph
from src.analyzer.dead_code import find_potentially_unreferenced_functions
from src.analyzer.architecture_issues import (
    detect_architecture_issues,
    summarize_architecture_issues,
)
from src.analyzer.graph_visualization import (
    create_dependency_graph,
    get_graph_statistics,
    save_dependency_graph,
    save_call_graph,
)
def analyze_project(
    repo_path: str,
    changed_module: str | None = None,
    changed_function: str | None = None,
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
    high_connectivity_modules = find_high_connectivity_modules(
        dependency_analysis
    )
    # 4. Detect circular dependencies
    circular_dependencies = find_circular_dependencies(
        dependency_graph
    )

    # 5. Detect architecture issues
    architecture_issues = detect_architecture_issues(
        dependency_graph,
        dependency_analysis,
        circular_dependencies,
        high_connectivity_modules,
    )
    architecture_issue_summary = summarize_architecture_issues(
        architecture_issues
    )
   
    # 6. Build call graph
    call_graph = build_call_graph(
        python_files,
        project_root,
    )

    # 7. Find potentially unused functions
    unreferenced_functions = find_potentially_unreferenced_functions(
        call_graph,
        entry_points={
            "src.analyzer.analyze_project.analyze_project",
            "src.analyzer.architecture_report.generate_architecture_report",
        },
    )  
    dependency_graph_visual = create_dependency_graph(
        list(dependency_graph.nodes),
        list(dependency_graph.edges),
    )

    graph_statistics = get_graph_statistics(
        dependency_graph_visual
    )  
    save_dependency_graph(
        dependency_graph_visual,
        "dependency_graph.html",
    )
    save_call_graph(
        call_graph,
        "call_graph.html",
    )
    # 8. Analyze change impact if a module was specified
    impact_analysis = None

    if changed_module:
        try:
            impact_analysis = explain_impact(
                dependency_graph,
                changed_module,
                call_graph,
                changed_function,
            )
        except ValueError as error:
            impact_analysis = {
              "error": str(error),
            }
    architecture_report = generate_architecture_report(
        architecture_issues,
        dependency_analysis,
        call_graph={
            "nodes": list(call_graph.nodes),
            "edges": list(call_graph.edges),
        },
        unreferenced_functions=unreferenced_functions,
        impact_analysis=impact_analysis,
        graph_statistics=graph_statistics,
    )        
    return {
        "files": [str(path) for path in python_files],
        "dependency_analysis": dependency_analysis,
        "high_connectivity_modules": high_connectivity_modules,
        "circular_dependencies": circular_dependencies,
        "architecture_issues": architecture_issues,
        "architecture_issue_summary": architecture_issue_summary,
        "architecture_report": architecture_report,
        "dependency_graph_nodes": list(dependency_graph.nodes),
        "dependency_graph_edges": list(dependency_graph.edges),
        "graph_statistics": graph_statistics,
        "call_graph_nodes": list(call_graph.nodes),
        "call_graph_edges": list(call_graph.edges),
        "unreferenced_functions": unreferenced_functions,
        "impact_analysis": impact_analysis,
    }