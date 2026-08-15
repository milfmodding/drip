# Parts, presets, and the question of who chooses them

**Sophia's question:** *"If we want to clone an item no one sells by default, can we make it so
you don't have to look up itemIDs for the soft armor pieces?"*

**Short answer: yes, and for the soft armour pieces there was never anything to choose.** The
field asks for information the game has already fully determined. That is a stronger answer than
"we can automate the lookup", and it changes what the schema should look like.

Everything below is measured against SPT 4.0.13's own database. Numbers marked *measured* were
counted from the files; nothing here is estimated.

---

## The finding the design turns on

Each slot on a vanilla item carries a filter — the list of what the game will accept in it.

| slots on the 60 vanilla armour carriers | how many legal items |
|---|---|
| **required** (soft armour, collar, groin, shoulders) — **275 of 275** | **exactly 1** |
| optional (plate slots) | 3, 4, 18, up to 20 |

*Measured: 275 required slots across 60 carriers, every one with a single-entry filter.*

So `includedParts` is really two fields wearing one name:

- **Soft armour.** Zero degrees of freedom. Asking an author for a 24-character ID here is
  asking them to transcribe a value the game already knows, where any answer but one is wrong.
- **Plates.** A genuine choice, with real consequences, and the reason this document exists.

That split is not a schema convenience. It is the line between *no choice exists* and *a choice
exists*, and the schema should fall on it rather than across it.

## What that means for the shape

Echo's suggestion was a keyword — `"includedParts": "vanilla"` — resolved at load time from the
vanilla default preset in `globals.ItemPresets`. That works, and the source is right: the
default preset is the one whose `_encyclopedia` points back at its own root, it does not depend
on any trader, and **it covers every required slot of all 59 carriers that have one** (measured;
one carrier has no preset at all).

But a keyword still puts a field on the page whose only correct value is the keyword. The
smaller version:

- **Required slots fill themselves.** Not author-facing at all. No field, no keyword, nothing on
  screen. There is one legal value and the game supplies it.
- **Plates get one plain-English field** — something a person can answer without looking anything
  up, because the answer is a yes or a no rather than an ID.

This is the same principle as the quest template: *a template's job is to reduce what is on
screen, not to fill the screen correctly.* A keyword fills the screen correctly.

**Two constraints on any version of this:**

1. **An explicit `includedParts` must win.** A keyword that silently overrode an author's own
   list would be worse than the bug it fixes.
2. **"No preset" must NOT be an error on its own.** This started life as "fail loudly if the
   base has no default preset" and that was wrong — 32 of DRIP's 59 distinct base items have no
   preset *and* no required slots, because most of them are hats, masks, bags and rigs. An
   unconditional error is 32 false positives and 0 real findings.

   The condition is the conjunction: **error only when required slots exist that the preset
   cannot fill.** Currently zero cases — all 59 vanilla carriers with a preset cover every
   required slot — so it is a **regression guard**, and its comment must say so or someone
   deletes it as dead code in six months. Written against *coverage* rather than *existence* so
   it still fires if a patch adds a slot to a carrier and the preset lags behind.

### Where the default would actually apply: nothing that exists today

Sophia's case for making `vanilla` the default rather than an opt-in is that a forgotten field
is *"wrong in a way that isn't visible to them"*, and that is right. But the population it acts
on is worth stating plainly, measured over all 276 configs:

| | configs |
|---|---|
| `copyOriginalOffers` on — children come from the trader, default irrelevant | 105 |
| own-priced with an explicit `includedParts` — explicit wins | 10 |
| own-priced, no required slots — nothing to fill | 25 |
| **own-priced, needs parts, has none — the default applies** | **0** |

**Its entire blast radius is the 13 worksheet items, once they are repriced.** So the argument
that "vanilla reproduces what traders already do" is reassuring rather than load-bearing — it
describes a population the default never reaches. For the 13 there is no existing behaviour to
preserve, because nobody sells them.

*(Measured separately: of the 20 DRIP bases with required slots that a trader offers, **19 have
at least one offer identical to the default preset and one — BNTI Zhuk — has none.** Six of the
twenty are sold by more than one trader, which is what made this easy to miscount: taking "the"
offer per item silently picks one, and the 6B43 has a bare offer and a complete offer. Count
offers, not items, and say which.)*

---

## The decision that is genuinely Colette's and Amber's

**Should a DRIP carrier bought from a trader come with ballistic plates in it?**

**Vanilla does not answer this per item — it answers per offer**, and for the 6B43 it ships
both ways from two different traders. So the question needs asking against the right
sub-population, and once you do, vanilla is unanimous:

| vanilla offers of DRIP's carrier bases | offers | match the default preset |
|---|---|---|
| **paid with money** (roubles, dollars, euros) | **11** | **11 — no exceptions** |
| paid by barter or GP coins | 15 | 13 |

*Both deviations are the non-cash ones:* Prapor sells the 6B43 bare for a barter (4 topographic
survey maps + 2 phase control relays) while Ref sells the same armour complete for 58 GP coins;
and Ref sells the Zhuk with soft armour only for 31 GP coins, omitting ~150k of plates the
preset carries.

**DRIP items are sold for money.** So for the only population DRIP actually lives in, *every
vanilla armour you can buy with cash comes with its plates fitted.* That is a fact rather than a
tendency, and it is worth saying plainly — it was obscured in both earlier counts by taking one
offer per item without stating which.

They are still choosing a policy rather than discovering a fact: DRIP may deviate deliberately.
But the fact underneath it is clean.

**And DRIP already inherits both behaviours.** Of the 32 DRIP carriers that copy a real trader
offer, 22 ship with plates and 10 without — not by anyone's decision, but because that is what
the trader they copy from does.

So neither answer is a departure. What differs is the money:

| base item | plates the preset adds (handbook) |
|---|---|
| LBT-6094A Slick | 105,800 |
| 5.11 TacTec | 107,602 |
| NFM THOR Integrated | 168,674 |
| Ars Arma A18 Skanda | 36,482 |

*This is the question to put in front of them, and it should be put as a question.* Both answers
are defensible and neither is a technical matter.

---

## The part nobody has connected yet — and it is the important one

**`docs/REPRICE-WORKSHEET.md` currently recommends a price for a different object than the one
the item will become.**

The worksheet tells Colette and Amber that the vanilla handbook price is the obvious default,
and lists Slick at 12,710, TacTec at 3,620, A18 at 3,036, THOR at 11,375. Those are the prices
of the **bare carrier shell**.

Vanilla does not price the shell. A trader's asking price covers the assembled item — measured
across 17 rouble-priced vanilla armour offers, asking price is **1.09 to 1.37×** the handbook
value of the carrier *plus everything in it* (median 1.11×).

| base item | worksheet says | with its inserts | with inserts + plates | vanilla-consistent asking |
|---|---|---|---|---|
| LBT-6094A Slick | 12,710 | 254,200 | 360,000 | ~399,600 |
| NFM THOR Integrated | 11,375 | 227,500 | 396,174 | ~439,754 |
| 5.11 TacTec | 3,620 | 72,398 | 180,000 | ~199,800 |
| Ars Arma A18 Skanda | 3,036 | 60,718 | 97,200 | ~107,892 |

The soft armour alone is worth **twenty times** the shell. This is the *"of what?"* question
again: 12,710 is a correct number about the wrong population.

**Why this matters more than it looks.** Right now the price and the parts are two separate
open items, and they interact badly in one specific direction:

- Today the thirteen have no seller, so nothing is buyable and nothing is wrong yet.
- Set a price with no parts, and you get an unwearable shell for 12,710 — **the bug Sophia
  spotted on the two helmets.** Loud, visible, caught within the hour.
- Fix the parts and keep the worksheet's price, and you get a fully-assembled 360,000-rouble
  carrier for 12,710. **Nothing looks wrong.** Nobody spots it, because there is nothing to
  spot.

Fixing the parts without revisiting the price converts a visible bug into an invisible one.
That is a worse outcome than either problem alone, and it is the reason these two decisions have
to be taken together rather than in sequence.

The worksheet does not need rewriting yet — the answer depends on the plates decision above. It
does need to stop recommending the shell price as the obvious default.

### The corpus is the argument, and it says the authors already know this

The obvious guard is a check comparing an own-priced item against what ships with it. On the
first pass it looked unbuildable: **20 of 35 own-priced items came out under a third of their
contents' value**, which is a flag firing on healthy data.

That was an error in the measurement, not in the corpus. **20 of the 171 priced items are in
dollars or euros** — USD is worth 120 roubles in game, EUR 133 — and the raw number was being
compared against a rouble handbook value. The same *"of what?"* mistake this document levels at
the worksheet, one field over.

Converted properly it inverts completely:

| | ratio of price to what ships with it |
|---|---|
| all 35 own-priced gear items | 0.51× – 6.23× |
| **the 10 with an explicit `includedParts`** | **0.83× – 1.99×** |
| under 0.33× | **0** |

**Nothing in the corpus is mispriced.** Colette and Amber already price assembled armour at
roughly what its contents are worth — AVS Tagilla 243,844 against 293,000, PlateFrame 260,953
against 267,608, Zhuk 2,450 USD (294,000) against 291,299.

