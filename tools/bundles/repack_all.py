"""Repoint stale shader references in DRIP bundles at the current game's shaders.

Each bundle records the vanilla bundle it was cloned from, so the correct externals
table and per-material shader pathIDs are looked up from that counterpart and
rewritten in place. Textures and meshes are untouched.

This fixes the magenta rendering. It does NOT fix missing mipmaps or bundle size --
only a real rebuild does those.

Usage:
  python repack_all.py <src-root> <game-StreamingAssets-Windows> <out-root> [--limit=N]
"""
import sys
import os
import shutil
import collections

import UnityPy


def serialized_files(env):
    for reader in env.files.values():
        inner = getattr(reader, "files", None)
        if isinstance(inner, dict):
            for f in inner.values():
                if hasattr(f, "externals"):
                    yield f


def probe(path):
    """(origin path, {material name: (fileID, pathID)}, [external paths])"""
    env = UnityPy.load(path)
    origin, mats = None, {}
    for obj in env.objects:
        if obj.type.name == "AssetBundle":
            try:
                origin = getattr(obj.read(), "m_Name", None)
            except Exception:
                pass
        elif obj.type.name == "Material":
            try:
                d = obj.read()
                sh = getattr(d, "m_Shader", None)
                if sh is not None:
                    mats[getattr(d, "m_Name", "?")] = (sh.m_FileID, sh.m_PathID)
            except Exception:
                pass
    ext = []
    for f in serialized_files(env):
        ext = [e.path for e in f.externals]
        break
    return origin, mats, ext


_VAN_CACHE = {}


def probe_vanilla(vpath):
    """Many DRIP bundles share one vanilla origin, so cache the lookup."""
    if vpath not in _VAN_CACHE:
        if len(_VAN_CACHE) > 64:
            _VAN_CACHE.clear()
        _VAN_CACHE[vpath] = probe(vpath)
    return _VAN_CACHE[vpath]


def repack(src, game, dst):
    origin, _m, src_ext = probe(src)
    if not origin:
        return "no-origin", 0
    vpath = os.path.join(game, origin.replace("/", os.sep))
    if not os.path.isfile(vpath):
        return "origin-missing", 0
    _o, van_mats, van_ext = probe_vanilla(vpath)

    os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
    if os.path.abspath(src) != os.path.abspath(dst):
        shutil.copyfile(src, dst)
    env = UnityPy.load(dst)

    # A material whose name has no vanilla counterpart still needs a live shader.
    # Its siblings in the same bundle are the best available evidence, so fall back
    # to whichever shader the majority of the vanilla materials here use.
    fallback = None
    if van_mats:
        fallback = collections.Counter(van_mats.values()).most_common(1)[0][0]

    # ext_fix maps "this external slot" -> "the path it must name", derived per
    # material from its vanilla counterpart's own fileID. This is authoritative:
    # DRIP's externals are not in the same order as vanilla's, so mapping the table
    # positionally puts the wrong CAB in the slot the shader pointer reads.
    ext_fix = {}
    unmatched, outofrange = [], []
    for obj in env.objects:
        if obj.type.name != "Material":
            continue
        d = obj.read()
        name = getattr(d, "m_Name", "?")
        van = van_mats.get(name) or fallback
        if van is None:
            unmatched.append(name)
            continue
        if name not in van_mats:
            unmatched.append(name)
        van_fid, van_pid = van
        sh = d.m_Shader
        if not (1 <= van_fid <= len(van_ext)) or not (1 <= sh.m_FileID <= len(src_ext)):
            outofrange.append(name)
            continue
        ext_fix[sh.m_FileID - 1] = van_ext[van_fid - 1]
        if sh.m_PathID != van_pid:
            sh.m_PathID = van_pid
            d.save()

    # Precedence matters: ext_fix wins. Positional mapping only fills the slots no
    # shader pointer reads, so stale cubemap/skeleton references get refreshed too
    # without ever displacing a shader slot.
    positional = len(src_ext) == len(van_ext)
    changes = 0
    for f in serialized_files(env):
        for i, e in enumerate(f.externals):
            want = ext_fix.get(i)
            if want is None and positional and i < len(van_ext):
                want = van_ext[i]
            if want and e.path != want:
                e.path = want
                changes += 1
    changes += len(ext_fix)

    try:
        data = env.file.save(packer="original")
    except TypeError:
        data = env.file.save()
    with open(dst, "wb") as fh:
        fh.write(data)

    # Save whatever was fixable before reporting a partial result -- bailing early
    # would discard correct repairs alongside the one that could not be made.
    if outofrange:
        return "fileID-out-of-range:" + ",".join(outofrange[:2]), changes
    if unmatched:
        return "ok-fallback-shader:" + ",".join(unmatched[:3]), changes
    return "ok", changes


def main(src_root, game, out_root, limit=None):
    targets = []
    for dp, _d, fs in os.walk(src_root):
        for f in sorted(fs):
            if f.endswith(".bundle"):
                targets.append(os.path.join(dp, f))
    if limit:
        targets = targets[: int(limit)]

    tally = {}
    for i, p in enumerate(targets, 1):
        rel = os.path.relpath(p, src_root)
        dst = os.path.join(out_root, rel)
        try:
            status, n = repack(p, game, dst)
        except Exception as e:
            status, n = f"ERROR {type(e).__name__}: {e}", 0
        key = status.split(":")[0]
        tally[key] = tally.get(key, 0) + 1
        flag = "" if key == "ok" else f"   <- {status}"
        print(f"[{i}/{len(targets)}] {n:>2} refs  {rel}{flag}", flush=True)

    print("\nsummary:")
    for k, v in sorted(tally.items(), key=lambda kv: -kv[1]):
        print(f"  {k:<24}{v}")


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    lim = None
    for x in sys.argv[1:]:
        if x.startswith("--limit="):
            lim = x.split("=", 1)[1]
    main(a[0], a[1], a[2], lim)
