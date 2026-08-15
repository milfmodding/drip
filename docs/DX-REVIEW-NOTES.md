# DX review notes — where to attack this work

Written at handover by the person who built the DX surface (schema, converter, validation,
authoring tools, docs). **This is not a summary.** `STATUS.md` is the record of what was done and
why; `FUTURE-WORK.md` is the docket of what was deliberately deferred.

This document is the other thing, and the harder one to write: **the places where my own position
made me a bad reviewer of my own work.** A reviewer with fresh eyes has exactly one advantage over
me, and it is not diligence. It is not having decided anything here. So this is a targeting guide,
ordered by where I would look first.

Read this expecting to find things. Several of the entries below are not "watch out" but "this is
wrong and I did not fix it, here is the fix I would have made."

---

## 0. Who this software is for, because it decides every judgement call

**Colette and Amber own the content and do not write code.** Not "are junior developers" — do not
write code. A terminal command over a config file is already past the line.

This is load-bearing for review. A change that makes a tool more correct and less usable by them is
a regression here, and will not look like one in a diff. Conversely, a wall of explanatory comments
that a programmer would call noise is often the feature: in Colette's own words, what stops her is
*"a ton of stuff I barely understand is in front of me and I have to figure out how to piece it
together to not break."* Cognitive load, not verbosity.

The two rules I kept getting wrong in opposite directions, both worth holding while reviewing:

- **Fewer characters and fewer unfamiliar things are not the same goal.** A comment explaining a
  field removes more load than deleting the field would.
- **A template's job is to reduce what is on screen, not to fill the screen correctly.** A generator
  that emits 153 correct lines has fixed the typing and left the barrier standing.

---

## 1. The four repair tables in `convert-legacy.py` — highest risk in the codebase

`OVERRIDES`, `RENAMES`, `PROMOTIONS`, `SLOT_FIXES`. Every entry is a decision, keyed by a value a
human typed. **An entry whose key matches nothing does not fail, does not warn, and repairs
nothing** — while continuing to read like a fix that is in place.

This is not hypothetical. I typed a base-item ID for the wrong armour during development; it would
have silently repaired nothing, and I caught it by checking the entry against the game's slot
filters rather than by reading it. The more likely future version is duller: someone renames a
source file and the table entry quietly outlives its subject.

`tools/audit-tables.py` (read-only, added at handover) checks that every entry still matches
something. It currently reports **0 dead across all four tables**, and I falsified it both ways
before believing that — injected a dead key into each of the two key shapes, confirmed it exits 1
and names the entry, restored the file byte-identically.

**What it deliberately does not check, and please do not "fix" this:** `QUEST_ID_MAP` is excluded.
The four above are *repair* tables — each entry asserts a specific broken thing exists, so an entry
matching nothing is a defect. `QUEST_ID_MAP` is a *reference* table mapping all 19 DRIP quests to
their renumbered IDs, of which 15 currently gate an item. The other 4 are not dead; completeness is
the property you want, so any future item gating on any quest resolves. Auditing it would report 4
non-problems forever, and the first person to clean up the noise would delete four correct entries.

**What the audit cannot see, which is the part that should worry you:** it checks that each key
*matches* something, never that the value is *right*. A correctly-spelled key holding a wrong ID
passes cleanly and still repairs the wrong thing. `drip check`'s `DRIP-409`/`DRIP-410` independently
derive the slot conditions from the game's own data, which is the only real defence — see §3.

---

## 2. `price_review.py` is the tool I would review hardest

It is the only tool my constituency drives completely unaided, **and it writes to configs.** That
combination exists nowhere else in the project.

Two defects already found in it, both of which had been live since the tool existed, and neither of
which any test would have caught because both produced plausible output:

- The Level column read `profileLevel`. Gear gates on `loyaltyLevel`. **The column was blank for
  every gear row since the sheet was created** — invisible precisely because that column is often
  legitimately empty.
- The sheet showed a bare price with no currency, and the write path sets `price` without touching
  `currency`. About 20 of 171 prices are USD (=120 roubles) or EUR (=133). A reviewer moving a
  dollar price would have been out by 120x, silently.

The pattern in both: **a field that is correct in isolation and wrong in relation to another
field.** Look for more of those. My attention was on the round-trip mechanics.

---

## 3. The checks, and what each one structurally cannot see

Every check in `drip check` was built to catch something real, and each has a blind spot I know
about. The ones I do not know about are your job.

- `DRIP-408` (unsellable items) errors on 13 and stays silent on 7 correct quest-locked ones — but
  prints the count of the silent 7, because the server log adds the two and an author who sees 13
  in one place and 20 in another cannot reconcile them.
- `DRIP-409`/`DRIP-410` derive slot correctness from the game database. **They cannot run without a
  game install**, and `drip check` says so rather than passing quietly. Verify that message still
  appears when `tools/spt-path.txt` is absent; a check that degrades to silence is worse than one
  that was never written.
- The converter's bundle-dependency guard compares against **what is currently on disk**. It
  therefore warns *before* a loss and can never detect one that already happened. It buys time; it
  is not the fix. Stating that alongside "it works" is what stops it being filed as solved.

**The general one, and the thing I would most want a reviewer to internalise:** almost every error
found in this project was in *verification* code, not in the work being verified. A claim feels like
a claim, so you mark your confidence in it. A grep feels like a measurement, so you do not.

---

## 4. Two known defects, specified and deliberately not applied

