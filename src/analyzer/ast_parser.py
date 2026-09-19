import ast
from pathlib import Path


def parse_python_file(file_path: Path) -> ast.AST:
    """Parse a Python file into an AST."""
    source = file_path.read_text(encoding="utf-8")
    return ast.parse(source, filename=str(file_path))


def extract_imports(tree: ast.AST) -> list[str]:
    """Extract imported module names from an AST."""
    imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    return imports
def extract_definitions(tree: ast.AST) -> dict[str, list[str]]:
    """Extract function and class names from an AST."""
    functions = []
    classes = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)

        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)

    return {
        "functions": functions,
        "classes": classes,
    }