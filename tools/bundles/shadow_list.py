"""Smoke test 6.1 asks "does vanilla still render correctly?" -- which is unanswerable
as written, because nobody knows which vanilla assets are at risk.

Every DRIP bundle self-declares a vanilla bundle path. This lists exactly which
vanilla assets our bundles claim, and flags the higher-risk case where SEVERAL DRIP
bundles claim the SAME one, so 6.1 becomes a targeted check instead of a vibe.

Usage: python shadow_list.py <repacked-store>
"""
import sys
import os
import collections

import UnityPy


def main(root):
    claims = collections.defaultdict(list)
    for dp, _d, fs in os.walk(root):
        for f in sorted(fs):
            if not f.endswith(".bundle"):
                continue
            p = os.path.join(dp, f)
            try:
                env = UnityPy.load(p)
            except Exception:
                continue
            for obj in env.objects:
                if obj.type.name == "AssetBundle":
                    try:
                        name = getattr(obj.read(), "m_Name", None)
                    except Exception:
                        name = None
                    if name:
                        claims[name].append(os.path.relpath(p, root))
                    break

    multi = {k: v for k, v in claims.items() if len(v) > 1}
    print(f"distinct vanilla paths claimed : {len(claims)}")
    print(f"claimed by more than one bundle: {len(multi)}\n")

    if multi:
        print("HIGHER RISK -- several DRIP bundles claim one vanilla identity.")
        print("If the client ever has two of these live at once, that is the 6.1 failure.\n")
        for k, v in sorted(multi.items(), key=lambda kv: -len(kv[1]))[:15]:
            print(f"  {k}")
            print(f"      claimed by {len(v)} bundles, e.g. {v[0]}")
        print()

    # Group the claimed paths by their vanilla category, to give the tester a short
    # list of what to actually look at in game.
    cats = collections.Counter()
    for k in claims:
        parts = k.split("/")
        cats["/".join(parts[:4]) if len(parts) >= 4 else k] += 1
    print("vanilla areas touched (check these for regression):")
    for c, n in cats.most_common():
        print(f"  {n:>4}  {c}")


if __name__ == "__main__":
    main(sys.argv[1])
