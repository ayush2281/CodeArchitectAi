import sys, json, re, shutil, tempfile, collections
from pathlib import Path
src = open(Path(__file__).resolve().parent / "eval_llm.py", encoding="utf8").read().split("out = []")[0]
exec(src)
reports = json.load(open(EXP / "llm_results.json"))
facts = {}
for name in SELECT:
    rel, pkgs = REPOS[name]; root = (D / rel).resolve(); tmp = Path(tempfile.mkdtemp()) / name
    for pk in pkgs: shutil.copytree(root / pk, tmp / pk, ignore=shutil.ignore_patterns("__pycache__"))
    res = analyze_project(str(tmp), generate_report=False, output_directory=Path(tempfile.mkdtemp()), entry_points=set())
    F = facts_of(res)
    F["n_high"] = len([m for m, v in res["dependency_analysis"].items() if v["total_connections"] >= 3])
    F["sev"] = res["architecture_issue_summary"]
    F["prompt_numbers"] = {F["n_mod"], F["n_func"], F["n_calls"], F["n_edges"], F["n_issues"], F["n_cycles"], F["n_high"], 8, F["sev"]["high"], F["sev"]["medium"], F["sev"]["total"]}
    for v in res["dependency_analysis"].values():
        if v["total_connections"] >= 0: pass
    top = sorted(res["dependency_analysis"].items(), key=lambda kv: kv[1]["total_connections"], reverse=True)[:8]
    for _, v in top: F["prompt_numbers"].update({v["fan_in"], v["fan_out"], v["total_connections"]})
    facts[name] = F
rows = []
agg = collections.defaultdict(lambda: collections.Counter())
for x in reports:
    if "report" not in x: continue
    F = facts[x["repo"]]; text = x["report"].replace("**", "")
    strict = lenient = n = 0; bad = []
    for pat, key in NOUNS.items():
        for m in re.finditer(rf"\b(\d[\d,\u202f]*)\s+(?:\w+\s+){{0,2}}?(?:{pat})\b", text, re.I):
            val = int(re.sub(r"[,\u202f]", "", m.group(1))); n += 1
            ok_strict = val == F[key] or (key == "n_mod" and val == F["n_high"])
            ok_len = val in F["prompt_numbers"]
            strict += ok_strict; lenient += ok_len
            if not ok_len: bad.append(m.group(0))
    a = agg[x["model"]]
    a["reports"] += 1; a["num_claims"] += n; a["num_strict"] += strict; a["num_lenient"] += lenient
    a["id_claims"] += x["id_claims"]; a["id_supported"] += x["id_supported"]; a["complete"] += (x["sections_present"] == 4)
    a["seconds"] += x["seconds"]
    rows.append({"repo": x["repo"], "model": x["model"], "num_claims": n, "strict_ok": strict, "lenient_ok": lenient, "ungrounded": bad})
json.dump({"by_model": {k: dict(v) for k, v in agg.items()}, "rows": rows}, open(EXP / "llm_scored.json", "w"), indent=1)
for k, v in agg.items(): print(k, dict(v))
for r in rows:
    if r["ungrounded"]: print(r["repo"], r["model"][:10], r["ungrounded"])
