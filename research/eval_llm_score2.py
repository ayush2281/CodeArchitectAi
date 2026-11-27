import sys, json, re, shutil, tempfile, collections
from pathlib import Path
src = open(Path(__file__).resolve().parent / "eval_llm.py", encoding="utf8").read().split("out = []")[0]
exec(src)
reports = json.load(open(EXP / "llm_results_rep.json"))
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
    rows.append({"repo": x["repo"], "model": x["model"], "rep": x.get("rep", 0), "num_claims": n, "strict_ok": strict, "lenient_ok": lenient, "ungrounded": bad})
json.dump({"by_model": {k: dict(v) for k, v in agg.items()}, "rows": rows}, open(EXP / "llm_rep_scored.json", "w"), indent=1)
for k, v in agg.items(): print(k, dict(v))
for r in rows:
    if r["ungrounded"]: print(r["repo"], r["model"][:10], r["ungrounded"])

import statistics, csv, random
# repeat-to-repeat variability: per (repo, model) fraction of numeric claims that are strictly correct, spread across 3 repeats
grp = collections.defaultdict(list)
for r in rows:
    grp[(r["repo"], r["model"])].append(r["strict_ok"] / r["num_claims"] if r["num_claims"] else None)
var = collections.defaultdict(list)
for (repo, mdl), v in grp.items():
    v = [x for x in v if x is not None]
    if len(v) >= 2: var[mdl].append(max(v) - min(v))
spread = {m: round(statistics.mean(v), 3) for m, v in var.items()}
unstable = {m: sum(1 for x in v if x > 0) for m, v in var.items()}
d = json.load(open(EXP / "llm_rep_scored.json")); d["repeat_spread_mean"] = spread; d["pairs_with_any_variation"] = unstable; d["pairs"] = {m: len(v) for m, v in var.items()}
json.dump(d, open(EXP / "llm_rep_scored.json", "w"), indent=1); print("spread", spread, unstable, d["pairs"])
# blinded rating sheet for human raters (rep 0 of every repository x model)
random.seed(11)
sel = [x for x in reports if x.get("rep", 0) == 0 and "report" in x]; random.shuffle(sel)
with open(EXP / "llm_rating_sheet.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["item_id", "repository", "ground_truth_summary", "report_text", "factual_correctness_1to5", "relevance_of_recommendations_1to5", "completeness_1to5", "clarity_1to5", "consistency_with_analysis_1to5", "comments"])
    key = []
    for n, x in enumerate(sel, 1):
        Fx = facts[x["repo"]]
        gts = f"modules={Fx['n_mod']}; functions={Fx['n_func']}; dependency edges={Fx['n_edges']}; call relationships={Fx['n_calls']}; issues={Fx['n_issues']}; cycles={Fx['n_cycles']}; modules with fan-in+fan-out>=3: {Fx['n_high']}"
        w.writerow([f"R{n:02d}", x["repo"], gts, x["report"], "", "", "", "", "", ""]); key.append({"item_id": f"R{n:02d}", "repo": x["repo"], "model": x["model"]})
json.dump(key, open(EXP / "llm_rating_key.json", "w"), indent=1)