I am writing these rather than shipping them, because a change landing after the team stands down
is a change nobody reviews. Both are small enough to review properly in a minute, which is the
point.

**4a. `DRIP-001` names three causes and omits the only invisible one.** `tools/drip.py:440`. When a
config will not parse, an author is told: *"A missing comma, a missing quote, or a stray bracket is
the usual cause."* All three are visible on screen. The corpus contains a real instance of the
fourth kind — `MARKSGORKA_BEREZKA_TOP.json5` has a **literal tab inside a string**, which is invalid
JSON and looks exactly like a space. An author would hunt for a bracket that is not there.

`json.JSONDecodeError` reports this distinctly (`e.msg` begins `Invalid control character`), so the
branch is available. Suggested wording, in the voice the other diagnostics use:

> There is a tab or other invisible character inside a piece of text here. It looks like a space
> but is not one. Delete the space at that position and retype it.

Note the converter's own reader already handles this via `repair_control_chars()` and reports the
repair — so this is a gap in the *author-facing* tools only. That asymmetry is exactly the kind of
thing that hides for a year.

**4c. `DRIP-102` cannot tell a harmless duplicate from a silent overwrite, and you will hit this
contradiction on day one.** As of handover, `drip check` reports **29 errors across the three
packs** while a verified server run of the same three packs reports **zero**. Both are correct, and
the reconciliation is a single measurable fact rather than a story:

28 of the 29 are `DRIP-408`, the known pricing queue, which is a work list rather than a defect.
The 29th is `DRIP-102` on `ZASLON_SOC_PANTS`, which ships in **both** Essentials and Part 3. The two
files are **byte-identical** (`md5 2e5e389b...`), so the loader — which hard-errors only on
*differing* content under one ID — is right to stay silent. `DRIP-102` keys on the filename alone
and cannot see that.

So the check is not wrong, it is *undiscriminating*, and the severity is what makes it expensive: an
error that a verified server run contradicts trains people to discount the mechanism. The loader
already implements the correct rule. Suggested split, matching it:

- same name, **differing** content -> error, as now. One silently overwrites the other.
- same name, **identical** content -> a note, not an error. Shipping one item in two packs may well
  be deliberate, so each pack stands alone when installed by itself.

I did not apply it because whether a duplicate is intentional is a **content** question for the pack
owners, and the answer decides whether the second bullet is a note or nothing at all. Do not silence
`DRIP-102` before that is answered — the differing-content case is a real silent-overwrite bug.

**4b. Four independent copies of the JSONC reader.** `strip_json5()` in `convert-legacy.py` plus
`strip_jsonc()` in `drip.py`, `price_review.py` and `build-release.py`. I diffed them at handover:
**the three `strip_jsonc` copies are behaviourally identical today** (one docstring differs), so
there is no live bug. The risk is purely future divergence, and 4a is the shape it would take —
the converter's path grew control-character handling and the other three did not.

I did not consolidate them because a shared module means an install step or a `sys.path` hack, and
these tools are deliberately runnable by double-click with a stock Python. If you consolidate,
**that constraint is the one to preserve**; correctness that costs the double-click is not a win.

---

## 5. My biases, stated so you can discount them

- **I built `drip new`, so "extend `drip new`" is the answer I reach for first.** When a user's
  answer once pointed the same way, it was rightly noted that *a bias pointing the right way is not
  a justified one* — the reason differed, and the reason decides what to build.
- **I once described a preventive guard as a caught bug.** Where I report a save, check whether the
  failure was actually reachable.
- **I am the author of every check, so I have never been surprised by one.** A reviewer who finds a
  check confusing has found a real defect, not a misunderstanding. The checks are written for
  someone who has never opened Visual Studio; if one reads as programmer-to-programmer, it has
  failed at its actual job regardless of whether it is correct.

---

## 6. Things that look wrong and are not — do not "fix" these

- **`vanilla-origins.json` is a record, not a cache.** After the bundle work, the value is no longer
  derivable from anything on disk. It was captured while it still was. Regenerating it is not
  possible; deleting it is not recoverable.
- **`DRIP-408` printing a count of items it deliberately does not flag** is not inconsistency. See §3.
- **The `- Copy.json5` source file in Part 1** is editor detritus carrying real content, handled by
  a `RENAMES` entry. It is ugly and it works; the source tree is read-only reference.
- **The 3.x tree at `Mods/DRIP-3.x-main/` is read-only.** Every correction lives in the converter's
  tables instead, because a fix applied downstream of a generator is a temporary edit — the next run
  reverts it, and the revert looks like success.
- **Part 1 converts 277 source files to 277 outputs, and that is a coincidence**, not pass-through.
  The sources are 275 item configs plus a quest file plus a locale file; the output is 276 items
  (275 plus one promoted from Part 3) plus one quest file. Two source files even share the stem
  `DRIP`, so any stem-keyed comparison collapses by one and can hide a genuinely missing item.
  **Compare by relative path.** Parts 2 and 3 have no quest or locale directories, so their source
  counts are already item counts.

---

## 7. If you change one thing about how this was built

Ship the check, then say in the same breath what it cannot see. Nearly every real defect here was
found by asking *"this is a count of what, exactly?"* and nearly none by re-reading the arithmetic.
A tool that reports what it skipped is worth more than one that runs clean, because a clean run that
quietly omitted a check is indistinguishable from a clean run that did not.
