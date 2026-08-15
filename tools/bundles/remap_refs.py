"""Repoint stale TEXTURE and MESH references at the objects the current game actually ships.

Companion to `repack_all.py`, which did exactly this for material -> shader pointers and left the
other two pointer types untouched. Those are the missing wristwatch on every hands bundle, the
white IOTV / FAST MT / AirFrame shroud, and the blank inventory cells.

HOW IT DIFFERS FROM repack_all.py, and why that matters:

  repack_all rewrote the EXTERNALS TABLE so a slot named the right bundle. That works when one
  pointer type reads a slot, and it caused a real bug when two disagreed about the same slot --
  190 materials pointed at a valid CAB that was not the shaders bundle.

  This script never rewrites the table. It rewrites the POINTER: if the bundle's externals
  already list the bundle an object lives in, the fix is to make fileID index that slot. Two
  pointer types can then want different targets without fighting over one entry.

The name is the key, as with shaders: DRIP's bundles are modified copies of vanilla ones, so a
material called `bear_wach` here corresponds to `bear_wach` there, and vanilla's own pointer says
where that texture now lives.

MESHES, AND THE TIEBREAKER THAT WOULD HAVE BEEN WRONG. The recorded plan for meshes was to look
the mesh name up in the target bundle and disambiguate collisions by vertex count. Both halves of
that were bad:

  * `cr_commando_mesh` holds 62 meshes under 36 names, 52 of them shared -- and every name these
    pointers land on has exactly TWO candidates, so a name lookup is a coin flip, not an edge case.
  * the two candidates are the static mesh and the skinned mesh, and their vertex counts are
    IDENTICAL in three cases out of four (3947/3947, 1484/1484, 2121/2121, 996/996). Vertex count
    would have "confirmed" an arbitrary pick. A tiebreaker that cannot distinguish the things it
    is tiebreaking is worse than no tiebreaker, because it reports success.

  What actually separates them is which kind of holder wants the mesh: vanilla's MeshFilter and
  its SkinnedMeshRenderer point at different pathIDs. So meshes match on (GameObject name, holder
  TYPE), and a name with two disagreeing vanilla candidates is refused, never guessed. A blank
  inventory cell is honest; a confidently wrong mesh is not, because nothing flags it.

  python remap_refs.py <pack-root> <game-StreamingAssets-Windows> [--apply] [--limit=N]
  python remap_refs.py --selftest

Dry run by default. Reports what it WOULD change and why. `--apply` writes.
"""
import sys
import os
import collections

import UnityPy

TEXTURE_TYPES = ("Texture2D", "Cubemap")
MESH_HOLDERS = ("MeshFilter", "SkinnedMeshRenderer", "MeshRenderer")


def serialized_files(env):
    for reader in env.files.values():
        inner = getattr(reader, "files", None)
        if isinstance(inner, dict):
            for f in inner.values():
                if hasattr(f, "externals"):
                    yield f


def cab_of(path):
    """The CAB name(s) a container publishes -- what other bundles refer to it as."""
    out = set()
    try:
        env = UnityPy.load(path)
    except Exception:
        return out
    for reader in env.files.values():
        inner = getattr(reader, "files", None)
        if isinstance(inner, dict):
            for n in inner:
                if not n.endswith(".resS"):
                    out.add(n)
    return out


def externals(env):
    for f in serialized_files(env):
        return [e.path.split("/")[-1] for e in f.externals]
    return []


def origin_of(env):
    for obj in env.objects:
        if obj.type.name == "AssetBundle":
            try:
                return getattr(obj.read(), "m_Name", None)
            except Exception:
                return None
    return None


_VAN = {}


