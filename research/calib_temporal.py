"""Leak-free (temporal) evaluation of the co-change model.
For each repository the newest 30% of qualifying commits are test commits. The dependency graph is built from the
snapshot that precedes the oldest test commit, and the history ratio uses only commits up to that snapshot.
Leave-one-repository-out: coefficients come from the other repositories. No analysed code is executed."""
import json, math, subprocess, tempfile, tarfile, io, itertools
from pathlib import Path
from collections import defaultdict
import numpy as np
import networkx as nx
import calib as C

EXP = Path(__file__).resolve().parent
D = EXP / "data"


def log_entries(repo_dir, pkg_paths):
    cmd = ["git", "-C", str(repo_dir), "log", f"-n{C.MAXC}", "--no-merges", "--name-only", "--pretty=format:@@%H", "--diff-filter=AM", "--"] + pkg_paths
    out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8").stdout
    res = []
    for line in out.splitlines():
        if line.startswith("@@"):
            res.append((line[2:], []))
        elif line.endswith(".py") and res:
            res[-1][1].append(line)
    return res  # newest first


def modname(path_in_repo, prefix):
    parts = list(Path(path_in_repo).with_suffix("").parts)
    pre = Path(prefix).parts
    if tuple(parts[:len(pre)]) != pre:
        return None
    parts = parts[len(pre):]
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts) or None


def build():
    X, y, rid, names, meta = [], [], [], [], []
    for rname, (rel, pkgs) in C.REPOS.items():
        repo = D / Path(rel).parts[0]
        prefix = Path(*Path(rel).parts[1:]).as_posix() if len(Path(rel).parts) > 1 else "."
        prefix = "" if prefix == "." else prefix
        pkg_paths = [(Path(prefix) / p).as_posix() for p in pkgs]
        entries = log_entries(repo, pkg_paths)

        def mods_of(files):
            return {m for m in (modname(f, prefix or ".") if prefix else modname(f, "") for f in files) if m}
        qual = [i for i, (_, fs) in enumerate(entries) if 2 <= len(mods_of(fs)) <= 15]
        if len(qual) < 10:
            continue
        n_test = max(1, int(round(0.3 * len(qual))))
        oldest_test = qual[n_test - 1]
        h = entries[oldest_test][0]
        par = subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", f"{h}^"], capture_output=True, text=True)
        if par.returncode != 0:
            continue
        snapshot = par.stdout.strip()
        arch = subprocess.run(["git", "-C", str(repo), "archive", snapshot], capture_output=True)
        if arch.returncode != 0:
            continue
        tmp = Path(tempfile.mkdtemp())
        with tarfile.open(fileobj=io.BytesIO(arch.stdout)) as tf:
            members = [m for m in tf.getmembers() if m.isfile() and m.name.endswith(".py") and any(m.name == p or m.name.startswith(p + "/") for p in pkg_paths)]
            tf.extractall(tmp, members=members, filter="data")
        root = (tmp / prefix) if prefix else tmp
        files = [f for pk in pkgs if (root / pk).exists() for f in (root / pk).rglob("*.py")]
        if len(files) < 3:
            continue
        g = C.E2.build_dependency_graph(C.E2.Project(root.resolve(), [f.resolve() for f in files]), strict_from_imports=True)
        mods = sorted(g.nodes)
        und = g.to_undirected()
        dist = dict(nx.all_pairs_shortest_path_length(und))
        anc = {m: nx.ancestors(g, m) for m in mods}; desc = {m: nx.descendants(g, m) for m in mods}
        co = defaultdict(lambda: defaultdict(int)); seen = defaultdict(int)
        for _, fs in entries[oldest_test + 1:]:                      # history: strictly before the test period
            ms = [m for m in mods_of(fs) if m in g]
            if len(ms) <= 15:
                for a in ms:
                    seen[a] += 1
                    for b in ms:
                        if a != b:
                            co[a][b] += 1
        r = len(names); used = 0
        for i in [q for q in qual if q <= oldest_test]:
            ms = sorted(m for m in mods_of(entries[i][1]) if m in g)
            if not 2 <= len(ms) <= 15:
                continue
            for m in ms:
                truth = set(ms) - {m}; used += 1
                for n in mods:
                    if n == m:
                        continue
                    d = dist[m].get(n)
                    X.append([float(g.has_edge(n, m)), float(g.has_edge(m, n)), float(n in anc[m] and not g.has_edge(n, m)),
                              float(n in desc[m] and not g.has_edge(m, n)), 1.0 / d if d else 0.0,
                              co[m][n] / seen[m] if seen[m] else 0.0, float(m.rpartition(".")[0] == n.rpartition(".")[0]),
                              math.log1p(g.in_degree(n)), math.log(len(mods))])
                    y.append(float(n in truth)); rid.append(r)
        if used:
            names.append(rname); meta.append({"repo": rname, "snapshot": snapshot, "test_commits": n_test, "modules": len(mods), "instances": used})
            print(rname, snapshot[:8], n_test, len(mods), used, flush=True)
    return np.array(X), np.array(y), np.array(rid), names, meta


