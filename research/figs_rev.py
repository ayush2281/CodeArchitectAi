"""Figures for the revised paper: Mermaid diagrams (rendered with headless Edge) and data charts from result files."""
import json, subprocess, sys, html as H
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageChops

EXP = Path(__file__).resolve().parent
OUT = EXP / "figrev"; OUT.mkdir(exist_ok=True)
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
J = lambda n: json.load(open(EXP / n, encoding="utf-8"))

D = {
 "arch": """flowchart LR
  R[Python repository] --> A[AST extraction]
  A --> DG[Module dependency graph]
  A --> CG[Function call graph]
  PY[PyCG backend<br/>optional] -.-> CG
  DG --> M[Metrics, cycles]
  CG --> U[Unreferenced functions]
  DG --> I[Impact paths with<br/>evidence labels]
  CG --> I
  H[(Git history<br/>optional)] --> C[Calibrated co-change<br/>confidence]
  DG --> C
  M --> J[Structured results]
  U --> J
  I --> J
  C --> J
  J --> L[LLM interpretation<br/>grounded prompt]
  J --> UI[Dashboard / JSON]
  L --> UI""",
 "ast": """flowchart TB
  F[Python file] --> P[ast.parse]
  P -->|SyntaxError| X[Record unparsed file]
  P --> T[Syntax tree]
  T --> IM[Import / ImportFrom<br/>level, names, aliases]
  T --> DF[FunctionDef / ClassDef<br/>qualified names, bases]
  T --> CA[Call expressions<br/>per enclosing scope]
  IM --> RS[Resolve against project modules]
  DF --> SY[Symbol tables per module and class]
  CA --> RC[Resolve callee]
  SY --> RC
  RS --> GD[Dependency edges]
  RC -->|scope, import, self, super, type| HI[High-evidence call edges]
  RC -->|unique method name only| LO[Low-evidence call edges]
  RC -->|no match| UN[Unresolved, not recorded]""",
 "conf": """flowchart LR
  CH[Changed module m] --> FE[Features for every module n:<br/>dependency relations, distance,<br/>history ratio, package, fan-in, size]
  G[(Dependency graph)] --> FE
  H[(Git history before change)] --> FE
  FE --> LR[Logistic model<br/>coefficients fitted on other repositories]
  LR --> P[Probability of co-change]
  LR --> E[Per-feature contributions]
  CH --> PA[Dependency paths and<br/>evidence labels]
  P --> OUT[Ranked, explained impact list]
  E --> OUT
  PA --> OUT""",
 "method": """flowchart TB
  S1[Step 1: Corpus: benchmark, generated test sets,<br/>20 repositories + django] --> S2[Step 2: Ground truth: hand-written, traced,<br/>by construction, annotated, commit co-change]
  S2 --> S3[Step 3: Analyses: baseline, proposed,<br/>PyCG, Pyan3]
  S3 --> S4[Step 4: Metrics: P, R, F1, AUC, AP,<br/>Brier, ECE, time, memory]
  S4 --> S5[Step 5: Statistics: bootstrap CIs,<br/>Wilcoxon with Holm correction]
  S5 --> S6[Step 6: Ablation and LLM grounding study]""",
 "eval": """flowchart LR
  RQ1[RQ1 Dependencies,<br/>cycles] --- D1[Annotation, bytecode reference,<br/>constructed cycles]
  RQ2[RQ2 Calls,<br/>unreferenced] --- D2[PyCG benchmark, traced held-out,<br/>traced dead-code set]
  RQ3[RQ3 Impact and<br/>confidence] --- D3[Benchmark callers, commit histories,<br/>leave-one-repository-out]
  RQ4[RQ4 LLM<br/>grounding] --- D4[10 repositories, 3 models,<br/>grounded vs file list only]
  RQ5[RQ5 Cost] --- D5[Time and memory on<br/>21 repositories]""",
}
HTML = """<!doctype html><html><head><meta charset="utf-8"><script src="https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.min.js"></script>
<style>body{{margin:20px;background:#fff}} .mermaid svg{{max-width:none !important}}</style></head><body><pre class="mermaid">{src}</pre>
<script>mermaid.initialize({{startOnLoad:true,theme:'neutral',themeVariables:{{fontFamily:'Times New Roman',fontSize:'24px'}},flowchart:{{useMaxWidth:false,rankSpacing:30,nodeSpacing:24}}}});</script></body></html>"""
for n, s in D.items():
    p = OUT / f"{n}.html"; p.write_text(HTML.format(src=H.escape(s, quote=False)), encoding="utf-8")
    png = OUT / f"{n}.png"
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2", "--window-size=2600,2600",
                    "--virtual-time-budget=15000", f"--screenshot={png}", p.as_uri()], capture_output=True, timeout=90)
    im = Image.open(png).convert("RGB"); b = ImageChops.difference(im, Image.new("RGB", im.size, "white")).getbbox()
    im.crop((max(b[0] - 15, 0), max(b[1] - 15, 0), min(b[2] + 15, im.width), min(b[3] + 15, im.height))).save(png)
    print(n, Image.open(png).size)

