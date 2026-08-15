"""Drop the duplicated vanilla geometry out of DRIP's bundles and reference the game's copy.

WHY THIS IS SAFE TO DO AT ALL, and it was not until 2026-07-31: SPT targets exactly one EFT
build for the foreseeable future -- EFT 1.0 moved to IL2CPP, so SPT downgrades Live to this
internal version and stays there. A stripped bundle depends on a pathID in a game bundle
continuing to exist, which is a bad bet against a moving target and a fine one against a frozen
one. If that ever changes, this is the first thing to revisit.

THE MATCH IS BY HOLDER, NOT BY MESH NAME. `cr_commando_mesh` holds 62 meshes under 36 names, 52
of them shared, and the two candidates behind a shared name routinely have IDENTICAL vertex
counts -- so a name lookup is a coin flip and a vertex-count tiebreaker "confirms" whichever way
it lands. What separates them is which holder wants them: vanilla's MeshFilter and its
SkinnedMeshRenderer point at different pathIDs. So every DRIP holder is matched to vanilla's
holder with the same (GameObject name, component type), and its mesh pointer is copied verbatim.
This is the same rule that repointed 49 stale mesh pointers correctly, confirmed in the client.

TWO THINGS THAT MAKE IT WORK, and the second is the one that cost an evening to learn:

  1. the bundle's externals table must name the vanilla bundle, and the pointer must index it
  2. the CONFIG must declare a dependency on that bundle, or the client never loads it and the
     item renders invisible -- a correct pointer into a file nobody loaded

Both are done here. Skipping (2) produces exactly the symptom that looks like "meshes cannot be
shared", which is the wrong conclusion and an expensive one.

REFUSALS ARE THE POINT. A bundle is skipped whole if anything about it is unclear: unreadable
origin, a holder with no vanilla counterpart, or a local mesh still referenced by something after
repointing. Half-stripping a bundle is worse than not stripping it.

  python strip_meshes.py <pack-root> <game-StreamingAssets> [--apply] [--limit=N]

Dry run by default. Nothing is written without --apply.
"""
import sys
import os
import copy
import json
import re
import collections

import UnityPy

HOLDERS = ("MeshFilter", "SkinnedMeshRenderer")


def sfile(env):
    for r in env.files.values():
        inner = getattr(r, "files", None)
        if isinstance(inner, dict):
            for f in inner.values():
                if hasattr(f, "externals"):
                    return f
    return None


def cab_of(env):
    for r in env.files.values():
        inner = getattr(r, "files", None)
        if isinstance(inner, dict):
            for n in inner:
                if not n.endswith(".resS"):
                    return n
    return None


def go_names(env):
    out = {}
    for o in env.objects:
        if o.type.name == "GameObject":
            try:
                out[o.path_id] = getattr(o.read(), "m_Name", None)
            except Exception:
                pass
    return out


def holders(env):
    """[(gameobject name, component type, read object, m_Mesh ptr)]"""
    names = go_names(env)
    out = []
    for o in env.objects:
        if o.type.name not in HOLDERS:
            continue
        try:
            d = o.read()
        except Exception:
            continue
        m = getattr(d, "m_Mesh", None)
        if m is None:
            continue
        go = getattr(d, "m_GameObject", None)
        gname = names.get(getattr(go, "m_PathID", None)) if go is not None else None
        out.append((gname or "<no-gameobject>", o.type.name, d, m))
    return out


_VAN = {}


def vanilla_holders(vpath):
    """{(GameObject name, component type): {pathID, ...}} for meshes LOCAL to the vanilla bundle.

    Only local ones. A vanilla holder pointing somewhere else is not a target we can borrow by
    naming this bundle in our externals.
    """
    if vpath in _VAN:
        return _VAN[vpath]
    if len(_VAN) > 24:
        _VAN.clear()
    idx = collections.defaultdict(set)
    try:
        env = UnityPy.load(vpath)
    except Exception:
        _VAN[vpath] = ({}, None)
        return _VAN[vpath]
    for gname, htype, _d, m in holders(env):
        if m.m_FileID == 0 and m.m_PathID != 0:
            idx[(gname, htype)].add(m.m_PathID)
    _VAN[vpath] = (dict(idx), cab_of(env))
    return _VAN[vpath]


