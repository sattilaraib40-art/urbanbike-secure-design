import json, sys
d = json.load(open(sys.argv[1]))
print(f"{'Rule':32} {'STRIDE':6} {'Line':4}  Threat")
for r in sorted(d["results"], key=lambda r: (r["extra"]["metadata"]["stride"], r["start"]["line"])):
    m = r["extra"]["metadata"]
    print(f"{r['check_id'].split('.')[-1]:32} {m['stride']:6} {r['start']['line']:<4}  {m['threat']}")