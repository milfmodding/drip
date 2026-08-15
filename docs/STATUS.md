# DRIP port — shared status

Single source of truth for who is doing what and which decisions are settled.

**Why this file exists:** cross-session messages arrive asynchronously and have crossed
several times, so items already closed were being reported as open and re-answered. Messages
are for discussion; *this file* is the state. Read it before asking whether something is
still open.

**How to use it:** own your section, update it when something lands, and don't edit anyone
else's. Echo maintains "Settled decisions" — if you need one changed, ask rather than editing.

Last updated: 2026-08-15 by Echo.

---

## Roles

| | Owner | Scope |
|---|---|---|
| **Echo** | adjutant | whole-project picture, arbitration, Unity bundle workstream |
| **Kappa** | codebase | C# loader, services, runtime correctness |
| **Tau** | DX | config schema, converter, validation, authoring tools, docs |

---

## Settled decisions

Do not relitigate without asking Echo. Sophia's calls are marked.

| Decision | Detail |
|---|---|
| Release target *(Sophia)* | Part 1 (Essentials) — 275 items. Parts 2/3 must stay drop-in; nothing hardcoded to "Essentials". |
| Profile compatibility *(Sophia)* | None. Blank slate, IDs are free. |
| Clothing tags *(Sophia)* | Tabled, moving to ICUP. Not modelled, not validated, **must round-trip untouched**. ICUP becomes a small mechanism-only mod; **DRIP takes a soft dependency** and publishes tags only when ICUP is present. Other mods then depend on ICUP, not on 3 GB of clothing — the integration surface is the shared database node, not the mod. |
| Tag weights are placeholders, and 3.x hid it *(Sophia)* | The `1` in every tag entry is copy-paste artifact, not data — weights were **intended to work**. **267 garments** carry tags. **Part 1 is 135 files and 135 garments, no duplicates** — that figure is clean and is the release-relevant one. All-parts derivation, independently verified: 269 files, minus **two** duplicate groups = 267. `ZASLON_SOC_PANTS` (byte-identical across Part 1 and Part 3) and `TSHIRT_DESERTTAN.json5` + `TSHIRT_KHAKI.json5` (byte-identical, *same folder*, same bundles, both naming themselves "T-Shirt - Khaki" at 42,069 — a real Part 3 content bug). **The equivalence you count by decides the answer**: filename gives 266, config content gives 268, config-plus-co-located-bundles gives 267, and only the last describes a garment. Four counts were attempted before this one and three were wrong — 264 from a regex missing indented keys, 268 from a file count that landed right only because an unparseable file was absent, 268 again from filename dedup that missed a same-folder duplicate. **Recounting the same way reproduces the blind spot rather than testing it; change the equivalence, not just the run.** ICUP was designed by someone else and never validated. Third instance of the same template-copy defect after `price: 0` and the profileLevel-10 cluster. **3.x masked it**: `ICUP.ts addWeights()` ignored authored values entirely and computed tag-selection weight by *counting items per tag*, so a 128-item tag was 128× likelier than a 1-item tag and no authored number was ever read. Porting that behaviour forward would perpetuate the mask. ICUP must read authored weights, and flag an all-`1` tag set the way `DRIP-307` flags `price: 0`. |
| Shipping model *(Sophia)* | **Part 1 always ships inside the DRIP archive** as the minimal install. Parts 2 and 3 are **separate add-on downloads** extracting into the same `ContentPacks/`. Hollowed-out bundles make re-extracting the base pack on update cheap enough that this is acceptable. |
| Content pack delivery — both mechanisms, eventually *(Sophia)* | `ContentPacks/` stays the path the team uses. A **public API** for third parties shipping DRIP support inside a larger mod is wanted **later, not now**. When it lands, both must converge on the same internal code path — two entry points that diverge is exactly the drift this table already warns about three times. |
| WTT *(Sophia)* | Vendor functionality, never take a `PackageReference`. Reference only. |
| `price: 0` *(Sophia)* | Legacy test junk, **not** intentional free items. Warn and name the files; do not hard-error. Runtime `NoClothingRequirements` zeroing is separate and stays valid. |
| ID collisions *(Sophia)* | Fail loudly. Identical content → skip and log; differing content → hard error naming both files. |
| Git contents | Configs only. `*.bundle` is git-ignored. Repo is **not** the distribution channel — players get a release archive; only developers see a bundle-less tree. |
| Canonical bundle home | `F:/SPT/Mods/DRIP-bundles/`, mirroring the ContentPacks layout, outside git. Rebuild output lands here. |
| Extracted art home | `F:/SPT/Mods/DRIP-art-library/` — content-addressed PNG pool plus `manifest.json`. |
| Case-insensitive JSON | Correct for DRIP's own config classes. **Never** for types binding onto SPT models — `TemplateItemProperties` declares both `ShotgunDispersion`/`shotgunDispersion` and `ExplDelay`/`explDelay`, and is unconstructable under case-insensitive options. It is the only such type in `SPTarkov.Server.Core.Models` (verified by full scan), so the **serializer** boundary is complete. Reflection lookups against BSG types need the same care separately — `copyPropertiesFrom` resolves property names by reflection, bypassing the serializer entirely, where a case-insensitive match returns the wrong field **with no exception at all**. Exact-match first there, case-insensitive only when unambiguous. |
| Role-based bundle dependency defaults | **Rejected.** Dependencies are derivable exactly — all 364 Part 1 bundles resolve to a vanilla origin — so a heuristic would be strictly worse. |
| Pre-v2 scaffold configs | Removed from the content pack. May be kept as `drip check` fixtures, but **outside any path the loader walks** — not under `bundles/ContentPacks/`. |
| Prices need human review *(Sophia)* | Tau's ten-item proposal is adopted as an **interim placeholder**, not a derivation — the sibling prices it interpolates from may themselves be arbitrary template copy-paste. Pricing across all content packs needs **Colette or Amber** to review by hand before ship. Not a call Sophia can make for them; the deliverable is tooling that makes it possible. |
| The content owners are not programmers *(Sophia)* | Colette and Amber own this content and do not write code — Sophia was brought onto the project to bridge exactly that gap. Terminal commands over `.jsonc` files are already past the line for them. Anything they are expected to *use* (as opposed to benefit from) must assume no code, no JSON, and no terminal. |
| `SLING_OLIVEDRAB_BAG` moves to Part 1 *(Sophia)* | A Part 1 quest hands it over and it shipped only in Part 3, so the quest could not load and a downstream quest depended on it. Do not mutate the 3.x source tree to achieve this — it is the reference corpus. |
| The converter is authoritative for what it writes and blind to what it doesn't | Two failures, one root cause, both silent. **Inputs reverting outputs:** content pack configs are *generated*, so editing one is a temporary edit — the next run reverts it and the revert is indistinguishable from success. Decisions need a home the converter reads (`tools/price-overrides.json`, `PROMOTIONS`, `RENAMES`). **Outputs outliving inputs:** a file the converter no longer writes just stays there — a stale config is indistinguishable from a real one. This bit three times (the `DRIP.json5` quest double-load, the `- Copy` rename leaving a duplicate item, superseded scaffolds) before the converter began listing anything in the destination it didn't write. |
| Build the charitable diagnostic, not the minimal one | Two diagnostics written for *other people's* mistakes paid out on their own authors first: the bundle-less-checkout message, and the config fallback that caught a missing comma Kappa introduced into `config.jsonc` — naming the line and column. Neither was built for us; both found us before anyone else. The extra sentence explaining *what to do* costs minutes when written and saves an hour when read, and the person it saves is as likely to be you as a stranger. Cheaper to do now than after release. |
| Every garment is a retexture — no *de novo* content *(Sophia)* | DRIP has never created an original garment; the project exists to retexture items the game already has. Not expected to change soon. This is a **structural invariant, not a coincidence**, and several things depend on it: `basedOn` is always resolvable, the suitability derivation covers 100% of content by construction, and all 364 Part 1 bundles resolving to a vanilla origin was never luck. **Consequence: a missing `vanillaOrigin` is an alarm, not a routine case** — it means either a tooling failure or genuinely new content, and the second would need a different creation path entirely rather than one optional field. Supporting *de novo* garments later is a feature, not a relaxation. |
| Two garment counts exist and they are *not* reconcilable | **267 tagged garments** (this table) and **268 garment keys** in `tools/vanilla-origins.json` measure different populations by different equivalences, and nobody should try to make them agree. Tags: 269 of the 270 clothing files carry one — the exception is `GHILLIE_WOODLAND_TOP` — deduplicated by *config + co-located bundles* → 267. Origins: all 270 clothing files, deduplicated by *STEM\|type* → 268 keys, stored as 269 entries because one rename carries an alias. Both are correct; they answer different questions. Quote the garment count for the population you mean, never the line count. |
| A DRIP content-creation app — recorded intent, not a plan *(Sophia)* | **Not now, deliberately.** But recorded because it changes a design decision that is live today. The idea: one place to create anything for DRIP — clone an item by picking it, choose quest objectives and rewards from lists, and **hand it an adjusted texture and have it assemble the bundle and write the config**. Interim answer is a `.cmd` plus interactive `drip new quest`; XAML is rejected *for now* on the grounds that a GUI validator competes with in-editor schema validation and loses, not on cost. **The constraint for Echo's bundle rebuild:** that app's hardest component — texture in, bundle out — is the same component the rebuild needs. So build the rebuild as a **reusable pipeline** (`texture + vanillaOrigin → bundle`), not a one-off migration script. Retrofitting a script into a pipeline later is far more expensive than writing it as one now, and steps 1–3 of "make a new DRIP item" being manual Unity work is plausibly why this mod was only ever retextures by a small number of people. |
| Documents describing *state* decay; documents describing *decisions* don't | Kappa's observation, evidenced by this very file. The settled-decisions table has not gone stale once in a day of heavy change; narrative describing current state went stale **twice within an hour** — Echo's smoke-test §1.4b described a live bug that got fixed underneath it, and Kappa's `ClothedBotTypes` comment described `assault` as present after he had removed it. Both were accurate when written, wrong an hour later, and sitting exactly where someone would look to decide what to do. Prose has no build step, so prefer framing as *"what to expect and why"* over *"what is currently broken"* — the first survives the fix. |
| Notice when an action is irreversible, then verify | Three near-losses in one day, each stopped by a check costing under a minute: `hellomilfy.bundle` deleted only after confirming it was byte-identical to the real one; the suit-id bug found by reading Ragman's actual data instead of trusting a clean load; 136 of Tau's `vanillaOrigin` fields saved by checking inodes before stripping what looked like self-inflicted contamination. **In each case the confident inference was reasonable, and twice it was wrong.** The operative skill is not general scepticism — it is *noticing you are about to do something irreversible*, at which point the check is always cheaper than the mistake. Kappa's framing. |
| Act without asking when a thing is wrong under *every* branch | The test for proceeding without a decision is not "am I confident" — it is **"is this wrong regardless of how the open question resolves?"** Unfiltered scavs were wrong whether or not Sophia took the derivation, so Kappa reverted rather than waiting. A half-applied appearance pin is wrong whether or not the garment matters, so it refuses outright. When both branches agree, there is nothing to wait for; when they don't, ask. |
| State the scope a number was measured within | Both Echo and Kappa did a version of this in one day: Echo measured 6 of 13 bot types and reported a total ("26 garments match nothing" — actually 7); Kappa re-derived a feature list from one 3.x file and reported it as complete. A number without its boundary reads as universal. Note the same hazard sits in our own tooling — the self-check reports "140 items" and would say so just as confidently having looked at a single content pack. It happens to look at all of them; nothing in the line tells you that. |
| A modelled field is not an implemented feature | `addToBots` sat in `ContentItemConfig` unread while 274 configs set it, and looked handled because the model listed it. Before calling any feature done, check what *consumes* the field, not what declares it. `scratchpad/unconsumed.py` automates this — it found two more afterwards (`botWeightMultiplier` unread; `Models/CustomClothingConfig.cs` entirely dead). Derive completeness from the 3.x source, never from our own notes. |
| Soft armour and helmet armour are not player-editable, and the templates say the opposite *(Sophia)* | **The item data is wrong here, not merely silent, and this is the class of fact that gets re-derived incorrectly with confidence.** A required `Soft_armor_*` / `Collar` / `Groin` / `Shoulder_*` / `Helmet_top` / `Helmet_back` insert **cannot be added or removed by a player, and no source in the game sells one.** Every such filler nonetheless reports `IsUnremovable: False`, `IsLockedafterEquip: False` and `CanSellOnRagfair: True`. Anyone deriving editability from `_props` will conclude these are freely removable and sellable. **Three consequences.** (1) *There is no balance decision about including them.* The unfilled state does not exist in the game, so filling every required slot is the only state the item can be in — not a policy choice, and not a question for Colette and Amber. (2) *The shell-only handbook price describes an impossible state* — the LBT Slick is 12,710 as a shell and 241,490 filled, so quoting the shell price to a price reviewer under-states these items by 5–19×. `price_review.py` already splits required-slot value from optional plate value in its "comes with" figure; the wording is what needs to carry this. (3) **No ballistic plate slot is ever required** — the THOR's ~618,000 of plates lives entirely in *optional* slots, so auto-filling required slots gives no plates away. **The derivable shadow**, and the check worth building: every legal filler for these slots is `unsold` by every trader, so *"a required slot whose only filler is obtainable from nowhere"* reaches the right conclusion mechanically. Use that, never the editability flags. Echo produced three successive wrong answers here (no balance call → one balance call → none again) by reading the templates; Sophia settled it from having played the game. |

---

## Kappa — codebase

**Landed:** csproj content rules; `DripJson` with scoped case-sensitivity; trader path fix;
`DoIfPathExists` awaits; hardcoded parent/price fields removed; 18 WTT features culled;
`ContentItemConfig` (schema v2); `DripCurrency`; `DripTraders` (derived from the `Traders`
enum, cannot drift); `updateFilters` as a single deferred pass; lenient enum parsing;
`docs/UPSTREAM-ISSUES.md`. `Models/CustomItemConfig.cs` deleted.

Clothing service rewritten (clones vanilla customization entries rather than
hand-constructing them, so it inherits BSG properties and cannot drift). Bundle discovery,
config enumeration and id derivation pulled into `DRIPBundleService` / `DripFiles` / `DripIds`
so the two loaders cannot disagree.

**Bundle-less checkout diagnostic — done**, so this is off Tau's plate. Aggregate report
instead of one line per config, with an un-bootstrapped checkout (warning, points at the fix)
distinguished from genuine missing bundles (error, names the files).

**Verified on a running 4.0.13 server, both scenarios:**

| | Result |
|---|---|
| Bootstrapped | **275/275 load** — 139 gear + 136 clothing, **0 errors, 0 warnings** beyond the 10 intended `price: 0` notices |
| Fresh clone (configs only) | 17 lines, down from 286; two aggregate warnings naming the fix |

**Two bugs found by checking rather than assuming:**

- Items with no model bundle were being **created anyway**, silently keeping the cloned item's
  model — shipping as visual duplicates of the vanilla item they retexture. Now a hard failure.
- Suits were given the same id for the trader's offer and the customization record. All 109 of
  Ragman's vanilla suits use distinct ids, as did 3.x. Fixed.

**`copyOriginalOffers` + `includedParts` — done.** `DRIPTraderAssortService`, deferred so the
trader index is built once for the whole load. Both indexes as specced: `_tpl → root offers`
and `parentId → children`.

```
[DRIP] Trader offers: 215 copied from the original items (627 fitted parts), 35 at their own price.
```

`no assort found` is gone, and **the whole server log is now zero errors**. All 139 gear items
have a sales route; the 627 fitted parts confirm the plate / soft-armour child path works.

**Found a 3.x bug while porting it.** The quest-locked skip at `collection.ts:213-217` indexed
`questassort.success` by the *array index* of the offer rather than by its assort id, so it
never matched anything — quest-locked offers were being copied to DRIP traders as freely
available for the life of the 3.x mod. Implemented correctly here: every quest-locked assort
id across started/success/fail is collected up front and skipped.

