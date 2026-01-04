# C:\FLOWORK\flowork-gateway\scripts\capsules_cli.py
# (English Hardcode) Simple CLI to manage capsules locally.
# (English Hardcode) Roadmap 8.3
import argparse, json
import os, sys

# (English Hardcode) Add parent 'flowork-gateway' to path to import 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.capsules.registry import list_capsules, get_capsule, install_capsule, remix_capsule

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    # (English Hardcode) List command
    sub.add_parser("list")

    # (English Hardcode) Get command
    g = sub.add_parser("get")
    g.add_argument("capsule_id")

    # (English Hardcode) Install command
    i = sub.add_parser("install")
    i.add_argument("json_path", help="Path to the capsule.json file to install")

    # (English Hardcode) Remix command
    r = sub.add_parser("remix")
    r.add_argument("base_capsule_id", help="The ID of the capsule to use as a base")
    r.add_argument("new_capsule_id", help="The ID for the new remixed capsule")
    r.add_argument("patch_json_path", help="Path to the patch.json file")

    args = ap.parse_args()

    if args.cmd == "list":
        print(json.dumps(list_capsules(), indent=2, ensure_ascii=False))
    elif args.cmd == "get":
        print(json.dumps(get_capsule(args.capsule_id), indent=2, ensure_ascii=False))
    elif args.cmd == "install":
        data = json.load(open(args.json_path, "r", encoding="utf-8"))
        print(json.dumps(install_capsule(data), indent=2, ensure_ascii=False))
    elif args.cmd == "remix":
        patch = json.load(open(args.patch_json_path, "r", encoding="utf-8"))
        print(json.dumps(remix_capsule(args.base_capsule_id, args.new_capsule_id, patch), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()