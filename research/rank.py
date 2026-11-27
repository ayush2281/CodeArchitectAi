"""Ranking metrics, stronger baselines, calibration, calendar cut-off, collinearity and a frozen test on new repositories.
Static analysis and git history only; no analysed code is executed. Gradient boosting is implemented here with NumPy."""
import io
import json
import math
import subprocess
import tarfile
import tempfile
from collections import defaultdict
from pathlib import Path

import networkx as nx
import numpy as np

import calib as C
import calib_temporal as T

EXP = Path(__file__).resolve().parent
NEW = EXP.parent / "newrepos"
NEW_REPOS = {
    "imbalanced-learn": ("imbalanced-learn", ["imblearn"]), "optuna": ("optuna", ["optuna"]),
    "seaborn": ("seaborn", ["seaborn"]), "networkx": ("networkx", ["networkx"]), "pint": ("pint", ["pint"]),
    "httpie": ("httpie", ["httpie"]), "mkdocs": ("mkdocs", ["mkdocs"]),
    "black": ("black/src", ["black", "blackd", "blib2to3"]),
}
FEATS = C.FEATS
COL = {f: i for i, f in enumerate(FEATS)}
STRUCT = ["direct_dependent", "direct_dependency", "indirect_dependent", "indirect_dependency", "inverse_distance"]
REDUCED = ["history_ratio", "inverse_distance", "same_package", "log_fan_in"]


def git(repo, *args):
    return subprocess.run(["git", "-c", "core.longpaths=true", "-C", str(repo), *args], capture_output=True)


def build(repos, data):
    cols = defaultdict(list)
    names, meta, inst = [], [], 0
    for rname, (rel, pkgs) in repos.items():
        repo = data / Path(rel).parts[0]
        prefix = Path(*Path(rel).parts[1:]).as_posix() if len(Path(rel).parts) > 1 else ""
        pkg_paths = [(Path(prefix) / p).as_posix() for p in pkgs]
        entries = T.log_entries(repo, pkg_paths)

        def mods_of(files):
            return {m for m in (T.modname(f, prefix) for f in files) if m}
        qual = [i for i, (_, fs) in enumerate(entries) if 2 <= len(mods_of(fs)) <= 15]
        if len(qual) < 10:
            print("skip", rname, len(qual)); continue
        n_test = max(1, int(round(0.3 * len(qual))))
        oldest = qual[n_test - 1]
        par = git(repo, "rev-parse", "--verify", f"{entries[oldest][0]}^")
        if par.returncode:
            print("skip", rname, "no parent"); continue
        snapshot = par.stdout.decode().strip()
        arch = git(repo, "archive", snapshot)
        if arch.returncode:
            print("skip", rname, "archive"); continue
        tmp = Path(tempfile.mkdtemp())
        with tarfile.open(fileobj=io.BytesIO(arch.stdout)) as tf:
            members = [m for m in tf.getmembers() if m.isfile() and m.name.endswith(".py")
                       and any(m.name.startswith(p + "/") for p in pkg_paths)]
            tf.extractall(tmp, members=members, filter="data")
        root = (tmp / prefix) if prefix else tmp
        files = [f for pk in pkgs if (root / pk).exists() for f in (root / pk).rglob("*.py")]
        if len(files) < 3:  # same rule as the original temporal evaluation
            print("skip", rname, "fewer than 3 files"); continue
        g = C.E2.build_dependency_graph(C.E2.Project(root.resolve(), [f.resolve() for f in files]), strict_from_imports=True)
        mods = sorted(g.nodes)
        dist = dict(nx.all_pairs_shortest_path_length(g.to_undirected()))
        anc = {m: nx.ancestors(g, m) for m in mods}
        desc = {m: nx.descendants(g, m) for m in mods}
        co, seen, total = defaultdict(lambda: defaultdict(int)), defaultdict(int), 0
        for _, fs in entries[oldest + 1:]:
            ms = [m for m in mods_of(fs) if m in g]
            if len(ms) <= 15:
                total += bool(ms)
                for a in ms:
                    seen[a] += 1
                    for b in ms:
                        if a != b:
                            co[a][b] += 1
        r, used = len(names), 0
        for i in [q for q in qual if q <= oldest]:
            ms = sorted(m for m in mods_of(entries[i][1]) if m in g)
            if not 2 <= len(ms) <= 15:
                continue
            when = int(git(repo, "show", "-s", "--format=%ct", entries[i][0]).stdout.decode().strip())
            for m in ms:
                truth = set(ms) - {m}
                for n in mods:
                    if n == m:
                        continue
                    d = dist[m].get(n)
                    cols["X"].append((g.has_edge(n, m), g.has_edge(m, n), n in anc[m] and not g.has_edge(n, m),
                                      n in desc[m] and not g.has_edge(m, n), 1.0 / d if d else 0.0,
                                      co[m][n] / seen[m] if seen[m] else 0.0, m.rpartition(".")[0] == n.rpartition(".")[0],
                                      math.log1p(g.in_degree(n)), math.log(len(mods))))
                    cols["y"].append(n in truth)
                    cols["rid"].append(r)
                    cols["inst"].append(inst)
                    cols["time"].append(when)
                    cols["support"].append(co[m][n])
                    cols["freq"].append(seen[n] / total if total else 0.0)
                inst += 1
                used += 1
        if used:
            names.append(rname)
            meta.append({"repo": rname, "head": git(repo, "rev-parse", "HEAD").stdout.decode().strip(), "snapshot": snapshot,
                         "modules": len(mods), "test_commits": n_test, "instances": used})
            print(rname, len(mods), used, flush=True)
    kinds = {"X": np.float32, "y": np.float32, "rid": np.int32, "inst": np.int32, "time": np.int64, "support": np.float32, "freq": np.float32}
    return {k: np.array(v, dtype=kinds[k]) for k, v in cols.items()}, names, meta


