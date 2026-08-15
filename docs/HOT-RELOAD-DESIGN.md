# DRIP texture hot-reload — dev plugin design

**Status:** design, 2026-08-15 late. Client survey measured; decisions locked with Sophia
(textures-only, Colette and Amber are the audience, preview-only). Not yet built.

## The problem it solves

Editing a texture today means: rebuild the bundle, redeploy, restart the server, re-enter
the raid — minutes per look, on work that is inherently "look, nudge, look again". The
plugin collapses that to: save the PNG, it appears on whatever is on screen.

## Measured client environment (2026-08-15, F:/SPT/SPT-4.1)

- **BepInEx 5.4.23.5** (BepInEx 5, not 6): standard plugin model, Chainloader,
  MonoBehaviour, `ConfigurationManager 18.4` already installed (config UI exists for free).
- **Unity "0.16.9.4074"** — Tarkov's custom version string; the APIs this needs
  (`Resources.FindObjectsOfTypeAll<Texture2D>`, `Texture2D.LoadImage`) are standard.
- **SPT 4.1.2** client, matching the server.
- Reference DLLs for building: `BepInEx/core` + `EscapeFromTarkov_Data/Managed`.

## How DRIP texture assets are named (measured over 12 bundles)

Vanilla-derived, lowercase, suffix-conventioned:

- Half-mask: `wildman_hats_d` / `_n` / `_g` (512–1024px)
- AirFrame: `helmet_crye_airframe_LOD0_diff_tan`, `..._nrm`, `..._gloss`
- Winter jacket: `Top_BOSS_Shturman_d` / `_n` / `_g`, `Hands_wild_bomber_d` ...

`_d`/`_diff` = diffuse (the one artists iterate), `_n`/`_nrm` = normal, `_g`/`_gloss` =
gloss. All are swappable by name; the diffuse is the 90% case.

**The collision, and why the plugin replaces every match:** three WINTERJACKET variants
(DRIP, HORNETSTRIPE, SOC) ship the *same* texture names (`Top_BOSS_Shturman_d`) — this is
the known "one vanilla path claimed by several bundles" property, measured again here.
A PNG therefore applies to **every loaded Texture2D with that name**. For a preview tool
that is acceptable and honest: it is visible, harmless, and reversible. If it proves
annoying in practice, v2 can scope by owning bundle (subfolder per item); not v1.

## Design

A dev-only BepInEx 5 plugin, shipped as a **separate optional download** (DRIP itself
stays server-only). Name: `DRIP.TexturePreview`.

- **Watch folder**: `BepInEx/plugins/DRIP.TexturePreview/HotReload/` (config-settable).
  Drop `texture_name.png` in; a FileSystemWatcher notices, decodes the PNG, and calls
  `LoadImage` on every loaded `Texture2D` whose name matches (case-insensitive).
- **Toast** on apply: name + how many instances changed (0 means "not on screen / not
  loaded", which is the single most likely confusion).
- **Hotkey** (default F8, config-bound): re-apply everything in the folder — covers
  watcher misses and "item just loaded after I saved".
- **Name discovery** (default F9): writes `texture-names.txt` beside the folder — every
  loaded Texture2D's name and size, so the artist never has to ask anyone what the asset
  is called. This is the piece that makes it usable without a programmer.
- **Preview-only, enforced**: the plugin never writes to the game folder, the server
  folder, or any bundle. The rebuild stays the real artifact; worst case is a
  weird-looking session.

## Known limits (stated to users, not hidden)

- Only affects textures that are **loaded** — the item must be on screen (in raid or an
  equip screen). A swap on a texture nobody loaded yet does nothing.
- Replaces all instances of a colliding name (see above).
- Mipmaps: `LoadImage` data may arrive without the original's mip chain — a distant
  texture can shimmer slightly. Preview-fidelity issue only; noted for v1 polish.

## Sequencing

1. Plugin project (net472, refs from BepInEx/core + Managed), build, deploy to
   F:/SPT/SPT-4.1.
2. Server-side test rig is useless here — verification needs a human in the client
   (Sophia or the content owners): drop a recoloured PNG, see it on the model.
3. Package as its own zip in the release, clearly labelled optional/dev.
