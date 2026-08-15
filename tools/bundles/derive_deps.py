"""Derive every bundle dependency from the bundles themselves, and write it into the configs.

WHY THIS EXISTS. A bundle that reads from another bundle needs TWO things, and only the first
lives inside the file:

  1. its externals table names the other bundle          -- in the .bundle, safe from regeneration
  2. the config declares a dependency on it              -- in a GENERATED .jsonc

`DRIPBundleService` REGISTERS every bundle beside a config but never makes one DEPEND on another,
so without (2) the client is never told to load the file and the item renders magenta, untextured,
or -- once geometry is stripped -- invisible. The pointer is correct the whole time, which is why
this costs an evening every time it is rediscovered.

`convert-legacy.py` regenerates the configs, so (2) cannot be hand-written: it is a fact about the
bundles on disk, not about the 3.x source. Deriving it is the same work as maintaining a list and
cannot go stale, so there is no list.

PLACEMENT, which is Tau's argument and correct: this is NOT part of the converter. A bundle
dependency changes when the bundles change (a strip, a rebuild); the converter changes when the
schema does. The converter calls this at the end so a conversion never leaves the pack broken;
run it standalone after stripping without converting anything.

  python derive_deps.py <pack-root> <game-StreamingAssets> [--apply]

Dry run by default. `drip check` catches what this fixes -- derive to fix, check to catch.
"""
import sys
import os
import re
import json
import collections

import UnityPy

# Applied to every bundle automatically by DRIPBundleService.DefaultDependencies. Emitting these
# would be noise, and would make a real dependency harder to see in the config.
AUTO = {"shaders", "cubemaps", "assets/commonassets/physics/physicsmaterials.bundle"}


def cabs_of(path):
    """Every CAB a container publishes. The pack has exactly one per bundle -- asserted, not
    assumed, because `audit_refs.py` records that 38 of 260 sampled GAME bundles publish two and
    that is exactly the kind of true-today that stops being true after a rebuild."""
    try:
        env = UnityPy.load(path)
    except Exception:
        return [], []
    names, ext = [], []
    for r in env.files.values():
        inner = getattr(r, "files", None)
        if isinstance(inner, dict):
            for n, f in inner.items():
                if n.endswith(".resS"):
                    continue
                names.append(n)
                if hasattr(f, "externals") and not ext:
                    ext = [e.path.split("/")[-1] for e in f.externals]
    return names, ext


def index(root, label):
    """CAB -> path relative to `root`."""
    out = {}
    multi = []
    for dp, _d, fs in os.walk(root):
        for f in sorted(fs):
            if f.endswith((".resS", ".manifest")):
                continue
            p = os.path.join(dp, f)
            if label == "pack" and not f.endswith(".bundle"):
                continue
            names, _e = cabs_of(p)
            if not names:
                continue
            rel = os.path.relpath(p, root).replace("\\", "/")
            if label == "pack" and len(names) != 1:
                multi.append(rel)
            for n in names:
                out[n] = rel
    return out, multi


def load_cfg(p):
    s = open(p, encoding="utf-8-sig").read()
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    s = re.sub(r"(?m)^\s*//.*$", "", s)
    s = re.sub(r",(\s*[}\]])", r"\1", s)
    return json.loads(s)


def write_block(cfg_path, block):
    """Rewrite only the bundles block, preserving the file's comments and author formatting."""
    txt = open(cfg_path, encoding="utf-8-sig").read()
    body = json.dumps(block, indent=4)
    body = "\n".join("  " + ln for ln in body.splitlines()).strip()
    if '"bundles"' in txt:
        new = re.sub(r'"bundles"\s*:\s*\{.*?\n  \}', f'"bundles": {body}', txt, count=1, flags=re.S)
        if new == txt:
            return "rewrite-failed"
        txt = new
    else:
        end = txt.rstrip().rfind("}")
        head = txt.rstrip()[:end].rstrip()
        if not head.endswith(",") and not head.endswith("{"):
            head += ","
        txt = (head + "\n\n  // Derived by tools/bundles/derive_deps.py from what these bundles\n"
               "  // actually reference. Registering a bundle is not the same as depending on it:\n"
               "  // without this the client never loads the file and the item renders wrong.\n"
               f'  "bundles": {body}\n}}\n')
    open(cfg_path, "w", encoding="utf-8").write(txt)
    return "written"


