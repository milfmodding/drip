# Client smoke test

Everything verified so far is server-side: *the database is built correctly*. That is not the
same as *the game behaves correctly*. This checklist covers the gap — the failures that a
clean server log cannot detect.

Run it the moment bundles render. It is deliberately short; the point is to touch each
mechanism once, not to test 275 items.

> **Start with 6.7, not 1.1.** Kappa's suggestion and it's right: it is the newest risk, the
> one neither of us predicted, and the only row that needs nothing to *look* correct — just
> two garments visible at once. Everything else can be judged afterwards; 6.7 tells you
> whether there is a structural problem before you spend an hour forming opinions about
> textures. Then 1.1 onwards.

**Why it exists:** every mechanism below is a place where the server can be right and the
client still wrong — because the client resolves ids the server never dereferences, renders
assets the server only registers by path, and enforces requirements the server merely records.

Each row names what to blame first, so a failure points somewhere instead of starting a hunt.

**Rows marked 🤖 are now covered by the server's self-check** (`DRIPVerificationService`), which
runs on every load and fails loudly naming the file. Those rows are still listed, because in
every case the automated check covers *part* of what a human would confirm — the marker says
what is machine-checked and what is left to your eyes. Everything unmarked needs a person.

---

## 1. Clothing — the customization path

| # | Check | Blame first |
|---|---|---|
| 1.1 | Aiden (Tupitsa) and Georgia both appear as traders, with portraits | trader registration, `imageRouter` |
| 1.2 | Both show a **Clothing** tab | `Base.CustomizationSeller` |
| 1.3 | **T-Shirt - Meowlette Special** is listed at Georgia, with its **name and description in English** | locale transformers — a raw id here means locales never applied. *Gear names are self-checked; clothing suite names are not, so this row still matters.* |
| 1.4 | Its price and level requirement match its config | `Suit.Requirements` |
| **1.4b** | **A quest-gated garment behaves correctly: hidden before its quest, available after.** Verifies a fix that is hours old — see below | `Suit.Requirements.QuestRequirements`, `QUEST_ID_MAP` |
| 1.5 🤖 | Buy it. The purchase completes | `Suit._id` vs `suiteId` — the two-ids-one-job bug lived exactly here. *Self-check asserts the two ids differ; that the purchase actually completes is still yours.* |
| 1.6 | Equip it. It appears on the player in third person | `TOP.bundle`, suite `Body` wiring |
| 1.7 | **First person: sleeves and hands render, watch included** | `HANDS.bundle`, suite `Hands` wiring |
| 1.8 | Textures are the DRIP retexture, not the vanilla garment | if vanilla appears, the model bundle silently fell back |
| 1.9 | No magenta anywhere on it | shader rebind — the whole bundle workstream |

Do 1.6–1.8 for a **bottom** as well (Barvikha Commando). Tops and bottoms take different
code paths and different prototype ids.

### §1.3 used to name the winter jacket. That was a trap — do not put it back.

`WINTERJACKET_SOC_TOP` is **quest-gated** (behind *Mosin Man*) as well as level 12. With the
1.4b fix working, it is *correctly absent* from Georgia's list until that quest is done — so
using it as the "are locales applied?" fixture makes a **passing** build look like a locale
failure, and sends you into the transformers for an hour.

The fixture for a row like 1.3 must be **ungated**, or the row cannot fail for the reason it
claims to test. `TSHIRT_COLETTE_TOP` is ungated. This is the same class of mistake as reading a
correctly-absent garment as a failure in 1.4b, which is called out below — I made it twice, once
in the row and once in its example.

### Concrete fixtures — exact names, so no hunting mid-test

Every one of these was read out of the shipped configs, not remembered. Level requirements are
irrelevant on the test profile (see below), prices are not.

| Use | Config stem | In game | Trader | Price | Level | Gated? |
|---|---|---|---|---|---|---|
| 1.3 / 1.4 / 1.6–1.9 top | `TSHIRT_COLETTE_TOP` | T-Shirt - Meowlette Special | Georgia | 69,420 | 10 | no |
| 1.6–1.8 bottom | `COMMANDO_BARVIKHAPROTO_BOTTOM` | Commando - Barvikha Prototype | Moron | 43,000 | 13 | no |
| **1.4b — expect ABSENT** | `WINTERJACKET_SOC_TOP` | Winter Jacket - AOR2 | — | — | 12 | **yes — *Mosin Man*** |
| 6.7 — what *you* wear | `TSHIRT_AGENDA_TOP` | T-Shirt - Gay Agenda | Georgia | 42,069 | 1 | no |
| **6.7 — what *bots* wear** | `TSHIRT_HEADPAT_WINTER_TOP` | T-Shirt - HeadPAT Winter | Georgia | 27,500 | 5 | no |

The 6.7 pair is the point: **all ten `TSHIRT_*` variants declare themselves to be
`tshirt_bear_black.bundle`.** Wearing one while every bot wears another puts two bundles
claiming one identity on screen simultaneously, which is the whole test.

**Why this specific pair, and not two arbitrary T-shirts.** I first picked Meowlette and
Immoral. Both are **black shirts with a chest graphic** — so telling them apart means reading a
print on a moving bot in Tarkov lighting, and "I could not tell" would have been recorded as
"looked fine". I pulled all ten diffuse maps out of the art library and looked at them:

- **HeadPAT Winter is an all-over light manga print** — the only one that changes the shirt's
  overall *value* rather than adding a motif. Recognisable at any distance, in any light.
