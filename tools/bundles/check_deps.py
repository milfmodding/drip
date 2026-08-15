"""Does every pointer that leaves a bundle land somewhere the client was told to load?

THE BUG THIS EXISTS FOR. A bundle that reads from another bundle needs two things, and only
the first lives inside the file:

  1. a pointer, and an externals entry naming the other bundle   -- in the .bundle
  2. a `bundles` declaration in the config                        -- in a GENERATED .jsonc

`DRIPBundleService` REGISTERS every bundle beside a config but never makes one DEPEND on
another. Without (2) the client is never told to load the file. The pointer is correct the
whole time, so nothing errors and nothing logs -- the item renders magenta, untextured, or
(once geometry is stripped) invisible. That cost four separate evenings before anyone opened a
binary, and three of the four diagnoses along the way were wrong.

WHY THIS IS POINTER-DRIVEN AND NOT EXTERNALS-DRIVEN. An externals table can name a bundle no
pointer actually uses -- leftovers from the vanilla bundle these were cloned from. Treating
every externals row as a dependency reports things that are not dependencies, and a check that
cries wolf on real content gets switched off. So this walks the POINTERS and asks what each one
needs. A row nothing points through is not a dependency and is not reported.

WHY IT DOES NOT SHARE CODE WITH `derive_deps.py`. That tool writes the declarations; this one
judges them. They index the CABs separately and resolve pointers separately on purpose --
derive to fix, check to catch. A checker that calls the generator can only ever confirm that
the generator did what the generator does.

WHAT IT DELIBERATELY DOES NOT DO. It never says "add a bundles block". Declaring the
dependency FIXES a half-mask and is necessary-but-insufficient on a helmet, whose externals
table still names the vanilla CAB -- so a check promising a remedy walks the next person into
the exact loop this file exists to end. It names the pointer, the bundle it needs, and stops.

  python check_deps.py <pack-root> <game-StreamingAssets>
  python check_deps.py --selftest <pack-root> <game-StreamingAssets>

Exit status is 1 if any pointer-backed dependency is undeclared, so it can gate a build.
"""
import sys
import os
import re
import json
import collections

import UnityPy

# Applied to every bundle by DRIPBundleService.DefaultDependencies, so a config that omits
# these is correct rather than incomplete.
AUTO = {"shaders", "cubemaps", "assets/commonassets/physics/physicsmaterials.bundle"}

POINTER_SOURCES = ("Material", "MeshFilter", "SkinnedMeshRenderer", "MeshRenderer", "Renderer")


def cabs_and_externals(path):
    """(names this container publishes, its first serialized file's externals)."""
    try:
        env = UnityPy.load(path)
    except Exception:
        return [], [], None
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
    return names, ext, env


def index(root, pack_only):
    """CAB -> path relative to root. Built here rather than imported, on purpose."""
    out = {}
    for dp, _d, fs in os.walk(root):
        for f in sorted(fs):
            if f.endswith((".resS", ".manifest")):
                continue
            if pack_only and not f.endswith(".bundle"):
                continue
            p = os.path.join(dp, f)
            names, _e, _env = cabs_and_externals(p)
            rel = os.path.relpath(p, root).replace("\\", "/")
            for n in names:
                out[n] = rel
    return out


def load_cfg(p):
    s = open(p, encoding="utf-8-sig").read()
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    s = re.sub(r"(?m)^\s*//.*$", "", s)
    s = re.sub(r",(\s*[}\]])", r"\1", s)
    return json.loads(s)


def outbound_pointers(env):
    """Every pointer that can leave this bundle, as (fileID, label).

    The four kinds are the four that have actually broken here: Material->Shader,
    Material->Texture, Renderer->m_Materials, and MeshFilter/SkinnedMeshRenderer->m_Mesh.
    """
    out = []
    for obj in env.objects:
        t = obj.type.name
        if t not in POINTER_SOURCES:
            continue
        try:
            d = obj.read()
        except Exception:
            continue
        if t == "Material":
            sh = getattr(d, "m_Shader", None)
            if sh is not None and getattr(sh, "m_FileID", 0):
                out.append((sh.m_FileID, f"Material.m_Shader"))
            sp = getattr(d, "m_SavedProperties", None)
            for name, tex in (getattr(sp, "m_TexEnvs", None) or []) if sp is not None else []:
                tx = getattr(tex, "m_Texture", None)
                if tx is not None and getattr(tx, "m_FileID", 0):
                    out.append((tx.m_FileID, f"Material.{name}"))
        else:
            m = getattr(d, "m_Mesh", None)
            if m is not None and getattr(m, "m_FileID", 0):
                out.append((m.m_FileID, f"{t}.m_Mesh"))
            for mp in (getattr(d, "m_Materials", None) or []):
                if getattr(mp, "m_FileID", 0):
                    out.append((mp.m_FileID, f"{t}.m_Materials"))
    return out


