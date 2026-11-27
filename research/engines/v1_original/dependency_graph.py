from pathlib import Path
import ast
import networkx as nx
from src.analyzer.ast_parser import parse_python_file, extract_imports
def build_dependency_graph(
    python_files: list[Path],
    project_root: Path,
) -> nx.DiGraph:
    """Build a directed graph of project-file dependencies."""
    graph = nx.DiGraph()

    module_map = {}

    for file_path in python_files:
        relative = file_path.relative_to(project_root)
        module = str(relative.with_suffix("")).replace("\\", ".").replace("/", ".")

        if module.endswith(".__init__"):
            module = module[:-9]

        module_map[module] = file_path

        if module.startswith("src."):
            module_map[module[4:]] = file_path

        graph.add_node(
            module,
            file_path=str(file_path),
        )

    for file_path in python_files:
        tree = parse_python_file(file_path)
        imports = extract_imports(tree)

        relative = file_path.relative_to(project_root)
        source_module = str(relative.with_suffix("")).replace("\\", ".").replace("/", ".")

        if source_module.endswith(".__init__"):
            source_module = source_module[:-9]

        for imported_module, level in imports:
            if level > 0:
                parts = source_module.split(".")
                base = ".".join(parts[:-level])

                if imported_module:
                    imported_module = f"{base}.{imported_module}"
                else:
                    imported_module = base

            _add_dependency(
                graph,
                source_module,
                imported_module,
                module_map,
            )

    return graph


def _add_dependency(
    graph: nx.DiGraph,
    source_module: str,
    imported_module: str,
    module_map: dict[str, Path],
) -> None:
    """Add an edge when an imported module belongs to the project."""
    if imported_module in module_map:
        graph.add_edge(source_module, imported_module)