"""Recover the DRIP_N -> MongoId quest mapping.

68 item configs gate on DRIP_N ids that no longer exist. The renumbering left BOTH
key styles in en.json, so the mapping can be recovered by matching the text rather
than guessed. Matches on several fields so a shared name cannot produce a false pair.

Usage: python questmap.py <en.json> <quests .jsonc>
"""
import sys
import json
import re
import collections

loc = json.load(open(sys.argv[1], encoding="utf-8-sig"))
raw = open(sys.argv[2], encoding="utf-8-sig").read()
quests = json.loads(re.sub(r'^\s*//.*$', '', raw, flags=re.M))

FIELDS = ("name", "description", "successMessageText", "failMessageText")


def profile(prefix):
    return tuple(loc.get(f"{prefix} {f}", "") for f in FIELDS)


old = {}
new = {}
for key in loc:
    m = re.match(r'^(DRIP_\d+) (\w+)$', key)
    if m and m.group(2) in FIELDS:
        old.setdefault(m.group(1), True)
    m = re.match(r'^([0-9a-f]{24}) (\w+)$', key)
    if m and m.group(2) in FIELDS:
        new.setdefault(m.group(1), True)

old = {k: profile(k) for k in old}
new = {k: profile(k) for k in new}

print(f"DRIP_N quests with locale text : {len(old)}")
print(f"MongoId quests with locale text: {len(new)}")
print(f"quests defined in the file     : {len(quests)}\n")

by_profile = collections.defaultdict(list)
for mid, prof in new.items():
    by_profile[prof].append(mid)

mapping, ambiguous, unmatched = {}, {}, []
for oid, prof in sorted(old.items(), key=lambda kv: int(kv[0].split("_")[1])):
    hits = by_profile.get(prof, [])
    if len(hits) == 1:
        mapping[oid] = hits[0]
    elif len(hits) > 1:
        ambiguous[oid] = hits
    else:
        unmatched.append(oid)

print(f"{'OLD':<10}{'NEW':<26}{'QUEST NAME':<34}IN FILE")
print("-" * 82)
for oid, mid in mapping.items():
    name = loc.get(f"{mid} name", "?")
    print(f"{oid:<10}{mid:<26}{name[:33]:<34}{'yes' if mid in quests else 'NO'}")

if ambiguous:
    print(f"\nambiguous ({len(ambiguous)}):")
    for oid, hits in ambiguous.items():
        print(f"  {oid} -> {hits}")
if unmatched:
    print(f"\nno text match ({len(unmatched)}): {', '.join(unmatched)}")
    for oid in unmatched:
        print(f"    {oid} name = {loc.get(oid + ' name', '<absent>')!r}")

print(f"\nresolved {len(mapping)} of {len(old)}")