def needs_of(path, pack_idx, game_idx, own_rel):
    """What this bundle's pointers require the client to have loaded.

    Returns (needed, unresolved) where `needed` maps a dependency path to the pointer labels
    that want it, and `unresolved` lists pointers whose externals row names nothing we hold.
    """
    _names, ext, env = cabs_and_externals(path)
    needed = collections.defaultdict(set)
    unresolved = []
    if env is None:
        return needed, [("<unreadable>", path)]
    for fid, label in outbound_pointers(env):
        if not (1 <= fid <= len(ext)):
            unresolved.append((label, f"fileID {fid} outside externals table"))
            continue
        cab = ext[fid - 1]
        if cab in pack_idx:
            sib = pack_idx[cab]
            if sib == own_rel:
                continue                              # its own CAB, listed for its own sake
            needed["ContentPacks/" + sib].add(label)
        elif cab in game_idx:
            g = game_idx[cab]
            if g in AUTO:
                continue
            needed[g].add(label)
        else:
            unresolved.append((label, f"externals names {cab}, which is in neither game nor pack"))
    return needed, unresolved


def run(pack, game, quiet=False):
    if not quiet:
        print("indexing ...", flush=True)
    pack_idx = index(pack, True)
    game_idx = index(game, False)
    if not quiet:
        print(f"  pack {len(pack_idx)} CABs   game {len(game_idx)} CABs\n")

    defects, unres, unbacked = [], [], []
    tally = collections.Counter()

    for dp, _d, fs in os.walk(pack):
        cfgs = [f for f in fs if f.endswith(".jsonc")]
        bundles = [f for f in fs if f.endswith(".bundle")]
        if not cfgs or not bundles:
            continue
        for c in cfgs:
            cpath = os.path.join(dp, c)
            try:
                declared = (load_cfg(cpath).get("bundles") or {})
            except Exception:
                tally["config unparseable"] += 1
                continue
            crel = os.path.relpath(cpath, pack).replace("\\", "/")
            for b in sorted(bundles):
                bpath = os.path.join(dp, b)
                brel = os.path.relpath(bpath, pack).replace("\\", "/")
                needed, u = needs_of(bpath, pack_idx, game_idx, brel)
                have = set(declared.get(b) or [])
                for lbl, why in u:
                    unres.append((crel, b, lbl, why))
                for dep, labels in sorted(needed.items()):
                    tally["pointer-backed dependencies"] += 1
                    if dep in have:
                        tally["  declared"] += 1
                    else:
                        tally["  NOT DECLARED"] += 1
                        defects.append((crel, b, dep, sorted(labels)))
                # A declaration nothing points through is NOT an error. A TOP binds to
                # skeleton.bundle by bone name at runtime and never references its CAB, so
                # this rule is structurally blind to it. Reported, never removed.
                for dep in sorted(have - set(needed)):
                    unbacked.append((crel, b, dep))

    return defects, unres, unbacked, tally


def report(defects, unres, unbacked, tally):
    for k, v in tally.most_common():
        print(f"  {v:>5}  {k}")
    print()

    if defects:
        print(f"UNDECLARED, and a pointer actually goes there ({len(defects)}):\n")
        for crel, b, dep, labels in defects:
            print(f"  {crel}")
            print(f"      {b} points into {dep}")
            print(f"      via {', '.join(labels[:4])}{' ...' if len(labels) > 4 else ''}")
            print(f"      The client is never told to load that file, so these pointers")
            print(f"      resolve to nothing at runtime. Whether declaring it is sufficient")
            print(f"      depends on whether the pointers name the right pathIDs -- this")
            print(f"      check cannot tell you that, and on the helmets it was not enough.")
            print()
    else:
        print("no undeclared pointer-backed dependencies\n")

    if unres:
        print(f"pointers whose target is in neither the game nor the pack ({len(unres)}):")
        for crel, b, lbl, why in unres[:10]:
            print(f"  {crel}  {b}  {lbl}: {why}")
        if len(unres) > 10:
            print(f"  ... and {len(unres)-10} more")
        print()

    if unbacked:
        print(f"declared, but no pointer uses it ({len(unbacked)}) -- NOT a defect:")
        print("  Runtime binding does not go through a pathID. A TOP binds to skeleton.bundle")
        print("  by bone name and never names its CAB, so this list is where the")
        print("  non-derivable dependencies live. Do not remove these.")
        for crel, b, dep in unbacked[:10]:
            print(f"    {crel}  {b} -> {dep}")
        if len(unbacked) > 10:
            print(f"    ... and {len(unbacked)-10} more")
        print()


