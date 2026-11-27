import ast
from pathlib import Path

import networkx as nx


def build_call_graph(
    python_files: list[Path],
    project_root: Path,
) -> nx.DiGraph:
    """Build a graph of calls between project-defined functions."""
    graph = nx.DiGraph()

    function_map = {}

    # First pass: collect all project-defined functions.
    for file_path in python_files:
        relative = file_path.relative_to(project_root)
        module = (
            str(relative.with_suffix(""))
            .replace("\\", ".")
            .replace("/", ".")
        )

        if module.endswith(".__init__"):
            module = module[:-9]

        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                function_name = f"{module}.{node.name}"
                function_map[(module, node.name)] = function_name
                graph.add_node(function_name)

    # Second pass: find function calls.
    for file_path in python_files:
        relative = file_path.relative_to(project_root)
        module = (
            str(relative.with_suffix(""))
            .replace("\\", ".")
            .replace("/", ".")
        )

        if module.endswith(".__init__"):
            module = module[:-9]

        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))

        import_map = {}

        for import_node in ast.walk(tree):
            if isinstance(import_node, ast.ImportFrom):
                if import_node.module:
                    for alias in import_node.names:
                        import_map[alias.asname or alias.name] = import_node.module
            elif isinstance(import_node, ast.Import):
                for alias in import_node.names:
                   import_map[alias.asname or alias.name] = alias.name            

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            caller = f"{module}.{node.name}"

            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    called_name = _get_called_name(child.func)

                    if called_name is None:
                        continue

                    if "." in called_name:
                       imported_name, function_name = called_name.split(".", 1)
                       target_module = import_map.get(imported_name, imported_name)

                       if target_module in {module.split(".")[0], imported_name}:
                           candidate = f"{module.rsplit('.', 1)[0]}.{imported_name}"
                           if (candidate, function_name) in function_map:
                               target_module = candidate
                    else:
                       target_module = import_map.get(called_name, module)
                       function_name = called_name

                    key = (target_module, function_name)

                    if key in function_map:
                        graph.add_edge(
                            caller,
                            function_map[key],
                        )

    return graph


def _get_called_name(node: ast.AST) -> str | None:
    """Extract the called function name."""
    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        if isinstance(node.value, ast.Name):
           return f"{node.value.id}.{node.attr}"

        return node.attr

    return None