- **Gay Agenda is black with a saturated rainbow motif** — the most colour-distinct of the rest.
- Vanilla is plain black with `BEAR` on the back. Tula Black and Head-Eyes are nearly
  indistinguishable from vanilla at a glance; **do not use those as fixtures for anything.**

A reference sheet of all ten plus vanilla is worth regenerating if this is ever rerun —
`tools/bundles/` has the extraction, and the tiles come straight out of
`DRIP-art-library/manifest.json`.

### 6.7's instrument is your eyes, not the log — and that is the whole design

The server log tells you what DRIP **requested**. It cannot tell you what the client
**realised**, because the server registers bundles by path and never opens them. In this
specific test those two things are exactly what might disagree — that *is* the bug.

So the pin's log line is **provenance, not evidence**: it makes a raid identifiable as pinned
afterwards. It is not a check that the garment rendered. Do not close this row on a clean log.

Credit where due — Framesaver's Alpha named this shape before I saw it: *an instrument that
returns its own success value*. A pin that logs its own request will report success in precisely
the case it is meant to detect, with a clean exit code. Their project has been bitten by it
twice, once printing a pass over zero rows for three days.

The pin is strong on the server side, which is worth knowing so you trust the right half of it:
`ApplyBotAppearance` does `Body.Clear()` and then sets the single pinned id to weight 1, so the
pinned garment is not merely favoured, it is **the only entry in the pool**. Any bot wearing
anything else is a client-side substitution, and that is the finding.

**Record which shirt you see, not whether it looked right:**

| What the bots wear | Meaning |
|---|---|
| light all-over manga print (HeadPAT) | **correct** — both bundles resolved independently, no double-claim problem |
| the rainbow motif *you* are wearing | **duplicate identity confirmed** — the player's bundle won the shared path |
| plain black with `BEAR` on the back | vanilla fallback — DRIP's bundle did not load at all; different bug |
| magenta | shader binding — check `HATS/ARMYCAP` first, they are the four that carry their own |
| some *third* DRIP shirt | duplicate identity, and the winner is neither participant — worst case, most informative |

### The test profile makes 1.4b and 3.1 observable — check before replacing it

`F:/SPT/Base` has one profile: **BORK**, USEC, **level 69** — and all **563** of its quest
entries are status `1` (*AvailableForStart*). **Nothing is completed.**

That combination is what this checklist needs and is hard to recreate deliberately: level 69
clears every `profileLevel` requirement so no ungated garment is hidden for a boring reason,
while a virgin quest log means every quest gate is genuinely closed — so 1.4b's "absent before
the quest" arm and 3.1's "vanilla item behind an unfinished quest" arm are both directly
observable. **A fresh profile would fail half these rows on level alone; a played profile would
have completed the gates.** If this profile is ever replaced, re-check both properties.

Side is not a confound: `Side` is widened to `["Usec", "Bear", "Savage"]` on every DRIP suite,
so a USEC character sees BEAR-origin garments — and `TSHIRT_COLETTE_TOP` is BEAR-origin, so
this is load-bearing for the fixtures above, not a detail.

### 1.4b — verifying a fix that is only hours old

**This section previously described a release blocker. It is fixed; the check is now a
verification.** Left in with its history because the history is the reason to run it.

**What was wrong.** 68 of Part 1's 276 items were gated behind quests that did not exist. The
configs named `DRIP_1`, `DRIP_12`, `DRIP_14` and twelve more; every real quest is keyed by a
24-character MongoId. Nothing resolved. **3.x carries the identical mismatch**, so it shipped
that way for years — the cause being that 3.x permitted arbitrary alphanumeric ids while 4.x
requires MongoId format, so quests were renumbered and the item references were not.

**Why it was fixable.** The renumbering left *both* key styles in `en.json`, so the mapping was
recoverable by matching quest text — 19 of 19, corroborated by sequential position. It now lives
in `QUEST_ID_MAP` in the converter. Verified downstream: 68 configs, 15 distinct gates, **15
resolve, 0 dangle.**

**So the outcome to expect is the third one** neither Echo nor Kappa listed while it was broken:
the gating now works. Expect a quest-gated garment to be **absent before its quest is done and
available after** — and do not read a correctly-absent garment as a failure.

| What you see | Meaning |
|---|---|
| absent before the quest, appears after | **correct** — the fix works |
| listed and buyable with the quest incomplete | gating is being ignored; `QUEST_ID_MAP` or the client |
| absent even after completing the quest | over-gated; check the mapped id matches the completed quest |

**Do not grind a quest to see the second arm.** *Mosin Man* is a real quest and completing it
costs an evening. Use a differential instead — two server starts, no raids:

| Run | `noClothingRequirements` | Winter Jacket - AOR2 at Georgia | Meaning |
|---|---|---|---|
| A | `false` (default) | absent | gating is applied |
| B | `true` | present and buyable | the item exists and is otherwise sound |

A-absent + B-present isolates the failure to *nothing* — the item is fine and the gate closes.
A-present is gating ignored; B-absent is the item itself broken, and then the gate was never the
story.

What this **does not** cover, stated so nobody thinks it does: a gate naming a *real but wrong*
quest. No amount of playing catches that either — it is a mapping question, and it is already
double-corroborated (19/19 recovered by locale-text match, then independently confirmed by
MongoId creation-timestamp ordering) with assertion 9 guarding it at load. Remember to set
`noClothingRequirements` back to `false`.

