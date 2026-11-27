"""Calibrated, explainable change-impact confidence: P(module n changes in the same commit | module m changed).
Static analysis + git history only; no analysed code is executed. Leave-one-repository-out evaluation."""
import sys, json, subprocess, math
from pathlib import Path
from collections import defaultdict
import numpy as np

EXP = Path(__file__).resolve().parent
sys.path.insert(0, str(EXP / "v2"))
import networkx as nx
from ca2 import engine as E2

src = open(EXP / "eval_repos.py", encoding="utf8").read()
REPOS = {}
exec(src[src.index("REPOS = {"):src.index('if "--django"')])
D = EXP / "data"
MAXC = 400
FEATS = ["direct_dependent", "direct_dependency", "indirect_dependent", "indirect_dependency", "inverse_distance",
         "history_ratio", "same_package", "log_fan_in", "log_modules"]


def commits(repo_dir, pkgdirs, root):
    cmd = ["git", "-C", str(repo_dir), "log", f"-n{MAXC}", "--no-merges", "--name-only", "--pretty=format:@@%H", "--diff-filter=AM", "--"]
    out = subprocess.run(cmd + [(root / pk).relative_to(repo_dir).as_posix() for pk in pkgdirs], capture_output=True, text=True, encoding="utf-8").stdout
    res, cur = [], None
    for line in out.splitlines():
        if line.startswith("@@"):
            cur = []; res.append(cur)
        elif line.strip().endswith(".py") and cur is not None:
            cur.append(line.strip())
    return res


def modname(rel, repo_dir, root):
    try:
        parts = list((repo_dir / rel).resolve().relative_to(root).with_suffix("").parts)
    except ValueError:
        return None
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def build():
    X, y, repo_id, inst_id = [], [], [], []
    names = []
    inst = 0
    for rname, (rel, pkgs) in REPOS.items():
        root = (D / rel).resolve(); repo_dir = D / Path(rel).parts[0]
        files = [f for pk in pkgs for f in (root / pk).rglob("*.py") if "__pycache__" not in f.parts]
        if not files:
            continue
        g = E2.build_dependency_graph(E2.Project(root, files), strict_from_imports=True)
        mods = sorted(g.nodes)
        if len(mods) < 3:
            continue
        und = g.to_undirected()
        dist = dict(nx.all_pairs_shortest_path_length(und))
        anc = {m: nx.ancestors(g, m) for m in mods}
        desc = {m: nx.descendants(g, m) for m in mods}
        parsed = [sorted({x for x in (modname(f, repo_dir, root) for f in fs) if x in g}) for fs in commits(repo_dir, pkgs, root)]
        # history from strictly older commits, accumulated oldest -> newest
        co = defaultdict(lambda: defaultdict(int)); seen = defaultdict(int)
        rid = len(names); used = 0
        for ms in reversed(parsed):
            if 2 <= len(ms) <= 15:
                for m in ms:
                    truth = set(ms) - {m}
                    for n in mods:
                        if n == m:
                            continue
                        d = dist[m].get(n)
                        X.append([float(n in set(g.predecessors(m))), float(n in set(g.successors(m))),
                                  float(n in anc[m] and not g.has_edge(n, m)), float(n in desc[m] and not g.has_edge(m, n)),
                                  1.0 / d if d else 0.0,
                                  co[m][n] / seen[m] if seen[m] else 0.0,
                                  float(m.rpartition(".")[0] == n.rpartition(".")[0]),
                                  math.log1p(g.in_degree(n)), math.log(len(mods))])
                        y.append(float(n in truth)); repo_id.append(rid); inst_id.append(inst)
                    inst += 1; used += 1
            if len(ms) <= 15:
                for a in ms:
                    seen[a] += 1
                    for b in ms:
                        if a != b:
                            co[a][b] += 1
        if used:
            names.append(rname)
        print(rname, len(mods), used, flush=True)
    return np.array(X), np.array(y), np.array(repo_id), np.array(inst_id), names


def fit(X, y, l2=1.0, iters=50):
    A = np.hstack([np.ones((len(X), 1)), X])
    w = np.zeros(A.shape[1])
    R = np.eye(A.shape[1]) * l2; R[0, 0] = 0
    for _ in range(iters):
        p = 1 / (1 + np.exp(-np.clip(A @ w, -30, 30)))
        grad = A.T @ (p - y) + R @ w
        H = (A * (p * (1 - p))[:, None]).T @ A + R
        step = np.linalg.solve(H, grad)
        w -= step
        if np.abs(step).max() < 1e-8:
            break
    return w


