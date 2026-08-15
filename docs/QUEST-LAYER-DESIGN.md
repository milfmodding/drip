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

1. **`NewQuestDetails.Locales` shape** — dict of language → *what*? For items it is
   `Dictionary<string, LocaleDetails>` (`Name`/`ShortName`/`Description`); quests need
   arbitrary keys (`<questId> name`, `<conditionId>`, `successMessageText`…). *Settle by:*
   one disassembly of `CustomQuestService.CreateQuest` (ILSpy is on this machine for the
   client source) or a one-quest experiment on the test install.
2. **Does CreateQuest validate reward targets?** — if it rejects a bad trader id we can
   delete our resolution of that class; if not (expected, per `Reward.Target` being a plain
   string) ours stays. *Settle by:* the same disassembly pass.
3. **Quest id derivation** — item ids derive via `DripIds.Derive(stem)`; quest ids should
   use the identical function so cross-references (`"quest": "GLOCK_WICK"`) resolve through
   one mechanism. No open question, just the rule.
4. **LockedToSide** — all 19 current quests are `Pmc`; expose only if someone asks.

## What is deliberately NOT here

- `drip new quest` scaffolding — blocked on Colette's mockup pick (A/B/C); orthogonal to
  the layer, which reads whatever format is agreed (and the format *is* agreed — §3-5).
- The GUI — future work item 3, unchanged.
- Weapon presets — explicitly out (proposal §"ordering").

## Sequencing

1. Settle open questions 1-2 (one sitting, disassembly or experiment).
2. `DRIPQuestFormat` model + loader path in `DRIPCustomQuestService` (new branch, old
   branch kept until the 19 are converted).
3. Converter `--quests` mode for the existing corpus; flip; retire the old path.
4. Validation: extend `drip check` (DRIP-5xx) for quest references — proposal §6's list,
   minus what's now structural (ids can no longer disagree with locale keys by
   construction).
5. `drip new quest` once Colette picks.

Estimated 2-4 afternoons end to end; step 1 first because it can change step 2's shape.