Worth knowing the fix is **hours old and has never been seen in a client.** It is also the one
place in the release where a years-old defect was repaired rather than merely ported, so it has
had the least real-world exposure of anything here.

Assertion 9 guards it server-side — every gate must name an installed quest — so a regression
in the map fails at load rather than in a raid.

## 2. Gear — the item path

| # | Check | Blame first |
|---|---|---|
| 2.1 🤖 | A copied-assort item (e.g. a retextured 6B2) appears at **the same trader** that sells the original | `copyOriginalOffers`, trader index. *Self-check asserts **some** trader sells every item; that it is the **same** trader is still yours.* |
| 2.2 | …at the same price and loyalty level as the original | barter scheme copy |
| 2.3 | An own-priced item (`copyOriginalOffers: false`) appears at its DRIP trader at its config price | own-price path |
| 2.4 🤖 | Buy, equip, inspect. Model and texture are the retexture | `GEAR.bundle`. *Self-check asserts no item shares its base item's model path — so a silent vanilla-clone is caught. Whether the texture is the intended one is still yours.* |
| 2.5 | A plate carrier arrives **with its plates fitted** | `includedParts`, 627 fitted parts |
| 2.6 | Plates can be removed and refitted | slot filters |
| 2.7 | A retextured rig/armour **accepts the same plates as the original** | `updateFilters` — 442 conflict + 5 slot entries |
| 2.8 | A retextured backpack accepts items and reports the right grid size | cloned `Properties` |

## 3. Quest-locked offers — the 3.x bug that never fired

3.x never skipped quest-locked offers (`for...in` yielded array indices against a
dictionary keyed by assort id), so DRIP sold retextures of quest-gated gear immediately.
4.x skips them properly.

| # | Check | Blame first |
|---|---|---|
| 3.1 | Pick a vanilla item gated behind an unfinished quest. Its DRIP retexture is **not** on sale | quest-locked skip |
| 3.2 | It appears after the gating quest completes, if the original does | started/success/fail collection |

**Expect a bug report about this.** Someone will remember buying something they now cannot,
and the new behaviour is the correct one.

## 4. Quests and locales

| # | Check | Blame first |
|---|---|---|
| 4.1 | DRIP quests appear in the quest list, under the right trader | quest loader |
| 4.2 | Names, descriptions and objectives are English text, not raw ids | `CustomLocales/en.json`. *Item names are self-checked; quest text is not.* |
| 4.3 | Quest images render | `/files/quest/icon/` routes |
| 4.4 🤖 | A quest can be accepted and an objective progressed | quest conditions survived conversion. *Self-check asserts every handover/find target is a real installed item — the Part 3 sling bag case. Whether the objective actually ticks is still yours.* |

## 5. Flea and bots

| # | Check | Blame first |
|---|---|---|
| 5.1 | DRIP items are listed on the flea | `RagfairConfig.Traders` |
| 5.2 🤖 | Prices are sane, not 69420 or 0 | handbook / flea price inheritance. *Self-check asserts every item has a non-zero handbook price. Whether the number is **sensible** is a human judgement and is Colette's and Amber's pricing pass, not this.* |
| 5.3 | Raid a map and find bots wearing DRIP gear | bot weighting (`addToBots`, `botWeightMultiplier`) |
| 5.4 | Bots render without magenta | bundles loading for bots as well as the player |

> **5.3 is runnable as of the bot weighting pass.** It was flagged here as unimplemented and
> has since landed — 1232 equipment entries, 255 loot entries, 10 attachment entries across
> every bot type. If no bot wears DRIP now, that is a real failure rather than a missing
> feature, and the place to look is the weighted pools keyed by template id. — Kappa

### Set AI Amount to High or AsOnline before running §5 — not Medium

**A quiet raid on Medium is not evidence the escort half of the feature works.** EFT's AI Amount
preset rewrites boss escort counts client-side, and on **Medium** the arithmetic is
`(max - min) / 2`.

**Provenance: now independently confirmed at C# source, and Framesaver's IL read was exactly
right.** `EFT/LocalGame.cs:278` in the decompiled client, inside `smethod_8`:

```csharp
case EBotAmount.Medium:
    int num2 = list.Max(...);   // max of the comma-separated BossEscortAmount
    int num3 = list.Min(...);
    bossLocationSpawn2.BossEscortAmount = ((num2 - num3) / 2).ToString();
```

Plain integer division of the half-range, no coefficient, no rounding — precisely what Alpha
derived from `sub`, `ldc.i4.2`, `div` with no `add`. Two independent routes to the same formula.

### There is a SECOND Medium formula, for ordinary waves, and it is not this one

This is the trap, and neither of us had it. Scav waves do **not** use the escort arithmetic. They
go through `GClass1895.ToBotAmountSlots`, called from `LocalGame.smethod_7` on **every** wave:

| Preset | Escorts (`smethod_8`) | Ordinary waves (`ToBotAmountSlots`) |
|---|---|---|
| Low | `min` | `(int)(0.5 + min × WAVE_COEF_LOW)` — coefficient is 1.0 |
| **Medium** | `(max - min) / 2` | `(int)(0.5 + 1.4 × (max - min) / 2)` |
| High | `max` | `(int)(0.5 + max × 1.8)` |
| Horde | `max` | `(int)(0.5 + max × 10)` |

`WAVE_COEF_MID` is **1.4** and `WAVE_COEF_HIGH` is **1.8**, from `globals.json` — identical on
4.0.11 and 4.0.13. The two Medium expressions look the same at a glance and differ by a 1.4×
multiplier and a half-unit round. Generalising the escort formula to waves would be wrong.

