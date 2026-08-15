"""Find config fields that are modelled but never consumed.

A property declared on a config class is not evidence that anything reads it. This
walks every [JsonPropertyName] property in the Models folder and checks whether the
C# property name appears anywhere OUTSIDE the model files.

Usage: python unconsumed.py <mod-root>
"""
import os
import re
import sys
import collections

PROP = re.compile(r'\[JsonPropertyName\("([^"]+)"\)\]')
NAME = re.compile(r'public\s+[\w<>,\?\[\]\s]+?\s+(\w+)\s*\{')


def model_properties(models_dir):
    """[(json name, csharp name, file)]"""
    out = []
    for dirpath, _d, files in os.walk(models_dir):
        for f in files:
            if not f.endswith(".cs"):
                continue
            p = os.path.join(dirpath, f)
            lines = open(p, encoding="utf-8", errors="replace").read().splitlines()
            pending = None
            for line in lines:
                m = PROP.search(line)
                if m:
                    pending = m.group(1)
                    # attribute and property may share a line
                    n = NAME.search(line)
                    if n:
                        out.append((pending, n.group(1), f))
                        pending = None
                    continue
                if pending:
                    n = NAME.search(line)
                    if n:
                        out.append((pending, n.group(1), f))
                        pending = None
    return out


def main(root):
    models = os.path.join(root, "Models")
    props = model_properties(models)

    # Gather all .cs outside Models/, plus obj/bin excluded.
    sources = []
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs
                   if d not in ("bin", "obj", ".git", ".idea", ".vscode", "Models")]
        for f in files:
            if f.endswith(".cs"):
                sources.append(os.path.join(dirpath, f))

    blob = ""
    for s in sources:
        blob += open(s, encoding="utf-8", errors="replace").read() + "\n"

    used, unused = [], []
    for json_name, cs_name, f in props:
        # word-boundary search for the C# property name
        if re.search(rf"\b{re.escape(cs_name)}\b", blob):
            used.append((json_name, cs_name, f))
        else:
            unused.append((json_name, cs_name, f))

    print(f"model properties: {len(props)}   consumed: {len(used)}   "
          f"NOT consumed: {len(unused)}\n")
    if unused:
        print("  These are modelled but nothing outside Models/ reads them:\n")
        by_file = collections.defaultdict(list)
        for j, c, f in unused:
            by_file[f].append((j, c))
        for f, items in sorted(by_file.items()):
            print(f"  {f}")
            for j, c in items:
                print(f"      {j:<28} -> {c}")
        print()
    print(f"  (scanned {len(sources)} source files outside Models/)")


if __name__ == "__main__":
    main(sys.argv[1])