def main(pack, game, apply):
    print("indexing ...", flush=True)
    pack_idx, multi = index(pack, "pack")
    game_idx, _ = index(game, "game")
    print(f"  pack: {len(pack_idx)} CABs   game: {len(game_idx)} CABs")
    if multi:
        print(f"  *** PRECONDITION FAILED: {len(multi)} pack bundle(s) publish more than one CAB.")
        print(f"  *** externals() reads the FIRST serialized file only, so a derivation here would")
        print(f"  *** be wrong rather than incomplete. Refusing. {multi[:4]}")
        return 1
    print(f"  precondition holds: every pack bundle publishes exactly one CAB\n")

    tally = collections.Counter()
    changed = []
    for dp, _d, fs in os.walk(pack):
        cfgs = [f for f in fs if f.endswith(".jsonc")]
        bundles = [f for f in fs if f.endswith(".bundle")]
        if not cfgs or not bundles:
            continue
        want = {}
        for b in sorted(bundles):
            _n, ext = cabs_of(os.path.join(dp, b))
            deps = []
            for cab in ext:
                if cab in pack_idx:
                    sib = pack_idx[cab]
                    if sib == os.path.relpath(os.path.join(dp, b), pack).replace("\\", "/"):
                        continue                      # its own CAB
                    deps.append("ContentPacks/" + sib)
                elif cab in game_idx:
                    g = game_idx[cab]
                    if g in AUTO:
                        continue                      # applied automatically; noise to emit
                    deps.append(g)
                else:
                    tally["external resolving to nothing (left alone)"] += 1
            seen = set()
            deps = [d for d in deps if not (d in seen or seen.add(d))]
            if deps:
                want[b] = deps
        for c in cfgs:
            p = os.path.join(dp, c)
            try:
                cur = (load_cfg(p).get("bundles") or {})
            except Exception:
                tally["config unparseable"] += 1
                continue

            # UNION, NEVER REPLACE. Derivation reads the externals table, and not every real
            # dependency appears there: a TOP binds to `skeleton.bundle` at runtime by bone name,
            # never by pathID, so its CAB is absent from externals. Replacing the block with the
            # derived set would have silently deleted that from 85 configs -- a dependency that is
            # genuinely needed and structurally invisible to this rule.
            #
            # So this tool can only ADD. What it cannot see is carried by the converter from the
            # legacy *Dependencies fields, and the two sets are complementary rather than rival.
            merged = {k: list(v) for k, v in cur.items()}
            added = 0
            for b, ds in want.items():
                have = merged.setdefault(b, [])
                for d in ds:
                    if d not in have:
                        have.append(d)
                        added += 1
            if not added:
                tally["already complete"] += 1
                continue
            tally["missing declarations"] += 1
            changed.append((os.path.relpath(p, pack).replace("\\", "/"), added, 0))
            if apply:
                tally[write_block(p, merged)] += 1

    print(f"{'APPLIED' if apply else 'DRY RUN'}\n")
    for k, v in tally.most_common():
        print(f"  {v:>5}  {k}")
    if changed:
        print(f"\nconfigs whose derived block differs from what is written ({len(changed)}):")
        for rel, m, e in changed[:20]:
            print(f"    +{m} -{e}  {rel}")
        if len(changed) > 20:
            print(f"    ... and {len(changed)-20} more")
    return 0


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    sys.exit(main(a[0], a[1], "--apply" in sys.argv))