**On Reserve this is not a rounding detail — it is the difference between a usable raid and a
misleading one:**

| Preset | Reserve scav slots (15 assault waves) |
|---|---|
| **High** | **84** |
| Low | 21 |
| **Medium** | **15** |

**Medium yields fewer scavs than Low.** That is the half-range formula being genuinely strange,
not an arithmetic slip — `2,2` contributes zero on Medium and two on Low. So "use High" is a
**5.6× effect on scav population**, not the escort-only precaution this section described before.

**The correction, from Alpha:** it is integer division, so the zeroing condition is
`max - min <= 1`, **not** `max == min`. An earlier version of this section said "a single value
gives zero followers", which is true but is the special case, not the rule.

**What I did verify independently** — against the shipped database on the install we are testing,
which is the part that decides whether §5 is observable:

- Every one of the **13** spawn entries for DRIP's five clothed escort types has
  `max - min <= 1`, so **all 13 zero on Medium.** `followerBully` on Customs is `"4"`, the three
  Gluhar followers on Reserve are `"2"`, `followerKojaniy` on Woods is `"2,3"` (range 1, floors
  to 0).
- Across every **real** escort garrison in the vanilla database — **133** entries — Medium yields
  **0 or 1 escort and never more.** 48 floor to zero, 85 give exactly one.

  *A correction from Kappa, worth keeping visible because it flatters the wrong thing:* I first
  said 161 entries and 76 zeroed. Those totals counted **28 entries whose escort amount is
  literally `"0"`** — bosses that bring nobody in the first place. Crediting the preset with
  emptying a garrison the database already left empty overstates the effect, and it hides
  something a tester needs (below). `161 = 133 + 28`, `76 = 48 + 28`. Same data, same formula,
  wrong inclusion rule.

  **Seven of those already-empty entries are ours, and they spawn nothing on *any* preset:**
  `followerBully` via `bossTagilla` on **both Factory variants**, and `followerGluharScout` via
  `bossKnight` on Customs, Lighthouse, Shoreline and Woods, and via `bossKolontay` on Streets.
  Raiding Factory hoping for a clothed Bully comes back empty on High, and the tester would be
  right to conclude the feature was broken. It isn't — that garrison is zero in vanilla.
  So our 13 entries are **6 real garrisons + 7 already empty.**

So the operational advice is unchanged and the reasoning underneath it is now sound: **avoid
Medium for anything escort-related.** A preset that reduces every garrison in the game to at
most one follower is a bad instrument regardless of which entries happen to floor to zero.

Low gives min, High and Horde give max, AsOnline draws per raid. This is client-side and
outside any server mod's reach — it can only be known, not fixed.

**To actually see clothed escorts, raid Reserve on High.** `bossGluhar` is a 50% spawn and brings
`followerGluharAssault`, `followerGluharScout` and `followerGluharSecurity` at 2 each — **three
clothed escort types in one raid.** Customs gives 4 `followerBully` at 39%, Woods 3
`followerKojaniy` at 50%. Nothing else comes close, so do not pick a map for this at random.

**No bot count for Reserve, deliberately.** `followerGluharSecurity` appears *both* as Gluhar's
primary `BossEscortType` and again in `Supports`, so the total is 6 or 8 depending on whether the
client stacks them or the primary is superseded. **The database cannot settle that** — it is
client behaviour. Kappa declined to put the number in a source comment on exactly that basis and
was right to; I had written "six bots", which was a guess wearing the clothes of a measurement.
Count what you see and tell me; that observation settles it.

Related, same source: **`ExcludedBosses`** comes from client raid settings and blocks a role
for the entire raid via `BotSpawner.SetBlockedRoles`. A garrison can pass every server-side
check and still produce nothing. Check it before concluding anything from an absent boss.

### Scavs are no longer excluded, and that demotes this whole section

`ClothedBotTypes` now has **13 entries and `assault` is the first of them** — Sophia's call, and
`MayWear` is the capability that made it safe (3.x excluded scavs as a workaround for not being
able to keep modern plate-carrier-era kit off them, not out of taste).

**Scavs are not escorts, are untouched by the AI Amount arithmetic, and are the most numerous bot
in any raid.** So **§5.3 is observable on any preset, on any map** — the opposite of what this
section said an hour ago.

**But only two of the thirteen types are preset-insensitive, not eight.** I claimed eight; Kappa
disagreed and he is right. Counted from vanilla location data — wave entries versus boss and
escort entries, per type:

| Group | Types | Basis |
|---|---|---|
| **Preset-insensitive: 2** | `assault` (**140 wave entries across 17 maps**), `marksman` (14) | Wave-spawned. Untouched by AI Amount. |
| **Preset-sensitive: 9** | the five followers, plus `pmcbot`, `exusec`, `pmcusec`, `pmcbear` | Zero wave entries. **SPT spawns PMCs through the boss mechanism**, so they are not the preset-proof control they look like. |
| **Never spawn at all: 2** | `usec`, `bear` | No wave entry, no boss entry, no escort entry anywhere. The 3.x names, superseded by `pmcusec`/`pmcbear`. Harmless in the list; **cannot be evidence of anything in a raid.** |

So the whole "observable on any preset" claim rests on **`assault` alone** — which is fine,
because scavs are the most numerous bot in the game. But the conclusion is narrower than
eight-of-thirteen made it sound, and the specific trap is real: **a tester who checks PMCs on
Medium and finds nothing has not learned what "preset-insensitive" implied they had.**

