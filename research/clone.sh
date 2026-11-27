cd "$(dirname "$0")/data"
for n in requests flask click jinja itsdangerous httpx attrs tqdm rich python-dotenv; do git -C $n fetch -q --depth 400 origin 2>&1 | tail -1; done
for r in pallets/werkzeug pallets/markupsafe pytest-dev/pluggy more-itertools/more-itertools urllib3/urllib3 encode/starlette python-jsonschema/jsonschema fastapi/typer hukkin/tomli kjd/idna; do n=$(basename $r); [ -d $n ] || git clone -q --depth 400 https://github.com/$r.git $n 2>&1 | tail -1; done
[ -d django ] || git clone -q --depth 1 https://github.com/django/django.git django 2>&1 | tail -1
for n in */; do n=${n%/}; echo "$n $(git -C $n rev-parse --short HEAD) $(git -C $n rev-list --count HEAD)"; done > ../clone_report.txt
echo done > ../clone.done
