# Pricing worksheet — 13 items that currently have no seller

**For Colette and Amber.** This is a real, finished-shaped task: thirteen items in Part 1 are
currently sold by nobody, and the fix is a price. No code, no tooling, one number per file.

You do not need to read the rest of this document to do the work — the table is the work. The
explanation is here so you can push back if a number looks wrong to you, because you know what
these things are worth in a raid and we do not.

---

## What went wrong

Every DRIP item says either *"sell this wherever the original is sold"* (`copyOriginalOffers`)
or *"sell it at my own price"*. These thirteen say the first — but **nothing in the game sells
their original.** So nothing sells the retexture either.

They were never really "sold where the original is sold". The only stockist was **Fence**, whose
inventory is generated from the entire item list, so "Fence sells the original" was true of
almost everything and meant almost nothing. That was masked until a load-order fix moved DRIP
earlier in startup than Fence's inventory gets built.

**So this is a pre-existing content bug that a code change made visible.** It is not something
either of you did wrong, and it is not something the tooling can decide — a price is a judgement
about how rare something should feel.

---

## Which files — ask the tool, not this page

```
drip check
```

It lists every affected file by name, with what to type. **This page deliberately does not repeat
that list**, so the two can never drift apart — the tool owns *which files*, this page owns *what
number*.

## What number — five decisions, not thirteen

All thirteen are patterns of five base items, and a DRIP retexture has **identical stats** to the
thing it retextures. So the real decision is five numbers, and `base price` — what the unmodified
item costs in the vanilla handbook — is the obvious default.

| Base item | Patterns affected | Base price | Your call |
|---|---|---|---|
| LBT-6094A Slick Plate Carrier | 5 | 12,710 | |
| 5.11 Tactical TacTec plate carrier | 4 | 3,620 | |
| Ars Arma A18 Skanda plate carrier | 2 | 3,036 | |
| NFM THOR Integrated Carrier | 1 | 11,375 | |
| Tac-Kek Heavy Trooper mask | 1 | 61,000 | |

**Same base item ⇒ same price is the sane default**, and matching the vanilla price means a DRIP
Slick costs what a Slick costs, which is defensible without anyone having to think about it.

Deviate where you have a reason: a pattern that should feel like a rare find can cost more, and
one you want people to actually wear can cost less. That judgement is yours — it is about how the
mod should feel, which is not something the tooling can know.

## What to change

In each file, replace:

```jsonc
"copyOriginalOffers": true,
```

with:

```jsonc
"copyOriginalOffers": false,
"price": 12710,
"loyaltyLevel": 1,
```

`traderId` is already set in every file, so the item knows who should sell it. `loyaltyLevel` is
how far you must have levelled that trader — 1 means available immediately.

---

## Seven items you will see reported the same way — do not touch these

The server also reports **no trader sells** for seven more. **These are correct and must be left
alone:**

```
TRIZIP_6COLOURWOODLAND_BAG        TRIZIP_OD_BAG
RAID_BLACK_BAG                    BLACKJACK_BLACK_BAG
AIRFRAME_RANGERGREEN_HELM         FASTMT_USEC_MESH
GEN4_MOBILITY_DIGITALTIGERSTRIPE
```

Their originals **are** sold — behind a quest. DRIP is deliberately refusing to sell a retexture
of something the player has not unlocked yet, which is a bug we just fixed: the 3.x mod sold
retextures of quest-locked gear as freely available for years because a lookup was written
against the wrong key.

**Giving these a price would put that bug back**, and it would look like a fix. If a future
version of the tooling lists all twenty together, that is a tooling bug — tell us rather than
pricing them.

The right eventual answer for these seven is for DRIP to copy the quest requirement along with
the offer, so they appear when the original does. That is loader work, not a config change.

---

## Why these thirteen and not others

Both groups were found by asking the shipped database, per item, whether **any** trader sells
the original as a purchasable offer, and if so whether that offer is quest-locked:

```
13 items   no root offer at any trader          -> Fence-only, vacuous  -> needs a price
 7 items   exactly one root offer, quest-locked -> deliberate refusal   -> leave alone
```

Getting that split right took several wrong attempts, including one query that read the wrong
file and confidently reported zero quest-locked offers when there are 236. **If a number here
looks wrong to you, say so** — the checks behind them have been wrong more than once, and you
know the content better than any of them do.

---

## Related

- Prices generally: much of the corpus carries placeholder values (69420, 42069) that were
  copy-pasted rather than chosen. That is a separate, larger pass — `Review Prices.cmd`.
- `AUTHORING.md` — how to add and edit items.
- `CONFIG-SCHEMA-v2.md` — every field a config can have.
