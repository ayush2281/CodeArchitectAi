for spec in "requests requests/src requests" "flask flask/src flask" "click click/src click" "jinja jinja/src jinja2" "itsdangerous itsdangerous/src itsdangerous" "httpx httpx httpx" "attrs attrs/src attr,attrs" "tqdm tqdm tqdm" "rich rich rich" "python-dotenv python-dotenv/src dotenv"; do
 set -- $spec
 for v in v1 v2; do
  out=$(timeout 60 ./venv/Scripts/python time_impact.py $v $1 $2 $3 2>&1 | tail -1)
  rc=$?
  [ -z "$out" ] && out="{\"repo\":\"$1\",\"engine\":\"$v\",\"timeout_60s\":true}"
  echo "$out"
 done
done > impact_time.jsonl
echo done >> impact_time.done