# ------------------------------------------------------------------ gradient boosting (histogram trees, log-loss)
def gb_fit(X, y, trees=150, depth=3, rate=0.05, bins=32, l2=1.0, min_leaf=50):
    edges = [np.unique(np.quantile(X[:, j], np.linspace(0, 1, bins + 1)[1:-1])) for j in range(X.shape[1])]
    B = np.stack([np.searchsorted(e, X[:, j], side="left") for j, e in enumerate(edges)], axis=1)
    base = math.log(y.mean() / (1 - y.mean()))
    score = np.full(len(y), base)
    forest = []
    for _ in range(trees):
        p = 1 / (1 + np.exp(-score))
        grad, hess = y - p, p * (1 - p)
        nodes = {}

        def grow(idx, level, key):
            G, H = grad[idx].sum(), hess[idx].sum()
            best = None
            if level < depth and len(idx) >= 2 * min_leaf:
                for j in range(X.shape[1]):
                    k = len(edges[j]) + 1
                    if k < 2:
                        continue
                    b = B[idx, j]
                    gl = np.cumsum(np.bincount(b, grad[idx], k))[:-1]
                    hl = np.cumsum(np.bincount(b, hess[idx], k))[:-1]
                    nl = np.cumsum(np.bincount(b, minlength=k))[:-1]
                    gain = gl ** 2 / (hl + l2) + (G - gl) ** 2 / (H - hl + l2) - G ** 2 / (H + l2)
                    gain[(nl < min_leaf) | (len(idx) - nl < min_leaf)] = -1
                    s = int(np.argmax(gain))
                    if gain[s] > 1e-9 and (best is None or gain[s] > best[0]):
                        best = (gain[s], j, s)
            if best is None:
                nodes[key] = ("leaf", rate * G / (H + l2))
                score[idx] += nodes[key][1]
                return
            _, j, s = best
            nodes[key] = ("split", j, float(edges[j][s]))
            left = B[idx, j] <= s
            grow(idx[left], level + 1, key * 2)
            grow(idx[~left], level + 1, key * 2 + 1)

        grow(np.arange(len(y)), 0, 1)
        forest.append(nodes)
    return base, forest


def gb_predict(model, X):
    base, forest = model
    score = np.full(len(X), base)
    for nodes in forest:
        stack = [(1, np.arange(len(X)))]
        while stack:
            key, idx = stack.pop()
            node = nodes[key]
            if node[0] == "leaf":
                score[idx] += node[1]
            else:
                left = X[idx, node[1]] <= node[2]
                stack += [(key * 2, idx[left]), (key * 2 + 1, idx[~left])]
    return 1 / (1 + np.exp(-score))


