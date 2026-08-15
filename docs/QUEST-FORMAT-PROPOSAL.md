# Quests: why they're painful, and a proposed format

**Status:** thinking, not building. For Sophia, Echo and Kappa to react to.

Sophia's framing is the point of this document:

> "Quests are a huge pain in the ass to add, and that's the major reason that Colette never
> added more than the few that you see in the repo. I know that she'd had so many ideas she'd
> like to execute on."

So the authoring cost isn't friction — it has been *suppressing content for years*. Nineteen
quests exist against "so many ideas". That's the thing to fix.

---

## 1. What a quest costs today

Measured from Part 1's `CustomQuests/DRIP.jsonc` and `CustomLocales/en.json`:

| | |
|---|---|
| quests | 19 |
| lines of JSON | 2,919 — **~153 per quest** |
| ids invented by hand | 183 — **~10 per quest** |
| locale strings | 216 |
| …of which keyed by a raw 24-character id | 32 |

**Every word a player reads lives in a different file from the quest.** Some entries are keyed
`<questId> description`, which is at least guessable. Thirty-two are keyed by a bare MongoId —
the id of the condition they describe:

```
"669a2d0bb5dd3cfc7a97282a": "Find in-raid and handover two bottles of Vodka."
```

To write one objective, an author invents a 24-character id, puts it in the quest file, then
opens a second file and uses that same id as a key. Nothing checks the two agree. Nothing tells
you if they don't — the objective simply renders blank.

That is the single worst authoring experience in this project, and it is worse than "the text is
in another file". The *link* is an opaque string the author had to make up.

---

## 2. The vocabulary is tiny

Nineteen quests use four condition types and four reward types, and nothing else:

```
conditions   HandoverItem 23   Level 19   Quest 15   CounterCreator 9
rewards      Item 46           Experience 19   TraderStanding 18   TraderUnlock 1
```

The fields each one actually carries are equally small — the rest is bookkeeping:

| type | what it really needs |
|---|---|
| `Level` | a number |
| `Quest` | which quest, and what status |
| `HandoverItem` | which item, how many, found-in-raid or not |
| `CounterCreator` | what to kill, how many, optionally where and with what |
| `Item` reward | which item, how many, found-in-raid or not |
| `Experience` | a number |
| `TraderStanding` | which trader, how much |
| `TraderUnlock` | which trader |

Two more things are fully derivable and never need writing:

- **Which group a condition belongs in.** `Level` and `Quest` are always `AvailableForStart`;
  `HandoverItem` and `CounterCreator` are always `AvailableForFinish`. 66/66, no exceptions.
- **Six top-level fields are identical in all 19 quests** — `side`, `isKey`, `restartable`,
  `secretQuest`, `instantComplete`, `canShowNotificationsInGame`.

`CounterCreator` looks like the hard one and isn't. Across all nine uses it contains only
`Kills` and `Location` sub-conditions.

---

## 3. Proposed shape

Text inline, ids derived, everything mechanical generated:

```jsonc
{
  "name": "A Wild Night",
  "trader": "moron",
  "image": "Boozey.png",

  "description": "Heyyy, come in, come in! How's it goin', bro? ...",
  "onSuccess": "Yooo, you're a badass, dude! Good shit too, cheers bro.",

  "requires": { "playerLevel": 2, "quest": "GLOCK_WICK" },

  "objectives": [
    { "handover": "VODKA", "count": 2, "foundInRaid": true,
      "text": "Find in-raid and hand over two bottles of Vodka." },
    { "kill": "AnyPmc", "count": 5, "at": "Interchange",
      "text": "Eliminate five PMCs on Interchange." }
  ],

  "rewards": [
    { "experience": 4500 },
    { "standing": 0.03 },
    { "item": "TSHIRT_COLETTE_TOP" }
  ]
}
```

Roughly 15 lines against 153. **The objective text sits on the objective**, so the id
disappears entirely rather than being made easier to type.

**Quest ids come from the filename**, exactly as item ids do — `A_WILD_NIGHT.jsonc` is the quest
`A_WILD_NIGHT`. Condition and reward ids derive from the quest id plus position. That is the
same trick already proven on 276 items, and it removes 183 hand-maintained ids.

---

## 4. On inline text — Echo's question

**Yes, inline, and the translator concern doesn't survive contact with the data.**

There is exactly one language today. `CustomLocales/` holds `en.json` and nothing else. So the
choice isn't "help authors or help translators" — it's "help the actual author, or preserve a
shape for a translator who does not exist and would be poorly served by it anyway."

Poorly served, because a translator arriving today would have to learn the naming convention
*and* the invented ids to work out which string is which quest's objective.

