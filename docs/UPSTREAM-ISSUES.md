# Upstream SPT issues found while porting DRIP

Bugs that live in the SPT server rather than in DRIP. Recorded here so they don't get lost, and so that whoever
reports them has the evidence to hand. None of these are blocking DRIP today; all of them are worked around.

---

## 1. `ValidateQuestAssortUnlocksExist` indexes `QuestAssort` unguarded

**Where:** `SPTarkov.Server.Core/Services/PostDbLoadService.cs:747-752` (verified against 4.0.13)

```csharp
var mergedQuestAssorts = new Dictionary<MongoId, MongoId>();
mergedQuestAssorts = mergedQuestAssorts
    .Concat(traderData.QuestAssort["started"])
    .Concat(traderData.QuestAssort["success"])
    .Concat(traderData.QuestAssort["fail"])
    .ToDictionary();
```

The method loops over **every trader in the database** and indexes `QuestAssort` by three hardcoded lowercase keys.
The null check immediately above it (`if (traderData.QuestAssort is null) continue;`) guards the dictionary itself but
not its contents.

**Impact:** any mod that registers a custom trader whose `QuestAssort` is missing one of those keys — or spells them
with different casing, since `Dictionary<string, …>` is case-sensitive by default — crashes the server during
`PostDbLoad` with a `KeyNotFoundException`. The stack trace points at SPT, not at the mod that caused it, so the
reporting user will file it in the wrong place.

DRIP hit exactly this: the trader service was creating `Started`/`Success`/`Fail`. It did not actually crash, purely
because DRIP registers its traders at `OnLoadOrder.PostSptModLoader + 2`, which runs *after* `PostDbLoadService`. Any
mod registering traders earlier trips it immediately, and DRIP is one `TypePriority` change away from tripping it too.

**Suggested fix upstream:** `TryGetValue` per key, or seed missing keys with an empty dictionary before merging.

**DRIP workaround:** lowercase keys in `Services/DRIPCustomTraderService.cs`, with a comment explaining why they must
stay lowercase.

---

## 2. Shared `JsonUtil` options are stricter than modded content can be authored

**Where:** `SPTarkov.Server.Core/Utils/JsonUtil.cs:17-28` (verified against 4.0.13)

Two related problems for mods that ship author-edited config files and read them via
`ModHelper.GetJsonDataFromFile`:

- **`AllowTrailingCommas` is never set**, so it defaults to `false`. `ReadCommentHandling = Skip` *is* set, which
  makes the format look like JSONC — but JSONC and JSON5 both treat a trailing comma as idiomatic. 279 of DRIP's 546
  content configs contain one, as did both of the example files shipped in the DRIP scaffold. Every one of them
  throws.

- **`UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow` under `#if DEBUG`.** A config carrying any field
  the mod's model doesn't bind loads fine on a release server and throws on a debug one. Combined with
  case-sensitive property binding, a simple casing typo in a config field is silently ignored in Release and fatal in
  Debug — behaviour that differs by build configuration, which is harder to diagnose than either failure alone.

**Impact:** mods can't safely use the shared helper to read their own authored content, and the failure mode depends
on how the user's server was built.

**Suggested fix upstream:** either set `AllowTrailingCommas = true` on the shared options, or — better — expose a
separate set of lenient options intended for mod-authored content, so server data files can stay strict.

**DRIP workaround:** `Utils/DripJson.cs` derives its own options from the server's (keeping all registered
converters) with `AllowTrailingCommas`, `PropertyNameCaseInsensitive`, and `UnmappedMemberHandling = Skip`.

---

## 3. The bundle hash cache never prevents a hash

**Where:** `SPTarkov.Server.Core/Services/BundleHashCacheService.cs:76-90` (verified against 4.0.13)

```csharp
public async Task<uint> CalculateMatchAndStoreHash(string BundlePath)
{
    var hash = await CalculateHash(BundlePath);          // <- always reads the whole file

    if (!MatchWithStoredHash(BundlePath, hash))
    {
        await StoreValue(BundlePath, hash);
    }

    return hash;
}
```

The cache is consulted *after* the hash has already been computed, and only to decide whether to store it. So
`bundleHashCache.json` never saves any work: every bundle is fully read and CRC32'd on every server start whether or
not it is cached and unchanged.

**Impact:** proportional to total bundle size, not to how much has changed. DRIP Part 1 is 3.1 GB across 365
bundles, which costs ~2.7s of startup on an SSD and considerably more on a mechanical drive. All three DRIP parts
will roughly double that. Any large bundle mod pays this on every restart, and modders restart a lot.

A cache keyed on size plus last-write time, falling back to a full hash when either differs, would skip the read
entirely in the common case.

**Second, smaller issue in the same area:** `WriteCache()` is only called at the end of
`BundleLoader.LoadBundlesAsync`, which returns early for any mod without a `bundles.json` manifest. A mod that
registers bundles programmatically via `AddBundle` therefore never persists its hashes at all. Currently harmless
precisely because of the bug above — the cache does nothing either way — but it would become a real gap the moment
the cache started working.

**DRIP workaround:** none, deliberately. The cost is tolerable, the CRC served to the client has to be correct, and
a mod-side cache keyed on file metadata would be guessing at something the server should own.