def probe_vanilla(vpath):
    """{material name: {property: (CAB, pathID)}} for every EXTERNAL texture pointer.

    Resolved to a CAB rather than a fileID, because vanilla's externals table and DRIP's are in
    different orders -- a fileID is only meaningful inside the file it came from. This is the
    same mistake that produced 190 broken materials the first time round, avoided by never
    carrying a raw index across a file boundary.
    """
    if vpath in _VAN:
        return _VAN[vpath]
    if len(_VAN) > 48:
        _VAN.clear()
    out = {}
    try:
        env = UnityPy.load(vpath)
    except Exception:
        _VAN[vpath] = out
        return out
    ext = externals(env)
    local = {o.path_id for o in env.objects if o.type.name in TEXTURE_TYPES}
    for obj in env.objects:
        if obj.type.name != "Material":
            continue
        try:
            d = obj.read()
        except Exception:
            continue
        sp = getattr(d, "m_SavedProperties", None)
        slots = {}
        for prop, tenv in (getattr(sp, "m_TexEnvs", None) or []):
            t = getattr(tenv, "m_Texture", None)
            if t is None or t.m_PathID == 0:
                continue
            if t.m_FileID == 0:
                # Lives inside the vanilla bundle itself. DRIP cannot point at that without
                # taking a dependency on the whole vanilla bundle, so it is not remappable here.
                slots[prop] = ("<vanilla-local>", t.m_PathID)
            elif 1 <= t.m_FileID <= len(ext):
                slots[prop] = (ext[t.m_FileID - 1], t.m_PathID)
        out[getattr(d, "m_Name", "?")] = slots
    _VAN[vpath] = out
    return out


_VANMESH = {}


def go_names(env):
    """pathID -> GameObject name, for GameObjects local to this container."""
    out = {}
    for o in env.objects:
        if o.type.name == "GameObject":
            try:
                out[o.path_id] = getattr(o.read(), "m_Name", None)
            except Exception:
                pass
    return out


def mesh_holders(env, ext):
    """[(gameobject name, holder type, obj, m_Mesh ptr, (CAB, pathID) it currently resolves to)].

    Resolved to a CAB for the same reason materials are: a fileID means nothing outside the file
    it came from, and vanilla's externals are not in DRIP's order.
    """
    names = go_names(env)
    out = []
    for o in env.objects:
        if o.type.name not in MESH_HOLDERS:
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
        if m.m_PathID == 0:
            cur = ("<unset>", 0)
        elif m.m_FileID == 0:
            cur = ("<local>", m.m_PathID)
        elif 1 <= m.m_FileID <= len(ext):
            cur = (ext[m.m_FileID - 1], m.m_PathID)
        else:
            cur = ("<fileID-out-of-range>", m.m_PathID)
        out.append((gname or "<no-gameobject>", o.type.name, d, m, cur))
    return out


def probe_vanilla_meshes(vpath):
    """{(GameObject name, holder type): {(CAB, pathID), ...}} for vanilla's mesh holders.

    A set, not a single value, so that a name+type wanting two DIFFERENT meshes is visible as
    ambiguity at the call site instead of being silently collapsed to whichever came last.
    """
    if vpath in _VANMESH:
        return _VANMESH[vpath]
    if len(_VANMESH) > 32:
        _VANMESH.clear()
    idx = collections.defaultdict(set)
    try:
        env = UnityPy.load(vpath)
    except Exception:
        _VANMESH[vpath] = {}
        return {}
    ext = externals(env)
    for gname, htype, _d, _m, cur in mesh_holders(env, ext):
        idx[(gname, htype)].add(cur)
    _VANMESH[vpath] = dict(idx)
    return _VANMESH[vpath]