def wilcoxon(a, b):
    d = np.array(a) - np.array(b); d = d[d != 0]; n = len(d)
    order = np.argsort(np.abs(d)); ranks = np.empty(n); ranks[order] = np.arange(1, n + 1)
    W = ranks[d > 0].sum(); mean = ranks.sum() / 2
    dist = np.zeros(int(ranks.sum()) + 1); dist[0] = 1
    for r in ranks.astype(int):
        dist[r:] += dist[:-r].copy()
    s = np.arange(len(dist))
    return float(min(1.0, dist[np.abs(s - mean) >= abs(W - mean) - 1e-9].sum() / dist.sum()))


if __name__ == "__main__":
    X, y, rid, names, meta = build()
    col = {f: i for i, f in enumerate(C.FEATS)}
    structural = ["direct_dependent", "direct_dependency", "indirect_dependent", "indirect_dependency", "inverse_distance"]
    MODELS = {"Full model": C.FEATS, "Without structural features": [f for f in C.FEATS if f not in structural],
              "Without history": [f for f in C.FEATS if f != "history_ratio"],
              "Without context features": structural + ["history_ratio"], "History ratio only": ["history_ratio"],
              "Direct relations only (fitted)": ["direct_dependent", "direct_dependency"]}
    P = {k: np.zeros(len(y)) for k in MODELS}; P["Constant base rate"] = np.zeros(len(y))
    pred = {k: np.zeros(len(y), bool) for k in MODELS}
    for r in range(len(names)):
        tr, te = rid != r, rid == r
        P["Constant base rate"][te] = y[tr].mean()
        for k, feats in MODELS.items():
            c = [col[f] for f in feats]
            w = C.fit(X[tr][:, c], y[tr])
            P[k][te] = C.predict(w, X[te][:, c])
            pred[k][te] = P[k][te] >= C.best_threshold(y[tr], C.predict(w, X[tr][:, c]))
    nb = ((X[:, col["direct_dependent"]] + X[:, col["direct_dependency"]]) > 0).astype(float)
    RANK = {"Reachability (binary)": ((X[:, col["direct_dependent"]] + X[:, col["indirect_dependent"]]) > 0).astype(float),
            "Direct neighbours (binary)": nb,
            "History ratio + 0.1 if neighbour (heuristic)": X[:, col["history_ratio"]] + 0.1 * nb}

    def prf(p):
        tp = (p & (y == 1)).sum(); fp = (p & (y == 0)).sum(); fn = ((~p) & (y == 1)).sum()
        P_ = tp / (tp + fp) if tp + fp else 0; R_ = tp / (tp + fn) if tp + fn else 0
        return {"P": float(P_), "R": float(R_), "F1": float(2 * P_ * R_ / (P_ + R_) if P_ + R_ else 0)}

    def slope(p):
        z = np.log(np.clip(p, 1e-9, 1 - 1e-9) / (1 - np.clip(p, 1e-9, 1 - 1e-9)))
        w = C.fit(z[:, None], y, l2=0.0)
        return {"intercept": float(w[0]), "slope": float(w[1])}

    base_brier = float(np.mean((P["Constant base rate"] - y) ** 2))
    res = {"repos": names, "meta": meta, "pairs": int(len(y)), "positives": int(y.sum()), "base_rate": float(y.mean()), "models": {}}
    for k, p in P.items():
        e, tbl = C.ece(y, p)
        br = float(np.mean((p - y) ** 2))
        m = {"auc": C.auc(y, p), "ap": C.average_precision(y, p), "brier": br, "bss": 1 - br / base_brier, "ece": e, "reliability": tbl}
        if k in pred:
            m.update(prf(pred[k])); m.update(slope(p))
        res["models"][k] = m
    for k, s in RANK.items():
        res["models"][k] = {"auc": C.auc(y, s), "ap": C.average_precision(y, s)}
    res["models"]["Reachability (binary)"].update(prf(RANK["Reachability (binary)"] > 0))
    res["models"]["Direct neighbours (binary)"].update(prf(nb > 0))
    comps = ["History ratio only", "Without structural features", "Without history", "Direct neighbours (binary)", "Reachability (binary)", "History ratio + 0.1 if neighbour (heuristic)"]
    def score(k): return P[k] if k in P else RANK[k]
    per = {k: [C.auc(y[rid == r], score(k)[rid == r]) for r in range(len(names)) if 0 < y[rid == r].sum() < (rid == r).sum()] for k in ["Full model"] + comps}
    raw = {k: wilcoxon(per["Full model"], per[k]) for k in comps}
    holm, running = {}, 0.0
    for i, k in enumerate(sorted(raw, key=raw.get)):
        running = max(running, min(1.0, raw[k] * (len(raw) - i))); holm[k] = running
    res["per_repo_mean_auc"] = {k: float(np.mean(v)) for k, v in per.items()}
    res["wilcoxon"] = {k: {"p_holm": holm[k], "wins": int(sum(a > b for a, b in zip(per["Full model"], per[k]))), "n": len(per[k])} for k in comps}
    rng = np.random.default_rng(0)
    idx_by = [np.where(rid == r)[0] for r in range(len(names))]
    boot = defaultdict(list)
    for _ in range(500):
        idx = np.concatenate([idx_by[c] for c in rng.integers(0, len(names), len(names))])
        for k in ["Full model"] + comps:
            boot[k].append(C.auc(y[idx], score(k)[idx]))
    res["auc_ci"] = {k: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] for k, v in boot.items()}
    res["auc_diff_ci"] = {k: [float(np.percentile(np.array(boot["Full model"]) - np.array(boot[k]), q)) for q in (2.5, 97.5)] for k in comps}
    res["coefficients"] = dict(zip(["intercept"] + C.FEATS, map(float, C.fit(X, y))))
    res["coefficients_without_history"] = dict(zip(["intercept"] + MODELS["Without history"], map(float, C.fit(X[:, [col[f] for f in MODELS["Without history"]]], y))))
    res["coefficients_direct_only"] = dict(zip(["intercept", "direct_dependent", "direct_dependency"], map(float, C.fit(X[:, :2], y))))
    json.dump(res, open(EXP / "temporal_results.json", "w"), indent=1)
    print("pairs", len(y), "positives", int(y.sum()), "repos", len(names))
    for k, m in res["models"].items():
        print(f"{k:46s}", {a: round(b, 4) for a, b in m.items() if a != "reliability"})
    print(res["wilcoxon"]); print(res["auc_diff_ci"]); print(res["coefficients"]); print(res["coefficients_direct_only"]); print(res["models"]["Full model"]["reliability"])