Two things follow. The plates question has a natural answer *in their own established practice*,
which is better than any recommendation from here. And the guard is buildable after all: the 13
at worksheet defaults land at **0.03×**, an order of magnitude below anything in the corpus, so
it would catch exactly the invisible failure and nothing else. Not built yet — the threshold
depends on the plates answer — but no longer blocked on a false-positive problem, because there
was never one.

### Found while checking that: the price sheet had no currency column

In the one tool the content owners drive completely unaided. `Price now` was a bare number, and
`cmd_apply` writes the new number into `"price"` **without touching `"currency"`** — so a
rouble-shaped edit on a dollar item was a silent 120× error. The two most exposed rows are
armour priced at 1,360 and 2,450, which look far too cheap beside a rouble-priced set and are
not.

Fixed: a locked **Currency** column (`NEW_PRICE_COL` 7 → 8; verified the reader still lands on
`NEW PRICE`, and an apply with no edits reads clean and writes nothing).

**What was not wrong, recorded so nobody "fixes" it:** no set mixes currencies, so
`Others in this set` and the `Odd for the set` flag have always compared like with like. The
exposure was cross-set comparison and the unit being typed into the yellow column.

---

## A correction to the brief

The four items whose `includedParts` disagree with the vanilla preset were described as possibly
deliberate, and parked for Colette. **They are not a decision. They are a bug, and there is
exactly one right answer.**

All four are the same shape: `Soft_armor_back` holds the ID that belongs in `Soft_armor_front`.
Every other slot in those files matches vanilla exactly.

| | |
|---|---|
| `ZHUK6A_BLACK_ARMOR` | back slot holds the front insert (`RibcageUp`, `RibcageLow` colliders — not the spine) |
| `RIG_AVSMBAV_EMR` / `_ERDL` / `_RUSPLINTER` | back slot holds the chest plate collider (`Plate_Granit_SAPI_chest`) |

And the game will not fit them: **the `Soft_armor_back` filter on both base items accepts exactly
one item, and it is not the one the config names.** So the slot is not mis-covered — it is
**empty**. Those four items have no back armour at all.

It reads as deliberate because the two inserts *share a name*. Both are called `Aramid insert`;
they differ only by which part of the body they cover. That is also how it got written: a
duplicated line with the slot name changed and the ID left behind.

`drip check` now reports this as `DRIP-410`, with the one ID that fits.

**It is inherited from 3.x, not introduced by the port**, and it is **8 files, not 4** — the 3.x
tree has the same IDs in `AVSTAGILLA/BLACK`, `GREEKLIZARD` (Part 2), `HEADPATNIGHT` and
`REDDAWN` (Part 3). Only Part 1 is converted, so `drip check` sees four of them today.

**So the fix belongs in the converter, not in the `.jsonc` files.** `convert-legacy.py` copies
`childAssorts` straight through, so correcting the four configs directly would be reverted by
the next conversion run, and the revert would look like a successful conversion. Not applied
here: it is a content change to shipped items, it should be made once across all three parts,
and Colette and Amber should know it is happening.

---

## What this changed in the tooling, and what it costs

`drip check` now reports **17 errors, up from 13** — the 13 unsold items and these 4. Same as
with `DRIP-408`, that means `build-release.py --check-only` says *"Content has errors"*, and the
new four are a real content bug rather than a work list someone has already accepted.

Also fixed while here, because the new check surfaced it: **game item names could crash the
tools.** Ten of the game's 5,155 item names contain non-ASCII characters — Cyrillic lookalikes
in three keys BSG spells `Сity key`, the `TT` in the 7.62x25 ammo packs, and a curly apostrophe
in `Global Armor's Steel ballistic plate`. `sys.stdout` on a stock Windows console is cp1252, so
printing one raises `UnicodeEncodeError` and ends the run in a Python traceback. `DRIP-410`
prints lists of plate names, which made it reachable. Game text is now folded to ASCII in
`sptdb.py` where it enters, rather than at each print — the rule is about the source of the
text, not about any one message.

---

## Still open, and with whom

| | |
|---|---|
| **Plates in the offer, or not** | Colette and Amber. Not a symmetric pair of options — vanilla ships these with plates in, so the question is *"do you want that, or the carrier bare?"*, with the 12k–169k range attached. 22 of the 27 bases with a preset are affected; only 5 are cases where the two answers mean the same thing. |
| **The worksheet's recommended price** | Follows from the above. Blocked on it, and currently wrong by ~20× either way. |
| **Whether required slots fill themselves or take a keyword** | Kappa and me, once the plates answer exists. For required slots "no field" and "default to vanilla" are the same thing; the disagreement was only ever about plates. |
| **The 8-file back-armour correction** | Mine to make in the converter; wants a nod first, since it changes shipped items. |
