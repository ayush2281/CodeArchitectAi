import sys, collections
sys.argv = ['x', '__none__']
import os; os.environ['CA_SNIP'] = str(__import__('pathlib').Path('heldout').resolve())
exec(open('eval_micro.py').read().split("TOOLS = {")[0])
cnt = collections.Counter(); tot = 0
for case in cases:
    mods = modules_of(case); gs, gl, _, _ = gt_edges(case, mods)
    s, l = to_norm(run_v2(case, mods), mods, False)
    for (c, d_) in gl - l:
        tot += 1; leaf = d_[1]
        kind = "dunder/implicit" if leaf.startswith("__") else ("property/operator" if leaf in ("double",) else "other")
        cnt[leaf if leaf.startswith('__') else 'named']+=1
print(tot, cnt.most_common(8))
