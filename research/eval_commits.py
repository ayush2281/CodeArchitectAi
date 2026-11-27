"""Module-level change-impact prediction vs co-changed modules in real commits."""
import sys, json, subprocess, random, logging
from pathlib import Path
from collections import defaultdict
EXP = Path(__file__).resolve().parent
sys.path.insert(0, str(EXP / "v1")); sys.path.insert(0, str(EXP / "v2"))
logging.disable(logging.CRITICAL)
import networkx as nx
from src.analyzer.dependency_graph import build_dependency_graph as v1_dep
from ca2 import engine as E2
from eval_repos import REPOS, D

MAXC = 400  # most recent commits inspected per repository
random.seed(0)


def commits(repo_dir, pkgdirs, root):
    cmd = ["git", "-C", str(repo_dir), "log", f"-n{MAXC}", "--no-merges", "--name-only", "--pretty=format:@@%H", "--diff-filter=AM", "--"]
    out = subprocess.run(cmd + [f"{(root / pk).relative_to(repo_dir).as_posix()}" for pk in pkgdirs], capture_output=True, text=True, encoding="utf-8").stdout
    res, cur = [], None
    for line in out.splitlines():
        if line.startswith("@@"):
            cur = [line[2:], []]; res.append(cur)
        elif line.strip().endswith(".py") and cur is not None:
            cur[1].append(line.strip())
    return res  # newest first


def modname(path_rel_repo, repo_dir, root):
    p = (repo_dir / path_rel_repo).resolve()
    try:
        parts = list(p.relative_to(root).with_suffix("").parts)
    except ValueError:
        return None
    if parts[-1] == "__init__": parts = parts[:-1]
    return ".".join(parts)


REPO_IDX = [0]
agg = defaultdict(lambda: [0, 0, 0])
pairs_log = defaultdict(list)
per_repo = {}
n_pairs = 0
for name, (rel, pkgs) in REPOS.items():
    root = (D / rel).resolve(); repo_dir = D / Path(rel).parts[0]
    if not root.exists() or not (repo_dir / ".git").exists():
        continue
    files = [f for pk in pkgs for f in (root / pk).rglob("*.py") if "__pycache__" not in f.parts]
    if not files: continue
    REPO_IDX[0] = len(per_repo)
    p = E2.Project(root, files); g2 = E2.build_dependency_graph(p)
    g1 = v1_dep(files, root)
    mods = set(g2.nodes)
    cl = commits(repo_dir, pkgs, root)
    # history (strictly older commits) for the history baseline
    parsed = []
    for h, fs in cl:
        ms = sorted({m for m in (modname(f, repo_dir, root) for f in fs) if m in mods})
        parsed.append(ms)
    local = defaultdict(lambda: [0, 0, 0]); npairs = 0
    for i, ms in enumerate(parsed):
        if not 2 <= len(ms) <= 15: continue
        older = parsed[i + 1:]
        co = defaultdict(set)
        for om in older:
            if len(om) <= 15:
                for a in om:
                    co[a].update(x for x in om if x != a)
        for m in ms:
            truth = set(ms) - {m}
            preds = {
                "dependents (v2, transitive)": nx.ancestors(g2, m),
                "dependents (v2, direct)": set(g2.predecessors(m)),
                "dependents (v1, transitive)": nx.ancestors(g1, m) if m in g1 else set(),
                "neighbours (v2, in+out, direct)": set(g2.predecessors(m)) | set(g2.successors(m)),
                "dependencies (v2, transitive)": nx.descendants(g2, m),
                "history (co-change in older commits)": co.get(m, set()),
                "dependents(v2, transitive) + history": nx.ancestors(g2, m) | co.get(m, set()),
                "all other modules": mods - {m},
            }
            k = len(preds["dependents (v2, transitive)"])
            others = sorted(mods - {m}); preds["random (same size as v2 dependents)"] = set(random.sample(others, min(k, len(others))))
            for lab, ref in (("random (same size as v2 direct dependents)", "dependents (v2, direct)"), ("random (same size as v2 neighbours)", "neighbours (v2, in+out, direct)")):
                kk = len(preds[ref]); preds[lab] = set(random.sample(others, min(kk, len(others))))
            for key, pr in preds.items():
                pr = pr - {m}
                tp = len(pr & truth); pairs_log[key].append((tp, len(pr - truth), len(truth - pr), REPO_IDX[0]))
                for tgt in (agg[key], local[key]):
                    tgt[0] += tp; tgt[1] += len(pr - truth); tgt[2] += len(truth - pr)
            npairs += 1
    n_pairs += npairs
    per_repo[name] = {"commits_scanned": len(cl), "pairs": npairs, "v2_dependents_F1": None}
    if local["dependents (v2, transitive)"][0] + local["dependents (v2, transitive)"][2] > 0:
        t = local["dependents (v2, transitive)"]; pr = t[0] / (t[0] + t[1]) if t[0] + t[1] else 0; rc = t[0] / (t[0] + t[2]) if t[0] + t[2] else 0
        per_repo[name]["v2_dependents_F1"] = round(2 * pr * rc / (pr + rc), 3) if pr + rc else 0.0
    print(name, len(cl), npairs); sys.stdout.flush()