**Cleanup done** (Echo's request): all four `*.bundle` files untracked — `git ls-files` now
reports zero — and the orphaned `hellomilfy.bundle` deleted from disk. Verified byte-identical
(matching MD5) to the legacy `GEAR.bundle` before deleting, so nothing unique was lost.
Untrack only, no history rewrite, per your recommendation.

**Bot weighting — done.** Third deferred pass, same shape as the other two: one sweep over
every bot type for the whole load rather than 3.x's sweep-per-item.

```
[DRIP] Bot loadouts: 1232 equipment entries, 255 loot entries, 10 attachment entries.
```

**I had missed this entirely.** It was the second-largest feature in Echo's original brief by
usage (274 configs) and never reached this table or my own list — the field existed in
`ContentItemConfig`, which made it look handled. Caught only while reviewing
`CLIENT-SMOKE-TEST.md` §5.3, where it would have presented as a bundle problem and sent
someone into the wrong workstream. Worth noting as a process point: a modelled config field is
not evidence of an implemented feature, and my "landed" list was built from the former.

**Quests, locales, bot appearance — all done.** Current full load:

```
[DRIP] CustomLocales: 216 strings across 17 locales (authored: en).
[DRIP] CustomItems:   139 new items.
[DRIP] CustomClothing: 136 new clothing items.
[DRIP] Inherited compatibility for 139 items: 5 slot filter entries, 442 conflict entries.
[DRIP] Bot loadouts: 1232 equipment entries, 255 loot entries, 10 attachment entries.
[DRIP] Bot appearance: 79 tops and 57 bottoms across 12 bot types.
[DRIP] CustomQuests: 18 quests, 5 icons, 14 item references resolved by name, 1 failed.
[DRIP] Trader offers: 215 copied from the original items (627 fitted parts), 35 at their own price.
```

**Bot *clothing* was a second miss, caught by re-deriving from the 3.x source.** `addClothingToBots`
(`collection.ts:536-566`) is separate from the gear weighting and from the tag system — it puts
garments into the weighted appearance pools bots choose from. Without it no bot wears any of the
136 clothing items, and with tags tabled it is the only path we have. Two bot types in the 3.x
list no longer exist in 4.0.13 and are dropped; `pmcusec`/`pmcbear` added, since those are what
PMCs are called now.

**Quests reference items by filename.** Under 3.x an item's id *was* its config filename, so
quest objectives and rewards say `"target": ["COMTAC4_BLACK_HEADSET"]`. 14 such references exist
across Part 1. They now resolve through the same derivation the item loader uses, validated
against the item table — so an ordinary string like `"HandoverItem"` is left alone because the id
it would derive to owns nothing.

**§6 global config options — done.** `config/config.jsonc`, all six options, verified by running
with non-default values rather than by reading the code:

```
[DRIP] Vanilla clothing: 91 outfits repriced to 40% of the original.
```

`UseDRIPTagSystem` and `vanillaclothing` dropped as tag-system options, per the schema. Names
normalised to camelCase and read case-insensitively, so 3.x PascalCase still binds. A missing or
broken config file logs once and falls back to defaults rather than failing the load.

Caught while testing: **the config file wasn't reaching the build output** — the SDK's default
globs cover `*.json` and would have missed a `.jsonc`, so DRIP would have silently ignored
whatever a player edited. Exactly the same class of bug as the original content-pack blocker, in
a place I'd have had no reason to look without running it. Fixed in the csproj.

**Self-check — done.** `DRIPVerificationService` runs on every load, ~20ms, seven assertions
each corresponding to a bug that actually reached us:

| Assertion | The bug it locks out |
|---|---|
| every item is sold by some trader | `no assort found` |
| no item shares its base item's model path | items created bundle-less, shipping as vanilla clones |
| every suit's offer id differs from its suite id | the two-ids-one-job bug |
| every quest handover/find target is an installed item | the Part 3 sling bag |
| every item has a non-zero handbook price | the 69420 placeholder |
| no two configs derive one id | collision guard, server side |
| every item has an English name that isn't its own id | locale transformer wiring |
| no two items share one model bundle | two configs in one folder rendering identically — the server-side half of Echo's duplicate-bundle-identity finding |

**Falsified rather than assumed.** A passing check proves nothing on its own, so each was made
to fail on purpose. Planting an item cloning a vanilla bag no trader sells tripped two
independent assertions at once, both naming the file; planting a second config in an occupied
folder tripped the shared-model check, naming both files and the bundle. Removed afterwards,
baseline re-confirmed clean.

The shared-model assertion is the server-side half of Echo's duplicate-bundle-identity finding.
The other half — 79 vanilla paths claimed by more than one DRIP bundle — is **not checkable from
here**: the server registers bundle keys and never opens the files. That is smoke test 6.7 and
stays a client-side question.

`CLIENT-SMOKE-TEST.md` rows are marked 🤖 where the self-check covers part of them, with the
residue spelled out. Deliberately conservative: 2.1 asserts *some* trader sells an item, not the
*same* one, and the marker says so. Overclaiming here would quietly delete a human check.

**Verified against the real deployed pack** (Echo's 365 repacked bundles, live configs — the
first run against the actual shipping configuration rather than my hard-linked test rig):

```
[DRIP] CustomLocales:  216 strings across 17 locales.
[DRIP] CustomItems:    140 new items.
[DRIP] CustomClothing: 136 new clothing items.
[DRIP] Bot loadouts:   1238 equipment / 255 loot / 10 attachment entries.
[DRIP] Bot appearance: 79 tops and 57 bottoms across 12 bot types.
[DRIP] CustomQuests:   19 quests, 5 icons, 15 item references resolved by name.
[DRIP] Trader offers:  217 copied (627 fitted parts), 35 at their own price.
[DRIP] Self-check passed (29ms).
```

**Zero DRIP errors, zero DRIP warnings.** The un-bootstrapped warning correctly stayed silent,
as Echo predicted. The ten `price: 0` notices are also gone, so the pricing pass has landed.
DRIP's whole load is 2.7s including hashing 3.1 GB of bundles.

Two things that only became visible with real bundles deployed, both recorded in
`UPSTREAM-ISSUES.md`:

- The remaining `Could not find manifest for mod DRIP Core` warning is **benign** — that is the
  manifest-driven path in `BundleLoader.LoadBundlesAsync`, which DRIP deliberately doesn't use.
  Programmatic `AddBundle` populates the same store the client is served from. Worth knowing so
  nobody chases it during the smoke test.
- **SPT's bundle hash cache never prevents a hash.** `CalculateMatchAndStoreHash` computes the
  full CRC32 before consulting the cache, so all 3.1 GB is read on every server start regardless
  of what changed. It roughly doubles with Parts 2/3 and is far worse on a mechanical drive. Not
  worked around on purpose — the CRC served to the client has to be correct, and a mod-side
  cache keyed on file metadata would be guessing at something the server should own.

**Bot appearance pinning — done**, for making 6.7 conclusive rather than suggestive.
`debugPinBotTop` / `debugPinBotBottom` in `config/config.jsonc`, named by config filename the
way everything else is. All three paths verified on a running server:

| State | Log |
|---|---|
| off | `Bot appearance: 79 tops and 57 bottoms across 12 bot types. Not pinned - bots roll normally.` |
| pinned | `Bot appearance PINNED ... exactly 1 top, TSHIRT_COLETTE_TOP (87c35f2b…) and exactly 1 bottom, GORKA4_BLACK_PANTS (c6265668…)` |
| bad name | `pin names the top "TSHIRT_COLLETTE_TOP", which isn't a top DRIP loaded ... REFUSED - nothing was pinned and no bot appearance was changed at all.` |

Alpha's three conditions are all in and all exercised. The pinned line reports the ids that
**actually landed in the pool**, not the config values. Absence is stated positively. Resolution
happens at point of use, after the 136 garments are registered. And in the refusal case the
*bottom was valid* — it was refused anyway, because a half-applied fixture has a name and looks
authoritative.

**Found a bug in my own config template while testing this**: I dropped the comma after
`debugNames` when appending the debug block, so `config.jsonc` was invalid JSON. The loader's
fallback caught it and named the line and column — the error handling earning its keep on its
author. Fixed.

**Bot escorts may never spawn, and it isn't ours.** Five of the twelve `ClothedBotTypes` are
boss escorts, and EFT's AI Amount preset rewrites escort counts client-side — on Medium the
arithmetic yields zero followers for bosses with a single-value escort amount. So ~42% of the
bot types this feature covers can silently never appear. Recorded next to the list in code,
because the natural reading of a quiet raid is "the feature works" and that would be wrong.
Test on High or AsOnline.

**Scavs are NOT in ClothedBotTypes - reverted, pending Sophia.** I added ssault on Echo''s
relay, then reverted it when her follow-up arrived: excluding scavs was never taste, it was a
workaround for a missing capability. This list is applied indiscriminately - every garment into
every bot type - so adding scavs as things stand also puts modern plate-carrier-era jackets on
them, which is exactly what the workaround prevented. Leaving ssault in would have shipped
the regression the exclusion existed to avoid.

The reasoning is recorded in full next to the list so the analysis is not lost: ~11 Part 1
garments genuinely are scav retextures, including a family named SCAVJEANS that no scav has
ever been able to wear. Scavs *should* be there; the list just cannot carry them yet.

The capability is derivable rather than annotatable, and it is Echo''s finding: a garment
belongs on a bot type exactly when the vanilla prefab it retextures is already in that bot''s
appearance pool. Same principle as copyOriginalOffers and updateFilters. It fixes every bot
type, not only scavs - a Gluhar follower can currently draw scav jeans. Not built; awaiting
Sophia, since it visibly reduces how much DRIP bots wear.

**Bot suitability derivation - done and matching.** A garment is offered to a bot type exactly
when the vanilla prefab it retextures is already in that bot's appearance pool, read from Tau's
`vanillaOrigin` field. Same rule as `copyOriginalOffers` and slot-filter inheritance. `assault`
is back, filtered.

```
assault 0/3   marksman 0/3   pmcbot 0/0    exusec 17/0   usec 27/23   bear 34/24
pmcusec 23/20 pmcbear 33/24  followerbully 3/0   followerkojaniy 9/5
followergluharsecurity 0/5    followergluharassault 0/0   followergluharscout 0/0
```

**Every cell matches Echo's independent measurement and a Python check run against the art
library manifest before any C# was written.** Three computations agree.

Per-item `botTypes` override exists from day one, as the escape hatch for the one assumption the
derivation rests on - that authors clone the base garment matching their intent. An empty list
means player-only, which is distinct from omitting the field.

**The 7 garments no bot wears are all boss retextures** - Black Knight, Birdeye x2, Zryachiy,
Shturman x3. Bosses are deliberately not clothed, so this is the derivation working rather than
failing: a garment whose original only Shturman wears should not turn up on a scav. They become
player-only.

**Two failures of mine worth recording:**

- The derivation silently returned **0 for every bot type** on first run, with no error.
  `CustomizationProperties.Prefab` is typed `object?`, so System.Text.Json materialises it as a
  `JsonElement` rather than the `Prefab` record the pattern match expected, and every vanilla
  pool read as empty. Only Echo's reference numbers caught it - "0/0 everywhere" reads as a
  plausible conservative result.
- I nearly deleted 136 correct `vanillaOrigin` fields. I had written scaffolding to inject them,
  found them already in the source tree, and inferred my script had contaminated the repo.
  Checking the mechanism first - different inodes, so no hard-linking, so my script *could not*
  have written there - showed Tau's converter had landed the field independently and my
  scaffolding had been a no-op from its first run. Acting on the inference would have destroyed
  their work and reported success.

**Missing-origin path - now falsified.** Stripped anillaOrigin from one config in the build
output and ran it:

`
1 garments have no vanillaOrigin, so DRIP cannot tell which bots should wear them and no bot
will: JEANS_BLACK_PANTS. Re-run the converter, or set botTypes on them explicitly.

assault 0/2, marksman 0/2, ...   (was 0/3, 0/3 - every other cell unchanged)
`

It alarms, names the garment, and the effect is exactly scoped: that one garment gone from
exactly the two bot types that would have worn it, nothing else moved. Restored and baseline
re-confirmed.

Worth doing because Sophia'''s no-de-novo-garments invariant makes this an **alarm rather than a
routine case** - for legitimate content it should never fire, which is precisely the kind of
check that rots unobserved. Every branch of this feature has now been watched to fail.

---

## Kappa-side Part 1 is functionally complete.

Everything from the 3.x mod is ported, except the clothing tag system, which is deliberately
tabled and belongs to ICUP. The remaining gate items are the bundle rebuild (Echo) and the client
smoke test, which cannot run until bundles render.

### Release gate — what Part 1 still needs

| Item | Owner | Why it gates |
|---|---|---|
| ~~`copyOriginalOffers`~~ | ~~Kappa~~ | **Done.** 215 offers copied + 35 own-priced; `no assort found` gone. |
| ~~Quests + locales~~ | ~~Kappa~~ | **Done.** 18/19 quests, 5 icons, 216 strings across 17 locales. The 19th is a content bug — see below. |
| ~~`includedParts`~~ | ~~Kappa~~ | **Done.** 627 fitted parts copied across the corpus. |
| ~~Bot weighting~~ | ~~Kappa~~ | **Done.** 1232 equipment + 255 loot + 10 attachment entries. Smoke test 5.3 is now runnable. |
| ~~§6 global config options~~ | ~~Kappa~~ | **Done.** All six ported and verified; two dropped as tag-system options. |
| ~~Bundle repack~~ | ~~Echo~~ | **Done and deployed.** This was the row that said "everything renders magenta until this lands"; the repack fixed the magenta without a rebuild. Re-verified against Base's vanilla assets: 365 bundles, 547 materials, 0 broken. |
| ~~Client smoke test~~ | ~~Sophia~~ | **§6 regression COMPLETE 2026-08-01.** 6.1 closed by 6.7's mechanism; 6.2 and 6.3 confirmed in a client; **6.4 pass on a dirty profile, profile MD5-identical afterwards**; 6.5 retired (no fixture — DRIP ships no plates); 6.6 closed statically across 17 locales, 0 collisions. |
| Converter guard for `bundles` is **wired and it refuses** | Tau | **Verified 2026-08-01. `--part 1` is SAFE to re-run.** `dependencies_at_risk()` (line 179) is called during conversion (932) and the run does a **full dry-run probe first**, then prints `STOPPED - nothing was written.` unless `--allow-dependency-loss` is passed. Nothing is dropped silently. **Echo asserted the opposite an hour earlier and was wrong** — worth keeping for the mechanism: I read the local variable `lost` in a grep result, *invented* the function name `lost_bundle_dependencies` from it, grepped for the name I had invented, found nothing, and reported the guard as dead code. **The absence of a name you made up is not evidence of anything.** Confirming a function is uncalled requires grepping for the name in the definition line, not the name you remember. Caught only because `--allow-dependency-loss` appeared in the CLI and contradicted the claim. **Confirmed by execution, not by reading:** a real `--part 1 --out <copy> --bundles link` against a byte-for-byte copy of the live Essentials output printed `STOPPED - nothing was written`, named **301 declarations across 222 files**, exited 1, and left all **653 files md5-identical**. The copy holds 554 paths; 301 are the ones this run could not re-emit. **Tau's classification, and it changes the remedy:** this is *not* another "a modelled field is not an implemented feature" — it is **a query that could not return a positive result**, where the zero was guaranteed before the code was ever a factor. The two look identical and pull opposite ways: the first says go implement a thing, the second says **re-point the instrument**. Reading it as the first would have had Tau building a guard that already existed. Same class as querying `assort.json` for a key that lives in `questassort.json`. **It happened twice in ninety minutes, in opposite directions** — Echo reported a live guard as absent by grepping a name that exists nowhere; Tau reported a fixed bug as live by calling `strip_json5` directly rather than the `read_legacy()` path the converter actually uses, which is where `repair_control_chars()` lives. Both were rigorous downstream of a wrong entry point, and neither error was reachable by reviewing the reasoning. |
| **Release gates remaining are Sophia's two** | **Sophia** | Neither is technical and neither is startable by anyone else. **Gate 1:** every public-facing word — README, forge description, docs — written by Sophia, not generated. **Gate 2:** Sophia reviews the code herself and demonstrates she understands what it does and can update it unaided. |
| ~~Bundle **rebuild**~~ | ~~Echo~~ | **Cancelled 2026-07-31 — all three justifications are gone, none of them needed Unity.** Duplicate identity: a bundle can be cloned with a **fresh CAB** (renamed serialized file, renamed `.resS`, stream refs repointed, pixel-identical) so new colourways cannot collide. Mipmaps: **argued down, do not do this** — see below. Size: **313 MB already recovered** by stripping duplicated geometry, no Unity involved. What still needs a Unity project is *custom meshes*, which Sophia has scoped out of the first release. |
| **Mesh strip — REVERTED 2026-08-15 (Sophia)** | ~~Echo~~ | **Strip reverted by Sophia's call ("a dumb decision to try and strip them") — the live bundles are broken and were restored from `DRIP-bundles-BEFORE-MESH-STRIP-2026-07-31`, all 653 files SHA-256-verified identical.** The pre-strip figure was 3.088 GB; the strip had taken it to 2.782. Configs went back to the pre-strip versions too, which drop the `bundles` dependency declarations the strip required — those were the only config difference (verified structurally across all 277 configs before restoring). **The stripped state is preserved at `DRIP-bundles-STRIPPED-STATE-2026-08-15`** if anyone wants to mine it; do not reinstall it without a new decision. Historical record of the strip: 294 of 365 bundles, 898 local meshes dropped. 71 bundles refused themselves for stated reasons; zero refused for ambiguity — matching on (GameObject name, component type) against vanilla's own holders resolved even `cr_commando_mesh`. |
| **300 declarations live in generated files** | **Tau** | **NEW, and it is the dangerous one.** Every borrowed-geometry bundle needs a `bundles` dependency in its config, and `convert-legacy.py` regenerates configs. A full conversion run silently drops all 300 — **294 items go invisible and the conversion reports success.** Root cause predates today: the converter drops `textureGearDependencies` believing "v2 discovers it on its own", and v2 does not. Fix is to derive it in the converter. **Coordinate before any full conversion until then.** |
| ~~First-run / bundle-less checkout~~ | ~~Tau~~ | **Done** (Kappa) — loader-side diagnostic landed. A written setup step in `AUTHORING.md` would still help. |
| ~~Load order — profile bricking~~ | ~~Kappa~~ | **Done and verified on a running server.** Moved to `PostDBModLoader + 2` (400,002), before profile validation at 700,000. Fixed two latent bugs on the way (trader resupply, static flea prices) and cost us Fence's generated assort — see below. |
| ~~Quest completion — trader aliases in rewards~~ | ~~Kappa~~ | **Done, confirmed in the client.** No DRIP quest could be completed; a hard 500 on `items/moving` desynced the whole UI. See below. |
| ~~Flea presets — armour arrives unwearable~~ | ~~Kappa~~ | **Done and deployed.** 62 presets created, all 62 clear SPT's own gate. Client confirmation of a wearable flea-bought armour is the remaining half, and is smoke test. See below. |
| **Bundle dependency not declared** | **Kappa** (C# half) / ~~Echo~~ (Python half **done** — `check_deps.py`, 437/437 declared, falsified 4 ways) | **Does not gate.** `DRIPBundleService` registers sibling bundles but does not make `GEAR.bundle` *depend* on them, so the client never loads the file holding the material. Fixed the four half-masks, confirmed in the client. **The base rate went through three wrong values before anyone opened a bundle — see below for the derived one.** Worth building as a C# load-time check; the deeper reachability version needs UnityPy and belongs in `tools/bundles/`. |
| ~~Stale mesh pointers~~ | ~~Echo~~ | **Done, confirmed in the client 2026-07-31.** All 49 repointed and verified end-to-end against the shipped game (49/49 resolve, 49/49 land on a mesh named after the GameObject asking for it). The planned vertex-count tiebreaker would have failed silently — every name has exactly two candidates and three of four pairs have identical vertex counts. Holder **type** is what disambiguates. |
| ~~White helmets / magenta half-masks~~ | ~~Echo~~ | **Done, confirmed in the client 2026-07-31.** Two unrelated causes under one symptom: the half-masks needed a `bundles` dependency declared; the helmets needed an externals-table entry repointed *as well*. 24/24 texture pointers now resolve, was 9 dangling. |
| **"16 dead externals" was wrong** | **Echo** | **Corrected, not a gate.** 4 of the 16 were live DRIP siblings; `audit_refs.py` built its CAB index from the game only, so every DRIP→DRIP reference read as dead **by construction**. Real figure 12. The companion number, 54 renderer-material dangling, was *correct but unearned* — 24 pointers were silently skipped by an early return. **One bug, two figures, wrong in opposite directions.** |

---

### Parts 2 and 3 — converted and through the whole bundle pipeline (Echo, 2026-08-01)

Sophia's call: convert both and make them installable. They stage at **`Mods/DRIP/staging-repacked/`**,
deliberately outside every path the loader walks, so nothing here can disturb the Part 1 install.

| | Part 2 | Part 3 |
|---|---|---|
| items converted | 136 | **132** (from 133 sources — `SLING_OLIVEDRAB_BAG` is promoted to Part 1) |
| bundles | 182 | 184 |
| final size | 1,489 MB | 1,415 MB |

**2,904 MB from 3,211 MB of source — 307 MB recovered**, on top of Part 1's 313.

**The order of operations is the thing to keep, because getting it wrong reports success.**
`remap_refs` rewrites *pointers* and can only act when the externals table already names the right
bundle; `repack_all` rewrites the *table*. Running remap first repointed **0 of 1440** and reported
861 `cab-not-in-externals` — correct behaviour, and it would have read as "nothing to fix" to
anyone not expecting a number. Correct sequence: **repack → remap → derive → strip → verify.**

```
unresolved pointers      1440 -> 0      (positive control: same grep still hits on the pre-repair tree)
externals -> nothing     1025 -> 33
declared dependencies      13 -> 456, all 456 verified by the independent checker
meshes stripped           844, 298.6 MB, ZERO ambiguity refusals
```

**`check_deps.py` found the Part 1 bug families in content it had never seen**, statically, before
any client was involved: 1 FAST MT helmet in Part 2 and **11 half-masks in Part 3**. That reframes
the Part 1 evening — the magenta half-masks and the white helmet were not two incidents, they were
**the first two instances of a class**, and the class recurs in every pack. That is a much stronger
argument for the derivation approach than 13/13 was.

**NEAR MISS, and the check took thirty seconds.** `convert-legacy.py --bundles link` **hard-links
the staged bundles to `DRIP-3.x-main`**. `remap_refs --apply` and `strip_meshes --apply` write **in
place**. Running either against `staging/` would have written straight through the shared inode into
the 3.x reference corpus — the tree this table forbids mutating, and the fallback if any of this
goes wrong. `fsutil hardlink list` showed two links per bundle. Doing the repack first was already
correct for other reasons and also breaks the links (1 link each afterwards, legacy byte total
unchanged at 6,678,190,651 before and after). **Also: never overwrite a hard link in place** —
`Copy-Item` onto one writes through it. Configs were copied *into* the repacked tree rather than
bundles into the linked one, for exactly that reason. Same class as Kappa's 136-field near-deletion:
the layout looked fine, the mechanism was the thing to check.

**Blocked on content, not on tooling.** Both packs carry one hard-error ID collision each —
`INFILTRATOR_NIGHTGREY_PANTS` (Part 2, TOP vs BOTTOM, different content) and `TSHIRT_KHAKI` ×2
(Part 3, different prices). These queue with Colette and Amber alongside pricing. A filename-detritus
sweep across all three parts found nothing new in 2/3: the only editor artefact is Part 1's known
`COMBAT_PANTS_URBANREED_BOTTOM - Copy.json5`, and the only duplicate stems are those two collisions
plus Part 1's `DRIP.json5` quest/locale pair.

**Two counts that must not be reconciled**, Tau's, and both are load-bearing:
Part 3 is **133 source configs and 132 emitted items** — one promoted, not one lost. And Part 1's
**277 in / 277 out is a coincidence of offsetting terms**, not a pass-through: 275 items + 1 quest +
1 locale in, 276 items + 1 quest out. Compare by relative path, never by stem — two Part 1 sources
share the stem `DRIP`, which collapses any stem-keyed comparison and would hide a genuinely missing
item.

**INSTALLED AND LOADING CLEAN, 2026-08-02 06:02.** All three packs in `SPT-DRIP-Test`, **zero load
errors** — the only two `[Error]` lines in the run are the self-check header and its one remaining
item.

```
[DRIP] Essentials: 140 items + 136 clothing   Part2: 65 + 69   Part3: 66 + 61
[DRIP] Inherited compatibility for 271 items: 6 slot filter entries, 933 conflict entries
[DRIP] Bot appearance: bear 76/46, pmcbear 75/46, usec 52/40, pmcusec 46/36, exusec 40/0 ...
[DRIP] Trader offers: 215 copied (500 fitted parts), 73 at their own price
[DRIP] Flea presets: 109 created for 271 items
[DRIP] Self-check found 1 problem: 28 no trader sells
```

**Verified by reconciliation, not by "it looks fine".** Every figure moved by exactly what was
removed: items 274→271, own-priced 76→73, presets 112→109 — all −3, the three BANSHEE armours.
Clothing failures 2→0. And the clothing *success* counts did not move (69 and 61 both runs), so
quarantining cost no working garment. `140+65+66 = 271` and `136+69+61 = 266` close exactly.

**The one remaining self-check problem is the pricing queue, not a defect.** 28 items whose vanilla
base no reachable trader sells, so `copyOriginalOffers` has nothing to copy — up from 13 with Part 1
alone. A further **11 are quest-locked-only**, which the loader treats as deliberate and explains in
place: copying a quest-locked offer would make gated gear freely available. Those stay lootable and
bot-wearable.

**Eight items quarantined to `Mods/DRIP/staging-quarantine/`** with a README explaining each, all
restorable by moving them back into both trees. Every one is a **content decision**, not a tooling
failure: two ID collisions, one config declaring a bundle that does not exist, and the three BANSHEE
armours that arrive from Fence with empty soft-armour slots. See that README before restoring the
`INFILTRATOR_NIGHTGREY` pair — it needs **two** fixes and Echo got the first one backwards.

**Still not done for 2/3:** no client has rendered either pack. The mesh strip was eye-verified for
Part 1 (Sophia caught an invisible balaclava in seconds); the same confirmation has not happened
here, and the server cannot provide it — 456/456 declared dependencies says the client will be
*told* to load the right bundles, not that anything renders.

### No DRIP quest could be completed — trader aliases survived on rewards (2026-07-31, fixed)

Accept a quest, hand in the items, press complete: the client wedged. Trader tabs stopped
responding and exiting to menu did not clear it. Found by Echo and Sophia in a live client
session.

The server threw `ObjectId must be a 24-character hex string (Parameter 'georgia')` inside
`RewardHelper.ApplyRewards`, reached from `/client/game/profile/items/moving`. That route is the
item-event router, so a 500 there desyncs *everything*, which is why the symptom looked like a
trader bug several screens from the cause.

`ResolveTraderName` rewrote a quest's own `traderId` and nothing else. Trader ids also live on
**rewards**, and all 19 of Part 1's kept the literal alias — 15 `moron`, 4 `georgia`, all
`TraderStanding` or `TraderUnlock`.

Why nothing caught it earlier: `Quest.TraderId` is a `MongoId`, so an unresolved alias there
fails at bind. `Reward.Target` is a plain **string**, so `"georgia"` binds cleanly, loads
cleanly, and sits in the database looking correct until a player presses complete. The strong
bind is a convenience, not a safety net.

Resolution is now **reward-type aware**, and that is not caution — it is required.
`ApplyRewards` casts `Reward.Target` to a MongoId at three sites, and the third is
`AddAchievementToProfile`, where `target` is an *achievement* id. `target` is also an item
template on `Item`, a pocket template on `Pockets`, and a skill *name* on `Skill`. Resolving
every target would have silently rewritten all of those.

The table of which reward types carry a trader lives in `DripTraders.TryGetTraderField`, once,
because the loader and the self-check both read it and two copies would drift. Each entry
records its provenance: `TraderStanding` and `TraderUnlock` are proven from the IL;
`TraderStandingReset`/`Restore` are by name and by vanilla data (4.0.13 has no branch for
either); `AssortmentUnlock` carries its trader in `traderId`, not `target`, per 236 vanilla
rewards.

Two things worth keeping:

- **All buckets, not just Success.** Vanilla docks standing on failure. A check that only looked
  at `Success` would have left the identical crash waiting behind a failed quest.
- **An unresolvable alias now rejects the quest at load**, naming file, quest, reward type and
  bucket. A quest that loads and bricks the client on completion is strictly worse than one that
  never loads.

New assertion `VerifyQuestTraderReferencesResolve` re-derives from the built database and catches
the case the loader structurally cannot: a syntactically valid 24-hex id for a trader nobody
installed.

Both halves were watched to fail before being trusted. `"georgai"` → loader rejects, 18 quests,
1 failed. `"aaaaaaaaaaaaaaaaaaaaaaaa"` → loader passes it (valid hex), verifier catches it. That
second one is also what makes the clean result *positive* rather than merely quiet: the verifier
reports zero across all 19 references and demonstrably fires when one is bad, so the aliases are
genuinely being rewritten. Confirmed in Sophia's own client afterwards — four `items/moving`
calls, no fatals, quest icons advancing Boozey → Drunkard → MaterialHandler.

**Not the cause, though it was suspected:** Echo retyped 143 `value` fields from JSON strings to
numbers. SPT registers a `SafeDoubleConverter` that falls back to `GetString()` +
`double.TryParse`, so strings bound into `Reward.Value` fine all along. The change is an
improvement in form; rule it out as a suspect.

### Six items looked like one bug and were two — and the count matching the rule is what made it feel finished

Echo's sentence, and the one to keep: *the half-masks needed a dependency declared; the helmets
need that **and** an externals entry repointed. Same symptom class, same missing `bundles` block,
unrelated underlying faults.*

Kept in full because the *number* is minor and the *shape* is not. Sequence, over five messages:

1. Echo: "6 directories hold more than one bundle and declare no dependency; 101 declare one" —
   and both render bugs are fixed.
2. Kappa: endorsed it, called it "a defect 6 times out of 6" and "a perfect base rate", wrote it
   into this file, **without opening a bundle.**
3. Echo: retracted — 4 of 6, the helmets are a different bug, the directory rule is "right by
   accident".
4. Echo: retracted the retraction, having opened the binaries a third time — the helmets' pathIDs
   *do* match their siblings, so the dependency is genuinely missing on all six.
5. Kappa: opened the binaries, confirmed the helmet claims, and derived the denominator.

**Final answer: the numerator was true all along and the denominator was never asked for.** 6 of
6 stands. That does not rescue step 2 — endorsing a true claim you have not derived is worth
exactly what endorsing a false one is worth, and "it arrived as a number" is why it felt safe.

**Derived from the tree on 2026-07-31, which nobody had done:**

| | count |
|---|---|
| directories containing at least one bundle | 276 |
| of those, holding **more than one** | **88** |
| of the 88, already declaring a dependency | **86** |
| of the 88, declaring none | **2** — `HELM/AIRFRAME/RANGERGREEN`, `HELM/FASTMT/USEC` |
| single-bundle directories declaring one anyway | 19 |

The denominator was never 6. It is **88**, and the argument for the check is not "6 of 6" but
that **86 multi-bundle directories already do the right thing** — a rule that stays silent on 86
real cases and fires on exactly the two known-broken ones. Echo's "6" was a pre-fix snapshot that
no longer exists (the four half-masks now read DECLARED, which is their fix, not the original
state).

**The 101-vs-86 gap: re-derived by both of us independently, digit for digit, and it is forced
rather than narrated.** It was left unreconciled on purpose for one exchange — a tidy story is
what we keep getting caught by — and then measured:

```
configs with a top-level 'bundles' key   105
   in the 86 multi-bundle directories     86
   in the 19 single-bundle directories    19      86 + 19 = 105 exactly
   directories with >1 declaring config    0      so config-count == directory-count
   configs that failed to parse            0
```

Echo's "101" was 105 minus the four half-mask configs, measured before those blocks were added;
their "6" was 2 plus the same four. Both stale by exactly 4, in opposite directions, from a
single edit: `101 + 4 = 105` and `6 - 4 = 2`, nothing left over. Two identities forced by one
measurable cause. Had it come out 103 there would have been a real problem.

The lasting point is not the arithmetic: **the counts were never wrong so much as counting the
wrong noun.** A *directory* is what the loader iterates and what an author edits; a *config* is
neither. Same failure as measuring the right thing over the wrong population, done to the
numerator instead of the denominator.

### Two rules, two severities — neither subsumes the other

Settled with Echo, and the reason the second cannot replace the first was **measured, not
argued**:

| | GEAR externals | sibling publishes | in externals? |
|---|---|---|---|
| HALFMASK SMILE1 | `7e182162…` `92f73786…` `1dc8d26b…` `bbf13a8c…` | `CAB-7e182162…` | **yes** |
| AIRFRAME | `56d919bd…` ×2 `4d8a4131…` `c4ae8b76…` | `CAB-545fb848…` | **no** |
| FASTMT | `56d919bd…` ×2 `4d8a4131…` `b9d9f8e1…` `c4ae8b76…` | `CAB-618fd314…`, `CAB-607fe1c2…` | **no** |

So an externals-based rule fires on the half-masks and is **structurally blind to the helmets** —
their GEAR tables still name the vanilla CAB, so the check inspects the wrong entry and reports
clean. It detects the *wired* state, not the broken one that shipped. A false negative on the
exact defect that reached a player is more dangerous than a false positive, because the false
positive gets argued about and the false negative gets trusted.

- **Directory shape** — more than one bundle beside a config, no `bundles` block. Catches both
  classes including the un-wired state. 6/6 real, 0 false positives across 86 declaring
  directories. Recall is the point. → **warning**, eye-catching, and it must **name the line to
  add**, not just the problem. It must not promise a fix: declaring the dependency *fixes* a
  half-mask and is necessary-but-insufficient on a helmet, and a check that says "add a bundles
  block" would send the next person round the loop Echo went round on 2026-07-31.
- **Externals cross-reference** — a bundle whose externals name a sibling CAB absent from its
  `DependencyKeys`. Cannot false-positive by construction; misses anything not yet wired. →
  **assertion**. This one is definitely broken, not "did you mean to".

Homes: the directory rule can be a C# load-time check (filesystem and config only). The externals
rule and any reachability check cannot — **the server never opens bundles** — so they belong in
`tools/bundles/` beside `audit_refs.py`, with `drip check` as the authoring-side home. Kappa
argued for putting the reachability version in the self-check without first checking what the
self-check can see.

Split agreed: **Kappa takes the C# directory check, Echo takes the Python externals/reachability
check.** Sophia greenlit both on 2026-08-01. Her conditions already on record are that it names
the line to add and that `drip check` is the better home for the authoring case.

**Echo's half is done: `tools/bundles/check_deps.py`, and the live pack passes clean.**

```
437 pointer-backed dependencies, 437 declared, 0 undeclared
117 declared but not pointer-backed  (NOT a defect -- see below)
```

**It is pointer-driven, not externals-driven, and that is the design decision.** An externals
table can name a bundle no pointer uses — leftovers from the vanilla bundle these were cloned
from. Treating every externals row as a dependency reports non-dependencies, and a check that
cries wolf on real content gets switched off. So it walks the pointers and asks what each one
needs; a row nothing points through is not reported.

**The 117 are the load-bearing output.** They are declarations no pointer backs — `skeleton.bundle`,
`bear_hands_watch_texture.bundles` — which is exactly the population `derive_deps.py` would have
deleted from 85 configs. The check reports them under a heading that says *do not remove these*.
The two tools are complementary by construction and **share no code on purpose**: derive to fix,
check to catch. A checker that calls the generator can only confirm that the generator did what
the generator does.

**Falsified before being trusted**, four states:

| planted | result |
|---|---|
| a real declaration removed | 0 → 1 undeclared, naming the config |
| a spurious declaration added | stays 0 — cannot false-positive |
| restored | back to baseline |
| restored | **byte-identical to the original** |

The fourth assertion exists because the first three can pass while the file is quietly damaged:
the selftest rewrites a live config, and a `utf-8-sig` read with a `utf-8` write drops a BOM. The
parse-level check says the file *reads* the same; only the byte compare says it *is* the same.

**One invocation trap, worth knowing before anyone reads a result.** The game root is
`StreamingAssets/**Windows**`, not `StreamingAssets`. Pointing it one level too high prefixes
every game path with `Windows/`, nothing matches `DefaultDependencies`, and it reports
**1027 of 1034 undeclared** — a confident, catastrophic, entirely false result. It was obviously
wrong only because 294 of those bundles are known to render.

Wording that survived the night, and the second clause is the load-bearing one:

> *N bundles here, no dependency declared — if one reads from another, declare it; if nothing
> does, ask why the extra bundle ships.*

"Add a bundles block" would have walked the next person through Echo's exact evening. Pointing at
the question rather than a remedy is what would have caught the helmets honestly.

**`audit_refs.py` index bug — found and fixed by Echo 2026-07-31.** It built its CAB index from
the game only, so every DRIP→DRIP reference read as a dead external *by construction*. Two
figures this file has quoted were wrong, **in opposite directions**:

- **"16 dead externals" was overstated.** Four were live pack siblings. Real figure **12**.
- **"54 RendererMaterial dangling" was correct all along, but for the wrong reason.** The old
  `check()` returned early on any CAB the game did not publish — so 24 pointers were never
  evaluated at all, rather than evaluated and passed. 78 was printed as the denominator while 54
  were examined. The coverage number was honest and the work behind it was not.

Echo pre-registered both numbers; the dead-external prediction hit and the RendererMaterial one
missed, and **the miss is what exposed the early return.** A hit would have left it in place.

Arithmetic now closes: **78 external `Renderer.m_Materials` pointers = 54 genuinely dangling + 24
resolving into pack siblings.** Independently re-derived by Kappa without using the tool's
classification — walking the 365 pack bundles, indexing every CAB the pack publishes, and
counting pointers directly — because a number produced by a just-changed tool, verified by that
same tool, is the instrument confirming itself. 78 / 24 / 54 reproduce exactly.

That run also closes a caveat Echo correctly refused to close: their output caps at 12 rows, so
they could see SMILE1–3 go and inferred SMILE4 from the count. Printing all 24 rows shows **all
four half-masks, six pointers each, all same-directory, all pathIDs resolving.** Observed, not
inferred.

Still wrong in the tool, named not fixed: `4 bundles with renderers but NO material (defect)`
counts materials *in* the bundle, so it still calls the half-masks defective when their material
ships one directory away and renders correctly in the client. True as written, wrong as read —
the same shape as "16 dead externals". Echo is fixing the wording alongside the helmets.

The tool now prints, on the sibling section: *resolving here means the pathID exists; it does NOT
mean the client loads it — that needs a `bundles` block and is not checkable here.* That
distinction is the whole content of 2026-07-31 and belongs in the tool rather than in anyone's
memory.

The helmet claims *were* checked against the binaries this time, and both hold:

- **AIRFRAME** — 12 texture pointers, 6 in-bundle, 6 external. Its own shell and rails materials
  resolve **in-bundle**; only `helmet_ops_core_fast_skeleton_shroud_tan_LOD0` points out, on
  externals slot 4, and all three pathIDs (`927251609553180867`, `3661562064799088673`,
  `-2623046207124936636`) are present in the sibling `TEXTURE.bundle` by exact match. That slot
  is used by nothing else. **One externals repoint from correct**, and the white part being the
  NVG shroud only is exactly Sophia's report.
- **FASTMT** — **zero in-bundle texture pointers**; all 12 are external. Slot 5 carries 6
  pointers (shroud + rails), all found in `TEXTURE2.bundle`. Slot 4 carries the main shell
  material and its three pathIDs are **in no sibling at all** — `TEXTURE1.bundle` holds DRIP's
  retextured shell under *different* pathIDs, so `TEXTURE1` is currently unreachable by any
  pointer or externals entry. **One repoint plus one genuine remap.**

So the two helmets are not the same shape as each other either, which is the fourth distinct
story these two items have produced in one evening. Nothing is being applied to them tonight.

### Own price + required slots + no `includedParts` = buyable and unequippable (built, awaiting a free box)

Echo and Sophia's, and **the only check here written before the bug rather than after it.**

A trader offer gets children exactly two ways: `copyOriginalOffers` brings them with the copied
offer, or `includedParts` fits them explicitly. An own-priced item whose base has required slots
and which declares neither ships a bare shell — it appears in the trader's list, it costs money,
it will not go on, and nothing errors.

**It flags nothing today. That is its success condition.** The comment at the declaration says so,
because a quiet check with no explanation is one somebody deletes in six months.

Where it earns its place is the **13-item reprice worklist**. Those items are on that list
*because* no reachable trader sells the original, so an own price is their only route — and the
split, derived from the server's own worklist rather than from a config sweep:

```
reprice worklist                                              13
   base has NO required slots (safe to reprice alone)          1   HELMET_TKHEAVYTROOPER_BLACK
   required slots AND already declares includedParts           0
   required slots and NO includedParts                        12   <- unwearable if priced
```

Twelve items become unwearable in one edit if prices are set and nothing else. Ranges from 2
required slots (SLICK ×5, TacTec ×4) to 8 (THOR Integrated). Echo's 10/8/2 census of *currently*
own-priced items was taken while the two helmets were temporarily priced for a render test; on
the reverted tree it is 8/8/0, which agrees.

**Derived from the built assort, not from the configs.** The config version answers "did the
author write `includedParts`"; this answers "does the thing on sale have its parts", which is the
actual question, and it also catches a `copyOriginalOffers` that copied nothing or an
`includedParts` that resolved to nothing.

**It reports and does not repair,** by decision. The vanilla default preset would fill all 12
exactly — one preset per base, no ambiguity — but that preset carries ballistic plates (the
THOR's come to ~618,000 roubles), so auto-filling silently decides whether every purchase ships
free plates. Balance call for Colette and Amber; not a default for a verification pass to pick.
Sophia's DX question about not hand-typing item ids sits with Tau, and the schema shape is theirs.

### Flea offers for armour are unwearable — no default preset (built 2026-07-31, not yet deployed)

Sophia's find. DRIP armour bought from a **trader** arrives with its soft armour and plates; the
same item bought on the **flea** arrives with empty required slots and cannot be equipped.

Only one of the two paths was ever implemented. Traders work by accident of
`copyOriginalOffers`, which copies the original offer's children. The flea copies nothing — it
builds armour offers from `globals.ItemPresets`, and DRIP never wrote to that table, so a clone
had no preset and the flea emitted a bare root.

Three requirements, read out of 4.0.13 rather than assumed, each easy to get wrong and none
visible from the JSON:

1. `RagfairAssortGenerator.GetPresetsToAdd` reads `ragfair.json`'s
   `dynamic.showDefaultPresetsOnly` (true by default) and takes `PresetHelper.GetDefaultPresets()`.
2. The equipment half filters on
   `preset.Encyclopedia.HasValue && itemHelper.ArmorItemCanHoldMods(preset.Encyclopedia.Value)`
   — it tests **`_encyclopedia`, not the root of `_items`**. That field is what decides whether a
   preset reaches the flea at all, and it must name the DRIP item.
3. `GetDefaultPresetsByTplKey` keys on `_items.First().Template` and `GetBaseItemTpl` finds the
   root by `_id == _parent`. The root must stay first; `_parent` must point at it.

Timing is fine as-is: presets are cached at `PresetCallbacks` (900,000) via
`PresetController.Initialize`, and DRIP writes at 400,002.

Population, re-derived from disk and matching Echo's independently: **140** DRIP items with a
vanilla base, **62** whose base has a default preset, **59** of those with required slots (8
declaring `includedParts`, 51 declaring nothing), over **25** distinct base items, each with
exactly one preset. Required-slot range is **2 to 9** — the top is IOTV Gen4 Full Protection Kit
MultiCam, not Zabralo at 8.

`DRIPItemPresetService` clones each base's default preset onto the DRIP item: preset id from
`SHA1(stem:preset)`, every child id from `SHA1(stem:preset-item-N)`, `_encyclopedia` and the root
`_tpl` set to the DRIP item. Children are re-idded rather than cloned verbatim, so DRIP's preset
and the vanilla one do not share item ids inside the same table. Derived, never generated — a
preset id that moves between builds is the bricked-profile failure with a different label.

It **asserts** the root is first rather than assuming it, and skips loudly if not: a preset
registered against the wrong template would sell the *wrong armour*, which is worse than the bug.

New assertion `VerifyArmourHasAFleaPreset`, re-derived from built globals. Honest scope: it
proves every item whose base has a preset has one of its own and that the root names the right
item. It does **not** prove the offer is wearable in game — that is smoke test material.

**Pre-registered before running**, so the log either matches or there is something to explain:
`62 created, 78 skipped, 0 failed`, self-check back to its one known problem. Supporting: 0 of
the 62 base presets have their root anywhere but first; 0 id collisions among themselves, against
vanilla item tpls, against DRIP item ids, or against existing preset ids.

Two scoping calls, both open to reversal:

- **Generates for all 62, not the narrower 59.** The extra 3 have no *required* slots, so they
  are "less complete than vanilla" rather than unequippable. Matching what vanilla sells beat
  encoding my own reading of which slots matter; SPT's own gate ignores any that don't qualify.
- **`includedParts` is not consulted.** It is a trader-assort concept here, and repurposing it
  for presets is a config-semantics decision for Tau and Colette. Echo measured what deferring it
  costs, so it is bounded rather than open: 10 configs declare `includedParts` (8 of them within
  this table's 59); 6 are byte-identical to the vanilla preset's children, and **4 differ in
  exactly one slot, `Soft_armor_back`** — BNTI Zhuk-6a Black and the three Crye AVS MBAV
  variants. Same armour class, same durability, differing only on colliders and one pair 0.02
  apart on blunt throughput. The sentence for Tau and Colette is *"the same item covers slightly
  different hitboxes depending on whether you bought it from a trader or the flea"* — invisible
  to a player without the stat panel, since both inserts are called "Aramid insert", which is the
  argument for writing it down rather than against.

Cross-checked against Echo's `tools/flea-preset-population.tsv`, derived independently: **0
mismatches** across all 59 rows on base tpl, source preset id and child count, and 0 rows in
their table that this generator would miss. Their `preset_parent_is_root` column tests
`Id == preset.Parent` while the loader tests `Items[0].ParentId is null` — two different
conditions, both true on 59/59, which is worth more than either alone. The 62/59 divergence is
exactly three all-optional-slot items (`HEXATAC_VZ95_ARMOR`, `RIG_PLATEFRAME_FLECK`,
`RIG_PLATEFRAME_USEC`): **59 is the population of the bug, 62 the population of the fix.**

**Deployed and verified 2026-07-31.** Prediction hit unaltered: `62 created for 140 items`, 78
skipped, 0 failed, self-check back to the 13 unsold, zero fatals. Re-confirmed on a second run
after Echo reverted two helmet configs — the counts are independent of that change, but the tree
moved under a verified result, and a result whose inputs changed afterwards has to be re-taken
rather than argued about. All **62 of 62** pass SPT's own
`ArmorItemCanHoldMods` gate — which is `IsOfBaseclasses(tpl, {Headwear, Chest rig, Armor})`, and
a DRIP clone inherits its base's `_parent`, so the chain is the base's chain. The gate says False
on controls (Roubles, Pack of nails), so 62-of-62 is a result rather than a predicate that always
agrees. Both new assertions were watched to fail first: mistargeting the first preset and
registering nothing past the 40th produced `22 missing` and `1 mistargeted` exactly.

Server-side chain is closed: registered → passes the equipment filter → `GetDefaultPresets` →
`GetPresetsToAdd`. The last link — an offer rendering wearable in the client — is smoke test.

### Pricing: DRIP armour is priced at about a third of what its preset is worth

`generatePresetPriceByChildren` is `true`, and the effect is large. **The first figure measured
was wrong and the way it was wrong matters more than the number.** Summing children from
`prices.json` gave a tidy +39% — but **287 of 354 preset children have no `prices.json` entry**,
so that summed 67 children and called it 354. Twenty-three items showed a x1.00 multiplier,
every one of them an item whose children all priced at zero. Ask what the denominator is before
believing a clean percentage.

With the handbook fallback SPT actually uses (`useHandbookPrice: true`) every child prices, and
the corpus splits into two populations that must not be averaged:

| Population | Items | Before | After | Median multiplier |
|---|---|---|---|---|
| Base has a **flea** price | 57 | 4,974,810 | 13,227,527 | **x2.58** (x1.77 – x3.42) |
| Base has **only a handbook** price | 5 | 46,207 | 2,008,630 | x46.55 (x20.0 – x55.3) |

**The 57 are the answer for Colette and Amber: median x2.58, tight range, no outliers.**

The 5 are a *finding*, not a pricing story, and were nearly reported as a x46 average: their
bases have no `prices.json` entry at all, so the "before" is a handbook number that was never a
flea price — two different quantities. They are `ARMOR_6B43_BLACK`, `ARMOR_6B43_FLORA`,
`ARMOR_THORINT_BLACK`, `AIRFRAME_RANGERGREEN_HELM` and `FASTMT_USEC_MESH`. THOR's inserts and
plates alone come to ~618,000 against an 11,375 handbook base. Two of the five are the helmets
being watched for the texture fix, so their price will look odd for a reason that is not a bug.

Caveat: this is a **static estimate of what the children are worth**, not an observed offer
price. SPT applies `priceMultiplier: 1.5` and other adjustments on top and no generated offer was
inspected. Read x2.58 as "the value the presets add", not as a sticker price.

---

## Tau — DX

**Landed:** `CONFIG-SCHEMA-v2.md`; `drip-item.schema.json`; `VALIDATION.md`;
`tools/convert-legacy.py` with per-file conversion reporting; `.vscode/settings.json`;
`drip.cmd`; `tools/drip.py` (`check`, `new`, `--path`); `AUTHORING.md`;
`tools/test-fixtures/pre-v2/`.

**The 275 are landed** in `bundles/ContentPacks/Essentials/` — configs, quests and locales,
no bundles. `drip check` over the live corpus: **0 errors, 11 warnings** (1 × `DRIP-200`
bundle-less checkout, 10 × `DRIP-307` `price: 0`). No old-format files remain in the pack.

Three superseded files removed, each only after confirming its replacement existed:
`COMMANDO_BARVIKHAPROTO_BOTTOM.json5`, `hellomilfy.jsonc` (the real item is
`DAYPACK_HELLOMILFY_BAG.jsonc`, from the legacy corpus), and `CustomQuests/DRIP.json5` —
which would otherwise have been **double-loaded** alongside its converted replacement, since
the differing extension meant nothing overwrote it. `drip check` now scans `.json5` too, and
raises `DRIP-112`, so that can't recur silently.

The two pre-v2 configs are kept as `drip check` fixtures in `tools/test-fixtures/pre-v2/`,
outside every path the loader walks.

**Bundle-less checkout (`DRIP-200`) is implemented**, judged by *proportion* rather than
`bundles.Count == 0`. The zero-check does not fire: four bundles are tracked in git from
before `.gitignore` covered them, and those four are enough to make the pack look populated.
Regression-tested both branches — a populated pack with one bundle missing still raises a
per-item `DRIP-201` and no pack-level message. Kappa has the detail for the loader side.

**Pack-level preconditions generalised.** Bundles and traders are the same failure shape —
one missing thing, every item fails for it — so they're one piece of work, written up in
`CONFIG-SCHEMA-v2.md` §8 rule 6 as *diagnose the precondition, not each of its consequences*.
`DRIP-400` covers a pack whose items sell through DRIP traders that nothing defines: one
message naming the traders and the count, instead of 136 identical lines. Vanilla traders are
excluded, since they need nothing shipped alongside. Verified both ways against the live pack
— with `CustomTraders` present it stays silent; with it removed, one message reporting 272 of
275 affected (the 3 `fence` items correctly excluded).
`PackPreconditions` in `VALIDATION.md` §5 has both checks in one place for the loader side.

**Diagnostic codes added since the catalogue was first written:** `DRIP-200` (pack-level
bundles), `DRIP-400` (pack-level traders), `DRIP-307` (`price: 0`), `DRIP-112` (old-format
file present).

**Conversion validated end to end:** Kappa has 275/275 Part 1 items loading on a running
server — 139 gear, 136 clothing, zero errors, zero warnings — against the converted corpus.
The schema, the converter and the runtime agree.

**Price proposal drafted** — `docs/PRICE-PROPOSAL.md`, for Sophia to accept or reject.
Nothing applied; the ten configs still say `price: 0`. Eight of the ten are not estimates:
their families charge one flat price for every variant, so the proposal is what their siblings
already cost. The two `GORKA4` items needed a judgement call — that family ladders price by
profileLevel (7 -> 45,000, 13 -> 70,500, 18 -> 95,000) and both blanks sit at level 10, so the
obvious family-median approach would have priced them at 95,000, the level-18 rate, 64% too
high. Interpolated to 57,500 instead.

Two things in there want a decision rather than a number: all ten are locked behind the same
quest `DRIP_12` and nothing else in Part 1 is, and nine sit at profileLevel 10 which is
otherwise unused in three of the four families involved. Both are consistent with one batch
built from a shared template — in which case the placeholder may not have been only the price.

**Price review tooling — built.** `Review Prices.cmd` (double-click), `tools/price_review.py`,
`tools/xlsx_lite.py`, `docs/REVIEWING-PRICES.md`. Exports all 171 priced items to a formatted
spreadsheet grouped by set, with each item's siblings alongside it so a price is judgeable
without opening anything else; reviewer edits one yellow column in Excel; re-running shows a
full before/after list and asks before writing. No terminal, no JSON, no install step —
`xlsx_lite` is a hand-rolled reader/writer on the standard library, because the people this is
for don't have a Python toolchain and shouldn't need one.

Reviewed prices land in `tools/price-overrides.json` as well as the configs, and the converter
reads that file. Without it, re-running the converter silently reverts every reviewed price and
the revert looks exactly like a successful run. Verified: apply -> re-convert -> price holds.

**Placeholder detection**: `Free` (price 0), `Odd for the set` (outside 0.55-1.75x the set
median), `Joke number`. 16 of 171 flagged. I removed a fourth flag (`level no sibling uses`)
after it fired on 34 items — in a set that prices by level every rung is the only one at its
level, so it fired on all of them and said nothing.

**Three content findings for the owners**, in `REVIEWING-PRICES.md`, not changed by me:
`COMBAT_PANTS_URBANREED_BOTTOM - Copy` is named the way Windows names a duplicate and is the
only file for that item, so an Explorer accident is currently deriving its item ID; it and
`COMBAT_PANTS_GHOSTPARTIZAN_PANTS` are 10,000 at level 3 in a set that is otherwise 66,000 at
level 13; the four `USECBASE` fatigues carry four different prices.

**The ten placeholder prices are applied** and recorded in `price-overrides.json`, with
`PRICE-PROPOSAL.md` noting Sophia's caveat that they are interim placeholders rather than
derived numbers.

**`SLING_OLIVEDRAB_BAG` promoted to Part 1** — declarative `PROMOTIONS` table in the converter,
so the 3.x tree stays pristine. Part 1 alone emits 276 including it; a combined 1+3 run emits it
once and does not trip the collision guard. Both verified.

**`COMBAT_PANTS_URBANREED_BOTTOM - Copy` renamed** to match its siblings, via a declarative
`RENAMES` table in the converter so the 3.x corpus stays pristine. Landed, stale file removed,
verified byte-identical apart from the name first.

**Two safety nets came out of doing it:**

- **Stale-output detection.** Renaming creates the new file but leaves the old one, and the
  result is a second valid config with a valid id of its own — a duplicate item that nothing
  downstream would question. The converter now lists any config in the destination it did not
  write this run. Same class as the `CustomQuests/DRIP.json5` double-load.
- **`DRIP-113`** in `drip check` — flags filenames containing " - Copy", "(1)", "Untitled" and
  similar, with the reason renaming is urgent: the filename derives the item id, so it is free
  to fix now and impossible after players have the item. An author duplicating a config in
  Explorer to make a variant produces exactly this, so it will recur.

**Filename sweep across all 544 + the live pack.** One genuine accident (renamed above). Four
naming-style inconsistencies — `HOODIE_BD` with no `_TOP` suffix, `ZASLON_BARVIKHAPROTO_BOTTOM`
among `_PANTS` siblings, `FLAKJACKET_3COLOURDESERT_VEST` among `_ARMOR`,
`COMBAT_PANTS_GHOSTPARTIZAN_PANTS` among `_BOTTOM` — deliberately **not** renamed. They are
real words someone chose, not accidents, and normalising them is a naming-convention decision
for the content owners. `DRIP-113` does not flag them, for the same reason the level flag was
deleted: a check that fires on healthy data trains people to ignore it.

**Also found:** `INFILTRATOR_USAF_DIGITIGERSTRIPE_TOP` (Part 2) is a top — `type: top`, with
`TOP.bundle` and `HANDS.bundle` — filed under `CLOTHING/BOTTOM/`. Harmless to the loader, which
reads the type field, but the converter derived output paths from the source folder and would
have carried the mistake across. It now places items by their declared `type`, so the output
tree is correct regardless of how the source was filed.

**Player-facing release story — built.** `tools/build-release.py`, `docs/RELEASING.md`, and
the `README.txt` that ships inside the archive.

A player gets one zip holding one `DRIP/` folder for `<SPT>\user\mods\`: the built assembly,
`config/config.jsonc`, and `bundles/ContentPacks/` with configs and `.bundle` files side by
side. Configs come from git, bundles from the store outside it, which is why this needs a
script — `git archive` or zipping the source produces an archive that installs cleanly and
loads nothing.

Nothing is packaged unverified: content check, then release-readiness against the store, then
build, stage, and a second verification **of the staged tree** confirming every item has its
bundles *in the package*. Tested against a miniature mod — happy path, a missing bundle, and an
empty store — and it refuses to package in both failure cases.

**`--check-only` answers "could we ship right now?" in a second, copying nothing. On its first
real run it found a release blocker** — `SLING_OLIVEDRAB_BAG` had no `GEAR.bundle` in the
store. **Resolved, and the root cause was not what I first reported.** The converter was
already correct: a promoted item's co-located bundles travel with it, and a Part 1 conversion
emits 365 bundles including that one (verified). The stale thing was the store, built before
the promotion landed. Echo regenerated it from the converter rather than hand-patching, and it
now holds 365. Readiness passes.

The checklist line is therefore **not** "move promoted bundles by hand" but **"regenerate the
store with the converter after any change to `PROMOTIONS` or `RENAMES`"** — those tables decide
which bundles belong in it and under what name. Same shape as the settled decision: the store is
downstream of the converter, so it cannot be maintained independently of it.

**The upgrade section was written, then cut on Sophia's ruling.** Profiles don't transfer
across SPT 3.x -> 4.x at all, so "your DRIP items won't survive" is subsumed by "nothing
survives", and telling players to sell their items first asks for work that cannot pay off —
in a section framed as protecting them. `README.txt` now has three sections: install, options,
troubleshooting. The install-hygiene line stays: replace an old 3.x DRIP folder rather than
merging into it.

**First-run setup step added to `AUTHORING.md`** (Kappa's note): a fresh clone has configs and
no bundles, so the doc now opens with the one command that fixes it and explains that
"273 of 275 items have no bundle" means un-bootstrapped, not broken.

`dist/` should be git-ignored — several GB of build output. Not my file to edit.

**`addClothingToBots` documented as a performance lever** in the shipped `README.txt`, per
Framesaver's finding that a GPU-side cost is invisible on a CPU-bound machine — theirs measures
zero no matter how much texture load is added, which says nothing about a GPU-bound player's
machine. DRIP puts 79 tops and 57 bottoms, mostly 2048x2048, into the appearance pools of 12
bot types.

New `IF RAIDS FEEL HEAVY` section names the exact setting, says plainly that we have not
measured it across hardware, and states what turning it off does and does not change.
Deliberately no numbers: the option and the feature both already existed, so the only thing
missing was telling a player it is the lever to reach for. Troubleshooting cross-references it.

Still reads as a taste setting in `config/config.jsonc` ("turn these off if you want DRIP to be
yours alone") — which is the file a player hunting for a fix is most likely to open. Two comment
lines would fix it; proposed to Echo rather than edited, since it is Kappa's file and he is
actively working on the §6 config options.

**Release build restructured for the two-archive model** (Sophia: Part 1 always ships with the
mod, Parts 2/3 are separate downloads).

`DRIP-<version>.zip` is the mod plus Essentials; `DRIP-<pack>-<version>.zip` is one pack's
configs and bundles and nothing else. Both extract into `user\mods\`; an add-on merges in and
adds one folder.

**The add-on-must-not-carry-base-files property is enforced, not assumed.** `verify_stage`
refuses an add-on containing the assembly, the config folder, `README.txt`, or the base pack,
and refuses a base archive holding anything but Essentials. Confirmed by smuggling a `DRIP.dll`
into a staged add-on and watching it be rejected.

**This is a preventive guard, not a caught bug** — Echo checked, and the repo and build output
currently hold only `Essentials`, so there is nothing yet for a naive path walk to have shipped
wrongly. The csproj content rules copy every pack present, so the base staging step drops
non-base packs explicitly rather than relying on their absence; that becomes load-bearing the
moment Parts 2 or 3 land. Built while it was still cheap, before the condition that triggers it
exists.

**Version skew:** each add-on carries `pack-info.json` stamped with the DRIP version it was
built from, and its README says what to check on mismatch. Warn-and-continue by design — a pack
is only configs and bundles, so the stamp exists to make skew diagnosable rather than to refuse
an install.

**`--check-only` now answers per pack**, since an add-on can be unshippable while the base is
fine and the base should still ship in that case.

Tested on a miniature two-pack mod: base excludes the add-on, add-on carries no base files,
version stamp present, a smuggled `DRIP.dll` is refused, and per-pack readiness reports one
pack broken while the other stays shippable. Real repo: `Essentials (base): 276 items, ready`.

**On the future public API:** nothing built, and nothing designed that would make convergence
awkward. A content pack is a self-describing directory the loader enumerates — that is already
the mechanism a third party would use, and `RELEASING.md` records that both routes must resolve
to the same code path when it lands.

**`docs/ICUP-HANDOFF.md` written** so the tag findings survive the gap between projects. Leads
with the reframing Echo asked me to carry: *anyone reviewing these weights is setting values for
the first time, not correcting them* — frame it as a correction pass and a reviewer spends an
afternoon hunting for a signal that was never in the data.

Records the measured shape — **Part 1: 135 files, 135 garments, no duplicates**, which is the
number to start from; all parts: **269 files, 267 garments**, 93 tag names, 673 entries, **one
distinct value**. (My earlier 268 was wrong: a stem-based recount catches the `ZASLON`
duplicate but not `TSHIRT_DESERTTAN`/`TSHIRT_KHAKI`, which are one garment under two different
filenames in one Part 3 folder. Counting by config-plus-bundles finds both.) Also the
`ICUP.ts addWeights()` behaviour that masked it by weighting on membership count so no authored
number was ever read, and why porting that forward would perpetuate the mask. Also what of the
price tooling is reusable and what isn't — including the deleted-flag lesson, since the same
trap is available in tag data.

**`vanillaOrigin` emitted by the converter** — the input Kappa needs to derive bot suitability
from the vanilla garment a retexture was cloned from, rather than putting all 136 garments in
every bot's pool as 3.x did.

Read out of each bundle's `AssetBundle` object with UnityPy. **All 136 Part 1 garments carry
one**, resolving to 23 distinct vanilla tops and 13 distinct vanilla bottoms. Emitted raw, never
resolved — pre-computing the bot list would freeze it against the game version the converter ran
on, and self-correcting when BSG changes a pool is the entire advantage of this approach over a
hand-written annotation.

Missing origin omits the field and names the file, per the agreed failure direction.

**Three supporting pieces**, because a derived field an author can't produce is a trap:
`DRIP-114` warns on any clothing config lacking one — and Sophia has since confirmed DRIP has **never** made a garment from scratch, everything is a retexture, so a missing origin is an alarm rather than an unset option. The message says so now; `drip origins` fills them in for
hand-authored garments (needs UnityPy — `check` and `new` stay standard-library-only);
`tools/vanilla-origins.json` **records** them — see below.

**Origins are now a record, not a cache** (Echo: the rebuild will break re-derivation). Rebuilt
bundles reference vanilla assets rather than copying them, so their internal `AssetBundle` name
will no longer carry the vanilla path, and a path+size cache would miss for every garment at
once and re-read nothing. Captured now, while still readable:

- **270 garments across all three parts, 36 distinct origins** — Parts 2 and 3 included, since
  their bundles are readable today and won't be after the rebuild.
- Keyed `<filename>|<type>`, verified unique: 267 keys with zero conflicting values. Filename
  alone is unsafe — a Part 2 top and bottom share the stem `INFILTRATOR_NIGHTGREY_PANTS` with
  different origins.
- One garment was unreadable via the expected filename (`INFILTRATOR_NIGHTGREY_PANTS`, whose
  bundle is misnamed — the known Part 2 content bug). Recovered by reading the single
  unambiguous bundle in its folder. That lineage would have been lost permanently.
- Converter and `drip origins` both read the record first and fall back to a bundle only for a
  garment nobody has recorded. Verified: origins still resolve with no bundle on disk *and*
  with UnityPy absent, while an unrecorded garment still fails loudly.
- **269 entries is not 269 garments.** 270 configs -> 268 distinct keys -> 269 entries, the
  extra being one deliberate rename alias: a renamed garment is recorded under both the name on
  disk and the name it ships under, so the record answers from either direction. That was
  emergent (capture used one name, the converter the other) and is now explicit in capture, so
  it holds even if the converter never runs. The counting rule is in the file's own `_README`,
  since the next person to reconcile 269 against 268 shouldn't have to derive it.
- **Known limit, recorded rather than fixed:** two garments identical in filename *and* type,
  differing only by folder, collapse to one key. Real in Part 3 (`TSHIRT_KHAKI` twice, different
  prices and bundles) where the record is correct only because both share a vanilla origin.
  Left as-is deliberately: that pair already hard-errors as an id collision so it cannot reach a
  release, and putting folder in the key would break the rename alias and stop keys surviving a
  file move. Noted in `_README`.

Verified end to end: `DRIP-114` fired on all 136 before the field existed, the converter filled
them, `drip origins` refilled a deliberately stripped one, and output stayed valid JSON.

**Quest format proposal — `docs/QUEST-FORMAT-PROPOSAL.md`.** Thinking, not building, per the
brief. Measured cost: **~153 lines and ~10 hand-invented ids per quest**, with every word of
player-facing text in a second file — 32 locale entries keyed by a bare 24-character condition
id the author had to make up. Proposed shape is ~15 lines with text inline and ids derived from
the filename, as items already do.

On Echo's inline-text question: **yes, inline.** There is exactly one language today, so the
trade isn't authors-versus-translators — and a translator arriving now would be worse served
than by an export, since they'd need to learn both the convention and the invented ids. The
locale file becomes an output; other languages get exported files keyed by generated keys, the
same round-trip shape as price review.

Agreed with reading the format directly rather than compiling: a build step is a second entry
point, which this table already warns about three times, and it puts a command between Colette
and her quest.

### Found while measuring: 68 items gated behind quests that don't exist

Every item `questRequirements` uses ids like `DRIP_1`; every quest is keyed by a MongoId.
**None of the 15 referenced ids resolve**, affecting **68 of Part 1's 276 items**.

**This predates the port** — the 3.x source has the same mismatch, so it has presumably been
shipping this way. It is easy to miss because the `DRIP_N` strings still exist as *locale* keys,
so the ids look alive.

**Fixed.** Sophia's context explained it — 3.x allowed any alphanumeric quest id, 4.x requires
MongoId format to match BSG — and the renumbering left *both* key styles in `en.json`, so the
mapping was recoverable by matching text rather than guessing. Matched on four fields together;
**19/19 resolved, none ambiguous, and sequential by id order**, so two independent derivations
agree. Echo derived it, I re-derived it rather than taking the table, and we match exactly.

Lives in `QUEST_ID_MAP` in `tools/convert-legacy.py`, upstream of the converter alongside
`PROMOTIONS` and `RENAMES`. All 68 gates remapped, all 15 distinct ids resolve to real quests,
`DRIP-502` is zero and the release gate cleared without needing a policy decision.

**Guard this:** the old `DRIP_N` locale keys are the only other record of the mapping and look
like dead weight. `QUEST_ID_MAP` is the durable copy — don't delete it because the locale keys
happen to survive, and don't delete them assuming the table is redundant.

**Text fields now take a string *or* a language map** (Sophia's call), applied to items as well
as the proposed quest format so there is one answer across every config type:

```jsonc
"name": "Winter Jacket - DRIP"
"name": { "en": "Winter Jacket - DRIP", "ru": "Зимняя куртка - DRIP" }
```

A map must carry `en`, since that is what unlisted languages fall back to — `DRIP-107` if it
doesn't. Verified: plain string accepted, language map accepted, map-without-`en` rejected,
empty string rejected, bad language code rejected.

Migration cost was zero: `translations` was in the schema and used by **none** of the 276
configs, so replacing its shape cost nothing. My export-to-`CustomLocales` proposal is demoted
to a convenience for the day a translator asks for a flat file — an *output* of the inline data
rather than the mechanism. Sophia's version is simpler and I'd have kept a round-trip that
needed synchronising.

### `DRIP-408` — the 13 unsellable items are now a work list, and they block the release build

Echo's ask after the load-order move: the server log says *20 configs have no trader*, which is
one number covering two situations with **opposite** correct fixes. `drip check` now separates
them, from the game's own database.

Re-derived independently before building anything, and it agrees with Echo exactly:
**13 configs / 5 base items** unsold (Slick ×5, TacTec ×4, A18 ×2, THOR, Tac-Kek) and
**7 configs / 6 base items** quest-locked. 236 quest-locked assort ids across 8 traders, matching.

| base item is | means | reported? |
|---|---|---|
| sold normally | copying offers works | no |
| sold only after a quest | DRIP refuses on purpose — correct | **no** |
| not sold anywhere | copying offers copies nothing | **`DRIP-408`, error, per file** |

**Only the third is a diagnostic.** Warning about quest-locked items would be a check firing on
healthy data — the same mistake as the deleted fourth price flag. But the server log *adds* the
two, so `drip check` prints the quest-locked count as a **note**: not a warning, not silence.
Without it an author reading both sees 13 and 20 and cannot reconcile them.

**Reading the database off disk agrees with the running server, and that was verified rather
than assumed.** DRIP loads at 400,002; Fence's assort is generated at 800,000; Fence's on-disk
`assort.json` is empty — which is exactly what DRIP sees. The static check and the runtime cannot
disagree about Fence, because both see nothing.

**Consequence, and it is Sophia's call not mine: `build-release.py` now refuses to package.**
`--check-only` went from *Essentials (base): 276 items, ready* to *content has errors*. That is
faithful — these items can never be bought, which is a real pre-existing content bug that Fence
was masking — but it is a new gate that did not exist yesterday. Downgrading `DRIP-408` to a
warning is one word if the release should ship ahead of the fix.

The gate is only enforced where it can be evaluated: with no SPT install configured the check is
skipped, and `drip check` **says which check it skipped** rather than reporting a clean run it
did not earn.

Falsified across all four branches before being trusted: an item based on a normally-sold item
stays silent, one based on a quest-locked item is counted in the note and not flagged, one based
on an unsold item raises `DRIP-408`, and the same item with `copyOriginalOffers: false` goes
quiet again.

### Authors no longer need a programmer for the one field they never could produce

`basedOn` is a 24-character ID written nowhere a content author would look, so the honest
instruction was "ask a coder" — the exact dependency DRIP exists to remove. `drip new` now takes
a **name**:

```
  Which item are you retexturing? (its name, e.g. Slick): slick
     3 items match 'slick':   1. ...(Black)  2. ...(Coyote Tan)  3. ...(Olive Drab)
     Which one? 2
     -> LBT-6094A Slick Plate Carrier (Coyote Tan)  (6038b4b292ec1c3103795a0b)
```

`drip id fast mt` does the same for a config that already exists, which is the commoner case.
The resolution is **always printed**: a name search can land on something reasonable but wrong
("vest" is a real short name belonging to one specific armour), and a silent correct-looking
answer is worse than a question.

New file `tools/sptdb.py` holds both — read-only, standard library, never writes to an install.
**It refuses to guess between installs.** This machine has three across two SPT versions, one of
them Framesaver's measurement corpus; it names them and asks for `tools/spt-path.txt` rather
than picking. `spt-path.txt` is per-machine and should be git-ignored.

**A bug in it, caught by testing rather than review, worth recording because the failure was
silent and confident.** The name filter first used the `Equipment` category node — but rigs and
backpacks hang off `SearchableItem`, not `Equipment`. So `drip id tactec` returned *zero
matches*, cleanly and with no error, for about a third of what DRIP retextures. Filtering on
three named roots fixes it. A filter that excludes real data reports it as absence.

### `Setup.cmd` — one double-click, and it reports what it *didn't* do

Sophia's ask, and it replaces "check which machine they use" with something that holds for every
future contributor. `Setup.cmd` → `tools/bootstrap.py`.

The batch shim exists because the first thing to check for is Python, which a Python script
cannot do. It offers a `winget` install behind an explicit prompt and never installs silently.
It also asks for a version number rather than trusting `where python`: the WindowsApps stub
`python.exe` answers `where` and then opens the Microsoft Store, so `where` alone passes on a
machine with no Python at all.

Five steps — Python, SPT install, editor binding, bundles, `drip check` — each reporting
**ok / info / todo**, and the summary lists every `todo` again. Two rules, both from failures on
this project:

- **It says what it skipped.** A setup exiting 0 having quietly not checked something is the
  same shape as `verify_repack` reporting 547/547 over a population it could not see.
- **It refuses to guess.** With three installs across two versions it lists them *with their
  versions* and asks. It writes `tools/spt-path.txt` only from an answer, never from a heuristic.

**Setup status and content status are reported separately**, because rolling them together
printed *"All set. Nothing left to do."* directly above 13 real errors on the first run. They are
different claims and the first one being true says nothing about the second.

**The editor step checks that the schema actually binds**, not that the file exists — that is the
one way this whole investment can look configured and silently do nothing. Falsified three ways:
invalid JSON, a `url` pointing at a missing file, and no schema declared at all. Each reports
distinctly and names the consequence; `settings.json` restored byte-identical afterwards.

Also caught by testing: `isatty()` is not a reliable guard on Windows shells, so the prompt threw
`EOFError` and turned a skippable step into a stack trace. Skipping is now a first-class answer.

`tools/spt-path.txt` is git-ignored — per-machine by construction, and pointing it at someone
else's install is worse than leaving it absent.

### Colette answered, and my quest proposal was aimed at the wrong barrier

Echo asked her directly rather than reasoning about it. Four things in her answer; **one** is
what `QUEST-FORMAT-PROPOSAL.md` measured.

I measured the file format — ~153 lines, ~10 hand-invented ids — and inferred **verbosity**. Her
answer is **cognitive load, ordering, and having no starting artefact**: *"a ton of stuff I
barely understand is in front of me and I have to figure out how to piece it together to not
break."* A generator emitting 153 correct lines fixes the typing and leaves that standing.
The measurement was right and the inference from it was wrong.

What her answer actually implies, which is Echo's formulation and worth keeping:

> **A template's job is to reduce what is on screen, not to fill the screen correctly.**

With one qualification the data supports: **fewer characters and fewer unfamiliar things are not
the same goal.** A comment explaining a field removes more load than deleting the field would.
`drip new gear` already emits 20 lines of which only **two** need editing, and half those lines
are explanation — that is closer to right than a stripped version would be.

**`docs/QUEST-TEMPLATE-MOCKUP.md`** — three mock-ups at 12, 19 and 25 lines, all with **4
decisions**, to be **chosen between** rather than approved. She has been gracious about this
process for years, so "is this what you wanted?" gets a yes; "which of these three?" gets an
answer. Variant C is deliberately her current workflow — copy a previous quest and edit it —
generated correctly instead of by hand.

**Her ordering complaint is already solved and nobody had said so.** No sequencing anywhere:
objectives and rewards are lists, prerequisites go in `requires`, and the
`AvailableForStart`/`AvailableForFinish` grouping follows from condition type in **66 of 66**
cases. Presets are the open one — that ordering problem is attachment/slot sequence, it is real,
and DRIP does not do presets at all.

**The bar is lower than we were building for**, from her own calibration: *"It's not that bad —
but it does often dissuade me from doing more of either."* Not a blocker, a discouragement. The
metric is whether she writes more quests.

**All three of my line counts in that document were off by one**, hand-counted, in a document
whose whole argument is counting what is on screen. Corrected by measuring.

### Gate 1 — `docs/PROSE-INVENTORY.md`, and it is much smaller than it reads

Sophia writes every word a player or author reads. Echo asked for an inventory rather than a
rewrite, on the grounds that *"31 diagnostics, 6 comment templates"* is a plan and *"all
user-facing text"* is a wall. Measured by script, not estimated.

**The finding that shrinks it by more than half: all 276 item names, short names and
descriptions are already Colette's and Amber's words** — the converter carried them through
untouched. Verified rather than assumed: 275 of 276 byte-identical against the 3.x source, none
differing; the one exception was only the deliberate `- Copy` filename rename and its text
matches too, so it is **276 of 276**. Same for every quest string in `en.json`.

So **~772 of ~940 human-readable strings in the shipped mod already pass Gate 1**, and they are
the ones players actually read. Worth knowing before reading the totals: "276 item descriptions"
looks like a month of work and is in fact zero.

What is genuinely ours: **~165 discrete strings and ~3,300 words**, plus a scope question on the
technical docs (~11,800 words) whose readers are coders, since Sophia's reasoning was about what
the SPT moderators see.

**The highest-leverage item is not the documentation.** Six comment templates inside the shipped
configs render into **1,445 comment lines across 277 files**, and the content owners read them
every time they open a file — far more often than they will ever open `AUTHORING.md`. Because
the converter generates them, that is **six strings to write, not 277 files to edit**. If only
one thing gets written, it is those six.

Echo's awkward case is real and named in the doc: if Colette picks a quest format tomorrow she
is picking between prose we wrote. **The design can survive being ours; the sentences cannot** —
choosing the shape and writing the words are separable and only the second is gated.

**Sophia's ruling on scope:** the three technical documents are **Gate 2, not Gate 1** — she does
not need to have written them, she needs to be able to answer questions from them. So the Gate 1
figure is ~3,300 words, not ~15,000. Asking rather than assuming halved the work.

### Gate 2 demonstrator — `docs/CHECK-REGISTRY-DESIGN.md`, signed off, not started

`check_config` is one long function with every rule inline, so adding a check means finding the
right place and not disturbing the thirty around it — Colette's *"figure out how to piece it
together to not break"*, pointed at Sophia. A registry of one function per check makes adding the
thirty-third mean writing one function beside thirty examples. The test is that she adds one
unaided.

**It acquired a second consumer after being proposed**, and that changes its shape rather than
its priority: a GUI (Colette asked for one independently) needs to enumerate checks and render
each result beside the field it concerns. Echo's consequence — **a diagnostic should carry which
field it concerns as data, not only as prose in its message**, since a GUI cannot put `'price' is
missing` next to the price box by parsing English.

Measured before signing up to it, because "add a field to 35 call sites" looks small and often
isn't: **28 of 35 concern a specific field** (21 name one literally, 4 interpolate it, 3 know it
without saying it). The other **7 are exactly the ones that should not have one** — invalid JSON,
duplicate filename, old-format file, accidental filename, and the two pack-level preconditions.
So `field=None` is information rather than a gap: it says "this is about the file or the pack,
not one line", which is what a GUI needs in order to render it somewhere else.

**One engine, two front ends** (Echo's constraint, and the load-bearing one). A GUI calls
`drip.py`; it does not reimplement it. Two implementations of "is this config valid" is the
population-disagreement problem with a user in the middle of it, watching one tool say yes and
the other say no.

**Sequencing note that matters:** do not rewrite the diagnostic wording and restructure the code
in the same pass. Gate 1 has Sophia rewriting all 32 messages, and a behaviour-preserving
refactor — verified by byte-identical `drip check` output — stops being verifiable the moment the
strings change.

**Next:** nothing blocking on my side. The `DRIP-408` severity question is with Sophia and Echo.

### Soft-armour parts: there was never a choice to make — `docs/PARTS-AND-PRESETS.md`

Sophia asked whether authors could stop looking up item IDs for the soft armour pieces. The
answer is better than "we can automate it": **across all 60 vanilla armour carriers, all 275
required soft-armour slots accept exactly one item and nothing else** (measured). The field asks
for a value the game has already determined.

The plate slots are the opposite — 3 to 20 legal choices each. **That split is the design.**
Required slots want no field at all rather than a keyword; plates want one plain-English
question, and that question is Colette and Amber's, not ours. Echo's `globals.ItemPresets`
source is right and covers every required slot of all 59 carriers that have a preset.

**The interaction nobody had connected, and it is the important part.** `REPRICE-WORKSHEET.md`
recommends the bare shell's handbook price — 12,710 for a Slick. Vanilla prices the *assembled*
item: measured across 17 rouble-priced vanilla armour offers, asking price is 1.09–1.37× the
handbook value of carrier plus contents. A vanilla-consistent Slick is **~400,000**. The soft
armour alone is worth twenty times the shell.

So the two open items interact in one bad direction: today the thirteen are unbuyable, so
nothing is wrong yet. Price them with no parts and you get an unwearable shell — the bug Sophia
caught within the hour. **Fix the parts and keep the worksheet price and you get a 360,000-rouble
carrier for 12,710, and nothing looks wrong.** Fixing parts without revisiting price converts a
visible bug into an invisible one.

### The four divergent `includedParts` are a bug, not a parked decision — and there are eight

Described in the brief as possibly deliberate. They are not: **`Soft_armor_back` holds the ID
that belongs in `Soft_armor_front`**, every other slot matches vanilla exactly, and the
`Soft_armor_back` filter on both base items accepts exactly one item which is not the one named.
**So the slot is not mis-covered, it is empty — those items have no back armour.**

It reads as deliberate because the two inserts *share a name*: both are `Aramid insert`,
differing only in which colliders they cover. That is also how it was written — a duplicated
line with the slot renamed and the ID left behind.

**Inherited from 3.x, not introduced by the port, and it is 8 files across all three parts**
(Part 1 ×4, Part 2 ×2, Part 3 ×2). Swept the whole 3.x corpus: 19 files use `childAssorts`, 8
entries would be rejected by the game, all the same slot, and only **two** distinct corrections
are needed. Nothing else is lurking.

**The fix belongs in `convert-legacy.py`, not in the `.jsonc` files** — the converter copies
`childAssorts` straight through, so a direct edit is reverted by the next run and the revert
looks like a successful conversion. Not applied: it changes shipped items, it should be done
once across all three parts, and the content owners should know.

### The converter now refuses to drop bundle dependency declarations

**Nothing is currently lost.** Verified independently before touching anything: the pack holds
**554 dependency paths**, a fresh conversion would emit **253**, so **301 declarations across 222
files exist only in the generated files** — Echo's count of ~300, arrived at from the other
direction. All 301 are intact.

The hazard is real and it is the worst shape available: a stripped bundle borrows its geometry
from another, which needs the externals table inside the `.bundle` (safe from the converter)
**and** a dependency declaration in the `.jsonc` (which the converter overwrites). Losing the
second half is not a crash and not magenta — the item renders as **nothing**, and the conversion
reports success.

`convert-legacy.py` now **probes before it writes**: a full dry pass first, and if the run would
drop declarations it cannot reproduce, it stops with nothing written and names them.
`--allow-dependency-loss` overrides for someone who has a copy and means it.

**Its limitation, stated because it decides how much this is worth:** it compares against what is
on disk, so it warns *before* a loss and can never detect one that already happened. It buys
time; it is not the fix.

Falsified five ways: fresh destination converts; re-converting its own output does not block; a
destination with declarations is refused **byte-identically**; the override writes and the loss
is real (554 -> 253); and once lost the guard correctly has nothing left to protect.

**Where the real fix belongs, having checked it is buildable.** Echo's rule — *for each bundle
beside a config, if its externals name a CAB published by another bundle, emit a dependency on
that bundle* — is exact and derives from the artefact that actually decides. The machinery
already exists in `tools/bundles/audit_refs.py` (`externals()`, `index_pack()`, `index_game()`),
and reading externals is cheap: **0.02s for three bundles**, headers only. Verified on both
shapes — AIRFRAME's `GEAR.bundle` names the CAB its sibling `TEXTURE.bundle` publishes, and
6B2's names CABs that resolve into the game.

But it should **not** live in `convert-legacy.py`. A bundle dependency is a fact about the
bundles on disk, not about the 3.x source, and the converter's job is 3.x -> v2. It wants to be
its own tool that the converter calls at the end — so a conversion never leaves the pack broken —
and that Echo can re-run standalone after stripping more, without converting anything. Plus a
`drip check` diagnostic as the net. **Same split as `SLOT_FIXES` and `DRIP-410`: derive to fix,
check to catch.**

Carry forward `audit_refs.py`'s own warning rather than rediscovering it: `externals()` returns
the **first** serialized file's list. All 365 pack bundles publish exactly one CAB today, but 38
of 260 sampled game bundles publish two, so the derivation should assert that precondition
rather than assume it.

**A measurement I got wrong first.** My opening count said *zero* dependencies present, which
would have meant the 301 were already destroyed. `bundles` is a dict of `bundle name -> [paths]`
and I looked for a list of entries with a `dependencies` key. The wrong shape returned a clean,
confident zero. Same failure as the `Equipment`-node filter: **a query that matches nothing
reports it as absence.**

### Back armour: eight carriers had none, now fixed in the converter (Sophia approved)

**They were not mis-covered. They were uncovered.** `Soft_armor_back` held the ID that belongs
in `Soft_armor_front`, and that slot accepts exactly one item which is not the one named — so
the game refused to fit the part and left the slot empty. These carriers have had **no back
armour at all since 3.x**. Anyone reading this later should not mistake it for a balance tweak.

Fixed as `SLOT_FIXES` in `convert-legacy.py`, **keyed by (base item, slot) rather than by
filename** — two entries covering all eight files, so Parts 2 and 3 are correct the first time
they are converted instead of being found and fixed twice.

`drip check` keeps deriving the same condition from the game's slot filters as `DRIP-410`. That
split is deliberate: **the table is the record, the check is the safety net.** A converter that
silently rewrote author data to match the game database would have fixed these eight and
documented nothing.

**I hand-typed one of the two IDs wrong.** `628dc750...` is ECLiPSE RBAV-AF, not AVS Tagilla —
the entry would have matched nothing and fixed nothing, silently. Caught by checking each entry
against the slot filter before running, then deriving both from the source files instead of
typing them. Second wrong-constant of the day, same shape as the 6B2/Zhuk mix-up: a wrong ID
looks exactly like a right one.

Verified: `drip check` **17 -> 13 errors**, all four `DRIP-410` gone, the remaining 13 are the
unpriced items. Re-running the converter produces **byte-identical output** over all 140 item
files, and all 10 price overrides survived.

Not yet told to Colette and Amber. Echo's read, which I agree with: a line in whatever goes to
them next rather than a message of its own — eight garments quietly gaining back armour they
never had belongs on the record. The pricing thread is already open.

**Found while there:** `build-release.py` printed `NOT READY — n problem(s)` with an em-dash, so
the release gate's own failure message mojibakes on a stock console. Fixed. Every remaining
non-ASCII character in the author-facing tools is in a comment or docstring, except the
deliberate lookalike table in `sptdb.py`. `convert-legacy.py` still has em-dashes in printed
strings; it is a developer tool nobody else runs, so it is noted rather than churned.

### A `vanilla` default applies to nothing that exists — and DRIP's own pricing is already sound

Checking the "default to `vanilla`" proposal, the population it would act on today is **zero
configs**. It cannot apply where `copyOriginalOffers` is on (105 configs — children come from
the trader), it must not apply where an explicit `includedParts` exists (10, constraint 1), and
25 own-priced items have no required slots. **Its entire blast radius is the 13 worksheet items,
once they are repriced.** The "17 of 18 trader offers already match the preset" argument is
reassuring but is about a population the default never reaches.

Two corrections to the measurements it rests on:

- **Count offers, not items.** Six of the 20 bases are sold by more than one trader, so "the"
  offer per item is an unstated sampling choice — and it produced three different answers today
  across two people. Counted properly: **19 of 20 bases have at least one offer identical to the
  preset; one (BNTI Zhuk) has none.** The 6B43 is not an exception at all — Prapor sells it bare
  for a barter, Ref sells the same armour complete for 58 GP coins.
- **And the split that actually answers the question: every vanilla offer paid with money ships
  the full preset. 11 of 11, no exceptions.** Both deviations are non-cash — the Prapor barter
  and Ref's GP-coin Zhuk. DRIP items are sold for money, so for the population DRIP lives in
  vanilla is unanimous rather than ambiguous.
- **Required-only vs whole-preset is not a small choice.** 22 of the 27 DRIP bases with a preset
  have optional parts in it, worth 12k–169k each. Only 5 are cases where the two options mean
  the same thing.

**The check I expected to build against the new default turned out to be unnecessary, and
finding that out corrected me twice.** A price-vs-contents check first appeared to fire on 20 of
35 own-priced items — a flag firing on healthy data. It was **my** error: 20 of the 171 priced
items are in **dollars or euros** (USD = 120 roubles, EUR = 133) and I compared the raw number
against a rouble handbook value. The same "of what?" mistake this file keeps recording.

Converted properly, **all 35 own-priced items fall between 0.51x and 6.23x of what ships with
them, and all 10 with `includedParts` sit in a tight 0.83–1.99.** Nothing is mispriced. Colette
and Amber are already pricing assembled armour at roughly its contents' value — which is the
best evidence available that the plates question has a natural answer for them.

The 13 at worksheet defaults would land at **0.03x**, an order of magnitude below anything in
the corpus. So the risk is real and the corpus is the argument against it, not for it.

### The price sheet can now ask about the 13 — async review, no second tool

Sophia is settling pricing over Discord rather than in the demo. The sheet Colette and Amber
already know **could not ask the question**: the 13 have no `price` field, which is precisely why
they are on the worksheet, so the exporter had nothing to export and produced 171 rows with none
of them in it. Now 184.

- **Selection is derived, not listed.** Same rule as `DRIP-408` — gear, copying the original's
  offers, no reachable trader selling the original. The sheet and the check cannot drift apart
  about which items are affected.
- **`Comes with`** — the column that prevents the failure. The anchor a reviewer reaches for is
  the vanilla handbook price, and for a carrier that is the *bare shell*: TacTec 3,620 against
  180,000 assembled. Someone pricing it at 3,620 has done something reasonable with the number
  in front of them and nothing afterwards looks wrong.
- **`Price now` reads `not sold yet`**, not blank. Blank in a price column invites being read as
  free.
- **`Others in this set` reads `none priced yet`** for all 13 — every set-mate is unpriced too,
  so the normally-most-useful column has nothing to offer them. Said rather than shown as a dash.
- **A second yellow cell: `Level`.** An own-priced item without `loyaltyLevel` fails to load
  (`DRIP-301`), so collecting only a price would have handed them 13 items that error after
  they did exactly what was asked. Pre-filled with 1, and 1–4 is validated before anything is
  written.
- **Apply writes all three** — `price`, `loyaltyLevel`, `copyOriginalOffers: false` — into both
  the config and `price-overrides.json`, or the converter regenerates an item that still has no
  seller.

**Found in passing: the `Level` column was blank for every gear row and always had been.** It
read `profileLevel`, which is clothing's field — gear uses `loyaltyLevel`, and `DRIP-306` warns
if gear has `profileLevel` at all. So 35 of 171 rows showed nothing in a column that is often
legitimately empty, which is why nobody noticed. Now picks the field by kind.

Round-tripped against a **copy** of the pack, never the live one: a level of 9 is rejected with
nothing written; a real answer produces a valid config with all three fields, the override
records all three, and `drip check` drops 17 -> 16. The live pack is untouched and still reports
17.

**Gate 1:** the sheet's wording is mine and has not had Sophia's pass. `export` prints that
reminder to whoever is about to send it — deliberately in the console and nowhere in the sheet,
since the marker's audience is Sophia and Echo, not the two people filling it in.

### The price sheet showed a bare number with no currency

Found while checking the above, and it is in the one tool my constituency drives unaided.
`Price now` was a bare number; **`cmd_apply` writes the new number into `"price"` and never
touches `"currency"`**, so a rouble-shaped edit to a dollar item was a silent 120x error. The two
most exposed rows are armour at 1,360 and 2,450 — which look far too cheap beside a
rouble-priced set and are not.

Added a locked **Currency** column (`NEW_PRICE_COL` 7 -> 8; verified the reader still lands on
`NEW PRICE`, and an apply with no edits reads clean and writes nothing).

**What was *not* wrong, and worth stating so nobody 'fixes' it:** no set mixes currencies, so
`Others in this set` and the `Odd for the set` flag have always compared like with like. The
exposure is cross-set comparison and the unit being typed in — not the flag logic.

### `DRIP-409` / `DRIP-410`, and a crash the new check surfaced

`drip check` now validates every `includedParts` entry against the game's own slot filter.
`DRIP-409` = no such slot; `DRIP-410` = the slot won't accept that part, printing the one ID
that fits. All eleven branches falsified, including staying silent where `DRIP-403` and
`DRIP-407` already own the failure.

**`drip check` is now 276 items, 17 errors** (13 unsellable + these 4), so
`build-release.py --check-only` still says *"Content has errors"* — same shape as `DRIP-408`,
and these four are an outright bug rather than an accepted work list.

Worth catching because of *how* it fails: the game does not reject the config, it declines to
fit the part. Empty slot, no log line, no in-game sign.

**Fixed en route: game item names could crash the tools.** 10 of the game's 5,155 names contain
non-ASCII — Cyrillic lookalikes in the three keys BSG spells `Сity key`, the `TT` in the
7.62x25 ammo packs, a curly apostrophe in `Global Armor's Steel ballistic plate`. `sys.stdout` on
a stock Windows console is cp1252, so printing one raises `UnicodeEncodeError` and ends the run
in a traceback. `DRIP-410` prints plate-name lists, which made it reachable. Folded to ASCII in
`sptdb.py` **where game text enters**, not at each print — the rule is about the source of the
text, not any one message. Verified the fold does not break name search.

### Handover — `docs/DX-REVIEW-NOTES.md`, and `tools/audit-tables.py` (2026-08-02)

Written for the incoming reviewers. **Not a summary** — this file is the record and
`FUTURE-WORK.md` is the docket; the notes are the third thing, *where my own position made me a
bad reviewer of my own work*. Ordered by where I would look first, and it names two defects I
specified deliberately without applying.

The one new tool is `tools/audit-tables.py`, read-only, exits 1 on a finding. The converter's four
**repair** tables (`OVERRIDES`, `RENAMES`, `PROMOTIONS`, `SLOT_FIXES`) are each keyed by a
hand-typed value, and an entry matching nothing repairs nothing while still reading like a fix in
place — I typed a wrong base-item ID once and only the game's slot filters caught it. Currently
**0 dead across all four**, falsified both key shapes before believing it (injected a dead key,
confirmed exit 1 and the named entry, restored byte-identically).

`QUEST_ID_MAP` is deliberately excluded, and that is the interesting half: repair tables want every
entry *used*, reference tables want every case *covered*. Its 19 entries map every DRIP quest;
only 15 gate an item, and the other 4 are correct. Auditing it would report 4 non-problems forever
and the first person to clean up the noise would delete four good entries. The check earns its keep
only because it stops at the tables where an unused entry is a defect.

**One number a reviewer will trip over immediately, reconciled here so nobody re-derives it:**
`drip check` reports **29 errors across the three packs** while Echo's server run of the same three
reports **zero**. Both are right. 28 are `DRIP-408`, the pricing queue. The 29th is `DRIP-102` on
`ZASLON_SOC_PANTS`, which ships in both Essentials and Part 3 — and the two files are
**byte-identical**, so the loader, which hard-errors only on *differing* content under one ID,
correctly stays silent. `DRIP-102` keys on filename alone and cannot see content. Not a wrong
check; an undiscriminating one at the wrong severity, which is expensive because an error that a
verified run contradicts trains people to discount the mechanism. Fix specified in the notes; not
applied, because whether a duplicate is intentional is a content question for the pack owners.

Deliberately **not** applied, and specified in the notes instead, because a change landing after
the team stands down is a change nobody reviews: `DRIP-001` tells an author a parse failure is
"a missing comma, a missing quote, or a stray bracket" — all three visible — when the corpus
contains a real instance of a **literal tab inside a string**, which looks exactly like a space.
The converter already repairs it; the author-facing tools do not name it. Exact branch, exact
wording, one minute to review.

---

## Echo — bundles

**Established:**

- Bundles are Unity 2018.4.28f1 / 2019.4.32f1 / 2019.4.39f1; the game is **2022.3.43f1**.
- The magenta rendering is **dangling shader references**, not shader recompilation. DRIP's
  bundles contain no shaders — materials point at shader object IDs in the game's `shaders`
  bundle, and none of the three IDs DRIP uses still exist among its 555 shaders.
- Meshes are unmodified vanilla in every case checked. Normal and gloss maps are unmodified
  in the large majority — median delta vs vanilla is **0.00**, i.e. exactly identical — but
  **26 of 302 do differ**, so "only the diffuse changes" is true as a tendency and false as a
  rule. Do not build anything that assumes it. **77% of Part 1's 2.1 GB payload is duplicated
  vanilla content.**
- All **364 of 364** Part 1 bundles self-declare a vanilla origin path that resolves against
  the live game install — so the rebuild is scriptable.
- 286 of 333 diffuse textures ship with **no mipmaps** (vanilla has 12 levels). Quality bug,
  fix during rebuild.
- Game renders in **Gamma** color space, not Linear.

**Art library extracted** — `F:/SPT/Mods/DRIP-art-library/`, 1.5 GB, complete for Part 1.
364 bundles, 0 errors, 0 without a resolvable vanilla origin. 1216 texture instances collapse
to **686 distinct images** (43.6% were duplicates). Of those, **391 images / 894 MB are
genuinely modified art or have no vanilla counterpart** — that is the irreplaceable set. The
other 295 images / 555 MB are vanilla copies and need not be shipped or rebuilt.

`manifest.json` maps every bundle to its vanilla origin and lists each texture with role,
dimensions, mip count, delta-vs-vanilla and its pooled PNG. That is the file the rebuild
should be driven from.

384 distinct images carry no mipmaps and want regenerating during the rebuild.

### Full diagnosis of the magenta rendering

A material's shader pointer is `(fileID → the Nth external bundle, pathID)`. Both halves are
stale, and both are mechanically derivable from the vanilla origin:

| | DRIP (2018/2019) | Vanilla / current game |
|---|---|---|
| `external[1]` | `cab-1dc8d26be8722a766953ce9d8a444e8c` — **gone** | `CAB-56d919bd5479d38f741da52a6beef92f` — the live `shaders` bundle |
| body shader pathID | `-9098473984068178372` — **gone** | `6014991791773097075` = `p0/Reflective/Bumped Specular SMap` |
| glass shader pathID | `6729946233178204048` — **gone** | `6719469288405062119` = `EFT/Glass` |

The bundles themselves load fine — meshes render, which is why the symptom is magenta rather
than missing items. Only the material→shader link is broken.

### Repack instead of rebuild — spike succeeded structurally

`tools/bundles/repack_all.py` rewrites both stale halves, looking the correct values up from
each bundle's vanilla counterpart by material name. Verified on `ADAPTIVECOMBAT/ERDL/HANDS`
and two more: after repacking, externals and all three material shader pathIDs are **identical
to vanilla**, every object survives (3 materials, 3 textures, 1 mesh, all dimensions
unchanged), and the file grows by 20 bytes.

**All 365 Part 1 bundles are repacked**, staged at `F:/SPT/Mods/DRIP-bundles/` in v2 layout
(via `convert-legacy.py --bundles copy`, so the 3.x originals are untouched). Verified
statically: **547 of 547 materials resolve to a shader that exists** — 543 into the live
`shaders` bundle, 4 to a Unity `Standard` shader embedded in the bundle itself.

**Deployed to the live content pack** — all 365 repacked bundles are now sitting beside their
configs in `bundles/ContentPacks/Essentials/`, ready for the client test. Bundles only: the
store's own configs differ from the live ones by a single `$schema` relative path (the store
sits at a different depth), so copying them would have left 276 configs pointing at a
non-existent schema. Verified after: 365 bundles, 0 configs without one, no config modified,
`git status` unchanged.

**Note for Kappa and Tau:** the pack is no longer bundle-less, so `DRIP-200` and the loader's
un-bootstrapped warning should now stay silent, and `--check-only` should report ready. If
either still fires, that is a real finding.

**The store is regenerated, never hand-patched.** It is downstream of the converter, so any
change to `PROMOTIONS` or `RENAMES` changes which bundles belong in it — `SLING_OLIVEDRAB_BAG`
was missing precisely because the store predated its promotion, and Tau's `--check-only` found
it. Rebuild with the converter then re-run the repack; do not copy files in by hand.

Two bugs in the repack were caught by that verification rather than by review, and both would
have shipped silently:

- Running with source == destination made every `copyfile` throw, so a whole "successful" run
  repacked **nothing** while reporting done.
- Mapping the externals table positionally overrode the correct per-material mapping. DRIP's
  externals are not in vanilla's order, so **190 materials** ended up pointing at a valid CAB
  that was not the shaders bundle. Precedence now favours the per-material mapping, with
  positional filling only the slots no shader reads.

**Residual risk, named:** the four `HATS/ARMYCAP/*` bundles use a locally embedded `Standard`
shader compiled by Unity 2018/2019. Every other material now binds to a shader the current
game ships, but those four carry their own — which is the one place the original
"2019 shader in a 2022 runtime" theory could still genuinely apply. If anything renders wrong
after the repack, check those first.

**Still unproven: whether any of it renders in game.** Structural correctness is not visual
correctness, and nothing here has been seen by a client. Deploy is pre-verified: all 365
staged bundles land in a directory that already holds their config, none orphaned.

### Re-verified against the install it will actually be tested on

The repack was built against `SPT4.0.13`'s vanilla assets, but DRIP will be tested on
`F:/SPT/Base` — see "Which install" below. Re-ran `verify_repack.py` over the **build output**
(`bin/Debug/DRIP`, i.e. the exact payload that gets installed) against **Base's** `shaders`
bundle: 365 bundles, 543 materials into the live shaders bundle, 4 resolving in-bundle,
**0 broken.** So the claim now covers the artefact-as-installed on the install-as-tested, not
just the staging copy on the machine it was built against.

**A bug in the verifier, found while doing that.** The copy of `verify_repack.py` moved into
`tools/bundles/` was the *pre-fix* version, which treats `m_FileID == 0` as "out of range" and
so reported the four healthy `HATS/ARMYCAP` materials as broken. The 547/547 figure above came
from a later scratchpad copy that was never the one checked in. Now fixed properly: `fileID == 0`
means "shader lives in this bundle", and rather than being waved through it is checked against
the bundle's own `Shader` objects and reported on its own line. Falsified before being trusted —
handed a decoy bundle in place of `shaders` it reports 5/5 broken and names the reason, so the
check is load-bearing rather than vacuous.

Worth stating plainly: **the verification tool was the least-verified thing in the workstream**,
and it was the one making all the claims.

### The art library is one bundle short of Part 1 — matters for the rebuild, not for tonight

Disk has 365 Part 1 bundles; `DRIP-art-library/manifest.json` records 364. Rather than explain
the gap, I diffed the two by path tail: the missing one is **`SLING/OLIVEDRAB/GEAR.bundle`** —
the Part 3 bag Sophia promoted into Part 1 *after* the art extraction ran. Nothing subtle.

Consequence is narrow: the repack covered it (it is in the 365 above and it resolves), but a
rebuild driven from `manifest.json` would silently skip it. **Re-run `extract_art2.py` before
the rebuild**, and treat "manifest count == on-disk bundle count" as a precondition of the
rebuild rather than something to check afterwards, since promotions change the corpus.

### Which install — DRIP tests on `F:/SPT/Base`, never on `F:/SPT/SPT4.0.13`

`F:/SPT/SPT4.0.13` is the **Framesaver team's measurement corpus** (Framesaver + BigBrain +
Waypoints + SAIN + LootingBots). Their gates depend on it staying single-version and
single-config, and installing a texture mod there invalidates it. Do not install DRIP into it,
and do not "just try one raid" there.

`F:/SPT/Base` is DRIP's test install. Server mods live at `Base/SPT/user/mods/`, which currently
holds `WTT-ServerCommonLib` and `EcoAttachmentEmporium`; client plugins include Framesaver,
WTT's client libs and `UseItemsFromAnywhere`. **Those other mods are a confound we own** — a
failure on Base needs isolating before it is attributed to DRIP.

Verified rather than assumed that this substitution is safe: Base's `shaders` bundle and vanilla
hands bundle are **byte-identical** (same MD5) to 4.0.13's, so the repack's hard-coded CAB name
and shader pathIDs are valid there. That is why the two workstreams can run in parallel tonight
instead of taking turns.

### Size reduction cannot avoid Unity — investigated and rejected

The shader fix worked by repointing a pointer, so the obvious next thought is to repoint
`_BumpMap` / `_SpecMap` at vanilla's textures and stop shipping our identical copies. It does
not work, and the reason is worth recording so nobody re-derives it:

**Vanilla's own material holds those textures locally** (`fileID=0`), inside the vanilla
bundle. Repointing would mean appending the vanilla bundle to DRIP's externals table and
depending on it at runtime — but DRIP's bundle *self-declares that same vanilla path*, so the
game would be asked to load two bundles claiming one identity. That is precisely the shadowing
risk in `CLIENT-SMOKE-TEST.md` §6.1, the one failure mode that breaks the **base game** rather
than DRIP. Avoiding it would need the bundle's internal identity renamed as well, stacking
three unverified modifications to save disk.

Unity gets the dependency graph and bundle naming right by construction. So the rebuild stays
the tool for size — **and since it is needed anyway, it fixes the 286 missing mipmaps for
free.** No separate mipmap spike is worth running.

> **SUPERSEDED 2026-07-31. Every claim in the paragraph above is now wrong and the conclusion
> reversed.** Internal identity *can* be renamed — proven, pixel-identical, so a fresh CAB is
> cheap rather than a third unverified modification. Size was recovered without Unity: 313 MB.
> And the mipmap count is **475, not 286** — the 286 was stale or measured over a subset.
>
> **Do not "fix" the mipmaps.** Three reasons, in increasing order of how much they settle it:
> a full mip chain adds ~⅓ to a texture, so it would add **~190 MB against a goal of removing
> size**; Sophia has watched for the aliasing across several raids and in the 3.x years and never
> seen it, and Colette would have raised it as a polish issue on bots before anyone; and the
> remaining argument — reduced sampling cost — is dead on Framesaver's PresentMon data, which
> shows this workload is **entirely CPU-bound with GPU headroom to spare**. If it ever returns it
> should return as a measurement from Gamma, not as a line in this file.

Known gap: vanilla materials carry a `_TintMask` texture slot that DRIP's lack. Unity
generally defaults absent properties, but it is the most likely cause if the repack renders
imperfectly rather than not at all.

This does **not** fix missing mipmaps or the 77% size problem — only a rebuild does. It is a
parallel fast path to make content visible, not a replacement for the rebuild.

**Blocked on:** a Unity 2022.3.43f1 project for the full rebuild, and whether the community
has an existing 2022.3.43f1 clothing template — with Sophia. The repack spike is not blocked.

---

## Client smoke test — first live results, 2026-07-29

**Nine of ten mechanisms had never met a game client before tonight.** Run on `F:/SPT/Base`
(SPT **4.0.11** — see below), profile BORK, Reserve on High, pinned arm ~20 minutes.

### §6.7 duplicate bundle identity — DOES NOT REPRODUCE

The risk that headed this checklist all day. Bots pinned to `TSHIRT_HEADPAT_WINTER_TOP`, player
wearing `TSHIRT_AGENDA_TOP`; all ten `TSHIRT_*` variants declare themselves to be
`tshirt_bear_black.bundle`.

| Population | Observed |
|---|---|
| `assault` (scav) | HeadPAT — and its *unpinned* DRIP top pool is empty, so the pin overrode nothing-at-all |
| Gluhar's followers ×6 | HeadPAT — across three distinct escort types |
| PMCs, multiple | HeadPAT |
| Player throughout | Gay Agenda |

Two bundles claiming one vanilla path were live simultaneously across three bot populations for
twenty minutes and **resolved independently every time.** So the rebuild is quality work on a
schedule, not a fix for a shipping bug. The interim levers (one variant per family,
`addClothingToBots: false`) stay unbuilt.

**The scav is the strongest sample, not the PMCs** — Kappa's point and he is right. `assault` has
an *empty* DRIP top pool when unpinned, so the pin overrode nothing at all and the client resolved
a DRIP path **with no vanilla competitor to fall back on**. A partial failure had nowhere to hide
there. The PMC case is weaker precisely because a fallback existed and could have masked one.

### The unpinned arm — `fine / fine`, so neither failure mode reproduces

Same raid, pin removed, texture variety restored from one garment to dozens while bot count and
renderer composition stayed identical. Scavs, PMCs, Raiders and Gluhar's full garrison: **no
graphical issues, no magenta, no stutter, no pop-in.**

Against the differential in `CLIENT-SMOKE-TEST.md` §6.7 that is the *both-clean* row: duplicate
bundle identity does not reproduce, **and neither does texture-variety cost.** §5.3 and §5.4 pass
with it — bots wear DRIP and render correctly.

One caveat on what the unpinned arm could see. Gluhar's garrison is close to a null sample for it:
`followergluharassault` 0/0, `followergluharscout` 0/0, `followergluharsecurity` 0 tops / 5
bottoms, and `pmcbot` (Raiders) 0/0. So the diversity observed on those bots is mostly vanilla.
**The populations that actually exercised texture variety were `pmcusec` (23/20), `pmcbear`
(33/24) and `exusec` (17/0)**, and those are the ones the result rests on.

**So the rebuild's justification is now entirely non-urgent:** 4.8 GB of duplicated vanilla
content, 286 missing mip chains, and the 49 dangling mesh pointers. Nothing on that list is a
rendering emergency.

**Also settled, and the database could not have told us:** `bossGluhar` brings **6** followers on
High, not 8. The `Supports` entries **supersede** the primary `BossEscortType` rather than
stacking with it. And Gluhar himself is unclothed, which is correct — `bossgluhar` is not in
`ClothedBotTypes`, only his followers are.

### Bugs the client found that no server check could

- **Magenta half-mask on a scav.** Predicted from static analysis an hour earlier, then observed.
- **Missing wristwatch** on the player's hands.
- **Blank inventory cells** — 6B23, BSS-MK1, Blackhawk! Commando.
- **Shiny white** — IOTV (all variants), OPS-Core FAST MT, and the AirFrame's NVG shroud only.

### Root cause: three pointer types, and the repack only ever fixed one

Every DRIP bundle references vanilla content by an `(external CAB, pathID)` pair. The bundles
were cloned from an older game build, so both halves went stale. `repack_all.py` walks
**materials** to find and fix them — which means it only ever saw one of the three:

| Pointer | Symptom | Fixed by the repack? |
|---|---|---|
| Material → **Shader** | magenta | **yes** |
| MeshFilter / SkinnedMeshRenderer → **Mesh** | blank inventory cell, no model | no |
| Material → **Texture** | missing watch and glasses, white parts | no |

`verify_repack.py` counts materials too, so **a bundle with no materials passed vacuously** —
that is the half-masks, whose every external is dead. **"547 of 547" was only ever a claim about
bundles that contain materials.**

Full audit is `tools/bundles/audit_refs.py`. Current numbers, and note the qualifier:

```
 49  Mesh: DANGLING pathID
809  Texture: DANGLING pathID   (_Cube 532, _MainTex 121, _BumpMap 78, _SpecMap 78)
 16  dead externals             (7 of the 20 CABs the pack references do not exist)
 13  bundles whose meshes are ALL external
 10  bundles with NO materials
```

**228 of the 809 are the watches** (`bear_wach`, `watch_usec`, `watch_bear`). **1204 texture
pointers are local (`fileID 0`) and unaffected**, which is exactly why the garments themselves
render correctly and only the shared vanilla sub-materials — watch, glasses — are missing.

The rebuild eliminates all three classes at once, since rebuilt bundles resolve their own
references. Remapping in place is possible but name-ambiguous: `ar_6b23_mesh` contains **two**
meshes both named `AR_6B23_lod0` with different pathIDs, so a name lookup needs a tiebreaker.

### Load order — the worst bug of the night, and it was invisible until someone bought something

DRIP registered at `PostSptModLoader + 2` (**1,100,002**). Profiles are loaded *and validated* at
`SaveCallbacks` (**700,000**). So DRIP's customization templates were written 400,000 priority
units **after** the validator looked for them, and **any profile that owned a DRIP suite was
marked invalid on the next server start.**

It stayed hidden through every clean load all day because it only fires once a profile actually
owns one. Sophia bought three T-shirts, restarted, and the profile bricked.

**Do not follow SPT's own advice on this.** The error instructs the user to set
`removeModItemsFromProfile: true`. `CheckForOrphanedModdedData` runs **six** validators and
`RemoveInvalidItems` is *first* — it deletes every item with a missing template from inventory
**and insurance**, then clothing, then trader purchases. Worse, `RemoveInvalidUserBuilds` has no
config gate and constructs no exception: a player with a DRIP item in a saved weapon or equipment
build loses that build **silently, on any config**.

Kappa's fix moves DRIP to `PostDBModLoader + 2` (400,002), which also fixes two things nobody had
connected: DRIP's own traders never received a `NextResupply` timestamp (set at 800,000), and
DRIP items were added after static flea prices were generated (1,000,000).

**Measured cost of moving early, and it is inherent rather than a bug to engineer around:** Fence's
assort is *generated* at `TraderCallbacks` (800,000), not loaded at 200,000. So a mod running
before 800,000 cannot mirror Fence. Profile validation needs us before 700,000 and Fence needs us
after 800,000 — **contradictory, so no single slot satisfies both.** Trader offers drop 217 → 115
and 20 configs lose their seller. Those 20 resolve cleanly:

- **13 configs / 5 base items** (Slick, TacTec, A18, THOR, Tac-Kek) have **no root offer at any
  trader**. Fence-only — and since `GenerateFenceBaseAssorts` walks the entire item list, "Fence
  sells the original" was always vacuous. **These were miscategorised before the move. Give them
  their own price.**
- **7 configs / 6 base items** (TriZip, IOTV-HighMob, 6SH118, Blackjack, AirFrame, FAST MT) each
  have exactly one root offer and **every one is quest-locked** (236 locked ids across 8 traders,
  in `questassort.json`). **Do not reprice these** — DRIP is correctly refusing them, and
  overriding it re-opens the 3.x leak at `collection.ts:213-217`.

### `removeExistingPmcWaves` — the config that has caught us out twice

`PmcConfig.RemoveExistingPmcWaves` is **true**, so `PostDbLoadService.RemoveExistingPmcWaves()`
strips every `pmcUSEC` and `pmcBEAR` entry from every map's `BossLocationSpawn` and
`customPmcWaves` injects different ones — **14 on Lighthouse, 14 on Reserve, several at 100%.**

**Any reasoning that starts from a location file's declared PMC entries is reasoning about a
population SPT deleted at load.** It caught me once concluding PMCs were preset-sensitive from
`base.json`, and again concluding Lighthouse could not dose the mipmap contrast because `exusec`
is the only clothed type in its garrison — when in fact PMCs outnumber Rogues there better than
2:1 and arrive on a wave schedule rather than a chance roll.

The general form, and it is the same one as the `MaxBotsAliveOnMap` and `BotMax` mistakes:
**config-driven `PostDbLoad` rewrites sit between the database files and the raid.** Reading the
files alone silently answers a question about the wrong layer.

### `ClothedBotTypes` is not the list of bots that can wear DRIP

It is the list DRIP **attempts** to clothe. Of its 13 entries, measured from a live load:

- **4 come back with an empty top pool** — `assault`, `marksman`, `pmcbot`, and three of the
  Gluhar followers. `assault` matters most: **no DRIP top retextures a scav garment**, so scavs
  contribute zero distinct tops however many spawn.
- **2 hold the two largest pools in the table and never spawn at all** — `usec` and `bear` have
  no wave, boss or escort entry on any map. They are the 3.x names, superseded by
  `pmcusec`/`pmcbear`.

**Five roles can actually put a DRIP top on screen:** `exusec`, `pmcusec`, `pmcbear`,
`followerbully`, `followerkojaniy`. Bottoms are a different set: `assault`, `marksman`,
`pmcusec`, `pmcbear`, `followergluharsecurity`, `followerkojaniy`.

Recorded because handing "the list" to someone as if it meant "who can wear DRIP" caused a 2×
error in Framesaver's dose count. **In-the-list and can-wear-DRIP are different populations.**

### Which install, and the shared port

`F:/SPT/Base` is **SPT 4.0.11**, not 4.0.13 — DRIP's assembly refused to load against it, which is
the *loud* version of a version mismatch and the reason it was caught. It compiles clean against
4.0.11 and was retargeted for tonight. **The EFT client is byte-identical across both installs**
(0.16.9.40087, same `globalgamemanagers` hash), so client-side findings transfer; only
server-behaviour findings need re-running on 4.0.13.

**Both installs bind `127.0.0.1:6969`.** Separate directories are not separate state. Only one
server can run at a time, and launching a client from one install while the other's server holds
the port produces a **silent cross-wire** — wrong version, wrong profile, no error. Give the
fresh 4.0.13 install port **6970** so that failure becomes a connection refusal instead.

> **Deploying to Base needs a 4.0.11 build. `bin/Debug/DRIP` is not it.**
> `DRIP.csproj` references `SPTarkov.*` **4.0.13**, so the normal build output will not load on
> Base and fails with an assembly error at startup. The source compiles clean against 4.0.11 with
> only the three `PackageReference` versions changed — no code changes were needed. The next
> person will reach for `bin/Debug/DRIP`, and it will be wrong. (Kappa's note, and he is right
> that the symptom is hard to trace if you are not expecting it.)

---

## Open with Sophia

Nothing. Both former entries are dead:

- ~~Who has Unity access to stand up the 2022.3.43f1 project.~~
- ~~Whether anyone has a working 2022.3.43f1 clothing or gear template.~~

**The rebuild was cancelled 2026-07-31** — all three of its justifications fell without Unity,
and the remaining Unity-only case (custom meshes) is out of scope for the first release. Do not
re-open these without re-opening the rebuild first.

Outstanding for Sophia is the **client smoke test §6**, and only part of it — see below.

## Known content bugs

**Release-blocking — Part 1**

- ~~**A Part 1 quest requires a Part 3 item.**~~ **Resolved.** Quest `669f78477ebc9a09e44cbd6d`
  needed `SLING_OLIVEDRAB_BAG`, which shipped only in Part 3. The item now exists at
  `CustomItems/BAGS/SLING/OLIVEDRAB/SLING_OLIVEDRAB_BAG.jsonc` and **all 19 quests load** — every
  server run since 2026-07-31 reports `19 quests, 5 icons`. This row said "18 of 19" for longer
  than it was true; if you are reading it as current state, check a log first.

**Not release-blocking, Parts 2/3**


- Part 2: a TOP and a BOTTOM both named `INFILTRATOR_NIGHTGREY_PANTS`.
- Part 3: two different `TSHIRT_KHAKI` at different prices.
- `ZASLON_SOC_PANTS` exists in both Part 1 and Part 3 — the collision guard catches it.
- Two files declare a bundle that is not on disk; both have likely never worked.
