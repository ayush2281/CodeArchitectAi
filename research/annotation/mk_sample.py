import json,random,sys
from pathlib import Path
sys.argv=['x']
sys.path.insert(0,'.')
src=open('eval_repos.py',encoding='utf8').read().split("def prf")[0].replace('if "--django" in sys.argv','if False')
__file__ = str(Path('eval_repos.py').resolve())
exec(src)
random.seed(7)
sample=[];mods_by_repo={}
for name,(rel,pkgs) in REPOS.items():
    root=(D/rel).resolve()
    files=[f for pk in pkgs for f in (root/pk).rglob("*.py") if "__pycache__" not in f.parts]
    mods={}
    for f in files:
        parts=list(f.relative_to(root).with_suffix("").parts)
        if parts[-1]=="__init__": parts=parts[:-1]
        mods[".".join(parts)]=str(f)
    mods_by_repo[name]=sorted(mods)
    cand=[f for f in files if len(f.read_text(encoding='utf-8',errors='replace').splitlines())>=15]
    for f in random.sample(cand,min(2,len(cand))):
        parts=list(f.relative_to(root).with_suffix("").parts)
        if parts[-1]=="__init__": parts=parts[:-1]
        sample.append({"id":len(sample)+1,"repo":name,"module":".".join(parts),"file":str(f)})
json.dump(sample,open('annot/sample.json','w'),indent=1)
json.dump(mods_by_repo,open('annot/project_modules.json','w'),indent=1)
print(len(sample),sum(len(v) for v in mods_by_repo.values()))
