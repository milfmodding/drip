"""Audit every cross-bundle reference in the pack: shader, mesh and texture.

WHY THIS EXISTS. `repack_all.py` fixed material -> shader pointers and `verify_repack.py`
counted materials to prove it. Both walk MATERIALS, so:

  * bundles with no materials were never examined, and verify_repack reported them clean because
    it had nothing to report -- the half-masks, whose every external is dead;
  * MeshFilter.m_Mesh, SkinnedMeshRenderer.m_Mesh and Material texture slots use exactly the same
    (external, pathID) mechanism as shaders, and nothing ever checked them -- the blank inventory
    items and Sophia's missing wristwatch.

Both gaps were found by a human looking at the game, not by the tooling.

THE RULE THIS FILE IS BUILT AROUND. Every verdict here is really "not found in my index", so the
index IS the finding. Anything the indexer fails to read becomes a false accusation against the
mod; anything it over-matches becomes a silent acquittal. So this script reports its own coverage
-- pointers examined per kind, files it could not read, bundles it could not open -- and those
counts are the first thing to check. A clean report with a collapsed denominator is the exact
failure mode it exists to catch.

Usage: python audit_refs.py <pack-root> <game-StreamingAssets-Windows>
"""
import os
import sys
import collections

import UnityPy

MESH_HOLDERS = ("MeshFilter", "SkinnedMeshRenderer")
TEXTURE_TYPES = ("Texture2D", "Cubemap")


def serialized_files(env):
    """The serialized files inside a container, by name (CAB-xxxx). Excludes .resS blobs."""
    out = {}
    for reader in env.files.values():
        inner = getattr(reader, "files", None)
        if isinstance(inner, dict):
            for name, sf in inner.items():
                if not name.endswith(".resS"):
                    out[name] = sf
    return out


def owning_cab(obj, fallback):
    """Which serialized file an object actually lives in.

    Kappa's finding: ~15% of the game's containers publish TWO CABs, so registering every object
    under every CAB the container publishes makes the index PERMISSIVE -- a pathID living in CAB A
    resolves when referenced through CAB B. That turns real dangles into passes, which is the
    direction that hides bugs rather than inventing them. Attribute to the owning file instead.
    """
    af = getattr(obj, "assets_file", None)
    name = getattr(af, "name", None)
    return name if name else fallback


def externals(env):
    """The external list of the container's serialized file.

    LATENT LIMITATION: returns the FIRST serialized file's list. All 365 pack bundles currently
    have exactly one, so this is correct today -- but multi-serialized-file containers plainly
    exist in the game (38 of 260 sampled publish two CABs). If the pack is ever built that way,
    `ext[fid - 1]` would index the wrong external list, producing false dangles AND false passes.
    """
    for sf in serialized_files(env).values():
        if hasattr(sf, "externals"):
            return [e.path for e in sf.externals]
    return []


def index_pack(root):
    """CAB -> path, and (CAB, pathID) -> type, for everything the PACK ships.

    THE BUG THIS FIXES, and it is the same bug this file was written to catch. `index_game` is
    named honestly: it indexes the game. Every verdict below then resolved references against the
    game alone -- so a DRIP bundle referring to ANOTHER DRIP BUNDLE was reported as a dead external
    BY CONSTRUCTION. There was no input that could have produced a different answer.

    That is not a measurement of the pack, it is a measurement of the tool's blind spot, and it
    is exactly the failure mode named in this file's own header: a verdict is really "not found in
    my index", so the index IS the finding. The header was right and the code did not obey it.

    It cost a real diagnosis: four half-mask bundles were reported as having dead externals and
    no material, when their material was packed in a sibling bundle with a correct pointer. The
    actual fault was that the client never LOADED the sibling, which is a dependency-declaration
    bug and looks nothing like a broken pointer.
    """
    cabs, objs = {}, {}
    for dp, _d, fs in os.walk(root):
        for f in sorted(fs):
            if not f.endswith(".bundle"):
                continue
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, root).replace("\\", "/")
            try:
                env = UnityPy.load(p)
            except Exception:
                continue
            sfs = serialized_files(env)
            only = next(iter(sfs)) if len(sfs) == 1 else None
            for c in sfs:
                cabs[c] = rel
            for o in env.objects:
                if o.type.name in ("Shader", "Mesh", "Material") + TEXTURE_TYPES:
                    objs[(owning_cab(o, only), o.path_id)] = o.type.name
    return cabs, objs


