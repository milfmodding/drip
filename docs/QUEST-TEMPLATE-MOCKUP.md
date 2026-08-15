# `drip new quest` — three mock-ups, to be chosen between

**Status:** a prop for a conversation with Colette, not a spec. Nothing here is built.

**Why it exists:** Colette said what actually stops her, and it was not what
[QUEST-FORMAT-PROPOSAL.md](QUEST-FORMAT-PROPOSAL.md) was designed against.

> "Having to go get IDs and figure out the order they're supposed to be in etc, and iirc I
> couldn't really make a template to do it easily besides basing it off previously done ones."
>
> "Basically ADHD brain hav hard time bc a ton of stuff I barely understand is in front of me
> and I have to figure out how to piece it together to not break. It's not *that* bad — but it
> does often dissuade me from doing more of either."

The proposal measured the file format — ~153 lines and ~10 hand-invented ids per quest — and
inferred that **verbosity** was the barrier. Her answer says it is **cognitive load, ordering,
and having no starting artefact**. Those want different things built. A generator that emits
153 correct lines fixes the typing and leaves the barrier standing.

**Ask her which of the three below she'd rather see appear**, not whether the idea is good. She
has been gracious about this process for years and "is this what you wanted?" will get a yes.

---

## What we're counting

Two numbers, because they are the ones her answer implies and they can be held to:

- **on screen** — lines in the file when it is created
- **to decide** — things she must supply before it works. Everything else is derived from the
  filename, defaulted, or absent.

For comparison, today a quest is **~153 lines** with **22 top-level fields** and **~10
hand-invented 24-character ids**, and every word the player reads lives in a different file.

---

## A — only the decisions

```jsonc
{
  "name": "A Wild Night",
  "trader": "moron",

  "objectives": [
    { "handover": "VODKA", "count": 2, "text": "Bring me two bottles of vodka." }
  ],

  "rewards": [
    { "experience": 4500 }
  ]
}
```

**on screen: 12 · to decide: 4**

Nothing is present that she doesn't have to fill in. The risk is that *"what else can go in
here?"* has no answer on screen — she'd have to know to look it up, which is close to the
position she is in today.

---

## B — the decisions, each explained

```jsonc
// A Wild Night   (the file's name is the quest's ID - nothing else to invent)
{
  "$schema": "../../../docs/drip-quest.schema.json",

  "name": "A Wild Night",

  // Who gives it out. 'moron' and 'georgia' are DRIP's own traders.
  "trader": "moron",

  // What the player has to do. Add as many as you like; order doesn't matter.
  "objectives": [
    { "handover": "VODKA", "count": 2, "text": "Bring me two bottles of vodka." }
  ],

  // What they get. Any of: experience, standing, item.
  "rewards": [
    { "experience": 4500 }
  ]
}
```

**on screen: 19 · to decide: 4 · unexplained things: 0**

Longer than A, and possibly *easier*, which is the thing worth testing. Her complaint was
"stuff I barely understand", not "too many lines" — and a comment that explains a field removes
more load than deleting the field would. **Fewer characters and fewer unfamiliar things are not
the same goal**, and A and B differ on exactly that.

The `$schema` line is what makes VS Code autocomplete and underline mistakes as she types, so
it earns its place even though she never edits it.

---

## C — a working quest, to edit in place

```jsonc
// A Wild Night   (the file's name is the quest's ID - nothing else to invent)
{
  "$schema": "../../../docs/drip-quest.schema.json",

  "name": "A Wild Night",
  "trader": "moron",
  "image": "Boozey.png",

  "description": "Heyyy, come in, come in! I need a favour, bro.",
  "onSuccess": "Yooo, you're a badass. Good shit too, cheers bro.",

  // Only start this once the player is level 2 and has finished GLOCK_WICK.
  "requires": { "playerLevel": 2, "quest": "GLOCK_WICK" },

  "objectives": [
    { "handover": "VODKA", "count": 2, "text": "Bring me two bottles of vodka." },
    { "kill": "AnyPmc", "count": 5, "at": "Interchange", "text": "Kill five PMCs on Interchange." }
  ],

  "rewards": [
    { "experience": 4500 },
    { "standing": 0.03 },
    { "item": "TSHIRT_COLETTE_TOP" }
  ]
}
```

**on screen: 25 · to decide: 4 (the rest are examples to change or delete)**

This is **the workflow she already has** — copy a previous quest and change it — except
generated fresh, guaranteed to work, and with nothing in it she has to reverse-engineer. It
shows what is possible by demonstrating it, which is the one thing A cannot do.

The cost is that everything here is a decision she didn't ask to make. Deleting is easier than
inventing, but it is not nothing.

---

## The ordering complaint — solved, and worth saying out loud

> "figure out the order they're supposed to be in"

**There is no order in any of the three.** Objectives are a list, rewards are a list, and
prerequisites go in `requires`. Nothing has to be sequenced by hand.

This is not a presentational choice — it is measured. In today's format each condition must be
filed into `AvailableForStart` or `AvailableForFinish`, and across all 19 quests **66 of 66**
follow from the condition's own type with no exceptions: `Level` and `Quest` always gate the
start, `HandoverItem` and `CounterCreator` always gate the finish. So the grouping is derivable
and she never has to think about it.

**Presets are the open one.** For weapons the ordering problem is attachment and slot sequence,
which is real, and DRIP does not do presets at all today. Nothing here addresses it and nothing
should pretend to.

---

## Questions worth asking with these in front of her

1. **Which of the three would you rather have appear?** (Not: is this better than today.)
2. **A or B** — do the explanation comments help, or are they more to read?
3. **Adding a second objective** — is copying a line the obvious move, or is that its own puzzle?
4. **The `text` on each objective** is what the player reads. Is having it right there what she
   wanted, or would she rather write all the text in one place?

---

## What "done" looks like

Her own calibration sets the bar, and it is lower and more measurable than a blocker:

> "It's not *that* bad — but it does often dissuade me from doing more of either."

So the win condition is not "make quests possible". It is **make them frictionless enough that
she writes more**, and the metric is whether she does.
