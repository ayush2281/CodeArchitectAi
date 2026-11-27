"""Automatic faithfulness check of LLM architecture reports (Groq models) against the structured analysis."""
import sys, os, json, re, time, tempfile, logging
from pathlib import Path
EXP = Path(__file__).resolve().parent
APP = Path(sys.argv[1])            # CodeArchitectAi-v2 folder
sys.path.insert(0, str(APP)); sys.path.insert(0, str(EXP))
logging.disable(logging.CRITICAL)
for l in open(r"<local-path>", encoding="utf8"):
    if "=" in l and not l.startswith("#"):
        k, v = l.strip().split("=", 1)
        if k == "GROQ_API_KEY": os.environ[k] = v.strip().strip('"')
from src.analyzer.analyze_project import analyze_project
from eval_repos import REPOS, D

MODELS = ["qwen/qwen3.8-27b", "openai/gpt-oss-20b", "openai/gpt-oss-120b"]
SELECT = ["itsdangerous", "python-dotenv", "markupsafe", "pluggy", "tomli", "click", "jinja", "requests", "flask", "httpx"]
SECTIONS = ["overview", "problem", "matter", "improve"]


def facts_of(res):
    mods = set(res["dependency_graph_nodes"]); funcs = set(res["call_graph_nodes"])
    ids = set(mods) | set(funcs) | {m.split(".")[-1] for m in mods} | {f.split(".")[-1] for f in funcs}
    for i in res["architecture_issues"]:
        ids.update(i.get("modules", []) + ([i["module"]] if "module" in i else []))
    return {"modules": mods, "funcs": funcs, "ids": ids,
            "n_mod": len(mods), "n_func": len(funcs), "n_calls": len(res["call_graph_edges"]), "n_edges": len(res["dependency_graph_edges"]),
            "n_issues": len(res["architecture_issues"]), "n_cycles": len(res["circular_dependencies"]),
            "analysis": res["dependency_analysis"]}


NOUNS = {"modules?": "n_mod", "functions?": "n_func", "call relationships?|call edges|function calls": "n_calls",
         "dependency (?:edges|relationships)|dependencies|import edges": "n_edges", "(?:architecture )?issues": "n_issues",
         "circular dependenc(?:y|ies)|cycles?": "n_cycles"}


def check(report, F):
    text = report.replace("**", "")
    # identifier claims: backticked or dotted code-like tokens
    toks = set(re.findall(r"`([A-Za-z_][\w.]*[\w])`", text)) | set(re.findall(r"\b([A-Za-z_]\w*(?:\.\w+){1,6})\b", text))
    toks = {t for t in toks if ("." in t or "_" in t) and not re.fullmatch(r"\d+(\.\d+)?", t) and not t.endswith((".py", ".md", ".js")) and len(t) > 3}
    toks = {t for t in toks if not re.fullmatch(r"(e\.g|i\.e|etc)\.?", t)}
    sup = {t for t in toks if t in F["ids"] or any(t in x or x.endswith(t) for x in F["modules"])}
    # numeric claims
    nclaims = ncorrect = 0; wrong = []
    for pat, key in NOUNS.items():
        for m in re.finditer(rf"\b(\d[\d,]*)\s+(?:\w+\s+){{0,2}}?(?:{pat})\b", text, re.I):
            val = int(m.group(1).replace(",", "")); nclaims += 1
            if val == F[key]: ncorrect += 1
            else: wrong.append((m.group(0), F[key]))
    # fan-in / fan-out claims about named modules
    for m in re.finditer(r"`?([A-Za-z_][\w.]*)`?[^.\n]{0,80}?fan-?\s?(in|out)\D{0,12}(\d+)", text, re.I):
        mod = m.group(1); kind = "fan_" + m.group(2).lower(); val = int(m.group(3))
        for cand in F["analysis"]:
            if cand == mod or cand.endswith("." + mod):
                nclaims += 1
                if F["analysis"][cand][kind] == val: ncorrect += 1
                else: wrong.append((m.group(0)[:60], F["analysis"][cand][kind]))
                break
    secs = sum(1 for s in SECTIONS if re.search(s, text, re.I))
    return {"id_claims": len(toks), "id_supported": len(sup), "num_claims": nclaims, "num_correct": ncorrect,
            "sections_present": secs, "unsupported_ids": sorted(toks - sup)[:15], "wrong_numbers": wrong[:6], "chars": len(report)}


out = []
for name in SELECT:
    rel, pkgs = REPOS[name]
    root = (D / rel).resolve()
    import shutil
    tmp = Path(tempfile.mkdtemp()) / name
    for pk in pkgs: shutil.copytree(root / pk, tmp / pk, ignore=shutil.ignore_patterns("__pycache__"))
    for model in MODELS:
      for rep_i in range(3):
          t0 = time.time(); rep = ""; err = None
          for attempt in range(3):
              res = analyze_project(str(tmp), generate_report=True, llm_settings={"provider": "groq", "model": model},
                                    output_directory=Path(tempfile.mkdtemp()), entry_points=set())
              rep, err = res["architecture_report"], res["report_error"]
              if rep: break
              time.sleep(8)
          row = {"repo": name, "model": model, "rep": rep_i, "seconds": round(time.time() - t0, 1), "error": (err or "")[:160]}
          if rep:
              row.update(check(rep, facts_of(res))); row["report"] = rep
          out.append(row); print(name, model, {k: v for k, v in row.items() if k != "report"}); sys.stdout.flush()
json.dump(out, open(EXP / "llm_results_rep.json", "w"), indent=1)