# ------------------------------------------------------------------ metrics
def ranking(D, score, seeds=10, k=5):
    """Per changed-module instance AP, reciprocal rank, precision@k and recall@k; ties broken at random and averaged."""
    n = int(D["inst"].max()) + 1
    out = np.zeros((4, n))
    positives = np.bincount(D["inst"], D["y"], n)
    for seed in range(seeds):
        rnd = np.random.default_rng(seed).random(len(score))
        order = np.lexsort((rnd, -score, D["inst"]))
        inst, y = D["inst"][order], D["y"][order].astype(np.float64)
        start = np.searchsorted(inst, np.arange(n))
        pos = np.arange(len(y)) - start[inst] + 1
        cum = np.cumsum(y)
        cum -= (cum - y)[start][inst]
        out[0] += np.bincount(inst, y * cum / pos, n) / positives
        first = np.bincount(inst, (y == 1) & (cum == 1), n)
        assert np.all(first == 1)
        out[1] += np.bincount(inst, np.where((y == 1) & (cum == 1), 1.0 / pos, 0.0), n)
        hits = np.bincount(inst, y * (pos <= k), n)
        out[2] += hits / k
        out[3] += hits / positives
    out /= seeds
    inst_repo = D["rid"][np.searchsorted(D["inst"], np.arange(n))]
    return out, inst_repo


def summarise(D, scores, reference="Full logistic model"):
    repos = np.unique(D["rid"])
    res, per_repo = {}, {}
    for name, s in scores.items():
        per, inst_repo = ranking(D, s)
        table = np.array([[per[m][inst_repo == r].mean() for r in repos] for m in range(4)])
        aucs = np.array([C.auc(D["y"][D["rid"] == r].astype(float), s[D["rid"] == r]) for r in repos])
        per_repo[name] = table
        res[name] = {"MAP": float(table[0].mean()), "MRR": float(table[1].mean()), "P@5": float(table[2].mean()),
                     "R@5": float(table[3].mean()), "repo_AUC": float(aucs.mean()),
                     "pooled_AUC": C.auc(D["y"].astype(float), s)}
    rng = np.random.default_rng(0)
    picks = rng.integers(0, len(repos), (2000, len(repos)))
    ref = per_repo[reference][0]
    raw = {}
    for name in scores:
        mine = per_repo[name][0]
        res[name]["MAP_CI"] = [float(q) for q in np.percentile(mine[picks].mean(axis=1), [2.5, 97.5])]
        if name != reference:
            res[name]["MAP_diff_ref_CI"] = [float(q) for q in np.percentile((ref - mine)[picks].mean(axis=1), [2.5, 97.5])]
            res[name]["ref_higher_in"] = int((ref > mine).sum())
            raw[name] = T.wilcoxon(ref, mine)
    running = 0.0
    for i, name in enumerate(sorted(raw, key=raw.get)):
        running = max(running, min(1.0, raw[name] * (len(raw) - i)))
        res[name]["p_holm"] = running
    return res


def pav(p, y):
    order = np.argsort(p, kind="mergesort")
    blocks = []
    for x, t in zip(p[order], y[order]):
        blocks.append([float(t), 1.0, float(x)])
        while len(blocks) > 1 and blocks[-2][0] / blocks[-2][1] >= blocks[-1][0] / blocks[-1][1]:
            s, c, hi = blocks.pop()
            blocks[-1][0] += s
            blocks[-1][1] += c
            blocks[-1][2] = hi
    return np.array([b[2] for b in blocks]), np.array([b[0] / b[1] for b in blocks])


def prob_metrics(y, p, base):
    e, _ = C.ece(y, p)
    brier = float(np.mean((p - y) ** 2))
    z = np.log(np.clip(p, 1e-6, 1 - 1e-6) / (1 - np.clip(p, 1e-6, 1 - 1e-6)))
    return {"brier": brier, "bss": 1 - brier / float(np.mean((base - y) ** 2)), "ece": float(e),
            "slope": float(C.fit(z[:, None], y, l2=0.0)[1])}


def lr(X, y, feats):
    c = [COL[f] for f in feats]
    w = C.fit(X[:, c], y)
    return lambda Z: C.predict(w, Z[:, c])


def all_scores(train_X, train_y, D):
    X = D["X"].astype(np.float64)
    ratio, sup = X[:, COL["history_ratio"]], D["support"].astype(np.float64)
    near = ((X[:, 0] + X[:, 1]) > 0).astype(float)
    return {
        "Full logistic model": lr(train_X, train_y, FEATS)(X),
        "Without structural features": lr(train_X, train_y, [f for f in FEATS if f not in STRUCT])(X),
        "Reduced model (4 features)": lr(train_X, train_y, REDUCED)(X),
        "Gradient boosting (9 features)": gb_predict(gb_fit(train_X, train_y), X),
        "History ratio only": ratio,
        "History ratio + neighbour heuristic": ratio + 0.1 * near,
        "Association rules (support at least 2)": ratio * (sup >= 2) + 1e-9 * sup,
        "Change frequency of candidate": D["freq"].astype(np.float64),
        "Direct neighbours": near,
        "Reachability": ((X[:, 0] + X[:, 2]) > 0).astype(float),
    }