def prf(v):
    tp, fp, fn = v
    p = tp / (tp + fp) if tp + fp else 0.0; r = tp / (tp + fn) if tp + fn else 0.0
    return [round(p, 4), round(r, 4), round(2 * p * r / (p + r), 4) if p + r else 0.0]

res = {k: {"tp": v[0], "fp": v[1], "fn": v[2], "P_R_F1": prf(v)} for k, v in agg.items()}
json.dump({"pairs": n_pairs, "methods": res, "per_repo": per_repo}, open(EXP / "commit_results.json", "w"), indent=1)
print("pairs", n_pairs)
for k, v in res.items(): print(k, v["P_R_F1"])

import numpy as np
rng = np.random.default_rng(0)
def f1_of(arr):
    tp, fp, fn = arr[:, :3].sum(0)
    p = tp / (tp + fp) if tp + fp else 0; r = tp / (tp + fn) if tp + fn else 0
    return 2 * p * r / (p + r) if p + r else 0
pl = {k: np.array(v) for k, v in pairs_log.items()}
n = len(next(iter(pl.values())))
boot = {k: [] for k in pl}
for _ in range(1000):
    idx = rng.integers(0, n, n)
    for k, a in pl.items(): boot[k].append(f1_of(a[idx]))
ci = {k: [round(float(np.percentile(v, 2.5)), 4), round(float(np.percentile(v, 97.5)), 4)] for k, v in boot.items()}
def diff(a, b):
    d = np.array(boot[a]) - np.array(boot[b]); return [round(float(d.mean()), 4), round(float(np.percentile(d, 2.5)), 4), round(float(np.percentile(d, 97.5)), 4)]
# repository-clustered bootstrap: resample repositories, then instances within each selected repository
repo_ids = sorted(set(int(x) for x in next(iter(pl.values()))[:, 3]))
by_repo = {k: {r: a[a[:, 3] == r] for r in repo_ids} for k, a in pl.items()}
# instances of all methods are aligned (same order) so a shared within-repo index is valid
cboot = {k: [] for k in pl}
for _ in range(1000):
    chosen = rng.choice(repo_ids, size=len(repo_ids), replace=True)
    sel = {}
    for r in chosen:
        nr = len(by_repo[next(iter(pl))][r]); idx = rng.integers(0, nr, nr)
        for k in pl: sel.setdefault(k, []).append(by_repo[k][r][idx][:, :3])
    for k in pl: cboot[k].append(f1_of(np.vstack(sel[k])))
cci = {k: [round(float(np.percentile(v, 2.5)), 4), round(float(np.percentile(v, 97.5)), 4)] for k, v in cboot.items()}
def cdiff(a, b):
    d = np.array(cboot[a]) - np.array(cboot[b]); return [round(float(d.mean()), 4), round(float(np.percentile(d, 2.5)), 4), round(float(np.percentile(d, 97.5)), 4)]
extra = {"F1_95CI_clustered": cci,
         "clustered_diff_direct_minus_random_direct": cdiff("dependents (v2, direct)", "random (same size as v2 direct dependents)"),
         "clustered_diff_neighbours_minus_random_neighbours": cdiff("neighbours (v2, in+out, direct)", "random (same size as v2 neighbours)"),
         "clustered_diff_history_minus_neighbours": cdiff("history (co-change in older commits)", "neighbours (v2, in+out, direct)"),
         "clustered_diff_transitive_v2_minus_v1": cdiff("dependents (v2, transitive)", "dependents (v1, transitive)"),
         "F1_95CI": ci,
         "diff_direct_minus_random_direct": diff("dependents (v2, direct)", "random (same size as v2 direct dependents)"),
         "diff_neighbours_minus_random_neighbours": diff("neighbours (v2, in+out, direct)", "random (same size as v2 neighbours)"),
         "diff_history_minus_neighbours": diff("history (co-change in older commits)", "neighbours (v2, in+out, direct)"),
         "diff_transitive_v2_minus_v1": diff("dependents (v2, transitive)", "dependents (v1, transitive)")}
d = json.load(open(EXP / "commit_results.json")); d["bootstrap"] = extra; json.dump(d, open(EXP / "commit_results.json", "w"), indent=1)
print(json.dumps(extra, indent=1))