**Every text field takes either a string or a map of language to string** — Sophia's refinement,
and better than the export mechanism this section originally proposed:

```jsonc
"description": "Heyyy, come in, come in! ..."
"description": { "en": "Heyyy, come in ...", "ru": "Привет ..." }
```

A map must include `en`, since that is what unlisted languages fall back to.

That keeps every language in one place rather than splitting English from the rest, and there
is no round-trip to keep synchronised. The earlier proposal — English inline, other languages
exported to `CustomLocales/<lang>.json` — is demoted to a convenience for the day a translator
actually asks for a flat file, and becomes an *output* of the inline data rather than the
mechanism.

The same shape now applies to item text (`CONFIG-SCHEMA-v2.md` §4.2), so there is one answer to
"how do I write this in another language" across every config type rather than two.

The one real cost is unchanged: a quest's text and its mechanics live together, so a translator
editing text touches a file authors also edit. With one language and two authors that isn't
worth designing around now.

---

## 5. Read it directly — agreeing with Echo, for a recorded reason

Echo's call is that the loader should read this format directly rather than compiling to SPT
quest JSON as a build step. Agreed, and the reason is already written down in `STATUS.md`:

> two entry points that diverge is a trap this project has documented three times

A build step means the shipped artefact isn't the authored one. Every diagnostic then has to
choose which to describe, and `drip check` can't meaningfully validate generated output. It also
puts a command between Colette and her quest, which is the exact barrier being removed.

Convert the existing 19 once, so there is one format rather than two.

---

## 6. Validation matters more here than anywhere else

Quests reference things: items to hand over, items to reward, other quests, traders, images. A
broken reference doesn't crash — it produces a quest that can't be completed, which a player
discovers halfway through.

`drip check` should verify, before the server ever starts, that:

- every `handover` and `item` names something the pack defines, or a real vanilla item
- every prerequisite quest exists
- the trader resolves
- the image file is present
- every objective has text

**This is not hypothetical.** Implementing the first of these turned up 68 broken gates in Part 1
today — see §7.

**Cross-pack dependencies** get the same treatment as bundles and traders (`CONFIG-SCHEMA-v2.md`
§8 rule 6): if a pack's quests depend on a pack that isn't installed, that is **one pack-level
message naming the missing pack**, not one error per quest. A quest requiring a Part 1 quest is
a normal thing for Part 2 to do; it only becomes an error when Part 1 isn't there.

---

## 7. A live bug this analysis found

**68 of Part 1's 276 items are gated behind quests that do not exist.**

Every item `questRequirements` uses ids of the form `DRIP_1`, `DRIP_14`. Every quest in
`CustomQuests/DRIP.jsonc` is keyed by a MongoId such as `669a1606666bd606fa3f897a`. **Zero of
the 15 referenced ids resolve.**

| referenced id | items gated |
|---|---|
| `DRIP_14` | 13 |
| `DRIP_1` | 12 |
| `DRIP_12` | 10 |
| …11 more | 33 |

**This predates the port.** The 3.x source has the same mismatch — its quest file is already
MongoId-keyed while its item configs already say `DRIP_N`. The quests were regenerated with new
ids at some point and the item configs were never updated. It has presumably been shipping that
way.

The `DRIP_N` strings do still exist as *locale keys* in `en.json`, which is why the mismatch is
easy to miss: the ids look alive because text is still filed under them.

Consequence: those 68 items can never be unlocked through the quest that was meant to award
them. Whether they are unobtainable or simply free depends on how SPT treats an unresolvable
requirement — worth confirming with Kappa, but either behaviour is wrong.

**Fixed.** `drip check` reported it as `DRIP-502`, one error per item, and the mapping turned out
to be recoverable without any content knowledge: the renumbering left *both* key styles in
`en.json`, so each `DRIP_N` was matched to its replacement by its four text fields together
(`name`, `description`, `successMessageText`, `failMessageText`). 19 of 19 resolved, none
ambiguous — and the result is sequential by quest id order, so position corroborates the text
match independently. Derived twice, by Echo and again by me, agreeing.

The mapping lives in `QUEST_ID_MAP` in `tools/convert-legacy.py`, upstream of the converter
alongside `PROMOTIONS` and `RENAMES`, because an edit to a generated config is reverted by the
next run. All 68 items now gate on quests that exist, and `DRIP-502` is zero.

**One thing worth guarding.** Those old `DRIP_N` locale keys are the only surviving record of
the mapping, and they look exactly like dead weight — the sort of thing a tidy-up removes.
`QUEST_ID_MAP` is now the durable copy; it should not be deleted on the grounds that the locale
keys still exist.