plt.rcParams.update({"font.family": "Times New Roman", "font.size": 8})
micro, held, synth, dep21, ann, cal, abl, imp = (J("micro_results.json"), J("micro_results_heldout.json"), J("synth_results.json"), J("dep21_results.json")["totals"],
                                              J("annot_results.json"), J("calib_results.json"), J("ablation_results.json"), J("impact_results.json"))
# comparative performance
fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.8), dpi=300, sharey=True)
tools = [("CodeArchitect v1", "Baseline"), ("CodeArchitect v2", "Proposed"), ("PyCG 2.0.0", "PyCG"), ("Pyan3 2.9.0", "Pyan3")]
for ax, (data, title) in zip(axes, ((micro, "Development benchmark (636 programs)"), (held, "Held-out set (40 projects)"))):
    for i, (lab, idx) in enumerate((("Precision", 0), ("Recall", 1), ("F1", 2))):
        vals = [data[t]["loose"]["P_R_F1"][idx] for t, _ in tools]
        ax.bar(np.arange(4) + (i - 1) * 0.26, vals, 0.26, label=lab, color=["#9bb7d4", "#5b84b1", "#1f3a5f"][i])
        if idx == 2:
            for x, v in enumerate(vals): ax.text(x + 0.26, v + 0.02, f"{v:.2f}", ha="center", fontsize=6)
    ax.set_xticks(range(4)); ax.set_xticklabels([l for _, l in tools]); ax.set_title(title, fontsize=8); ax.set_ylim(0, 1.12)
axes[0].legend(fontsize=6, ncol=3, loc="upper left"); plt.tight_layout(); plt.savefig(OUT / "calls.png"); plt.close()
# reliability + AUC/AP (temporal evaluation)
T = J("temporal_results.json")
fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.6, 2.9), dpi=300)
rel = T["models"]["Full model"]["reliability"]
a1.plot([0, 1], [0, 1], "--", color="gray", lw=0.8, label="Perfect calibration")
a1.plot([r[0] for r in rel], [r[1] for r in rel], "o-", color="#1f3a5f", label="Full model")
for r in rel: a1.annotate(f"{r[2]:,}", (r[0], r[1]), fontsize=5, xytext=(3, -7), textcoords="offset points")
a1.set_xlabel("Mean predicted probability"); a1.set_ylabel("Observed co-change frequency"); a1.set_xlim(0, 0.8); a1.set_ylim(0, 0.8); a1.legend(fontsize=6)
keys = [("Full model", "Full"), ("Without structural features", "No structure"), ("Without history", "No history"), ("History ratio only", "History only"),
        ("History ratio + 0.1 if neighbour (heuristic)", "Heuristic"), ("Direct neighbours (binary)", "Neighbours"), ("Reachability (binary)", "Reachability")]