**So if you see no DRIP clothing at all on any bot, the preset is not your excuse** — that is a
real failure and the place to look is the weighted pools keyed by template id. The escort caveat
above narrows to "do not conclude anything about *escorts* from a Medium raid", which is a much
smaller claim than the one this section used to make.

> The stale version of this note said scavs were excluded and that the escort gate was therefore
> "fully in play". Both halves stopped being true when `assault` was added. Left visible because
> the failure mode is worth seeing: this section was written to stop someone misreading a quiet
> raid, and it had itself gone quietly wrong in the direction of excusing one.

## 6. Regression — do not skip

| # | Check | Blame first |
|---|---|---|
| ~~6.1~~ | ~~**Vanilla clothing still renders correctly**~~ | **CLOSED 2026-08-01 — answered by 6.7, not by a new test.** See below. |
| ~~6.2~~ | ~~Vanilla armour still accepts its plates~~ | **PASS 2026-08-01 (Sophia)** — plates observed moving into and out of vanilla carriers. Agrees with the by-construction argument below. |
| ~~6.3~~ | ~~Ragman's suit list is intact and correctly priced~~ | **PASS 2026-08-01 (Sophia)** — Ragman's prices untouched. |
| ~~6.4~~ | ~~Server starts clean with DRIP **removed**~~ | **PASS 2026-08-01** on a dirty profile. Three things the pass conceals — see below. |
| ~~6.5~~ | ~~A DRIP plate is **rejected** by a slot that rejects the vanilla plate it clones~~ | **RETIRED 2026-08-01 — no fixture exists.** Replaced by a 5-row audit, see below. |
| ~~6.6~~ | ~~Vanilla names/descriptions unchanged in a **non-English** locale~~ | **CLOSED 2026-08-01 without a client** — answered statically across all 17 locales, see below. |

### 6.6 needed no client, and nobody had to read Russian

The row assumed a human comparing vanilla strings in a foreign UI. That was never the right
instrument: a tester can eyeball a dozen items in one locale, and the failure is a *key
collision* which is exactly enumerable.

DRIP authors **216 locale keys** in `CustomLocales/en.json` and applies them to every locale.
Intersected against the game's own locale tables:

```
17 locales, 31,084 vanilla keys each (ru 31,233), collisions: 0
```

**No DRIP key exists in any vanilla locale, so no vanilla string can be overwritten in any
language.** Positive control run alongside it: planting a real vanilla key into DRIP's set
produces exactly 1 collision, so the comparison demonstrably fires rather than being quiet by
construction.

**Honest scope, because this closes only part of the row.** It covers the *authored* keys. Item
and clothing names are written under **derived** keys (`<tpl> Name` / `ShortName` /
`Description`) that do not exist until the ids are computed at load, so they are not
enumerable from disk. That half currently rests on the existing self-check assertion that DRIP
ids never collide with vanilla item tpls — if a tpl cannot collide, `<tpl> Name` cannot either.

**Worth one cheap assertion from Kappa to close it properly**, since it belongs where the
derived keys actually exist: *no DRIP locale write lands on a key that already had a value*,
over all 17 locales, at load. That converts 6.6 from a smoke-test row that nobody can run into
a permanent check, and it would fire on the exact defect this row was invented for.

### 6.1 is closed by 6.7's mechanism, and no client test was needed

`shadow_list.py` reports **120 distinct vanilla identities claimed by DRIP bundles, 79 of them by
more than one bundle** — ten `TSHIRT_*` variants all declare themselves `tshirt_bear_black.bundle`.
So the mechanism for a 6.1 failure is present by construction and the risk looked real.

It is not, and **§6.7 already proved it.** Two bundles claiming one identity stayed live across
three bot populations for twenty minutes and resolved independently every time. Had the client's
bundle store been keyed on the internal name, one of the ten would have won and every variant
would have rendered as a single garment. It keys on the path each bundle is *served* under, DRIP's
sit at `Essentials/…` keys, and the vanilla path is not in that key set. Nothing can shadow it.

**Why the raid census could NOT have closed this, and this is the part to keep.** A shadowed
vanilla `tshirt_bear_black` renders as a DRIP tee on a bot — which is precisely what the bot
appearance feature is *supposed* to produce. "I saw DRIP clothing and nothing looked wrong" is the
report a working shadow generates. The observation was never able to distinguish the failure from
another feature's success; the mechanism argument is what settles it.

§6.7 ran on SPT 4.0.11 and we now run 4.0.13. **Sophia's call, and it is the right one: bundle
resolution belongs to EFT and Unity, and neither version moved** — SPT's server version does not
touch it.

### 6.5 has no fixture — DRIP ships no plates

Checked 2026-08-01: gear categories are ARMOR, BAGS, FACE, HATS, HEADSET, HELM, RIGS. "Plate"
occurs only in the names of plate *carriers*. There are no DRIP plates or inserts to mis-fit, so
the row as written is untestable.

**Do not simply drop it — the risk it covers is real.** Over-permissive `updateFilters` is not
about plates; it is about any DRIP id being added wherever its base id appears, including places
that do not generalise to a retexture. The load reports **5 slot filter entries**, which is a
hand-audit rather than a client test. Kappa's, and it retires the row honestly.

### 6.4 RESULT — pass, 2026-08-01, and what the pass conceals

