# Pre-registered signature mapping — the mipmap / material-variety question

**Written 2026-07-29, before any DRIP-present measurement leg has been run.** That is the whole
point of the document. Alpha proposed registering the mapping in advance because the two
candidate outcomes land on different desks, the signatures are close enough to argue about, and
whoever reads the result first has an interest in which way it goes.

Written afterwards this is unfalsifiable, and the person it exonerates is the one holding the pen.

## Independent drafts, deliberately

Alpha offered to draft this and let me attack it. I asked for the opposite arrangement: **we each
write our prediction without seeing the other's, then exchange.** Attacking someone's draft
anchors me to their framing, and an agreed document written by two people in conversation is one
prediction with two signatures, not two predictions. This file is the DRIP half. Framesaver's
half lives in their structured predictions file.

If the two drafts disagree about what a signature means, that disagreement is the most valuable
thing either of us will get out of this, and it only exists if neither of us saw the other first.

## What is being measured

A DRIP-present versus DRIP-absent leg on Lighthouse, using Framesaver's frame decomposition:
CPUBusy and GPUBusy split by the PresentMon `CPUStartQPC` join, per-window medians for
`aiTotal`, `playerLate`, `playerTick` and the render phase.

The DRIP-present arm loads garment textures of which **286 of 333 diffuse maps have no mip
chain** (vanilla ships 12 levels), and raises unique material count per raid from vanilla's small
garment pool to potentially dozens.

## The mapping — committed in advance

| CPUBusy | GPUBusy | Verdict | Whose problem |
|---|---|---|---|
| flat | rises | **Sampling bandwidth / texture cache.** Missing mip chains, sampled at full resolution regardless of distance. | **Mine.** The rebuild regenerates mip chains and fixes it as a side effect of work already scoped. |
| rises | rises | **Draw-call setup from unique-material count**, with a sampling cost on top. | **Sophia's**, and she will hate it. The fix is reducing garment variety per raid, which is a content decision, not a build-pipeline one. The rebuild does *not* fix this. |
| rises | flat | **Draw-call setup alone.** Material variety, no meaningful sampling cost. | Sophia's, same as above, and it would mean the mipmap story was never the issue. |
| flat | flat | **Neither.** No detectable cost from DRIP's texture payload at this bot count. | Nobody. The rebuild still proceeds — it is justified by 4.8 GB of duplicated vanilla content and the duplicate-identity fix, independent of performance. |

## The escape hatch, named in advance

**If both move but in proportions that fit neither story** — for example GPUBusy rises by a large
multiple of CPUBusy, or either moves in a direction the table does not predict at all — the
verdict is **"unresolved, insufficient to attribute"**, and the next step is a third arm, not a
narrative. Specifically: pinned versus unpinned with DRIP present, which holds bot count and
renderer composition identical while collapsing texture variety to one garment. That contrast
isolates variety from presence.

I am writing that down now because "the numbers were mixed, but on balance it looks like X" is
exactly the sentence this document exists to prevent.

## What would make me abandon my own preferred branch

My preferred outcome is row 1 — it makes this my problem and my problem is already scheduled.
So, stated in advance:

- **If CPUBusy rises by more than the noise floor** (Framesaver measured 0.68–0.74 ms), I do not
  get to call it sampling. That is the threshold, fixed now, before I know the answer.
- **A rise in the render phase specifically, with `aiTotal` flat**, points at draw-call setup
  regardless of what GPUBusy does, because AI cost is not where material variety would land.
- **I do not get to argue that the bots were unrepresentative** unless the exempt fraction differs
  materially between arms. Framesaver measures `exempt` per raid, so this is checkable rather
  than assertable.

## Why Lighthouse, and a caveat about it

Framesaver measured `exempt` at 9 of 24 bots there — boss- and escort-class roles never enter
stand-by and are never animator-culled, so their materials stay resident and animating for the
whole raid. **DRIP clothes that population**: `exusec` (Lighthouse's Rogues), `pmcbot`, `pmcusec`,
`pmcbear` and the five followers are all in `ClothedBotTypes`. It is the population where a
texture-variety cost would surface, and Framesaver already has a full decomposition for that map
and build.

**Caveat:** that same property makes Lighthouse the *worst case*, not the typical one. A result
there is an upper bound on the cost, and should be reported as one. A scav-dominated map would
show less, and most players are not on Lighthouse.

## Related

- `tools/bundles/README.md` — the extraction that produced the 286-of-333 figure.
- `CLIENT-SMOKE-TEST.md` §6.7 — the pin, which is the knob the third arm would use.
- [[falsify-checks-before-trusting-them]] is the general form of why this file exists.