def main():
    D, names, meta = build(C.REPOS, C.D)
    X, y, rid = D["X"].astype(np.float64), D["y"].astype(np.float64), D["rid"]
    print("pairs", len(y), "positives", int(y.sum()), "repos", len(names), flush=True)
    res = {"original": {"pairs": len(y), "positives": int(y.sum()), "repos": names, "instances": int(D["inst"].max()) + 1}}

    folds = {}
    for r in range(len(names)):
        tr, te = rid != r, rid == r
        sub = {k: v[te] for k, v in D.items()}
        sub["inst"] = sub["inst"] - sub["inst"].min()
        for k, s in all_scores(X[tr], y[tr], sub).items():
            folds.setdefault(k, np.zeros(len(y)))[te] = s
        print("fold", names[r], flush=True)
    res["original"]["rankers"] = summarise(D, folds)

    # calibration with maps fitted on out-of-fold predictions of the training repositories only
    raw, iso, platt, base = (np.zeros(len(y)) for _ in range(4))
    for r in range(len(names)):
        te = rid == r
        oof = np.zeros(len(y))
        for q in range(len(names)):
            if q != r:
                tr = (rid != r) & (rid != q)
                oof[rid == q] = lr(X[tr], y[tr], FEATS)(X[rid == q])
        tr = rid != r
        raw[te] = folds["Full logistic model"][te]
        xs, ys = pav(oof[tr], y[tr])
        iso[te] = ys[np.minimum(np.searchsorted(xs, raw[te]), len(ys) - 1)]
        logit = lambda p: np.log(p / (1 - p))[:, None]
        w = C.fit(logit(np.clip(oof[tr], 1e-6, 1 - 1e-6)), y[tr], l2=0.0)
        platt[te] = C.predict(w, logit(np.clip(raw[te], 1e-6, 1 - 1e-6)))
        base[te] = y[tr].mean()
        print("calibration", names[r], flush=True)
    res["calibration"] = {k: prob_metrics(y, p, base) for k, p in (("Uncalibrated", raw), ("Platt", platt), ("Isotonic", iso))}
    res["calibration"]["Gradient boosting"] = prob_metrics(y, folds["Gradient boosting (9 features)"], base)
    res["calibration_auc"] = {k: C.auc(y, p) for k, p in (("Uncalibrated", raw), ("Platt", platt), ("Isotonic", iso))}

    # single calendar cut-off
    cut = int(np.median(D["time"]))
    tr, te = D["time"] < cut, D["time"] >= cut
    sub = {k: v[te] for k, v in D.items()}
    sub["inst"] = np.unique(sub["inst"], return_inverse=True)[1].astype(np.int32)
    res["cutoff"] = {"unix_time": cut, "train_pairs": int(tr.sum()), "test_pairs": int(te.sum()),
                     "test_repos": int(len(np.unique(sub["rid"]))), "rankers": summarise(sub, all_scores(X[tr], y[tr], sub))}

    # collinearity
    Z = (X - X.mean(0)) / X.std(0)
    corr = np.corrcoef(Z, rowvar=False)
    res["vif"] = dict(zip(FEATS, map(float, np.diag(np.linalg.inv(corr)))))
    res["coefficients_reduced"] = dict(zip(["intercept"] + REDUCED, map(float, C.fit(X[:, [COL[f] for f in REDUCED]], y))))

    # frozen method on repositories not used before: everything is fitted on the original repositories only
    N, new_names, new_meta = build(NEW_REPOS, NEW)
    ny = N["y"].astype(np.float64)
    scores = all_scores(X, y, N)
    res["new"] = {"pairs": len(ny), "positives": int(ny.sum()), "repos": new_names, "meta": new_meta,
                  "instances": int(N["inst"].max()) + 1, "rankers": summarise(N, scores),
                  "full_probabilities": prob_metrics(ny, scores["Full logistic model"], np.full(len(ny), y.mean()))}
    json.dump(res, open(EXP / "rank_results.json", "w"), indent=1)
    print("DONE")


if __name__ == "__main__":
    main()
