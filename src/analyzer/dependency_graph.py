import ast
from pathlib import Path
import networkx as nx


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

        graph.add_node(
            module,
            file_path=str(file_path),
        )

    for file_path in python_files:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))

        relative = file_path.relative_to(project_root)
        source_module = str(relative.with_suffix("")).replace("\\", ".").replace("/", ".")

        if source_module.endswith(".__init__"):
            source_module = source_module[:-9]

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    _add_dependency(
                        graph,
                        source_module,
                        alias.name,
                        module_map,
                    )

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    _add_dependency(
                        graph,
                        source_module,
                        node.module,
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