# SPT 4.1 migration map

Measured 2026-08-15 by reflection over the restored NuGet packages (SPTarkov.* 4.1.2,
`F:\SPT\SPT-4.1\SPT_Runtime` is a 4.1.2-RELEASE install, commit cf04a11). This is the
reference for the 4.0.13 -> 4.1 port so nobody re-derives it from build errors.

## The three structural breaks

1. **net10.0.** The 4.1 packages target .NET 10 (`NU1202` against net9.0). SDK 10.0.102
   is installed. `<TargetFramework>net10.0</TargetFramework>` and the three
   `PackageReference`s at 4.1.2.
2. **Database access is injection-first.** `DatabaseService`, `DatabaseServer`,
   `DatabaseTables` and `ConfigServer` are GONE. Services inject the tables they need
   directly: `TemplateTable` (was `Tables.Templates`), `LocaleTable` (`.Locales`),
   `TradersTable` (`.Traders`), `GlobalTable` (`.Globals`), `BotTable` (`.Bots`),
   `HideoutTable`, `LocationTable`. Configs inject as typed objects:
   `configServer.GetConfig<TraderConfig>()` -> inject `TraderConfig`. See any 4.1
   service ctor (e.g. `CustomItemService`) for the shape.
3. **Mod metadata is an interface.** `AbstractModMetadata` is gone;
   `SPTarkov.Server.Core.Models.Spt.Mod.IModMetadata` (Author, Contributors,
   HasPrepatcher, Incompatibilities, License, ModDependencies, ModGuid, Name, SptVersion,
   Url, Version - all get;set;). DRIP's `ModMetadata` record must become a class (or
   record with settable props) implementing it; init-only setters do NOT satisfy the
   interface's set accessors.

## Namespace moves DRIP's usings need

| 4.0 | 4.1 |
|---|---|
| `Models.Spt.Server` | GONE - the table/config types above live in `Models.Spt.Tables` / `Models.Spt.Config` |
| `Services.X` | `Services.Server.X` (BundleHashCacheService, PostDbLoadService...) |
| `Services.Mod.CustomItemService` | `Services.Modding.Custom.CustomItemService` |
| `Helpers.X` | `Helpers.Items.X`, `Helpers.Traders.X`, `Helpers.Profile.X`, `Helpers.Server.X` (ModHelper) |
| `Models.Utils.ISptLogger` | `SPTarkov.Common.Models.Logging.ISptLogger\`1` |

`Utils.Cloners.ICloner`, `Utils.JsonUtil`, `Routers.ImageRouter`, `Loaders.BundleLoader`,
`Models.Eft.Common.Tables.*` keep their names.

## IOnLoad and the load order

`IOnLoad` is now `Task OnLoadAsync(CancellationToken)`. `OnLoadOrder` lost BOTH
mod-loader slots (`PostDBModLoader`, `PostSptModLoader`); the 4.1 enum is:

```
0  Watermark      100k Preload(ImageRouteImporter)   200k GameCallbacks
400k Routers      500k HandbookCallbacks             600k SaveCallbacks
700k TraderCallbacks   800k PresetCallbacks          900k RagfairCallbacks   1M PostLoad
```

Measured `[Injectable]` priorities agree with the enum (only callbacks/routers carry
explicit ones; services default to int.MaxValue and are ordered by the host).

**DRIP's slot:** the old constraint was "DB loaded, before profile validation" and the
old answer was `PostDBModLoader + 2` (400,002). In 4.1 the equivalent window is
**any priority after DB hydration and before `SaveCallbacks` (600,000)** - DRIP also
wants to precede `HandbookCallbacks` (500,000), `TraderCallbacks` (700,000, resupply
timestamps) and `RagfairCallbacks` (900,000, flea static prices). A priority in
(400,000, 500,000) - e.g. `OnLoadOrder.Routers + 50000` = 450,000 - satisfies every
constraint with room either side. **The old "+2 after WTT" convention is retired
outright (Sophia's ruling, 2026-08-15): the WTT tooling was an abandoned pre-4.1
experiment, so there is nothing to re-derive against.**

**Not yet verified:** whether mods' `IOnLoad` types actually interleave with these
stages by priority (the enum suggests yes). The proof is running DRIP on the 4.1
server and watching the log position - not yet done.

## New capability worth knowing

4.1 ships a first-class modding API: `CustomItemService.CreateItemFromClone(...)` /
`CustomQuestService.CreateQuest(...)` in `Services.Modding.Custom`, plus
`ModItemCacheService` and `ProfileDataService`. DRIP predates it and hand-rolls its own
item creation; whether to converge on the official API is a refactor decision for
Sophia, NOT part of the mechanical port.

## Status

- [x] csproj: net10.0, packages 4.1.2, `SptVersion` "~4.1.0" (the field SPT hard-checks)
- [x] API surface mapped (this doc)
- [x] `ModMetadata` -> IModMetadata class
- [x] `DRIP.OnLoad` -> `OnLoadAsync(CancellationToken)` + new priority
- [x] Nine services: DatabaseService/DatabaseServer/ConfigServer -> table/config injection
- [x] Build clean, deploy to `F:\SPT\SPT-4.1\SPT_Runtime\user\mods`, server log shows DRIP loading

**VERIFIED ON THE RUNNING SERVER, 2026-08-15 20:20Z**: ModValidator accepts DRIP Core 2.0.0
(~4.1.0), all services fire, server starts and listens. **The mods folder is
`SPT_Runtime\user\mods\`** - the root-level `user\mods\` belongs to the launcher layout
and the server never scans it (cost an afternoon of "0 server mods" confusion).

**Deltas vs the 4.0.13 baseline that are NOT yet understood/fixed:**
- **14 items fail to create: `FleaPriceRoubles is null or 0 while trying to add to flea`**
  (6B43 x2, THORINT, RAID, BLACKJACK, TROOPER35, WELDINGSHIELD x2, ARMYCAP x4, AIRFRAME,
  FASTMT - the handbook-only/flea-less bases). 140 -> 126 created. The 4.0 path had a
  fallback; the 4.1 flea-price lookup path needs it restored. Real regression.
- Trader offers copied: 215 -> 110; own-priced 35 -> 29; and FOUR vanilla traders have no
  root offers at 450,000 (4.0.13: one, Fence). Assort timing in 4.1 differs at this slot.
- Self-check flags 6 multi-bundle folders with no dependency declared - was 0 on the
  stripped tree (which needed declarations). Pre-strip bundles are self-contained, so this
  may be a verifier calibrated to the stripped era; adjudicate with audit_refs.py before
  acting.
- Headless-launch trap: SPT.Server.exe crashes in Watermark.SetTitle() with no console
  (CREATE_NO_WINDOW/DETACHED). Launch with CREATE_NEW_CONSOLE.