def remap(path, game, apply):
    env = UnityPy.load(path)
    origin = origin_of(env)
    if not origin:
        return "no-origin", collections.Counter(), []
    vpath = os.path.join(game, origin.replace("/", os.sep))
    if not os.path.isfile(vpath):
        return "origin-missing", collections.Counter(), []

    van = probe_vanilla(vpath)
    vanmesh = probe_vanilla_meshes(vpath)
    if not van and not vanmesh:
        # Only give up when BOTH indexes are empty. Bailing on `not van` alone would have skipped
        # mesh work in every bundle whose vanilla origin has no materials -- the same
        # walk-only-materials blindness that hid the half-masks from verify_repack.
        return "vanilla-unreadable", collections.Counter(), []

    ext = externals(env)
    slot_of = {c: i + 1 for i, c in enumerate(ext)}  # CAB -> fileID
    local = {o.path_id for o in env.objects if o.type.name in TEXTURE_TYPES}

    changed, notes = collections.Counter(), []
    for obj in env.objects:
        if obj.type.name != "Material":
            continue
        try:
            d = obj.read()
        except Exception:
            continue
        name = getattr(d, "m_Name", "?")
        vmat = van.get(name)
        if vmat is None:
            notes.append(f"no-vanilla-material:{name}")
            continue
        sp = getattr(d, "m_SavedProperties", None)
        dirty = False
        for prop, tenv in (getattr(sp, "m_TexEnvs", None) or []):
            t = getattr(tenv, "m_Texture", None)
            if t is None or t.m_PathID == 0:
                continue
            if t.m_FileID == 0:
                continue  # DRIP's own retextured art. Correct by construction; never touch it.
            want = vmat.get(prop)
            if want is None:
                notes.append(f"no-vanilla-slot:{name}.{prop}")
                continue
            cab, pid = want
            if cab == "<vanilla-local>":
                notes.append(f"target-is-vanilla-local:{name}.{prop}")
                continue
            fid = slot_of.get(cab)
            if fid is None:
                # The bundle holding this texture is not in our externals at all. Adding an
                # entry is a structural change, not a repoint, so it is reported not guessed.
                notes.append(f"cab-not-in-externals:{name}.{prop}->{cab[:20]}")
                continue
            if (t.m_FileID, t.m_PathID) != (fid, pid):
                t.m_FileID, t.m_PathID = fid, pid
                dirty = True
                changed["texture"] += 1
        if dirty and apply:
            d.save()

    # ---- meshes: the blank inventory cells -------------------------------------------------
    for gname, htype, d, m, cur in mesh_holders(env, ext):
        if cur[0] in ("<local>", "<unset>"):
            continue  # DRIP's own mesh, or no mesh at all. Never touch either.
        cands = vanmesh.get((gname, htype))
        if not cands:
            notes.append(f"no-vanilla-holder:{gname}[{htype}]")
            continue
        if len(cands) > 1:
            # Vanilla itself has two holders of this name and type wanting different meshes.
            # Nothing here can choose between them, and choosing wrong renders a plausible
            # incorrect model that no check would ever flag. Refuse.
            notes.append(f"AMBIGUOUS:{gname}[{htype}]x{len(cands)}")
            continue
        cab, pid = next(iter(cands))
        if cab in ("<local>", "<unset>", "<fileID-out-of-range>"):
            notes.append(f"vanilla-target-{cab.strip('<>')}:{gname}[{htype}]")
            continue
        fid = slot_of.get(cab)
        if fid is None:
            notes.append(f"cab-not-in-externals:{gname}[{htype}]->{cab[:20]}")
            continue
        if (m.m_FileID, m.m_PathID) != (fid, pid):
            m.m_FileID, m.m_PathID = fid, pid
            changed["mesh"] += 1
            if apply:
                d.save()

    if apply and changed:
        try:
            data = env.file.save(packer="original")
        except TypeError:
            data = env.file.save()
        with open(path, "wb") as fh:
            fh.write(data)

    status = "ok" if not notes else "ok-with-notes"
    return status, changed, notes


