"""Fault-injection behaviour test of the deployed tool's own project.

For each project function in turn, its body is replaced by `raise` in a throw-away copy, a fixed set of end-to-end
scenarios is run in a fresh process, and the project functions through which the injected error propagates are recorded.
These observed callers are compared with the callers the tool's impact analysis predicts on the unmodified code.
The language-model service is replaced by a local stand-in, so no network call or API key is used."""
import ast
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DRIVER = r'''
import json, sys, tempfile, traceback, types
from pathlib import Path
repo = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(repo))

class _Groq:
    def __init__(self, **kw):
        message = types.SimpleNamespace(content="report")
        reply = types.SimpleNamespace(choices=[types.SimpleNamespace(message=message)])
        self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=lambda **k: reply))

sys.modules["groq"] = types.SimpleNamespace(Groq=_Groq)
sys.modules["dotenv"] = types.SimpleNamespace(load_dotenv=lambda *a, **k: None)
import os
os.environ["GROQ_API_KEY"] = "not-a-real-key"

def small_project():
    d = Path(tempfile.mkdtemp())
    files = {"a.py": "import b\ndef main():\n    return b.f()\n",
             "b.py": "import c\nimport a\ndef f():\n    return c.g()\n",
             "c.py": "def g():\n    return 1\ndef _hidden():\n    return 2\n",
             "d.py": "import a\nimport b\nimport c\n", "e.py": "import b\n", "f.py": "import b\n"}
    for name, text in files.items():
        (d / name).write_text(text)
    return d

P = "src.analyzer."
def scenario_self():
    from src.analyzer.analyze_project import analyze_project
    analyze_project(str(repo), changed_module=P + "repository_scanner", changed_function=P + "repository_scanner.find_python_files")

def scenario_indirect():
    from src.analyzer.analyze_project import analyze_project
    analyze_project(str(repo), changed_module=P + "ast_parser", changed_function=P + "ast_parser.parse_python_file")

def scenario_small():
    from src.analyzer.analyze_project import analyze_project
    analyze_project(str(small_project()), changed_module="c", changed_function="c.g", entry_points={"a.main"})

observed, failed = set(), []
for scenario in (scenario_self, scenario_indirect, scenario_small):
    try:
        scenario()
    except Exception as error:
        failed.append(scenario.__name__)
        for frame in traceback.extract_tb(error.__traceback__):
            path = Path(frame.filename).resolve()
            if repo in path.parents and frame.name != "<module>":
                module = ".".join(path.relative_to(repo).with_suffix("").parts)
                observed.add(module + "." + frame.name)
        if not traceback.extract_tb(error.__traceback__):
            raise
print("RESULT" + json.dumps({"observed": sorted(observed), "failed": failed}))
'''


def functions(repo):
    for path in sorted((repo / "src").rglob("*.py")):
        module = ".".join(path.relative_to(repo).with_suffix("").parts)
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                yield module, node.name, path.relative_to(repo), node


def mutate(file, node):
    lines = file.read_text(encoding="utf-8").split("\n")
    first, last = node.body[0].lineno - 1, node.end_lineno
    indent = " " * node.body[0].col_offset
    lines[first:last] = [indent + 'raise RuntimeError("INJECTED")']
    file.write_text("\n".join(lines), encoding="utf-8")


def run(repo, driver):
    done = subprocess.run([sys.executable, str(driver), str(repo)], capture_output=True, text=True, timeout=300, cwd=repo)
    line = [x for x in done.stdout.splitlines() if x.startswith("RESULT")]
    if not line:
        raise RuntimeError(done.stderr[-800:])
    return json.loads(line[0][6:])


def main(source):
    source = Path(source).resolve()
    work = Path(tempfile.mkdtemp())
    driver = work / "driver.py"
    driver.write_text(DRIVER, encoding="utf-8")
    clean = work / "clean"
    shutil.copytree(source, clean, ignore=shutil.ignore_patterns(".git", "__pycache__", "outputs", ".env"))
    base = run(clean, driver)
    assert not base["failed"], ("unmodified code fails", base)

    # predictions come from the unmodified deployed analyser
    sys.path.insert(0, str(clean))
    import networkx as nx
    from src.analyzer.repository_scanner import find_python_files
    from src.analyzer.call_graph import build_call_graph
    graph = build_call_graph(find_python_files(str(clean)), clean)

    rows = []
    for number, (module, name, rel, node) in enumerate(functions(clean)):
        target = f"{module}.{name}"
        copy = work / f"m{number}"
        shutil.copytree(clean, copy, ignore=shutil.ignore_patterns("__pycache__", "outputs"))
        mutate(copy / rel, node)
        result = run(copy, driver)
        observed = set(result["observed"]) - {target}
        predicted = set(nx.ancestors(graph, target)) if target in graph else set()
        # functions in the Streamlit script are never run by the scenarios
        predicted = {p for p in predicted if not p.startswith("src.app.")}
        executed = bool(result["failed"])
        rows.append({"function": target, "executed": executed, "scenarios_failed": result["failed"],
                     "observed": sorted(observed), "predicted": sorted(predicted),
                     "tp": len(observed & predicted), "fp": len(predicted - observed), "fn": len(observed - predicted)})
        print(f"{target:70s} executed={executed!s:5s} observed={len(observed)} predicted={len(predicted)}", flush=True)
        shutil.rmtree(copy, ignore_errors=True)

    used = [r for r in rows if r["executed"]]
    tp, fp, fn = (sum(r[k] for r in used) for k in ("tp", "fp", "fn"))
    precision, recall = tp / (tp + fp), tp / (tp + fn)
    summary = {"functions": len(rows), "executed_mutants": len(used), "tp": tp, "fp": fp, "fn": fn, "precision": precision,
               "recall": recall, "f1": 2 * precision * recall / (precision + recall),
               "mutants_exactly_right": sum(r["fp"] == 0 and r["fn"] == 0 for r in used),
               "not_executed": [r["function"] for r in rows if not r["executed"]]}
    json.dump({"summary": summary, "rows": rows}, open(Path(__file__).with_name("behaviour_results.json"), "w"), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
