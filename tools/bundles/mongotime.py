"""Verify the DRIP_N -> MongoId mapping against creation timestamps.

A MongoId's first four bytes are a Unix timestamp. If the recovered mapping is
correct AND the original numbering was sequential-by-creation, then DRIP_0..DRIP_18
should map to strictly ascending creation times. That signal is independent of the
text matching used to recover the map, so agreement is real corroboration rather
than self-consistency.
"""
import datetime

MAP = [
    ("DRIP_0",  "669a1606666bd606fa3f897a", "A Wild Night"),
    ("DRIP_1",  "669cdb5039f39e1bd6019b56", "The Morning After"),
    ("DRIP_2",  "669f74d7e7211bf21d8af254", "Material Handler"),
    ("DRIP_3",  "669f759a1c5ee26e33c5afb2", "Glock Wick: Part 1"),
    ("DRIP_4",  "669f76cb1fec55b3413b554c", "Glock Wick: Part 2"),
    ("DRIP_5",  "669f775edfe50ca330aaa91d", "Glock Wick: Part 3"),
    ("DRIP_6",  "669f77bd952e94e100e88847", "Full Life Consequences"),
    ("DRIP_7",  "669f78036d104f2127da9a3b", "Shock and Awe"),
    ("DRIP_8",  "669f78477ebc9a09e44cbd6d", "Lack of Lubrication"),
    ("DRIP_9",  "669f78890cf4da93267775f6", "Junker"),
    ("DRIP_10", "669f78e3ea69f9bde9904a1b", "Party City"),
    ("DRIP_11", "669f795b4657ccef2265f1be", "System Destroyer: Part 1"),
    ("DRIP_12", "669f79c7f8b1f185365997e3", "System Destroyer: Part 2"),
    ("DRIP_13", "669f7a04a6bd56d17bae1089", "Head, Eyes"),
    ("DRIP_14", "669f7a46a33b9e7cbda18b33", "Mosin Man"),
    ("DRIP_15", "669f7a86fd2585b9526ea0ed", "Power Supply and Demand"),
    ("DRIP_16", "669f7ab67cf81b4cfa87028f", "First Impressions"),
    ("DRIP_17", "669f7af0dec2d6cd48b2bf1d", "The Best Defense"),
    ("DRIP_18", "669f7b28d1dbbbdb0475e7be", "Friendly Feud"),
]

rows = []
for old, mid, name in MAP:
    ts = int(mid[:8], 16)
    rows.append((old, mid, datetime.datetime.utcfromtimestamp(ts), name))

print(f"{'OLD':<9}{'CREATED (UTC)':<22}{'GAP':>9}  QUEST")
print("-" * 74)
prev = None
inversions = 0
for old, mid, dt, name in rows:
    gap = "" if prev is None else f"+{int((dt - prev).total_seconds())}s"
    if prev is not None and dt < prev:
        gap += "  <-- INVERSION"
        inversions += 1
    print(f"{old:<9}{dt.strftime('%Y-%m-%d %H:%M:%S'):<22}{gap:>9}  {name}")
    prev = dt

print(f"\ninversions: {inversions}  ->  {'strictly monotonic' if inversions == 0 else 'NOT monotonic'}")

# the tight cluster
last = [r for r in rows if r[2].date() == rows[-1][2].date()]
span = (last[-1][2] - last[0][2]).total_seconds()
print(f"same-day cluster: {len(last)} quests created within {int(span // 60)}m{int(span % 60)}s")
print(f"distinct calendar days: {len({r[2].date() for r in rows})}")