def index_game(game):
    """CAB -> path, and (CAB, pathID) -> type, for everything the game ships."""
    cabs, objs, n = {}, {}, 0
    unreadable, unindexed = [], []
    non_bundle = 0
    for dp, _d, fs in os.walk(game):
        for f in fs:
            if f.endswith((".resS", ".manifest")):
                continue
            p = os.path.join(dp, f)
            n += 1
            rel = os.path.relpath(p, game).replace("\\", "/")
            try:
                env = UnityPy.load(p)
            except Exception as ex:
                unreadable.append(f"{rel}  ({type(ex).__name__})")
                continue

            sfs = serialized_files(env)
            if not sfs:
                # Loaded but published no CAB. Usually a loose non-bundle file and harmless -- but
                # if it holds objects, it is a bundle we failed to enumerate, and references into
                # it will read as dead externals. That is a false accusation, so separate the two
                # rather than tallying both as "expected".
                if any(True for _ in env.objects):
                    unindexed.append(rel)
                else:
                    non_bundle += 1
                continue

            only = next(iter(sfs)) if len(sfs) == 1 else None
            for c in sfs:
                cabs[c] = rel
            for o in env.objects:
                if o.type.name in ("Shader", "Mesh", "Material") + TEXTURE_TYPES:
                    objs[(owning_cab(o, only), o.path_id)] = o.type.name
    return cabs, objs, n, unreadable, unindexed, non_bundle


