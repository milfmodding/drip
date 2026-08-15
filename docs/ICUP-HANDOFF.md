# Notes for ICUP, from DRIP's side

The clothing tag system is moving to ICUP. DRIP carries `tags` through untouched and doesn't
read them. This is what we learned about that data while porting, recorded now because it will
otherwise be lost between projects.

Nothing here is a request. It's context for whoever picks the work up.

---

## The single most important thing

**Anyone reviewing these tag weights is setting values for the first time, not correcting
them.**

That sounds like a detail and isn't. Frame it as a correction pass and a reviewer goes looking
for *mistakes* — comparing entries, hunting for the odd one out, trying to infer what was
intended. There is nothing to infer. Every number is the same number, and no number was ever
read (see below). They are making judgements from scratch, and should be told so, or they'll
spend an afternoon looking for a signal that was never in the data.

---

## What the data actually is

Measured from disk across all three parts:

| | |
|---|---|
| **Part 1 — the release target** | **135 files, 135 garments, no duplicates** |
| files carrying `tags`, all parts | 269 — Part 1: 135, Part 2: 71, Part 3: 63 |
| distinct garments, all parts | **267** |
| distinct tag names | 93 |
| total tag entries | 673 |
| distinct *values* used | **one — every entry is `1`** |

**Start with 135.** Part 1 is clean — every file is its own garment, nothing duplicated,
nothing ambiguous. The all-parts number needs two content bugs resolved before it settles.

### How to count these, and how not to

A garment is *a config plus the bundles beside it*. Two files describing the same config over
the same bundles are one garment however they happen to be named. Counting that way gives 267,
from 269 files and two duplicate groups:

| | |
|---|---|
| `ZASLON_SOC_PANTS` | the same garment in Part 1 and Part 3, byte-identical. The loader's collision guard loads it once. |
| `TSHIRT_DESERTTAN` + `TSHIRT_KHAKI` | **both in the same Part 3 folder**, so literally the same two bundles, and identical configs — both say "T-Shirt - Khaki" at 42,069. Two files, one garment, and one of them shouldn't exist. |

Two other ways of counting are available and both are wrong:

- **By filename** gives 266. `INFILTRATOR_NIGHTGREY_PANTS` (a top and a bottom sharing a name)
  and `TSHIRT_KHAKI` (in two different folders at two different prices) are four genuinely
  distinct garments that merely collide by name. Counting stems merges them and undercounts.
- **By filename, deduplicating only identical stems** gives 268 — it catches `ZASLON` but not
  the `TSHIRT_DESERTTAN` pair, because those two have different names. This is the number this
  document carried until it was rechecked by a different method.

The lesson worth carrying more than the number: repeating a count the same way reproduces its
blind spot. Changing the *equivalence* — filename, then config, then config-plus-bundles — is
what surfaced the disagreement.

### A content bug this turned up

`Part 3/items/CLOTHING/TOP/TSHIRT/DESERTTAN/` holds **two configs for one pair of bundles**:
`TSHIRT_DESERTTAN.json5` and `TSHIRT_KHAKI.json5`, identical, both naming the item
"T-Shirt - Khaki". It reads like someone copied the khaki config in to make a desert tan
variant, renamed the copy, and never edited its contents or removed the original. Meanwhile the
real khaki shirt lives in a sibling `KHAKI/` folder at a different price.

Part 3, so not release-gating, and a decision for the content owners rather than for ICUP — but
it needs resolving before the all-parts garment count means anything.

The shape is `"tags": { "woodland": 1, "civilian": 1 }`. Tag sizes are very uneven: `woodland`
covers 127 garments, `civilian` 83, `operator` 53 — while 12 tags have exactly one member.

---

## Why the uniform `1` is not a decision

Sophia confirmed weights were *intended* to work; the uniform `1` is copy-paste artifact from a
shared template. It is the third instance of that same defect we found, after `price: 0` on ten
items and a cluster of items all sitting at `profileLevel` 10.

**3.x hid it.** `ICUP.ts addWeights()` computed a tag's selection weight by *counting the items
in it*, not by reading the authored values:

```ts
bottomTagWeight = Object.keys(this.clothingTags[tag]["bottoms"]).length;
topTagWeight    = Object.keys(this.clothingTags[tag]["tops"]).length;
this.clothingTagWeights[tag] = bottomTagWeight + topTagWeight;
```

So `woodland` was ~127× likelier to be chosen than a single-item tag, purely by membership, and
no authored number was read at any point. Two consequences:

- The uniform `1` was invisible for the life of the mod. Nothing could have surfaced it.
- **Porting that behaviour forward would perpetuate the mask.** If weights are read properly but
  selection still counts members, authored values remain decorative and the next person to look
  will find the same uniform data and reach the same wrong conclusion.

A tag set where every weight is identical is worth flagging the way `DRIP-307` flags `price: 0`
— it almost certainly means nobody has set them yet.

---

## The review tooling is reusable

`tools/price_review.py` plus `tools/xlsx_lite.py` is a spreadsheet round-trip built for exactly
this audience: export to a formatted `.xlsx`, they edit one column in Excel, re-import shows a
full before/after and asks before writing. No terminal, no JSON, no install step —
`xlsx_lite` is a hand-rolled reader/writer on the standard library because the content owners
have no Python toolchain and shouldn't need one.

Generic and worth keeping:

- the export/edit/diff/confirm loop, and the refusal to write anything unconfirmed
- writing results to a file the generator also reads, so a re-run can't silently revert them
  (`price-overrides.json` — see *"the converter is authoritative for what it writes"* in
  `STATUS.md`)
- `xlsx_lite` itself

Needs replacing: the columns, and the flagging logic.

**One lesson from the flagging, learned the hard way.** I built a fourth flag — *a level no
sibling uses* — and deleted it after it fired on 34 of 171 items, because in a set that prices
by level every rung is by definition the only one at its level. It was flagging healthy data as
suspicious.

A flag that fires on healthy data trains people to ignore the column, and then the real one goes
past unnoticed. For an audience who can't tell which flags to trust, a noisy flag is worse than
no flag. For tags specifically that means: *"every weight in this set is identical"* is a good
flag; *"this tag has few members"* is not.

---

## Where the data lives

Untouched, in each item config:

```
bundles/ContentPacks/<Pack>/CustomClothing/{TOPS,BOTTOMS}/**/*.jsonc
```

DRIP's loader captures unknown fields rather than dropping them, and the schema deliberately
does not model `tags` (`CONFIG-SCHEMA-v2.md` §4.7), so the field round-trips byte-for-byte. The
converter preserves it too — verified across all 135 Part 1 configs that carry it.