x = np.arange(len(keys))
a2.bar(x - 0.2, [T["models"][k]["auc"] for k, _ in keys], 0.4, label="ROC AUC", color="#5b84b1")
a2.bar(x + 0.2, [T["models"][k]["ap"] for k, _ in keys], 0.4, label="Average precision", color="#1f3a5f")
a2.set_xticks(x); a2.set_xticklabels([l for _, l in keys], rotation=40, ha="right", fontsize=6); a2.set_ylim(0, 0.9); a2.legend(fontsize=6)
plt.tight_layout(); plt.savefig(OUT / "calibration.png"); plt.close()
# call-resolution ablation
order = ["Full resolver", "- unique-name heuristic", "- self/cls resolution", "- super() resolution", "- instance-type tracking", "- local aliases", "- re-export following", "Scope and imports only", "Name-based baseline"]
fig, ax = plt.subplots(figsize=(6.4, 3.0), dpi=300); y = np.arange(len(order))
ax.barh(y - 0.2, [abl["development"][k]["F1"] for k in order], 0.4, label="Development benchmark", color="#5b84b1")
ax.barh(y + 0.2, [abl["held_out"][k]["F1"] for k in order], 0.4, label="Held-out set", color="#1f3a5f")
for i, k in enumerate(order):
    ax.text(abl["development"][k]["F1"] + 0.005, i - 0.2, f"{abl['development'][k]['F1']:.3f}", va="center", fontsize=6)
    ax.text(abl["held_out"][k]["F1"] + 0.005, i + 0.2, f"{abl['held_out'][k]['F1']:.3f}", va="center", fontsize=6)
ax.set_yticks(y); ax.set_yticklabels(order); ax.invert_yaxis(); ax.set_xlim(0, 0.9); ax.set_xlabel("Call-edge F1"); ax.legend(fontsize=6, loc="lower right")
plt.tight_layout(); plt.savefig(OUT / "ablation.png"); plt.close()
# explainable impact example (real output)
sys.path.insert(0, str(EXP / "v2")); sys.path.insert(0, str(Path(sys.argv[1]) if len(sys.argv) > 1 else EXP))
from ca2 import engine as E2
from src.analyzer import confidence
root = (EXP / "data/click/src").resolve()
files = [f for f in (root / "click").rglob("*.py")]
g = E2.build_dependency_graph(E2.Project(root, files), strict_from_imports=True)
repo = EXP / "data/click"
paths = {Path(d["file_path"]).resolve().relative_to(repo.resolve()).as_posix(): n for n, d in g.nodes(data=True)}
hist = confidence.history_counts(repo, paths)
changed = "click.types"
ranked = confidence.rank_cochange(g, changed, hist, top=6)
feats = ["direct_dependent", "direct_dependency", "indirect_dependent", "indirect_dependency", "inverse_distance", "history_ratio", "same_package", "log_fan_in", "log_modules"]
base = confidence.COEFFICIENTS["with_history"]["intercept"]
fig, ax = plt.subplots(figsize=(6.6, 2.8), dpi=300)
cmap = plt.get_cmap("tab10"); left_pos = np.zeros(len(ranked)); left_neg = np.zeros(len(ranked))
for i, f in enumerate(feats):
    v = np.array([r["contributions"].get(f, 0.0) for r in ranked])
    ax.barh(range(len(ranked)), np.where(v > 0, v, 0), left=left_pos, color=cmap(i), label=f.replace("_", " "))
    ax.barh(range(len(ranked)), np.where(v < 0, v, 0), left=left_neg, color=cmap(i))
    left_pos += np.where(v > 0, v, 0); left_neg += np.where(v < 0, v, 0)
ax.set_yticks(range(len(ranked))); ax.set_yticklabels([f"{r['module']}  (p = {r['confidence']:.2f})" for r in ranked]); ax.invert_yaxis()
ax.axvline(0, color="black", lw=0.6); ax.set_xlabel(f"Contribution to log-odds (intercept {base:.2f} not shown)"); ax.legend(fontsize=5, ncol=1, loc="center left", bbox_to_anchor=(1.0, 0.5))
plt.tight_layout(); plt.savefig(OUT / "explain.png"); plt.close()
json.dump({"changed": changed, "ranked": ranked, "paths": {r["module"]: __import__("networkx").shortest_path(g, r["module"], changed) if __import__("networkx").has_path(g, r["module"], changed) else None for r in ranked}},
          open(EXP / "explain_example.json", "w"), indent=1)
print("charts done")
