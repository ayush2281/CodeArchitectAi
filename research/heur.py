"""Paired comparison of the history-plus-neighbour heuristic with the history ratio, per repository.
Neither ranker is fitted. Also verifies that the association-rule score ranks like the history ratio."""
import json
from pathlib import Path

import numpy as np

import calib_temporal as T
import rank as R

out = {}
for label, repos, data in (("original", R.C.REPOS, R.C.D), ("new", R.NEW_REPOS, R.NEW)):
    D, names, _ = R.build(repos, data)
    X = D["X"].astype(np.float64)
    ratio = X[:, R.COL["history_ratio"]]
    near = ((X[:, 0] + X[:, 1]) > 0).astype(float)
    sup = D["support"].astype(np.float64)
    scores = {"heuristic": ratio + 0.1 * near, "history": ratio, "association": ratio * (sup >= 2) + 1e-9 * sup}
    per = {k: R.ranking(D, s) for k, s in scores.items()}
    ids = np.unique(D["rid"])
    table = {k: np.array([[v[0][m][v[1] == r].mean() for r in ids] for m in range(4)]) for k, v in per.items()}
    res = {"repos": len(ids), "pairs": int(len(D["y"])), "association_equals_history": bool(np.allclose(per["association"][0], per["history"][0]))}
    rng = np.random.default_rng(0)
    picks = rng.integers(0, len(ids), (10000, len(ids)))
    for m, metric in enumerate(("MAP", "MRR", "P@5", "R@5")):
        diff = table["heuristic"][m] - table["history"][m]
        res[metric] = {"heuristic": float(table["heuristic"][m].mean()), "history": float(table["history"][m].mean()),
                       "difference": float(diff.mean()), "ci95": [float(q) for q in np.percentile(diff[picks].mean(axis=1), [2.5, 97.5])],
                       "wilcoxon_p": T.wilcoxon(table["heuristic"][m], table["history"][m]),
                       "higher": int((diff > 1e-12).sum()), "lower": int((diff < -1e-12).sum())}
    out[label] = res
json.dump(out, open(Path(__file__).with_name("heuristic_results.json"), "w"), indent=1)
print("RESULT")
print(json.dumps(out, indent=1))
