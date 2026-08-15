"""Extract DRIP's artwork out of obsolete Unity bundles into a content-addressed
PNG pool.

Design note: an earlier version tried to decide per texture whether it differed
from vanilla, using a mean-delta threshold. That is fragile -- re-encoded vanilla
measures ~1.5 and genuinely retextured art ~5.6, which is too close to separate
safely, and guessing wrong loses irreplaceable art.

So instead: extract EVERYTHING, and deduplicate by exact hash of the decoded
pixels. Identical images are stored once. No threshold, nothing lost, and the
dedup ratio measures the real redundancy exactly rather than estimating it.

The vanilla comparison is still recorded per texture, as metadata for the rebuild
to use -- it just no longer decides what gets kept.

Usage:
  python extract_art2.py <pack-dir> <game-StreamingAssets-Windows> <out-dir> [--limit=N]
"""
import sys
import os
import json
import time
import hashlib

import UnityPy


def human(n):
    n = float(n)
    for u in ("B", "KB", "MB", "GB"):
        if abs(n) < 1024.0:
            return f"{n:.1f}{u}"
        n /= 1024.0
    return f"{n:.1f}TB"


def role_of(name):
    n = name.lower()
    if n.endswith(("_n", "_nrm", "_normal")):
        return "normal"
    if n.endswith(("_g", "_gloss", "_spec")):
        return "gloss"
    if n.endswith(("_d", "_diff", "_albedo")):
        return "diffuse"
    return "other"


def read_bundle(path):
    env = UnityPy.load(path)
    origin = None
    tex = {}
    for obj in env.objects:
        if obj.type.name == "AssetBundle":
            try:
                origin = getattr(obj.read(), "m_Name", None)
            except Exception:
                pass
        elif obj.type.name == "Texture2D":
            try:
                d = obj.read()
                name = getattr(d, "m_Name", None) or "?"
                sd = getattr(d, "m_StreamData", None)
                stored = int(getattr(sd, "size", 0) or 0) if sd else 0
                if not stored:
                    try:
                        stored = len(d.image_data)
                    except Exception:
                        stored = 0
                tex[name] = (d.image, {
                    "width": int(getattr(d, "m_Width", 0) or 0),
                    "height": int(getattr(d, "m_Height", 0) or 0),
                    "mipCount": int(getattr(d, "m_MipCount", 0) or 0),
                    "storedBytes": stored,
                })
            except Exception:
                continue
    return origin, tex


def mean_delta(a, b):
    if a is None or b is None or a.size != b.size:
        return None
    ab, bb = a.convert("RGBA").tobytes(), b.convert("RGBA").tobytes()
    n = min(len(ab), len(bb))
    if not n:
        return None
    step = max(1, n // 200_000)
    tot = cnt = 0
    for i in range(0, n, step):
        tot += abs(ab[i] - bb[i])
        cnt += 1
    return round(tot / cnt, 3)


def main(pack, game, out, limit=None):
    pool = os.path.join(out, "textures")
    os.makedirs(pool, exist_ok=True)

    seen = {}           # pixel-hash -> {png, bytes, refs}
    entries = []
    vcache = {}
    stats = {"bundles": 0, "textures": 0, "errors": 0, "no_origin": 0,
             "pool_bytes": 0, "stored_bytes_total": 0}
    t0 = time.time()

    targets = []
    for dirpath, _d, files in os.walk(pack):
        for f in sorted(files):
            if f.endswith(".bundle"):
                targets.append(os.path.join(dirpath, f))
    if limit:
        targets = targets[:int(limit)]

    for i, p in enumerate(targets, 1):
        rel = os.path.relpath(p, pack).replace("\\", "/")
        try:
            origin, mine = read_bundle(p)
        except Exception as e:
            stats["errors"] += 1
            print(f"[{i}/{len(targets)}] ERROR {rel}: {e}", flush=True)
            continue
        stats["bundles"] += 1

        van = {}
        if origin:
            vp = os.path.join(game, origin.replace("/", os.sep))
            if os.path.isfile(vp):
                if vp not in vcache:
                    try:
                        vcache[vp] = read_bundle(vp)[1]
                    except Exception:
                        vcache[vp] = {}
                    if len(vcache) > 16:
                        vcache.pop(next(iter(vcache)))
                van = vcache[vp]
        else:
            stats["no_origin"] += 1

        rec = {"bundle": rel, "vanillaOrigin": origin, "textures": []}
        for name, (img, meta) in sorted(mine.items()):
            stats["textures"] += 1
            stats["stored_bytes_total"] += meta["storedBytes"]
            raw = img.convert("RGBA").tobytes()
            h = hashlib.sha1(raw).hexdigest()

            if h not in seen:
                sub = os.path.join(pool, h[:2])
                os.makedirs(sub, exist_ok=True)
                png = os.path.join(sub, f"{h}.png")
                try:
                    img.save(png, optimize=True)
                    sz = os.path.getsize(png)
                except Exception as e:
                    png, sz = None, 0
                    print(f"    save failed {name}: {e}", flush=True)
                seen[h] = {"png": os.path.relpath(png, out).replace("\\", "/")
                           if png else None,
                           "bytes": sz, "refs": 0,
                           "firstSeenAs": name}
                stats["pool_bytes"] += sz
            seen[h]["refs"] += 1

            vimg = van.get(name, (None, None))[0]
            rec["textures"].append({
                "name": name,
                "role": role_of(name),
                "hash": h,
                "png": seen[h]["png"],
                "width": meta["width"], "height": meta["height"],
                "mipCount": meta["mipCount"],
                "storedBytes": meta["storedBytes"],
                "meanDeltaVsVanilla": mean_delta(img, vimg),
            })
        entries.append(rec)

        if i % 25 == 0 or i == len(targets):
            print(f"[{i}/{len(targets)}] {time.time()-t0:6.0f}s  "
                  f"textures={stats['textures']} distinct={len(seen)} "
                  f"pool={human(stats['pool_bytes'])}", flush=True)

    manifest = {
        "stats": stats,
        "distinctImages": len(seen),
        "pool": {h: v for h, v in seen.items()},
        "bundles": entries,
    }
    with open(os.path.join(out, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1)

    print()
    print(f"bundles           : {stats['bundles']}   ({stats['errors']} errors, "
          f"{stats['no_origin']} without vanilla origin)")
    print(f"texture instances : {stats['textures']}")
    print(f"distinct images   : {len(seen)}")
    if stats["textures"]:
        dedup = 100.0 * (1 - len(seen) / stats["textures"])
        print(f"=> {dedup:.1f}% of texture instances are duplicates of another instance")
    print(f"in-bundle payload : {human(stats['stored_bytes_total'])}")
    print(f"PNG pool on disk  : {human(stats['pool_bytes'])}")
    print(f"manifest          : {os.path.join(out, 'manifest.json')}")


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    lim = None
    for x in sys.argv[1:]:
        if x.startswith("--limit="):
            lim = x.split("=", 1)[1]
    main(a[0], a[1], a[2], lim)
