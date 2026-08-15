# What looks removable and is not

Internal engineering note (Kappa). Companion to the "five that must be told" in `RELEASING.md`.

A new maintainer can find what is *used* — the compiler and a grep will both tell them. What they
cannot find is what appears unused and is load-bearing. This is that list, with the measurements
behind it, so the next person can re-derive it rather than trust it.

Every count below is over the C# source only: **19 files, 4,287 lines**, measured 2026-07-30.

---

## The headline: a naive sweep is wrong far more often than it is right

A "delete members with no external references" pass over this codebase flags **99 of 181 declared
names**. Nearly all 99 are private helpers used inside their own file, which is what a private
helper is. The true-positive count is approximately zero.

The sharper cut is worse, not better. **Nine members have nothing but their declaration — no
reference anywhere, including their own file — and all nine are load-bearing:**

```
Author   Contributors   SptVersion   Incompatibilities   ModDependencies
Url      IsBundleMod    License      ModGuid
```

Every one is a `public override` on `AbstractModMetadata`, consumed by SPT's mod loader through the
base class. They are the mod's identity block. Deleting them stops DRIP loading, and they would
appear to be the nine safest deletions on the list.

**The general form, and the reason this file exists:** the risk is not deleting something used, it
is deleting something whose use is invisible to the check being used. Nothing textual reaches a
framework contract, an accessor chain, or a content author's intent.

---

## Four categories, with different answers

### 1. Framework contracts — invisible to any textual check

The nine overrides above. Also anything bound by attribute rather than by call: `[Injectable]`
registration, `[JsonPropertyName]` binding, `IOnLoad`. The code that consumes these is in SPT, not
here, so no amount of searching *this* repository will find the caller.

### 2. Accessor chains — a field read only by a property that is itself read

Both known instances resolve correctly and both look dead to a shallow check:

- `botWeightMultiplier` → `EffectiveBotWeightMultiplier` → `DRIPCustomItemService.cs:306`
- `currency` → `CurrencyRaw` → `Currency` → `CurrencyTpl` → assort service and clothing service

A check that excludes `Models/` condemns both. A check that includes `Models/` absolves everything,
because every field is referenced by its own accessor. `tools/bundles/unconsumed.py` has the first
blind spot and its only finding to date — `botWeightMultiplier` — was a false positive.

### 3. Intentionally unused — Sophia has ruled, and the code cannot say so

`botWeightMultiplier` is the example: deliberately a real knob rather than a vestigial field, unset
meaning 1.0, kept so the first person to write `0.5` genuinely gets one. Identical to dead code from
any angle a tool can see. **The rulings live in the settled-decisions table in `STATUS.md`** — check
there before removing anything that looks like an unused option.

### 4. Modelled but never implemented — a missing feature, not dead code

**This category has produced real bugs and deleting it would have been the wrong fix both times.**
`addToBots` was set by 274 configs and read by nothing; `addClothingToBots` likewise. Both were
missing implementations, not residue. The fix was to implement them.

Audited 2026-07-30: **all 36 JSON-bound config fields are consumed**, following accessor chains.
The category is currently empty. Re-run this audit rather than assuming it stays empty — a field
added to a model and not wired up looks exactly like a field that is no longer wired up.

---

## Specific things not to tidy

- **The `+ 2` in `DRIP.cs`'s `[Injectable(TypePriority = ...)]`.** Encodes "one slot after
  WTT-ServerCommonLib", which registers at `PostDBModLoader + 1`. Nothing in the code expresses
  this and DRIP declares no dependency on WTT — every available signal says tidy it to `+ 0`.
  Documented at the declaration; see also `RELEASING.md`.
- **The load-order comment block in `DRIP.cs`.** Longer than the code it annotates, and that is
  correct: it is the only defence against a change that silently invalidates player profiles. It
  names all three consumer stages and why no single slot satisfies them.
- **The two options objects in `DripJson`.** `Options` is case-insensitive for DRIP's configs;
  `SptTypeOptions` is case-sensitive because `TemplateItemProperties` declares both
  `ShotgunDispersion` and `shotgunDispersion` and is unconstructable case-insensitively. They
  differ in one flag and look like duplication. Merging them breaks thirty armour items and
  nothing else.
- **The isolation wrapper `Run(...)` in `DRIPVerificationService`.** Looks like defensive noise
  around calls that "cannot throw". One of them did, on exactly the input it existed to detect, and
  killed the server. Nothing in a verification pass is worth a failed startup.
- **The four TODOs in `DRIPCustomTraderService`.** Notes recording real unfinished work — config
  injection, trader avatar, name/surname construction. They are the only record that this is the
  least-finished file in the mod.

## What was actually removed

One thing, and it was a correctness fix rather than a deletion: six commented-out
`// await wttCommon.*` lines in `DRIP.cs`. Two of the six named locales and quests, which DRIP
implements twenty lines above — so the block advertised as missing two features that exist.
Commented-out code that no longer compiles against a vendored dependency decays like any other
comment and **a build cannot catch it**.

That is the entire WTT residue in the 4.x codebase. There is no vendored WTT code, no abandoned
services, no dead models. Any impression of a large WTT surface comes from the 3.x tree.
