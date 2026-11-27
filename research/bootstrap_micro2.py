import json, numpy as np, sys
tag = sys.argv[1] if len(sys.argv) > 1 else ""
pc = json.load(open(f"micro_cases{tag}.json"))
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
out = {"cases": n, "ci": {t: {"point": [round(x, 4) for x in f1(arr[t])], "F1_CI": [round(float(np.percentile(boot[t][:, 2], q)), 4) for q in (2.5, 97.5)],
                               "P_CI": [round(float(np.percentile(boot[t][:, 0], q)), 4) for q in (2.5, 97.5)], "R_CI": [round(float(np.percentile(boot[t][:, 1], q)), 4) for q in (2.5, 97.5)]} for t in arr}, "diff": {}}
for a, b in (("CodeArchitect v2", "CodeArchitect v1"), ("PyCG 2.0.0", "CodeArchitect v2"), ("CodeArchitect v2", "Pyan3 2.9.0")):
    d = boot[a][:, 2] - boot[b][:, 2]; out["diff"][f"{a} minus {b}"] = [round(float(d.mean()), 4), round(float(np.percentile(d, 2.5)), 4), round(float(np.percentile(d, 97.5)), 4)]
json.dump(out, open(f"micro_bootstrap{tag}.json", "w"), indent=1)
print(json.dumps(out["ci"], indent=0)[:900]); print(out["diff"])