def main(root, game, apply, limit):
    targets = []
    for dp, _d, fs in os.walk(root):
        for f in sorted(fs):
            if f.endswith(".bundle"):
                targets.append(os.path.join(dp, f))
    if limit:
        targets = targets[:limit]

    print(f"{'APPLYING' if apply else 'DRY RUN'} over {len(targets)} bundles\n", flush=True)
    tally = collections.Counter()
    notes = collections.Counter()
    total = collections.Counter()
    for i, p in enumerate(targets, 1):
        rel = os.path.relpath(p, root)
        try:
            status, n, ns = remap(p, game, apply)
        except Exception as e:
            status, n, ns = f"ERROR {type(e).__name__}: {e}", collections.Counter(), []
        tally[status.split(":")[0]] += 1
        total.update(n)
        for x in ns:
            notes[x.split(":")[0]] += 1
        if n or status not in ("ok", "ok-with-notes"):
            kinds = " ".join(f"{v} {k}" for k, v in sorted(n.items())) or "-"
            print(f"[{i}/{len(targets)}] {kinds:>22}  {rel}"
                  f"{'' if status.startswith('ok') else '   <- ' + status}", flush=True)

    print(f"\npointers repointed: {sum(total.values())} total")
    for k, v in sorted(total.items()):
        print(f"  {k:<26}{v}")
    print("bundle status:")
    for k, v in tally.most_common():
        print(f"  {k:<26}{v}")
    if notes:
        print("notes (not repointed, and why):")
        for k, v in notes.most_common():
            print(f"  {k:<26}{v}")
    if notes.get("AMBIGUOUS"):
        print("\n  AMBIGUOUS means vanilla has two holders of the same name and type wanting")
        print("  DIFFERENT meshes. Those are left dangling on purpose: a blank inventory cell is")
        print("  honest, a confidently wrong mesh is not. Do not 'fix' these by picking one.")


def selftest():
    """Drive every decision branch with planted data.

    Both mesh branches that matter reported ZERO on the real pack, and a check that reports
    nothing is indistinguishable from a check that does nothing. These exist so that stays
    falsifiable after the next edit.
    """
    def decide(van, gname, htype, cur, slot_of):
        cands = van.get((gname, htype))
        if not cands:
            return "no-vanilla-holder"
        if len(cands) > 1:
            return "AMBIGUOUS"
        cab, pid = next(iter(cands))
        if cab in ("<local>", "<unset>", "<fileID-out-of-range>"):
            return "vanilla-target-unusable"
        if cab not in slot_of:
            return "cab-not-in-externals"
        return "already-correct" if (slot_of[cab], pid) == cur else "REPOINT"

    cases = [
        ("vanilla disagrees with itself",
         {("A", "MeshFilter"): {("X", 1), ("X", 2)}}, "A", "MeshFilter", (1, 9), {"X": 1},
         "AMBIGUOUS"),
        ("two vanilla holders that AGREE -> not ambiguous",
         {("A", "MeshFilter"): {("X", 1)}}, "A", "MeshFilter", (1, 9), {"X": 1}, "REPOINT"),
        ("right name, wrong holder type",
         {("A", "MeshFilter"): {("X", 1)}}, "A", "SkinnedMeshRenderer", (1, 9), {"X": 1},
         "no-vanilla-holder"),
        ("no vanilla holder at all",
         {}, "A", "MeshFilter", (1, 9), {"X": 1}, "no-vanilla-holder"),
        ("pointer already right",
         {("A", "MeshFilter"): {("X", 1)}}, "A", "MeshFilter", (1, 1), {"X": 1},
         "already-correct"),
        ("target bundle not in our externals",
         {("A", "MeshFilter"): {("Y", 1)}}, "A", "MeshFilter", (1, 9), {"X": 1},
         "cab-not-in-externals"),
        ("vanilla's own pointer is local",
         {("A", "MeshFilter"): {("<local>", 1)}}, "A", "MeshFilter", (1, 9), {"X": 1},
         "vanilla-target-unusable"),
    ]
    bad = 0
    for label, van, g, t, cur, slots, expect in cases:
        got = decide(van, g, t, cur, slots)
        if got != expect:
            bad += 1
        print(f"  {'PASS' if got == expect else '*** FAIL ***':<12} {label:<44} -> {got}")
    print(f"\n{len(cases) - bad}/{len(cases)} branches behave as documented")
    return bad == 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    ap = "--apply" in sys.argv
    lim = None
    for a in sys.argv[1:]:
        if a.startswith("--limit="):
            lim = int(a.split("=", 1)[1])
    main(args[0], args[1], ap, lim)
