import json, numpy as np, calib as C
X, y, rid, iid, names = C.build()
col = {f: i for i, f in enumerate(C.FEATS)}
out = {}
for key, feats in (("with_history", C.FEATS), ("without_history", [f for f in C.FEATS if f != "history_ratio"])):
    w = C.fit(X[:, [col[f] for f in feats]], y)
    out[key] = dict(zip(["intercept"] + feats, [round(float(v), 6) for v in w]))
out["trained_on"] = {"repositories": len(names), "pairs": int(len(y)), "positives": int(y.sum())}
json.dump(out, open("cochange_coefficients.json", "w"), indent=1)
print(json.dumps(out)[:600])
