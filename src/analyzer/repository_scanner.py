from pathlib import Path
EXCLUDED_DIRS = {
    ".venv",
    ".git",
    "__pycache__",
    "github-test-repo",
}

def find_python_files(repo_path: str) -> list[Path]:
    """Find Python files while ignoring generated/dependency directories."""
    root = Path(repo_path)

    if not root.exists():
        raise FileNotFoundError(f"Repository not found: {root}")

    python_files = []

    for path in root.rglob("*.py"):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue

        python_files.append(path)

    return python_files