Run on the dirty profile deliberately: `6a6c3de5a2ff2389c81c3a0d`, with DRIP items bought and a
DRIP quest completed. Mod folder **moved**, not deleted; cache confirmed empty first so nothing
stale could make the server look cleaner than it was.

```
ModLoader: loading: 0 server mods...                          <- the removal was real
Fatal  Failed to load profile '6a6c3de5a2ff2389c81c3a0d'. Marked as invalid.
       InvalidModdedItemException: Item: 6a6c47c8c2a447a7e418c5d2 ...
Started webserver at https://127.0.0.1:6970 — Server has started
```

**Pass on every pre-registered condition:** the server survived, named the offending item,
refused the profile rather than mutating it, and nothing in the log names anything that is not
ours. `removeModItemsFromProfile` was confirmed `false` beforehand, and the profile file was
**MD5-identical after the run** — nothing was written to it.

**Three things the pass hides. All three were found by looking past the log at the profile.**

1. **The message names 1 of 6.** Six distinct unknown tpls sit in that profile — 2 PMC-side, 4
   scav-side. Validation throws on the first, so the message is a *sample presented as a
   finding*. Never read that error as a list.
2. **It names the `_id`, not the `_tpl`.** `6a6c47c8c2a447a7e418c5d2` is an item *instance*; the
   unknown template is `6c28a405782dd6c09d2d78ed`. Anyone following that message to identify
   which mod item is at fault will search for something that cannot be found. Upstream issue.
