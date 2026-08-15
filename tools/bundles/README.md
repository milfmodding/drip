# Bundle and audit tooling — Echo's workstream

Python, UnityPy required (`pip install UnityPy`). These were written during the 4.x port and
moved here from a session scratchpad because Sophia signed off on the bundle rebuild being a
**reusable pipeline** rather than a one-off migration — which makes these pipeline components,
not throwaway analysis.

Every result quoted below was verified when written. Re-run rather than trust: several of these
exist *because* a plausible number turned out to be wrong.

---

## The rebuild pipeline

### `repack_all.py` — repoint stale shader references

```
python repack_all.py <src-root> <game-StreamingAssets-Windows> <out-root>
```

Fixes the magenta rendering. Every DRIP bundle records the vanilla bundle it was cloned from;
this reads that origin, looks up the vanilla counterpart's *current* externals entry and shader
pathIDs, and rewrites both. Safe in place (src == dst).

**Why two things are rewritten, not one:** a material's shader pointer is
`(fileID → the Nth external, pathID)` and *both halves* were stale. Fixing only the pathID
leaves it resolving through a CAB that no longer exists.

**The precedence bug worth not reintroducing:** per-material mapping must win over positional
mapping of the externals table. DRIP's externals are not in vanilla's order, so mapping the
table positionally puts the wrong CAB in the slot the shader reads. That silently broke 190
materials in an otherwise "successful" run.

Result on Part 1: 365 bundles, **547 of 547 materials resolve** — 543 into the live `shaders`
bundle, 4 to a Unity `Standard` shader embedded in the `HATS/ARMYCAP/*` bundles themselves.
Those four are the residual risk if anything still renders wrong.

### `verify_repack.py` — prove it worked

```
python verify_repack.py <repacked-root> <shaders-bundle>
```

Checks every material resolves to a shader that actually exists, via an external naming the
live shaders bundle. **Run this after every repack.** It caught both repack bugs; without it
the run reported success twice while having done nothing and then having half-worked.

Note `fileID == 0` means "shader is in this bundle" and is valid. **The copy first checked in
here was the pre-fix version that got this wrong**, so it reported the four healthy ARMYCAP
materials as broken and the 547/547 figure quoted above came from a scratchpad copy that was
never committed. Now handled explicitly: `fileID == 0` is checked against the bundle's *own*
`Shader` objects and counted on its own line, rather than either being flagged or waved through.

Falsified before being trusted: hand it a decoy bundle in place of `shaders` and it reports every
material broken with the reason named. **If you change this script, break it on purpose and
confirm it screams.** It is the thing making all the claims in this workstream, and for a while
it was the least-verified thing in it.

### `contact_sheet.py` — look at the art before choosing a fixture

```
python contact_sheet.py <dir-of-pngs> <vanilla-bundle> <out.png>
```

Tiles a set of extracted diffuse maps plus the vanilla original into one labelled sheet. Written
for smoke test 6.7, where the fixtures have to be **visually** distinguishable and I had picked
two garments that were not — both black shirts with a chest graphic, chosen because they shared a
vanilla origin, which was the only property I had checked.

Generalises past that: a test whose fixture cannot fail *visibly* records "I could not tell" as
"looked fine". `docs/tshirt-reference.png` is the output for the T-shirt family.

### `extract_art2.py` — get the artwork out

```
python extract_art2.py <pack-dir> <game-StreamingAssets-Windows> <out-dir>
```

Content-addressed PNG pool plus a manifest mapping every bundle to its vanilla origin and
textures. Extracts **everything** and deduplicates by exact hash of decoded pixels.

**Do not reintroduce threshold-based filtering.** An earlier version decided per texture whether
it differed from vanilla using a mean-delta threshold; re-encoded vanilla measures ~1.5 and
genuinely retextured art ~5.6, which is far too close to separate safely. Guessing wrong loses
irreplaceable art — and 26 of 302 normal/gloss maps *do* genuinely differ, so "only the diffuse
changes" is true as a tendency and false as a rule.

Part 1: 1216 texture instances → 686 distinct, 1.5 GB at
`F:/SPT/Mods/DRIP-art-library/`. 391 images / 894 MB are genuinely modified art.

---

## Audits — one-off, but re-runnable as evidence

| script | what it establishes |
|---|---|
| `questmap.py` | Recovers the `DRIP_N` → MongoId quest mapping by matching locale text. 19/19, zero ambiguous. The mapping now lives in `QUEST_ID_MAP`; this is how to re-derive it. |
| `mongotime.py` | Corroborates that mapping independently, by decoding MongoId creation timestamps. Zero inversions, strictly monotonic — 17 quests made in one 27-minute sitting on 2024-07-23. |
| `suitability.py` | Which DRIP garments each bot type should wear, derived from vanilla appearance pools. Reference numbers for Kappa's implementation. |
| `unconsumed.py` | Config fields that are *modelled but never read*. Found `addToBots` unimplemented. **Known blind spot:** it excludes `Models/` from the search, so a field consumed through an accessor defined there reads as dead — that produced one false positive. |
| `shadow_list.py` | Which vanilla bundle paths our bundles claim. 120 distinct, **79 claimed by more than one DRIP bundle** — the duplicate-identity risk in `CLIENT-SMOKE-TEST.md` §6.7. |

---

## The thing that makes the rebuild possible

`tools/vanilla-origins.json` records each garment's lineage **outside the bundle**. Before it
existed, keeping the bot-suitability derivation working across a rebuild would have required
rebuilt bundles to keep vanilla names — which is exactly what creates the §6.7 duplicate-identity
risk. Recording lineage externally is what lets the artefact change freely.

So rebuilt bundles can carry whatever internal names Unity assigns. **Do not force vanilla
names.**
