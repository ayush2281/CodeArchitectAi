# Supplementary materials – CodeArchitect AI evaluation

Everything needed to inspect or re-run the experiments in the paper. Raw outputs are in `results/`.

## Environment used (23 Nov 2026)
Windows 11, AMD Ryzen 5 3500U, 5.9 GB RAM, Python 3.12.10, NetworkX 3.3, PyVis 0.3.2, NumPy 2.5.5, matplotlib 3.11.2,
python-docx 1.2.0, Groq SDK 1.7.0, Pyan3 2.9.0, PyCG 2.0.0 (repository commit 5a735f77fa34e12ea578fb1682561213b251e503).
Repository commits: `results/commit_hashes_full.jsonl`. Repositories were cloned with `clone.sh` (history depth 400).

## Layout
- `engines/v1_original`: original analysis modules. `engines/v2/engine.py`: v2 engine (flag `strict_from_imports=True` = v2.1).
- `eval_micro.py` development benchmark (set `CA_SNIP` and `CA_TAG` for another snippet folder, e.g. `heldout_projects`'s parent).
- `gen_heldout.py` + `_tracer.py`: generate the 40 held-out projects and trace their ground-truth call graphs (seeded).
- `eval_repos.py`, `eval_dep21.py`, `counts.py`: dependency agreement, PyCG overlap, edge counts, v2.1 patch check.
- `annotation/`: sample, project module lists, annotator A/B outputs, adjudicated truth, tool edges, `annot_eval.py` (scoring).
  Annotators were two blind AI-assistant instances; a human replication using the same `sample.json` is recommended.
- `eval_commits.py`: real-commit experiment with repository-clustered bootstrap. `eval_impact.py`: benchmark-derived impact.
- `eval_llm_rep.py`, `eval_llm_score2.py`: 90 LLM reports and automatic checks; `results/llm_rating_sheet.csv` (+ `llm_rating_key.json`)
  is the blinded rubric sheet for human raters (not yet completed).
- `bootstrap_micro2.py`: bootstrap intervals for the call-graph experiments.

## Notes
- The LLM scripts read the Groq key from the project's `.env` (never stored here). Reports are in `results/llm_results_rep.json`.
- PyCG 2.0.0 is run from a repository checkout (`PYTHONPATH=<checkout>`); it exceeded the 300 s limit on rich.
- Paths inside the scripts point to the original scratch layout (`exp/`); adjust `EXP`/`D` constants if relocating.

## Added for the revised manuscript
- `calib.py` (confidence model, leave-one-repository-out, Wilcoxon-Holm), `calib_final.py` (shipped coefficients)
- `synth.py` (constructed cycle set; traced unreferenced-function set), `synthetic_sets/`
- `ablate.py` (resolver ablation), `stats.py` (dataset table), `llm_ungrounded.py` (grounding ablation), `figs_rev.py` (figures)
- `calib_temporal.py`: leak-free temporal evaluation (primary co-change result); `calib.py` is the superseded non-temporal analysis kept for transparency.

## Added for the revised manuscript (27 November 2026)
- rank.py: ranking metrics, baselines (gradient boosting in NumPy), recalibration, calendar cut-off, VIF, frozen test on eight new repositories (results/rank_results.json)
- depnew.py: dependency and cycle accuracy on 20 original and 8 new repositories (results/depnew_results.json)
- leak.py: effect of using the latest snapshot, all else equal (results/leak_results.json); run after rank.py
- timing.py: repeated timings; `python timing.py small` and `python timing.py django`
The eight new repositories are cloned with `git clone --depth 1500` into ../newrepos; commit identifiers are in results/rank_results.json under new.meta.
Not yet verified: a rerun from a fresh clone.