def predict(w, X):
    return 1 / (1 + np.exp(-np.clip(w[0] + X @ w[1:], -30, 30)))


def auc(y, s):
    order = np.argsort(s, kind="mergesort"); s_sorted = s[order]
    ranks = np.empty(len(s))
    i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and s_sorted[j + 1] == s_sorted[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2 + 1
        i = j + 1
    n1 = y.sum(); n0 = len(y) - n1
    return float((ranks[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def average_precision(y, s):
    # tie-aware: precision/recall evaluated at distinct score thresholds
    order = np.argsort(-s, kind="mergesort"); ys = y[order]; ss = s[order]
    tp = np.cumsum(ys); k = np.arange(1, len(ys) + 1)
    last = np.r_[np.where(np.diff(ss))[0], len(ss) - 1]
    rec = tp[last] / ys.sum(); prec = tp[last] / k[last]
    return float(np.sum(np.diff(np.r_[0, rec]) * prec))


def ece(y, p, bins=10):
    idx = np.minimum((p * bins).astype(int), bins - 1)
    tot = 0.0
    table = []
    for b in range(bins):
        m = idx == b
        if m.any():
            tot += m.mean() * abs(p[m].mean() - y[m].mean())
            table.append((float(p[m].mean()), float(y[m].mean()), int(m.sum())))
    return float(tot), table


def best_threshold(y, p):
    ths = np.unique(np.quantile(p, np.linspace(0, 1, 201)))
    best, bf = 0.5, -1
    for t in ths:
        pred = p >= t; tp = (pred & (y == 1)).sum()
        f = 2 * tp / (pred.sum() + y.sum()) if pred.sum() + y.sum() else 0
        if f > bf:
            bf, best = f, t
    return best


if __name__ == "__main__":
    X, y, rid, iid, names = build()
    print("rows", len(y), "positives", int(y.sum()), "instances", iid.max() + 1, "repos", len(names))
    col = {f: i for i, f in enumerate(FEATS)}
    structural = ["direct_dependent", "direct_dependency", "indirect_dependent", "indirect_dependency", "inverse_distance"]
    MODELS = {
        "Full (structure + history + context)": FEATS,
        "Without history": [f for f in FEATS if f != "history_ratio"],
        "Without structure": [f for f in FEATS if f not in structural],
        "Without context (package, fan-in, size)": structural + ["history_ratio"],
        "History only": ["history_ratio"],
        "Distance only": ["inverse_distance"],
        "Direct relations only": ["direct_dependent", "direct_dependency"],
    }
    probs = {k: np.zeros(len(y)) for k in MODELS}
    preds = {k: np.zeros(len(y), bool) for k in MODELS}
    probs["Base rate"] = np.zeros(len(y))
    reach = ((X[:, col["direct_dependent"]] + X[:, col["indirect_dependent"]]) > 0)
    for r in range(len(names)):
        tr, te = rid != r, rid == r
        probs["Base rate"][te] = y[tr].mean()
        for k, feats in MODELS.items():
            c = [col[f] for f in feats]
            w = fit(X[tr][:, c], y[tr])
            probs[k][te] = predict(w, X[te][:, c])
            t = best_threshold(y[tr], predict(w, X[tr][:, c]))
            preds[k][te] = probs[k][te] >= t
        print("fold", names[r], flush=True)
    res = {"rows": int(len(y)), "positives": int(y.sum()), "instances": int(iid.max() + 1), "repos": names, "base_rate": float(y.mean()), "models": {}}

    def prf(pred):
        tp = (pred & (y == 1)).sum(); fp = (pred & (y == 0)).sum(); fn = ((~pred) & (y == 1)).sum(); tn = len(y) - tp - fp - fn
        p = tp / (tp + fp) if tp + fp else 0; r_ = tp / (tp + fn) if tp + fn else 0
        return {"tp": int(tp), "fp": int(fp), "fn": int(fn), "tn": int(tn), "P": float(p), "R": float(r_), "F1": float(2 * p * r_ / (p + r_) if p + r_ else 0)}

    for k, p in probs.items():
        e, tbl = ece(y, p)
        m = {"auc": auc(y, p), "ap": average_precision(y, p), "brier": float(np.mean((p - y) ** 2)),
             "logloss": float(-np.mean(y * np.log(p + 1e-12) + (1 - y) * np.log(1 - p + 1e-12))), "ece": e, "reliability": tbl}
        if k in preds:
            m.update(prf(preds[k]))
        res["models"][k] = m
    res["reachability_binary"] = dict(prf(reach), auc=auc(y, reach.astype(float)), ap=average_precision(y, reach.astype(float)))
    # repository-clustered bootstrap for AUC / AP / Brier of the main comparisons
    rng = np.random.default_rng(0)
    per = [np.where(rid == r)[0] for r in range(len(names))]
    keys = ["Full (structure + history + context)", "Without history", "History only", "Distance only", "Without structure"]
    boot = {k: [] for k in keys}
    for b in range(500):
        chosen = rng.integers(0, len(names), len(names))
        idx = np.concatenate([per[c] for c in chosen])
        for k in keys:
            p = probs[k][idx]
            boot[k].append((auc(y[idx], p), average_precision(y[idx], p), float(np.mean((p - y[idx]) ** 2))))
    boot = {k: np.array(v) for k, v in boot.items()}
    ci = lambda v: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]
    res["ci"] = {k: {"auc": ci(v[:, 0]), "ap": ci(v[:, 1]), "brier": ci(v[:, 2])} for k, v in boot.items()}
    full = "Full (structure + history + context)"
    res["diff_vs_full"] = {k: {"auc": [float(np.mean(boot[full][:, 0] - boot[k][:, 0]))] + ci(boot[full][:, 0] - boot[k][:, 0]),
                               "ap": [float(np.mean(boot[full][:, 1] - boot[k][:, 1]))] + ci(boot[full][:, 1] - boot[k][:, 1]),
                               "brier": [float(np.mean(boot[full][:, 2] - boot[k][:, 2]))] + ci(boot[full][:, 2] - boot[k][:, 2])}
                           for k in keys if k != full}
    # final coefficients trained on all repositories (shipped with the tool)
    w = fit(X, y)
    res["coefficients"] = dict(zip(["intercept"] + FEATS, map(float, w)))
    res["feature_means"] = dict(zip(FEATS, map(float, X.mean(0))))
    # per-repository paired tests: exact two-sided Wilcoxon signed-rank with Holm correction
    import itertools
    def wilcoxon(a, b):
        d = np.array(a) - np.array(b); d = d[d != 0]; n = len(d)
        order = np.argsort(np.abs(d)); ranks = np.empty(n); ranks[order] = np.arange(1, n + 1)
        W = ranks[d > 0].sum(); mean = ranks.sum() / 2
        dist = np.zeros(int(ranks.sum()) + 1); dist[0] = 1
        for r in ranks.astype(int):
            dist[r:] += dist[:-r].copy()
        sums = np.arange(len(dist)); p = dist[np.abs(sums - mean) >= abs(W - mean) - 1e-9].sum() / dist.sum()
        return float(min(1.0, p))
    per_auc, per_brier = {}, {}
    for k in keys + ["reach"]:
        p = reach.astype(float) if k == "reach" else probs[k]
        per_auc[k] = [auc(y[rid == r], p[rid == r]) for r in range(len(names))]
        per_brier[k] = [float(np.mean((p[rid == r] - y[rid == r]) ** 2)) for r in range(len(names))]
    comps = [k for k in ["Without history", "History only", "Distance only", "Without structure", "reach"]]
    raw = {k: wilcoxon(per_auc[full], per_auc[k]) for k in comps}
    holm, running = {}, 0.0
    for i, k in enumerate(sorted(raw, key=raw.get)):
        running = max(running, min(1.0, raw[k] * (len(raw) - i))); holm[k] = running
    res["per_repo_auc"] = per_auc; res["per_repo_brier"] = per_brier
    res["wilcoxon_auc_vs_full"] = {k: {"p": raw[k], "p_holm": holm[k], "wins": int(sum(a > b for a, b in zip(per_auc[full], per_auc[k]))), "n": len(names)} for k in comps}
    print(res["wilcoxon_auc_vs_full"])
    json.dump(res, open(EXP / "calib_results.json", "w"), indent=1)
    for k, m in res["models"].items():
        print(f"{k:42s} auc={m['auc']:.3f} ap={m['ap']:.3f} brier={m['brier']:.4f} ece={m['ece']:.4f} F1={m.get('F1', 0):.3f}")
    print("reach", {k: round(v, 3) for k, v in res["reachability_binary"].items()})
    print(json.dumps(res["coefficients"], indent=1))
    print(res["diff_vs_full"])
