"""Can bot-type suitability be DERIVED rather than annotated?

Every DRIP bundle records the vanilla bundle it was cloned from. Vanilla bot types
already carry appearance pools naming which garments they wear, and each of those
resolves to a prefab path. So if a DRIP garment's origin prefab is in a bot type's
vanilla pool, that bot type already wears that garment -- and the retexture inherits
the suitability by construction.

That is the same principle as copyOriginalOffers and updateFilters: a retexture
behaves like the thing it retextures.

Usage: python suitability.py <db-root> <art-library manifest.json>
"""
import sys
import json
import os
import collections

db, manifest_path = sys.argv[1], sys.argv[2]

cust = json.load(open(os.path.join(db, "templates", "customization.json"),
                     encoding="utf-8"))


def pool_prefabs(bot_type, slot):
    """The set of prefab paths a vanilla bot type wears in this slot."""
    p = os.path.join(db, "bots", "types", f"{bot_type}.json")
    if not os.path.isfile(p):
        return None
    bot = json.load(open(p, encoding="utf-8"))
    ids = (bot.get("appearance") or {}).get(slot) or {}
    out = set()
    for cid in ids:
        entry = cust.get(cid)
        if not entry:
            continue
        path = ((entry.get("_props") or {}).get("Prefab") or {}).get("path")
        if path:
            out.add(path.lower())
    return out


BOTS = ["assault","pmcusec","pmcbear","marksman","exusec","pmcbot","usec","bear","followerbully","followergluharassault","followergluharscout","followergluharsecurity","followerkojaniy"]
pools = {}
for b in BOTS:
    pools[b] = {"body": pool_prefabs(b, "body") or set(),
                "feet": pool_prefabs(b, "feet") or set()}
    print(f"{b:<16} body={len(pools[b]['body']):>3} prefabs   "
          f"feet={len(pools[b]['feet']):>3} prefabs")

m = json.load(open(manifest_path, encoding="utf-8"))
print()

# Classify each DRIP clothing bundle by which vanilla bot types already wear its origin.
hits = collections.defaultdict(list)
unmatched = []
for b in m["bundles"]:
    rel = b["bundle"].replace("\\", "/")
    origin = (b.get("vanillaOrigin") or "").lower()
    if not origin:
        continue
    if "/TOP/" not in b["bundle"] and "/BOTTOM/" not in b["bundle"]:
        continue
    slot = "body" if "/TOP/" in b["bundle"] else "feet"
    if rel.endswith("HANDS.bundle"):
        continue  # hands accompany a top; the top decides suitability
    matched = [bot for bot in BOTS if origin in pools[bot][slot]]
    if matched:
        for bot in matched:
            hits[bot].append(rel)
    else:
        unmatched.append((rel, origin))

print("DRIP garments whose vanilla origin is already in a bot type's pool:")
for bot in BOTS:
    print(f"  {bot:<16}{len(hits[bot]):>4}")

print(f"\ngarments matching NO vanilla pool: {len(unmatched)}")
for rel, origin in unmatched[:8]:
    print(f"  {rel}")
    print(f"      origin: {origin}")
