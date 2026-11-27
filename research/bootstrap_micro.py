import json, numpy as np
pc = json.load(open("micro_cases.json"))
names = list(pc)
arr = {t: np.array([[c[1], c[2], c[3]] for c in v]) for t, v in pc.items()}
n = len(next(iter(arr.values())))
def f1(a):
    tp, fp, fn = a.sum(0); p = tp/(tp+fp) if tp+fp else 0; r = tp/(tp+fn) if tp+fn else 0
    return (p, r, 2*p*r/(p+r) if p+r else 0)
rng = np.random.default_rng(0); B = 2000
boot = {t: np.zeros((B, 3)) for t in arr}
for b in range(B):
    idx = rng.integers(0, n, n)
    for t, a in arr.items(): boot[t][b] = f1(a[idx])
out = {"cases": n, "ci": {}, "diff": {}}
for t in arr:
    out["ci"][t] = {"point": [round(x, 4) for x in f1(arr[t])],
                    "P_CI": [round(float(np.percentile(boot[t][:, 0], q)), 4) for q in (2.5, 97.5)],
                    "R_CI": [round(float(np.percentile(boot[t][:, 1], q)), 4) for q in (2.5, 97.5)],
                    "F1_CI": [round(float(np.percentile(boot[t][:, 2], q)), 4) for q in (2.5, 97.5)]}
for a, b in (("CodeArchitect v2", "CodeArchitect v1"), ("PyCG 2.0.0", "CodeArchitect v2"), ("CodeArchitect v2", "Pyan3 2.9.0"), ("CodeArchitect v2", "CodeArchitect v2 (no heuristic)")):
    d = boot[a][:, 2] - boot[b][:, 2]
    out["diff"][f"{a} minus {b}"] = [round(float(d.mean()), 4), round(float(np.percentile(d, 2.5)), 4), round(float(np.percentile(d, 97.5)), 4)]
json.dump(out, open("micro_bootstrap.json", "w"), indent=1)
print(json.dumps(out, indent=1))