3. **The residue is bigger than items and nothing reported it.** All **19 DRIP quests** remain in
   `characters.pmc.Quests` and both DRIP traders (`cd736677…` moron, `d6f8d358…` georgia) remain
   in `TradersInfo`. The validator mentioned neither — plausibly because it threw on an item and
   never reached them. **SPT's own advice inside that error — set `removeModItemsFromProfile:
   true` — removes items and does NOT remove quest or trader records**, so following it yields a
   profile that *loads* while carrying quests pointing at a trader that no longer exists. That is
   the same shape as the bug that threw a 500 on `items/moving` and desynced the whole UI.

**Sophia's call, 2026-08-01, and it closes this:** uninstalling any trader-adding mod — especially
one with quests — is well known in the SPT community to leave a profile in odd states. DRIP has
done more than most mods do to be safe here. **A player who uninstalls and hits this accepted that
risk.** Not a release blocker, not a bug to fix. Recorded so nobody re-opens it as one.

### 6.4 wanted the DIRTY profile — why (kept, the reasoning still applies)

A profile that never held a DRIP item passes trivially and proves nothing. **Run it on the profile
that has DRIP items purchased** — that is the positive control, and Sophia's concern about the
confound is what makes it the better test.

Pre-register the expected result or it reads as a bug: with DRIP removed the server will hit
unknown tpls and throw `InvalidModdedItemException` **naming them**. That is correct behaviour,
not a DRIP defect. The failure would be an *unnamed* crash, or one naming something that is not a
DRIP item.

The second half is the actual question — a profile that existed while DRIP was installed but never
acquired a DRIP item should start **clean**. That tests what DRIP leaves behind *beyond* the
items: traders, quests, customization suites, flea presets, user builds.

Standing constraints, unchanged: never set `removeModItemsFromProfile: true` (it deletes from
inventory **and** insurance), and `RemoveInvalidUserBuilds` has no config gate.

### On 6.2 — the aliasing risk isn't there, but a different one is

Worth stating so nobody spends time on the wrong thing: **`updateFilters` cannot corrupt a
vanilla item by aliasing.** `CustomItemService.CreateItemFromClone` clones via `ICloner`, and
every implementation of it is a deep clone (`FastCloner.DeepClone`), so a DRIP item's
`ConflictingItems` and slot `Filter` sets are distinct objects from the vanilla item's. Adding
to one cannot touch the other. Both are `HashSet<MongoId>`, so the adds are idempotent too.

6.2 should therefore pass by construction, and it is cheap to confirm. The pass only ever
**adds** ids, never removes, so a vanilla item losing a filter entry would mean something
other than this code did it.

The reachable failure is the opposite one, and it is why **6.5** is the row that matters: DRIP
ids are added wherever the cloned base id appears. If that is ever too broad — a base item
that appears in a filter for reasons that don't generalise to its retextures — a DRIP item
becomes fittable somewhere it shouldn't be. Nothing errors, nothing logs, and the only symptom
is a plate going into a slot it has no business in.

### Two more that a clean server log cannot see

- **6.6** exists because clothing writes exactly one locale key per suite and falls back to
  English for all 17 locales. If a transformer ever wrote to the wrong key, the damage would
  show up in `ru` or `ch` while `en` looked perfect.
- **Two configs sharing one folder** would both claim the same co-located bundle and render as
  the same model, with no error. Not currently true of Part 1, but it is the shape of mistake
  the drop-in Parts 2/3 requirement invites. Worth one look if a new pack ever appears to have
  duplicate-looking items.

6.1 matters most. Every DRIP bundle self-declares a vanilla bundle path, so a mistake in the
repack or rebuild could plausibly shadow the vanilla asset rather than sit alongside it. That
would look like "DRIP works" while quietly breaking the base game.

### 6.7 — two DRIP variants of the same garment, visible at once

I enumerated what our 365 bundles actually claim. **120 distinct vanilla paths, and 79 of them
are claimed by more than one DRIP bundle.** Ten different T-shirt retextures all declare
themselves to be `tshirt_bear_black.bundle`; nine ZASLON trousers all claim
`pants_bear_zaslon.bundle`.

Unity normally refuses to load two bundles carrying the same internal name. 3.x shipped this
way for years without obvious complaint, which suggests it is tolerated — but "suggests" is
doing a lot of work there, and the situation just changed:

**Bot appearance landed this session** (79 tops, 57 bottoms across 12 bot types). Before it,
two variants of one base garment being live simultaneously was nearly impossible — a player
wears one shirt. Now a bot can wear a second one in the same raid. If duplicate bundle
identity is a real problem, this is the release where it starts happening.

**The check — no longer a dice roll.** In `config/config.jsonc`, uncomment and set:

```jsonc
"debugPinBotTop": "TSHIRT_HEADPAT_WINTER_TOP",
```

Every bot then wears that exact top. Buy and wear **T-Shirt - Gay Agenda** yourself, enter a
raid, and look at any bot. Both garments claim `tshirt_bear_black.bundle`, so if duplicate
internal identity is a real problem, this is the configuration that shows it. The config is read
at load, so **restart the server** after changing it.

Repeat with `ZASLON`, `GORKA4`, `HOODIE` — the other families where nine or ten variants share
one identity. **Turn the pin off afterwards**; it is not a normal game.

### Raid Reserve on High for the pinned/unpinned pair

Counted from vanilla spawn data rather than picked by feel. Reserve is **the densest scav map in
the game — 15 `assault` waves, 47 max slots**, well clear of Factory's 29 and Shoreline's 23. With
the pin active every one of those scavs wears the fixture, so the map that spawns the most scavs
is the map that gives the most independent looks at it.

It also carries `bossGluhar` at 50%, which is the only garrison bringing three clothed escort
types at once. So **one Reserve raid on High covers 6.7, 5.3, 5.4 and the escort question
together** — and it is where to count Gluhar's followers to settle the 6-or-8 ambiguity above.

**Plan the raid length, not just the map — the 47 is a budget spent over time, not a crowd.**
Those are wave entries with their own spawn windows:

```
t = -1 (raid start)   10 slots   21% of the budget, immediately
by ~3.3 min           14
by ~10 min            24
by ~17 min            40         85% of the budget
by 40 min             47         the last 7 sit in two waves at t=1200-2400s
```

**So ~20 minutes gets ~85% and the tail is expensive.** Do not read an early extract as "the pin
only produced twelve looks". Framesaver raised the cumulative-versus-concurrent distinction; the
schedule is from Reserve's own wave table. Raw `slots_max` shown — on High each is scaled by 1.8,
so the real budget is ~84 and the *shape* is what this table is for.

**A line here used to say "by ~13 min: 28 = the concurrent cap". It was wrong twice over:**

1. **`BotMax` is not a concurrency cap.** It is read in exactly one place —
   `NonWavesSpawnScenario`, the continuous *trickle* spawner. `WavesSpawnScenario` and
   `BossSpawnerClass` never look at it. Alpha caught this having made the identical mistake two
   days ago and published a per-map table of "cap violations" before Beta killed it by
   enumerating the field's readers.
2. **On Reserve the trickle spawner is switched off entirely** — `NewSpawn: false` and
   `OfflineNewSpawn: false`. `BotMax: 28` is the ceiling of a system that never runs here.

I quoted a real number, did correct arithmetic with it, and never asked what reads it. **A field
that is present can still be the wrong instrument, and the failure is its scope** — harder to
catch than a missing field, because the number is real and the arithmetic is right.

The genuine concurrency limit is **`MaxBotsAliveOnMap: 36`**, in `globals.json` rather than the
location files, which is why searching there came up empty. It **paces** arrivals rather than
reducing the total — a wave held at the cap spawns later, not never.

**How it is enforced, verified at source, because the obvious answer is wrong.** `CheckOnMax` has
exactly two call sites and they guard different paths:

| Path | Call site | Guard |
|---|---|---|
| Boss / garrison spawns | `BossSpawnerClass.cs:51` | `if (!wave.IgnoreMaxBots)` — where `wave` is a **`BossLocationSpawn`** |
| Ordinary waves | `BotSpawner.cs:449` | `if (withCheckMinMax && !forcedSpawn)` — `IgnoreMaxBots` is not involved |

**`IgnoreMaxBots` does not exist on wave entries at all.** It is declared once, on
`BossLocationSpawn.cs:366`. Census of every `base.json`: **0 of 154 wave entries** carry it;
**139 of 140 `BossLocationSpawn` entries** do, **119 `true` / 20 `false`**. So the well-travelled
"119 of 140" figure is a statement about *garrisons bypassing the cap* — the opposite population
from the one it kept getting attached to.

So the cap gates **both** paths, with most bosses exempt. Reserve's scav waves are capped, but via
`BotSpawner.cs:449` — not via a field they cannot have. An earlier version of this section said
"all 15 Reserve waves leave `IgnoreMaxBots` unset, so they go through `CheckOnMax` there." Right
conclusion, wrong mechanism: unset because the field does not exist on that type.

**The rule this cost us:** enumerating a field's readers is necessary and not sufficient — **for
each reader, ask what *type* it reads the field from.** Alpha had already enumerated both
`CheckOnMax` sites and still matched the field name to the population they expected. And say the
denominator out loud: *"119 of 140 what?"* would have killed this the first time anyone asked.

**Raiders do not replace scavs on Reserve — they are added, and SPT boosts them.** Sophia asked
this in pre-flight and it was worth asking. `PostDbLoadService.AdjustMinReserveRaiderSpawnChance`
rewrites every `pmcBot` entry on Reserve to **80% untriggered / 90% triggered**, against the
40/30/30/30% the raw location file declares — and it only ever *raises*, never lowers. Scav waves
are untouched (`customWaves` is empty for both `boss` and `normal`). Since `pmcBot` is itself a
clothed type, this makes Reserve better for us, not worse.

### Careful: the spawn data in `base.json` is not what the server runs

`removeExistingPmcWaves` is **true**, so `PostDbLoadService.RemoveExistingPmcWaves()` strips every
`pmcUSEC` and `pmcBEAR` entry from every map's `BossLocationSpawn` and `customPmcWaves` puts
different ones back — **14 on Reserve, several at 100% chance.**

The spawn-mechanism table above was derived from `base.json`, which is the *pre-mutation* layer.
The conclusion survives intact — substituted PMC waves are still `BossLocationSpawn`-shaped, so
PMCs still spawn through the boss mechanism and are still preset-sensitive — but it survives by
luck, not because the measurement was right. **Config-driven `PostDbLoad` rewrites sit between
the database files and the raid, and reading the files alone will silently answer a question
about the wrong layer.**

**Not Lighthouse, tonight.** It has 10 Rogue (`exUsec`) entries and Rogues *are* a DRIP-clothed
type, which makes it tempting. Two reasons against: its scav count is 14 against Reserve's 47,
and the Rogues will kill you at range while you are trying to look at shirts — Framesaver lost
half a raid there to the AGL this evening.

Lighthouse becomes the *right* map later, for a different question. Framesaver measured `exempt`
at **9 of 24 bots** there: boss- and escort-class roles never enter stand-by and are never
animator-culled, so their materials stay resident and animating for the whole raid. That is
exactly the population where a **texture-variety** cost would surface, and DRIP clothes it —
Rogues, PMCs, and the five followers are all in `ClothedBotTypes`. It is also the map Framesaver
now has a full frame decomposition for. When the mipmap ride-along happens, it happens there.

### If bots do render badly, the pin tells you *which* problem it is

Two unrelated causes produce similar-looking symptoms from an identical setup, and it would
be easy to spend an evening on the wrong one:

- **Duplicate bundle identity** — two bundles claiming one internal name.
- **GPU cost** — many distinct unmipped 2048×2048 garment textures resident at once. 286 of
  our 333 diffuse maps have no mip chain, so they sample at full resolution at any distance,
  and that cost scales with *variety* rather than with the number of bots.

**The pin separates them.** Pinned, every bot wears one garment — so texture variety collapses
to almost nothing, while duplicate identity is *fully* in play (you wear variant A, they all
wear variant B, both still claiming one bundle name).

| Pinned | Unpinned | Conclusion |
|---|---|---|
| broken | broken | **duplicate identity** — variety was never the issue |
| fine | broken | **load** — identity is fine, this is texture cost |
| fine | fine | neither reproduces |

Kappa's, and worth having in hand beforehand rather than deriving it while confused.

The log states which ids actually landed in the pool, so a pinned run is identifiable
afterwards rather than having to be remembered. A name DRIP doesn't recognise refuses the
*whole* pin and changes nothing — it will never apply half of what you asked for, because a
half-applied fixture looks authoritative and isn't.

Without the pin this was: wear a DRIP T-shirt, find a bot wearing a different one, and hope.
Kappa's refinement was that it needs only **the player and a bot** rather than two bots rolling
variants of one garment — far more likely, so it should reproduce if
it is real.

**If it is real, the bundle rebuild fixes it outright** — this is no longer a mitigation
question. DRIP bundles claim vanilla names only because they were built as modified *copies*
of vanilla bundles. Rebuilt bundles get unique names assigned by the Unity project, so no two
DRIP bundles would share an identity and the condition simply stops existing. Safe because the
client requests bundles by **key** (the mod-relative path, unchanged) — the internal name is
only Unity's runtime registry, so renaming breaks nothing.

`tools/vanilla-origins.json` is what makes this free: lineage is now recorded independently of
the bundles, so the rebuild has no reason to preserve vanilla names. Before that record
existed, keeping the derivation working would have meant forcing vanilla names and
perpetuating this very risk.

The interim levers — one variant per garment family, or `addClothingToBots: false` — remain
unbuilt and are now unlikely to be needed. Recorded so they aren't invented under pressure if
6.7 reproduces before the rebuild lands.

**The server cannot see this.** It registers bundle keys derived from file paths and never
opens the files, so no assertion reaches it. Assertion 8 checks the *sibling* case — two
configs in one folder claiming the same co-located bundle — which is a different cause with the
same symptom. If a bot renders wrong because of duplicate internal identity, assertion 8 will
have been green throughout. Do not read a passing self-check as covering this row.

If one renders and the other is invisible or wrong, that is this, and it is not something any
server-side check can see.

**Vanilla areas our bundles claim**, for the 6.1 regression sweep — 62 under
`assets/content/items/equipment`, 38 under `assets/content/characters/character`, the rest
hands. So the vanilla items worth spot-checking are rigs, armour, helmets, bags, and the base
BEAR/USEC outfits.

---

## Recording results

Note the item and what you saw, not just pass/fail — "renders but the normal map looks flat"
is far more actionable than "fail", and points at `_TintMask` rather than at the shader
rebind. Anything ambiguous is worth a screenshot.