def strip(path, game, apply):
    env = UnityPy.load(path)
    origin = None
    for o in env.objects:
        if o.type.name == "AssetBundle":
            try:
                origin = getattr(o.read(), "m_Name", None)
            except Exception:
                pass
    if not origin:
        return "no-origin", 0, 0, origin
    vpath = os.path.join(game, origin.replace("/", os.sep))
    if not os.path.isfile(vpath):
        return "origin-missing", 0, 0, origin
    vidx, vcab = vanilla_holders(vpath)
    if not vidx or not vcab:
        return "vanilla-has-no-local-meshes", 0, 0, origin

    hs = holders(env)
    local_mesh = {o.path_id for o in env.objects if o.type.name == "Mesh"}
    if not local_mesh:
        return "nothing-to-strip", 0, 0, origin

    # Plan every holder first. One refusal skips the whole bundle.
    plan = []
    for gname, htype, d, m in hs:
        if m.m_PathID == 0:
            continue
        if m.m_FileID != 0:
            continue                      # already external; not ours to move
        if m.m_PathID not in local_mesh:
            return "holder-points-at-a-missing-local-mesh", 0, 0, origin
        cands = vidx.get((gname, htype))
        if not cands:
            return f"no-vanilla-holder:{gname}[{htype}]", 0, 0, origin
        if len(cands) > 1:
            return f"AMBIGUOUS:{gname}[{htype}]x{len(cands)}", 0, 0, origin
        plan.append((d, m, next(iter(cands))))
    if not plan:
        return "no-local-mesh-pointers", 0, 0, origin

    # Every local mesh must end up unreferenced, or we would delete something still in use.
    referenced_after = set()
    for o in env.objects:
        if o.type.name in HOLDERS:
            continue
        try:
            d = o.read()
        except Exception:
            continue
        for attr in ("m_Mesh",):
            p = getattr(d, attr, None)
            if p is not None and getattr(p, "m_FileID", 1) == 0 and p.m_PathID in local_mesh:
                referenced_after.add(p.m_PathID)
    moving = {m.m_PathID for _d, m, _t in plan}
    orphaned = local_mesh - referenced_after
    if not moving <= orphaned:
        return "local-mesh-still-referenced-elsewhere", 0, 0, origin

    sf = sfile(env)
    ext = [e.path.split("/")[-1] for e in sf.externals]
    if vcab not in ext:
        new = copy.deepcopy(sf.externals[0])
        new.path = f"archive:/{vcab}/{vcab}"
        sf.externals.append(new)
        ext.append(vcab)
    fid = ext.index(vcab) + 1

    before = os.path.getsize(path)
    for d, m, target in plan:
        m.m_FileID, m.m_PathID = fid, target
        d.save()
    removed = 0
    for pid in sorted(orphaned):
        if pid in sf.objects:
            del sf.objects[pid]
            removed += 1
    sf.mark_changed()

    if apply:
        try:
            data = env.file.save(packer="original")
        except TypeError:
            data = env.file.save()
        with open(path, "wb") as fh:
            fh.write(data)
        after = len(data)
    else:
        try:
            after = len(env.file.save(packer="original"))
        except TypeError:
            after = len(env.file.save())
    return "ok", removed, before - after, origin


def add_dependency(cfg_path, bundle_name, vanilla_path, apply):
    """Declare the borrowed bundle in the config, merging rather than overwriting."""
    txt = open(cfg_path, encoding="utf-8-sig").read()
    stripped = re.sub(r"/\*.*?\*/", "", txt, flags=re.S)
    stripped = re.sub(r"(?m)^\s*//.*$", "", stripped)
    stripped = re.sub(r",(\s*[}\]])", r"\1", stripped)
    try:
        cfg = json.loads(stripped)
    except Exception:
        return "config-unparseable"
    block = cfg.get("bundles") or {}
    have = block.get(bundle_name) or []
    if vanilla_path in have:
        return "already-declared"
    block[bundle_name] = have + [vanilla_path]
    cfg["bundles"] = block
    if not apply:
        return "would-add"
    # Rewrite only the bundles block, so the file keeps its comments and author formatting.
    body = json.dumps(block, indent=4)
    body = "\n".join("  " + ln for ln in body.splitlines()).strip()
    if '"bundles"' in txt:
        txt = re.sub(r'"bundles"\s*:\s*\{.*?\n  \}', f'"bundles": {body}', txt, count=1, flags=re.S)
    else:
        end = txt.rstrip().rfind("}")
        head = txt.rstrip()[:end].rstrip()
        if not head.endswith(",") and not head.endswith("{"):
            head += ","
        txt = (head + "\n\n  // Geometry lives in the game's own bundle rather than being copied in\n"
               "  // here. The pointer is only half of that: without this the client never loads\n"
               "  // the file and the item renders invisible.\n"
               f'  "bundles": {body}\n}}\n')
    open(cfg_path, "w", encoding="utf-8").write(txt)
    return "added"


def main(root, game, apply, limit):
    targets = []
    for dp, _d, fs in os.walk(root):
        for f in sorted(fs):
            if f.endswith(".bundle"):
                targets.append(os.path.join(dp, f))
    if limit:
        targets = targets[:limit]
    print(f"{'APPLYING' if apply else 'DRY RUN'} over {len(targets)} bundles\n", flush=True)

    status = collections.Counter()
    saved = 0
    meshes = 0
    cfgres = collections.Counter()
    for i, p in enumerate(targets, 1):
        rel = os.path.relpath(p, root).replace("\\", "/")
        try:
            st, n, delta, origin = strip(p, game, apply)
        except Exception as e:
            st, n, delta, origin = f"ERROR {type(e).__name__}: {e}", 0, 0, None
        status[st.split(":")[0]] += 1
        if st == "ok":
            saved += delta
            meshes += n
            cfgs = [f for f in os.listdir(os.path.dirname(p)) if f.endswith(".jsonc")]
            for c in cfgs:
                cfgres[add_dependency(os.path.join(os.path.dirname(p), c),
                                      os.path.basename(p), origin, apply)] += 1
            print(f"[{i}/{len(targets)}] -{delta/1024:>8,.0f} KB  {n:>2} mesh  {rel}", flush=True)
        elif not st.startswith(("nothing", "no-local")):
            print(f"[{i}/{len(targets)}] {'SKIP':>11}  {rel}   <- {st}", flush=True)

    print(f"\n{meshes} local meshes dropped, {saved/2**20:,.1f} MB saved")
    print("bundle outcome:")
    for k, v in status.most_common():
        print(f"  {k:<42}{v}")
    print("config dependency:")
    for k, v in cfgres.most_common():
        print(f"  {k:<42}{v}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    lim = None
    for a in sys.argv[1:]:
        if a.startswith("--limit="):
            lim = int(a.split("=", 1)[1])
    main(args[0], args[1], "--apply" in sys.argv, lim)
