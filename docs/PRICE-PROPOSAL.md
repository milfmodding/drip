# Proposed prices for the ten Part 1 items left at 0

**For Sophia to accept, adjust or reject.** Nothing here is applied — the ten configs still say
`price: 0` and `drip check` still reports them as `DRIP-307`.

Context: Sophia confirmed these zeroes are leftovers — *"just for testing back in the day"* —
not deliberate free items.

---

## Proposal

| file | type | trader | lvl | **suggested** | basis |
|---|---|---|---|---|---|
| `URBANFIGHTER_CADPAT_PANTS` | bottom | georgia | 7 | **32,000** | exact — siblings at this level |
| `URBANFIGHTER_SIXCOLOURURBAN_PANTS` | bottom | moron | 7 | **32,000** | exact — siblings at this level |
| `URBANFIGHTER_UCPBRUSH_PANTS` | bottom | moron | 7 | **32,000** | exact — siblings at this level |
| `COMBATPARKA_NAVY_TOP` | top | georgia | 10 | **46,000** | family is flat at 46,000 |
| `FIGHTINGJACKET_FLORA_TOP` | top | moron | 10 | **42,000** | family is flat at 42,000 |
| `FIGHTINGJACKET_SKOL_TOP` | top | moron | 10 | **42,000** | family is flat at 42,000 |
| `OLDSCHOOL_SKOL_PANTS` | bottom | moron | 10 | **84,000** | family is flat at 84,000 |
| `OLDSCHOOL_TARNANZUG_BOTTOM` | bottom | georgia | 10 | **84,000** | family is flat at 84,000 |
| `GORKA4_SKOL_PANTS` | bottom | moron | 10 | **57,500** | ⚠️ interpolated — see below |
| `GORKA4_SKOL_TOP` | top | moron | 10 | **57,500** | ⚠️ interpolated — see below |

Eight of the ten are not estimates. Their families charge a single price for every variant, so
the proposal is simply *what its siblings already cost*.

---

## Method, and why the obvious approach was wrong

The first pass took the median price of each item's family. That gives **95,000** for the two
GORKA4 items, and it is wrong — 64% too high.

Most families are **flat**: one price for every variant regardless of level.

```
OLDSCHOOL        lvl 16 -> 84,000                          flat
URBANRESPONDER   lvl 6, 7, 8 -> 32,000                     flat
AGGRESSOR        lvl 8, 11 -> 46,000                       flat
SUMMERFIELD      lvl 12 -> 42,000                          flat
```

GORKA4 is not:

```
GORKA4           lvl  7 -> 45,000
                 lvl 13 -> 70,500
                 lvl 18 -> 95,000                          laddered by level
```

Both GORKA4 blanks sit at **level 10**, which has no priced sibling. 95,000 is what GORKA4
charges at level 18 — taking the family median would have priced a level-10 garment as if it
were the family's top tier.

Interpolating between the two bracketing rungs:

```
45,000 + (70,500 - 45,000) x (10 - 7) / (13 - 7)  =  57,750  ->  57,500 (rounded)
```

Rounded to the nearest 500, matching the corpus — every price in all 544 configs is a round
number.

**This is the one judgement call in the table.** The other nine follow from data. If the level
on those two items is itself wrong — see below — the right fix is to correct the level and take
the matching rung (45,000 at level 7, 70,500 at level 13) rather than to keep 57,500.

---

## Two observations worth a decision

**All ten are locked behind the same quest, `DRIP_12`.** Nothing else in Part 1 is. That is
consistent with them having been built as one batch from a shared template — which is exactly
how ten copies of the same blank price field end up in a release.

**Nine of the ten sit at profileLevel 10**, the three `URBANRESPONDER` items at 7. Level 10 is
otherwise unremarkable in Part 1, and in three of the four families involved it is a level no
other garment uses. If the template that produced these carried a placeholder level as well as
a placeholder price, the levels deserve the same scrutiny — I have not assumed either way, and
the table above takes each item's stated level at face value.

---

## Applying it

Ten single-line edits; each file already has a `price` field to change. After that:

```bash
python tools/drip.py check
```

`DRIP-307` should fall from 10 to 0. Anything else that appears is unrelated and pre-existing.

If a different pricing philosophy is preferred — free because they are quest rewards, or
uniform across the batch because they unlock together — say so and the table is easy to redo.
The method is only worth as much as the assumption behind it, which is that these ten were
meant to look like their neighbours.