def selftest(pack, game):
    """A check nobody has watched fail is indistinguishable from one that cannot fail.

    Plants three states against the live tree, in a temporary copy of one config, and asserts
    the check distinguishes them. Restores the config afterwards.
    """
    print("SELFTEST -- planting known-bad states and requiring the check to fire\n")
    base_defects, _u, _ub, _t = run(pack, game, quiet=True)
    print(f"  baseline: {len(base_defects)} undeclared\n")

    # Find a config that currently declares a pointer-backed dependency, so removing it must
    # produce exactly one new defect.
    victim = None
    for dp, _d, fs in os.walk(pack):
        cfgs = [f for f in fs if f.endswith(".jsonc")]
        if not cfgs or not any(f.endswith(".bundle") for f in fs):
            continue
        for c in cfgs:
            p = os.path.join(dp, c)
            try:
                blk = (load_cfg(p).get("bundles") or {})
            except Exception:
                continue
            if any(v for v in blk.values()):
                victim = p
                break
        if victim:
            break
    if not victim:
        print("  CANNOT SELFTEST: no config declares a dependency")
        return 1

    # Bytes, not text. `utf-8-sig` on read plus `utf-8` on write silently drops a BOM, so a
    # text round-trip would restore a file that is *nearly* the original -- the quiet kind of
    # damage a passing selftest would then report as clean.
    original_bytes = open(victim, "rb").read()
    original = original_bytes.decode("utf-8-sig")
    rel = os.path.relpath(victim, pack).replace("\\", "/")
    try:
        # 1. dependency removed -> must gain at least one defect naming this config
        stripped = re.sub(r'"bundles"\s*:\s*\{.*?\n  \}', '"bundles": {}', original,
                          count=1, flags=re.S)
        if stripped == original:
            print(f"  CANNOT SELFTEST: could not rewrite {rel}")
            return 1
        open(victim, "w", encoding="utf-8").write(stripped)
        d1, _u, _ub, _t = run(pack, game, quiet=True)
        gained = [d for d in d1 if d[0] == rel]
        ok1 = len(d1) > len(base_defects) and gained
        print(f"  [{'PASS' if ok1 else 'FAIL'}] declaration removed -> "
              f"{len(d1)} undeclared (was {len(base_defects)}), {len(gained)} name {rel}")

        # 2. an EXTRA dependency nothing points through must NOT be reported as a defect
        extra = original.replace('"bundles": {', '"bundles": {\n      "NOTHING.bundle": ["shaders"],', 1)
        open(victim, "w", encoding="utf-8").write(extra)
        d2, _u2, ub2, _t2 = run(pack, game, quiet=True)
        ok2 = len(d2) == len(base_defects)
        print(f"  [{'PASS' if ok2 else 'FAIL'}] spurious declaration added -> "
              f"{len(d2)} undeclared (must equal {len(base_defects)})")
    finally:
        open(victim, "wb").write(original_bytes)

    d3, _u3, _ub3, _t3 = run(pack, game, quiet=True)
    ok3 = len(d3) == len(base_defects)
    # Two restore assertions, because they can disagree: the check re-deriving the baseline
    # says the file PARSES the same, and the byte compare says it IS the same. A whitespace or
    # BOM change passes the first and fails the second.
    ok4 = open(victim, "rb").read() == original_bytes
    print(f"  [{'PASS' if ok3 else 'FAIL'}] restored -> {len(d3)} undeclared "
          f"(must equal baseline {len(base_defects)})")
    print(f"  [{'PASS' if ok4 else 'FAIL'}] restored file is byte-identical to the original")
    print()
    ok3 = ok3 and ok4
    return 0 if (ok1 and ok2 and ok3) else 1


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--selftest" in sys.argv:
        sys.exit(selftest(args[0], args[1]))
    d, u, ub, t = run(args[0], args[1])
    report(d, u, ub, t)
    sys.exit(1 if d else 0)
