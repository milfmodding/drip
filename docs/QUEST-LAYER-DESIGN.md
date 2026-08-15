# Quest authoring layer — design

**Status:** design, 2026-08-15, per Sophia's direction ("a better layer on top of it like we
did for items"). Nothing here is built. Grounded in: QUEST-FORMAT-PROPOSAL.md (the format),
QUEST-TEMPLATE-MOCKUP.md (the scaffolding choice, Colette's pending), the current
`DRIPCustomQuestService`, and the measured 4.1 API shapes.

## The one-line summary

Items got easier by calling SPT's `CustomItemService.CreateItemFromClone` with a details
object. Quests get easier the same way: **a small authoring format that expands into a
fully-built `Quest`, fed to SPT's `CustomQuestService.CreateQuest` via `NewQuestDetails`** —
which is exactly `{ Quest NewQuest, Locales, LockedToSide }`. The API does insertion,
locale wiring and attribution; the layer does derivation, grouping and reference resolution.

## What each side owns

Measured against the two known cost centres: the 153-lines-per-quest problem and the
georgia/moron reward crash (see the long comment in `DRIPCustomQuestService`).

| Concern | Owner | Notes |
|---|---|---|
| 22 top-level quest fields | **layer** — six are constant across all 19 quests, the rest derive or default | e.g. `side: Pmc`, `instantComplete: false` |
| condition/reward ids | **layer** — derive from quest id + position (proposal §3) | kills ~10 invented ids/quest |
| condition grouping (Start/Finish) | **layer** — derived, 66/66 by condition type | author never sees it |
| objective/reward vocabulary | **layer** — `handover`/`kill`/`at`, `experience`/`standing`/`item`/`unlock` map to the 4+4 condition/reward types the corpus uses | CounterCreator only ever carries Kills+Location |
| inline text → locale keys | **split** — layer builds the locale *table* (`<questId> name/description/…`, `<conditionId>` for objectives); **CreateQuest** inserts it via `NewQuestDetails.Locales` | the 32 bare-MongoId keys stop being hand-maintained |
| trader alias resolution | **layer**, before the Quest is built — `DripTraders.TryResolve` on `trader` and on every `standing`/`unlock` reward | the crash class the API does *not* catch (verified: `Reward.Target` is a plain string) |
| item-by-name resolution | **layer** — same derive-and-check as today (`ResolveItemNameReferences`) | quests may name pack items by filename |
| quest insertion + attribution | **CreateQuest** — `_id` conflicts, `templateTable.Quests`, mod cache by GUID | what the API actually buys us |
| images | unchanged — `ImageRouter.AddRoute` beside the configs | |

## Pipeline

```
A_WILD_NIGHT.jsonc          (authoring format, ~15-25 lines)
  → expand()                layer: derive ids, defaults, grouping, resolve names/traders
  → NewQuestDetails {       fully-built Quest + locale table + side lock
        Quest, Locales, LockedToSide }
  → CustomQuestService.CreateQuest(NewQuestDetails)
  → templateTable.Quests    with attribution in ModItemCacheService
```

Loader entry mirrors items: one file per quest under `CustomQuests/`, filename derives the
quest id (same trick as 276 items). The existing keyed-blob `DRIP.jsonc` format converts
once via `convert-legacy.py` (a `--quests` expansion mode emitting the friendly format), so
one format survives — proposal §5's "no build step, read it directly" ruling applies: the
loader reads the friendly format; the full Quest JSON is never authored or shipped.

## Why feed CreateQuest rather than writing `templateTable.Quests` directly (as today)

1. **Attribution** — items we create via the API are known to `ModItemCacheService` by mod
   GUID; quests should be too, or profile-validation and future tooling sees them as
   second-class.
2. **Locale insertion** — the locale-table plumbing is the API's, not ours; our current path
   hands locales to the pack locale service separately and the two can drift.
3. **We are already on this road** — the item loader converged in the port; quests are the
   same decision at one-tenth the size.

Cost: none identified. The API validates little that we care about (insertion conflicts
excepted), so our reference-resolution stays authoritative regardless.

## Open questions, each with a cheap settle

1. **`NewQuestDetails.Locales` shape** — **SETTLED 2026-08-15 by IL disassembly + reflection:**
   `Dictionary<string, Dictionary<string, string>>` — language → arbitrary key → text. Arbitrary keys
   is exactly what quests need (`<questId> name`, `<conditionId>`, `successMessageText`…); no
   LocaleDetails constraint, no schema to fight. `AddQuestLocales` (dumped) iterates the dict,
   requires each language to exist in `LocaleTable` (`could_not_find_language_key`), rejects empty
   per-language dicts, and inserts via the same `AddTransformer` our locale service already uses
   on `LazyLoad` values — so insertion composes with the pack locale pass instead of racing it.
2. **Does CreateQuest validate reward targets?** — **SETTLED 2026-08-15 by IL disassembly:**
   `CreateQuest` is 216 bytes of IL and contains exactly three code paths: duplicate-id rejection
   (`quest_id_already_exists`), empty-locale rejection (`no_languages_for_quest`), then
   `AddQuestLocales` + `RestrictQuestSide`. **No reward validation whatsoever** — our
   trader-alias/item resolution stays load-bearing, exactly as the design assumed. Bonus finding:
   `RestrictQuestSide` validates `LockedToSide` and its error strings are localised — the API is
   stricter than expected on side, looser than expected on everything else.
3. **Quest id derivation** — item ids derive via `DripIds.Derive(stem)`; quest ids should
   use the identical function so cross-references (`"quest": "GLOCK_WICK"`) resolve through
   one mechanism. No open question, just the rule.
4. **LockedToSide** — all 19 current quests are `Pmc`; expose only if someone asks. Note the
   API validates it (see 2), so exposing it later costs nothing in safety.

## What is deliberately NOT here

- `drip new quest` scaffolding — blocked on Colette's mockup pick (A/B/C); orthogonal to
  the layer, which reads whatever format is agreed (and the format *is* agreed — §3-5).
- The GUI — future work item 3, unchanged.
- Weapon presets — explicitly out (proposal §"ordering").

## Sequencing

1. ~~Settle open questions 1-2~~ **DONE 2026-08-15** — see above; both settled in favour of
   the design as written, no shape changes needed.
2. ~~`DRIPQuestFormat` model + loader path in `DRIPCustomQuestService`~~ **DONE 2026-08-15**
   (95ba62f) — structural discriminator (`"objectives"` member) routes a file to the
   expander; the legacy blob path is retained for Glock Wick: Part 1.
3. ~~Converter `--quests` mode; flip~~ **DONE 2026-08-15** (0b98d20, 322ae3d) — 18/19
   converted (Glock Wick: Part 1 stays legacy: Started Item reward outside the friendly
   vocabulary); the flip rewrote 66 item gates to the filename-derived ids and filtered
   the blob to its one-quest remainder, verified on a live server (19 quests,
   self-check unchanged). The Python-side derivation was verified byte-for-byte against
   the real SPTarkov `HashUtil` before rewriting.
4. ~~Validation: extend `drip check` (DRIP-5xx)~~ **DONE 2026-08-15** — codes below.
5. `drip new quest` once Colette picks.

## drip check codes for quests

All run over the friendly files only; the legacy blob is the converter's business.
Cross-pack dependencies aggregate to one message per pack (CONFIG-SCHEMA-v2 §8 rule 6).

| Code | Severity | Catches | Example shape |
|---|---|---|---|
| `DRIP-503` | error | `trader`, or a `standingWith`/`unlock` reward, names a trader that doesn't resolve | `There's no trader called "gerogia".` + did-you-mean |
| `DRIP-504` | error | a `handover` or `item` reference is neither a pack filename nor a real item id (checked against the packs plus the game's database when one is found) | `The handover names "SLICK_CADPT_ARMOR", which is neither an item ID nor a DRIP filename.` |
| `DRIP-505` | error | `requires.quest` is a quest nothing defines — or the quest requiring itself | `This quest requires "A_WILD_NGHT"...` + did-you-mean over the pack's quest filenames |
| `DRIP-506` | warning | `image` names a pack icon whose `.png` isn't beside the quest configs (MongoId-stemmed names are vanilla icons served by the client — not checked) | `"image" names "Boozy", but there is no Boozy.png...` |
| `DRIP-507` | warning | an objective has no `text`, so players would read the auto-generated sentence | names the exact auto-text they'd see |
| `DRIP-508` | warning | one per pack: quests reference items no pack being checked ships | names the items; checking all packs together clears it if they resolve |

`DRIP-502` (item gates naming a quest nothing defines) predates these and now resolves
both spellings of a friendly quest's id — the derived MongoId or the bare filename —
because the loader resolves filenames the same way.
