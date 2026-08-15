# Quarantine — items pulled from Parts 2 and 3, pending Colette and Amber

Nothing here is deleted and nothing here is a tooling failure. Each entry is a **content
decision nobody on the engineering side should make**, so the item was moved out to let the
packs load, and the decision queued.

**To restore any of them:** move the directory (or the `.jsonc`) back to the path its name
encodes, in **both** trees — `Mods/DRIP/bundles/ContentPacks/` and
`SPT-DRIP-Test/SPT/user/mods/DRIP/bundles/ContentPacks/`. Nothing else needs re-running.

Pulled 2026-08-01 by Echo, on Sophia's call.

## The two ID collisions

Two files deriving one item ID. The loader hard-errors on differing content, which would have
blocked the whole pack.

| entry | what happened |
|---|---|
| `Part3__..__DESERTTAN__TSHIRT_KHAKI.jsonc` | The `DESERTTAN` folder held **two** configs — its own correct `TSHIRT_DESERTTAN.jsonc` plus a stray `TSHIRT_KHAKI.jsonc` that also claimed the same `TOP.bundle`. That one file caused both the ID collision with the real `KHAKI/TSHIRT_KHAKI.jsonc` **and** a shared-model-bundle violation. **Removing it costs nothing** — both real t-shirts still ship. |
| `DIR_Part2_INFILTRATOR_NIGHTGREY_TOP` + `DIR_Part2_INFILTRATOR_NIGHTGREY_BOTTOM` | Two genuinely different garments — a top and a bottom — both named `INFILTRATOR_NIGHTGREY_PANTS`, so both derive one ID. **Both are now out and the decision is a rename.** |

**Read this before restoring the Infiltrator pair.** Echo first kept the bottom and pulled the
top, reasoning that a *top* named `..._PANTS` had the wrong filename for its content. That was
backwards: the **bottom** is the one that never loaded, because its bundle is named
`INFILTRATOR_NIGHTGREY_PANTS.bundle` while its config declares `BOTTOM.bundle` — the converter
had already flagged it with *"this item may never have worked."* The top had a proper
`TOP.bundle` and `HANDS.bundle` and was the working one.

So restoring the pair needs **two** fixes, not one:
1. a new filename for one of them, so the IDs stop colliding, and
2. the bottom's bundle renamed to `BOTTOM.bundle` to match what its own config already asks for.

## Failed to load

| entry | what happened |
|---|---|
| `DIR_Part3_BLACKLYNX_ORANGE` | `TACTICALHOODIE_ORANGE_TOP` declares a `HANDS.bundle` that **does not exist** — the folder has `ORANGE.bundle` and `TOP.bundle`. Already recorded in `CONFIG-SCHEMA-v2.md` as a known Part 3 content bug. Either the hands bundle was never built, or `ORANGE.bundle` is it under the wrong name. |

## Buyable and unequippable

| entry | what happened |
|---|---|
| `DIR_Part3_BANSHEE_RUSSIANSPLINTER`, `_SPETSNAZSPLINTER`, `_USEC` | These **loaded fine** — they are not failures. They were caught by the self-check for offers that arrive with a required slot empty: a player can buy them and cannot equip them. All four `Soft_armor_*` slots come through empty. |

The trader is `579dc571d53a0658a154fbec` — **Fence**. DRIP loads at 400,002 and Fence's assort is
generated at 800,000, so Fence has no assort when DRIP looks and `copyOriginalOffers` **cannot**
mirror it. Sophia's read is that Fence selling these at all is a misconfiguration in the 3.x
original.

Note these are `CustomItems/ARMOR/BANSHEE`, a different base item from the `CustomItems/RIGS/BANSHEE`
rigs in Essentials and Part 2 — those are unaffected and still ship.

Two ways back if they are wanted: give them `includedParts` so they arrive with soft armour
whatever sells them, or fix whatever routes them to Fence.

## Confirmed on a running server, 2026-08-02 06:02

With these eight out, all three packs load with **zero errors**. Every figure moved by exactly
what was removed, which is what makes this a verification rather than an impression:

| | before | after | why |
|---|---|---|---|
| items | 274 | **271** | −3, the BANSHEE armours |
| own-priced offers | 76 | **73** | −3, same |
| flea presets | 112 | **109** | −3, same |
| clothing that failed to load | 2 | **0** | Infiltrator bottom, orange hoodie |
| self-check problems | 2 | **1** | buyable-and-unequippable cleared |

**No working garment was lost.** Clothing *successes* were 69 (Part 2) and 61 (Part 3) both before
and after — the quarantine removed only things that were already failing or already unequippable.

The one remaining self-check problem is `28 no trader sells`, which is the pricing queue and not a
defect.

## What this is NOT

None of these are pointer, dependency, mesh or conversion problems. Parts 2 and 3 came through
that pipeline clean — 456/456 pointer-backed dependencies declared, 0 unresolved pointers, 844
meshes stripped with zero ambiguity refusals. Every entry here is authored content that two
different files disagree about, and only the content owners can say which is right.
