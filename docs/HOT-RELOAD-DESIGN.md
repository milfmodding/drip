# DRIP texture hot-reload — dev plugin design

**Status:** v0.2.0 built, 2026-08-15 late. Client survey measured; decisions locked with
Sophia (textures-only, Colette and Amber are the audience, preview-only, **scoped matching
required before hand-off**). Compiled and deployed; in-client verification pending (human).

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

**Update, Sophia's ruling (23:33):** name-only matching would confuse the content owners —
it recolours every jacket variant at once — so **scoped matching is required before any
hand-off** (v0.2.0). The rule: a PNG in a subfolder applies only to bundles whose path
contains the subfolder (`HotReload/WINTERJACKET/DRIP/Top_BOSS_Shturman_d.png`), which also
lets several variants be edited side by side. PNGs in the folder root keep name-only,
all-bundles behaviour (the quick-test case).

How scope is known (measured): Unity gives no back-reference from a loaded Texture2D to
its bundle, and SPT's client `BundleManager.Bundles` holds only manifest metadata
(`BundleItem`: filename/CRC/deps — surveyed across spt-*.dll, 2026-08-15), not
`AssetBundle` instances. So the plugin records paths itself: Harmony postfixes on
`AssetBundle.LoadFromFile/Async` capture (bundle, path) at load time — engine API, no game
internals — and a texture→bundle map is built from each bundle's `GetAllAssetNames()`,
cached and rebuilt when a new bundle finishes loading. Bundles that predate the plugin or
load from memory are invisible to scoped applies; that is stated in the toast, never
hidden, and a scoped miss never silently falls back to all-bundles.

For a preview tool the every-match rule (still true for root PNGs) is acceptable and
honest: it is visible, harmless, and reversible.

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