def main(root, game):
    print("indexing the pack's own bundles ...", flush=True)
    pack_cabs, pack_objs = index_pack(root)
    print(f"  {len(pack_cabs)} CABs published by the PACK itself, {len(pack_objs)} objects")
    print("indexing the game's bundles (slow, once) ...", flush=True)
    cabs, objs, scanned, unreadable, unindexed, non_bundle = index_game(game)
    print(f"  {scanned} files, {len(cabs)} CABs, {len(objs)} shader/mesh/texture objects")

    # A CAB published by BOTH would make every lookup order-dependent, and DRIP's bundles are
    # clones of vanilla ones so this is a live risk rather than a theoretical one. Say so loudly.
    both = set(cabs) & set(pack_cabs)
    if both:
        print(f"  *** {len(both)} CABs are published by the game AND the pack. Lookups below")
        print(f"  *** resolve game-first; that is a choice, not a fact. {sorted(both)[:4]}")
    else:
        print("  0 CABs published by both -- no ambiguity about where a reference resolves")
    print(f"  {non_bundle} loose non-bundle files (expected)")
    if unreadable:
        print(f"  *** {len(unreadable)} GAME files unreadable -- every verdict below is an UPPER")
        print(f"  *** BOUND: a reference into one of these reads as dangling when it may be fine.")
        for u in unreadable[:10]:
            print(f"        {u}")
    if unindexed:
        print(f"  *** {len(unindexed)} GAME files loaded but published no CAB while holding objects.")
        print(f"  *** References into these will read as dead externals. Same false-accusation risk.")
        for u in unindexed[:10]:
            print(f"        {u}")
    if not unreadable and not unindexed:
        print("  0 unreadable, 0 unindexed -- verdicts below are findings, not upper bounds")
    print(flush=True)

    tally = collections.Counter()
    seen = collections.Counter()  # the DENOMINATOR: how much work each check actually did
    broken = collections.defaultdict(list)
    unset_maintex = []
    sibling_refs = []  # pack -> pack references. Legal, and formerly counted as dead.

    for dp, _d, fs in os.walk(root):
        for f in sorted(fs):
            if not f.endswith(".bundle"):
                continue
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, root).replace("\\", "/")
            tally["bundles"] += 1
            try:
                env = UnityPy.load(p)
            except Exception:
                tally["PACK bundles unloadable (pointers UNAUDITED)"] += 1
                continue

            ext = externals(env)
            sfs = serialized_files(env)
            only = next(iter(sfs)) if len(sfs) == 1 else None
            if len(sfs) > 1:
                tally["PACK bundles with >1 serialized file (externals() may be wrong)"] += 1

            local_mesh, local_shader, local_tex, local_material = set(), set(), set(), set()
            for o in env.objects:
                t = o.type.name
                if t == "Mesh":
                    local_mesh.add(o.path_id)
                elif t == "Shader":
                    local_shader.add(o.path_id)
                elif t == "Material":
                    local_material.add(o.path_id)
                elif t in TEXTURE_TYPES:
                    local_tex.add(o.path_id)

            # "No materials" was a conflated tally: it counted pure texture-atlas bundles, whose
            # whole job is to carry a few Texture2Ds and which CORRECTLY have no material, beside
            # the half-masks, which have renderers demanding a material that was never packed.
            # 6 innocent + 4 defective read as "10 problems". Split by whether anything in the
            # bundle actually needs a material. (Kappa)
            n_mat = sum(1 for o in env.objects if o.type.name == "Material")
            n_rend = sum(1 for o in env.objects
                         if o.type.name in ("MeshRenderer", "SkinnedMeshRenderer"))
            if n_mat == 0:
                if n_rend:
                    tally["bundles with renderers but NO material (defect)"] += 1
                else:
                    tally["pure texture/atlas bundles, no material needed (fine)"] += 1

            for e in ext:
                cab = e.split("/")[-1]
                seen["externals examined"] += 1
                if cab in cabs:
                    seen["externals resolving into the GAME"] += 1
                elif cab in pack_cabs:
                    # A DRIP bundle naming another DRIP bundle. Perfectly legal, and previously
                    # reported as a dead external because the index only held the game.
                    seen["externals resolving into the PACK (sibling)"] += 1
                    sibling_refs.append(f"{rel}  {cab} -> {pack_cabs[cab]}")
                else:
                    tally["dead externals (in neither game nor pack)"] += 1
                    broken["dead external"].append(f"{rel}  {cab}")

            def check(ptr, kind, want_types, local, label):
                fid, pid = ptr.m_FileID, ptr.m_PathID
                seen[f"{kind} pointers examined"] += 1
                if fid == 0:
                    seen[f"{kind} local"] += 1
                    if pid not in local:
                        tally[f"{kind}: in-bundle pathID missing"] += 1
                        broken[f"{kind} in-bundle"].append(f"{rel}  {label}")
                    return
                seen[f"{kind} external"] += 1
                if not (1 <= fid <= len(ext)):
                    tally[f"{kind}: fileID out of range"] += 1
                    broken[f"{kind} fileID"].append(f"{rel}  {label}")
                    return
                cab = ext[fid - 1].split("/")[-1]
                in_game, in_pack = cab in cabs, cab in pack_cabs
                if not in_game and not in_pack:
                    return  # already counted as a dead external
                # Resolve against whichever ships it. Game first, and the collision count printed
                # above is what licenses that ordering rather than assumption.
                found = objs.get((cab, pid)) if in_game else None
                if found is None and in_pack:
                    found = pack_objs.get((cab, pid))
                    if found in want_types:
                        seen[f"{kind} resolved into a PACK sibling"] += 1
                if found not in want_types:
                    tally[f"{kind}: DANGLING pathID"] += 1
                    broken[f"{kind} dangling"].append(f"{rel}  {label} -> {cab}")

            n_meshref = 0
            for obj in env.objects:
                t = obj.type.name
                if t == "Material":
                    try:
                        d = obj.read()
                    except Exception:
                        tally["materials unreadable (slots UNAUDITED)"] += 1
                        continue
                    mat = getattr(d, "m_Name", "?")
                    seen["materials"] += 1

                    sh = getattr(d, "m_Shader", None)
                    if sh is not None:
                        check(sh, "Shader", ("Shader",), local_shader, mat)

                    sp = getattr(d, "m_SavedProperties", None)
                    tex_envs = getattr(sp, "m_TexEnvs", None) if sp is not None else None
                    if not tex_envs:
                        # If UnityPy ever renames these, every texture check silently examines
                        # nothing and the report reads clean. Count it so the denominator moves.
                        tally["materials with no usable m_TexEnvs"] += 1
                        continue
                    for prop, tenv in tex_envs:
                        tex = getattr(tenv, "m_Texture", None)
                        if tex is None:
                            continue
                        if tex.m_PathID == 0:
                            seen["texture slots unset"] += 1
                            if tex.m_FileID != 0:
                                # Half-pointer: a real broken reference, not an empty slot.
                                tally["Texture: fileID set but pathID 0"] += 1
                                broken["texture half-pointer"].append(f"{rel}  {mat}.{prop}")
                            elif prop == "_MainTex":
                                # Benign on ARMYCAP SHADOW_TRUE and Unity default materials, but a
                                # genuinely missing diffuse would hide here. Name them.
                                unset_maintex.append(f"{rel}  {mat}")
                            continue
                        # Property-aware: _Cube wants a Cubemap, every other slot a Texture2D.
                        # Lumping them is a no-op today only because nothing resolves at all; once
                        # these are remapped it would pass a _MainTex bound to a Cubemap.
                        want = ("Cubemap",) if prop == "_Cube" else ("Texture2D",)
                        check(tex, "Texture", want, local_tex, f"{mat}.{prop}")

                elif t in MESH_HOLDERS or t == "MeshRenderer":
                    try:
                        d = obj.read()
                    except Exception:
                        tally["mesh holders unreadable (pointers UNAUDITED)"] += 1
                        continue
                    m = getattr(d, "m_Mesh", None)
                    if m is not None:
                        n_meshref += 1
                        check(m, "Mesh", ("Mesh",), local_mesh, t)

                    # FOURTH pointer type, and the one that explains the half-masks. A renderer
                    # names its materials by the same (external, pathID) pair as everything else.
                    # All six of SMILE1's point at one pathID in a DEAD external, so the material
                    # was never packed and its source bundle is gone from the game -- which no
                    # pathID remap can repair. Walking only Material objects made a bundle with
                    # zero materials look like it had nothing to check. (Kappa)
                    for mp in (getattr(d, "m_Materials", None) or []):
                        check(mp, "RendererMaterial", ("Material",), local_material,
                              f"{t}.m_Materials")

            if n_meshref and not local_mesh:
                tally["bundles whose meshes are ALL external"] += 1

    print("=" * 66)
    print("COVERAGE -- check these before the findings. A collapsed denominator")
    print("means the checks examined nothing and the report is vacuous.")
    for k, v in sorted(seen.items()):
        print(f"{v:7}  {k}")
    print("-" * 66)
    print("FINDINGS")
    for k, v in sorted(tally.items()):
        print(f"{v:7}  {k}")
    print("=" * 66)
    if sibling_refs:
        print(f"\n{len(sibling_refs)} external(s) point at ANOTHER PACK BUNDLE, not at the game.")
        print("These are legal. Earlier versions of this script counted every one as a dead")
        print("external because the index held only the game -- a verdict no input could change.")
        print("NOTE: resolving here means the pathID exists. It does NOT mean the client loads it;")
        print("that needs a `bundles` dependency block in the config, and is not checkable here.")
        for r in sibling_refs[:12]:
            print(f"    {r}")
        if len(sibling_refs) > 12:
            print(f"    ... and {len(sibling_refs) - 12} more")
    if unset_maintex:
        print(f"\nunset _MainTex on {len(unset_maintex)} materials (benign on ARMYCAP/Unity defaults,")
        print("but a genuinely missing diffuse would be hiding here):")
        for u in unset_maintex[:14]:
            print(f"    {u}")
    for k, rows in sorted(broken.items()):
        print(f"\n--- {k}: {len(rows)}")
        for r in rows[:12]:
            print(f"    {r}")
        if len(rows) > 12:
            print(f"    ... and {len(rows) - 12} more")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
