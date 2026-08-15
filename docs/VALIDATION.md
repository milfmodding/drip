# DRIP Config Validation — reference implementation

Companion to `CONFIG-SCHEMA-v2.md` §8, which defines the rules and the diagnostic catalogue.
This document is the working code for them.

**The code below is deliberately not shipped as `.cs` files.** SDK-style projects glob
`**/*.cs`, so dropping these into the mod folder would pull them into `DRIP.csproj` and break
the build before anyone chose to adopt them. Copy them into the project when you want them —
suggested home is `Validation/`.

---

## Why this exists

The port's current validators throw messages like:

```
masterySections[3].level2 is required
'type' must be 'top' or 'bottom', got 'TOP'.
```

The audience is people who retexture armour in GIMP. The second message is worse than the
first: it is *correct*, it names the offending value, and it still doesn't tell the reader that
lowercase is the fix, or which of their 275 files it came from. Meanwhile the throw aborts the
whole content pack, so one stray capital letter costs the author every other item too.

Three properties fix that, and they are all structural rather than cosmetic:

1. **Collect, don't throw.** One bad file loses one item.
2. **Every diagnostic names the file and the fix.**
3. **Report once, at the end.** Authors read the last screen, not the scrollback.

---

## 1. Diagnostics

```csharp
namespace DRIP.Validation;

public enum Severity { Info, Warning, Error }

/// <summary>
/// One thing worth telling the author about a content file. Rendered by DiagnosticReport;
/// never thrown.
/// </summary>
public sealed record Diagnostic(
    string Code,            // "DRIP-301" — stable, greppable, safe to put in a wiki
    Severity Severity,
    string File,            // path relative to the content pack, not an absolute path
    string Message,         // what is wrong, in plain language
    string? Fix = null)     // what to do about it, copy-pasteable where possible
{
    public static Diagnostic Error(string code, string file, string msg, string? fix = null)
        => new(code, Severity.Error, file, msg, fix);

    public static Diagnostic Warning(string code, string file, string msg, string? fix = null)
        => new(code, Severity.Warning, file, msg, fix);

    public static Diagnostic Info(string code, string file, string msg)
        => new(code, Severity.Info, file, msg);
}
```

---

## 2. Reading the files

Per `CONFIG-SCHEMA-v2.md` §7, SPT's shared `JsonUtil` options are wrong for author-written
files in three ways. DRIP needs its own, and must not route content configs through
`ModHelper.GetJsonDataFromFile`.

```csharp
using System.Text.Json;
using System.Text.Json.Serialization;

namespace DRIP.Validation;

public static class ContentPackJson
{
    /// <summary>For DRIP's own config classes, where authors type the field names.</summary>
    public static readonly JsonSerializerOptions Options = new()
    {
        ReadCommentHandling         = JsonCommentHandling.Skip, // authors comment their files
        AllowTrailingCommas         = true,                     // and leave trailing commas
        PropertyNameCaseInsensitive = true,                     // addtoBots == addToBots
        // Deliberately no UnmappedMemberHandling: unknown keys land in Extra so that 'tags'
        // survives for ICUP, and typos become DRIP-110 rather than a hard failure.
    };

    /// <summary>
    /// For binding anything that is an SPT/BSG model type. Case-SENSITIVE, and it must stay
    /// that way: TemplateItemProperties declares both ExplDelay/explDelay and
    /// ShotgunDispersion/shotgunDispersion, and under case-insensitive matching
    /// System.Text.Json refuses to build metadata for the type at all. See
    /// CONFIG-SCHEMA-v2.md §7 — this is not a style preference, it throws at runtime.
    /// </summary>
    public static readonly JsonSerializerOptions SptTypeOptions = new()
    {
        ReadCommentHandling = JsonCommentHandling.Skip,
        AllowTrailingCommas = true,
        PropertyNameCaseInsensitive = false,
    };

    /// <summary>Read a config, turning any malformed JSON into a diagnostic rather than a throw.</summary>
    public static bool TryRead<T>(string absolutePath, string relativePath,
                                  out T? config, out Diagnostic? problem)
    {
        config = default;
        problem = null;
        try
        {
            config = JsonSerializer.Deserialize<T>(File.ReadAllText(absolutePath), Options);
            if (config is null)
            {
                problem = Diagnostic.Error("DRIP-001", relativePath, "This file is empty.");
                return false;
            }
            return true;
        }
        catch (JsonException ex)
        {
            // ex.Message carries C# framing; the line and position are the useful parts.
            problem = Diagnostic.Error("DRIP-001", relativePath,
                $"This file isn't valid JSON — line {ex.LineNumber + 1}, character {ex.BytePositionInLine + 1}.",
                "A missing comma, a missing quote, or a stray bracket is the usual cause.");
            return false;
        }
    }
}
```

---

## 3. The model

Mirrors `CONFIG-SCHEMA-v2.md` §4. Every property is nullable so that "absent" and "set to
zero" stay distinguishable — ten Part 1 items are legitimately priced at `0`, and a
`price == 0` check would wrongly report them as missing a price.

```csharp
using System.Text.Json;
using System.Text.Json.Serialization;

namespace DRIP.Validation;

public sealed class ItemConfig
{
    // Bound as a string on purpose. A JsonStringEnumConverter throws on an unrecognised value,
    // which would abort the whole file before DRIP-101 ever got to suggest a spelling — see
    // CONFIG-SCHEMA-v2.md §4.1.
    [JsonPropertyName("type")]        public string? Type { get; set; }
    [JsonPropertyName("id")]          public string? Id { get; set; }

    [JsonPropertyName("name")]        public string? Name { get; set; }
    [JsonPropertyName("shortName")]   public string? ShortName { get; set; }
    [JsonPropertyName("description")] public string? Description { get; set; }
    [JsonPropertyName("translations")]
    public Dictionary<string, LocaleText>? Translations { get; set; }

    [JsonPropertyName("traderId")]    public string? TraderId { get; set; }
    [JsonPropertyName("price")]       public double? Price { get; set; }
    [JsonPropertyName("currency")]    public string? Currency { get; set; }
    [JsonPropertyName("loyaltyLevel")] public int? LoyaltyLevel { get; set; }
    [JsonPropertyName("profileLevel")] public int? ProfileLevel { get; set; }
    [JsonPropertyName("standing")]    public double? Standing { get; set; }
    [JsonPropertyName("questRequirements")] public List<string>? QuestRequirements { get; set; }

    [JsonPropertyName("basedOn")]     public string? BasedOn { get; set; }
    [JsonPropertyName("copyOriginalOffers")] public bool? CopyOriginalOffers { get; set; }
    [JsonPropertyName("addToBots")]   public bool? AddToBots { get; set; }
    [JsonPropertyName("botWeightMultiplier")] public double? BotWeightMultiplier { get; set; }
    [JsonPropertyName("includedParts")] public Dictionary<string, string>? IncludedParts { get; set; }
    [JsonPropertyName("properties")]  public Dictionary<string, JsonElement>? Properties { get; set; }
    [JsonPropertyName("copyPropertiesFrom")]
    public Dictionary<string, List<string>>? CopyPropertiesFrom { get; set; }

    [JsonPropertyName("handbookPrice")] public double? HandbookPrice { get; set; }
    [JsonPropertyName("fleaPrice")]   public double? FleaPrice { get; set; }

    [JsonPropertyName("bundles")]     public Dictionary<string, List<string>>? Bundles { get; set; }

    /// <summary>
    /// Anything the schema doesn't name: 'tags' (reserved for ICUP), '$schema', and author
    /// typos. Preserved so nothing is silently destroyed; inspected by DRIP-110.
    /// </summary>
    [JsonExtensionData] public Dictionary<string, JsonElement> Extra { get; set; } = new();

    // Defaults live here rather than in the JSON, so an omitted field and an explicit one
    // behave identically.
    public bool EffectiveCopyOriginalOffers => CopyOriginalOffers ?? true;
    public bool EffectiveAddToBots          => AddToBots ?? true;
    public double EffectiveBotWeight        => BotWeightMultiplier ?? 1.0;
    public string EffectiveCurrency         => Currency ?? "RUB";
    public bool IsGear     => string.Equals(Type, "gear", StringComparison.OrdinalIgnoreCase);
    public bool IsClothing => string.Equals(Type, "top", StringComparison.OrdinalIgnoreCase)
                           || string.Equals(Type, "bottom", StringComparison.OrdinalIgnoreCase);
}

public sealed class LocaleText
{
    [JsonPropertyName("name")]        public string? Name { get; set; }
    [JsonPropertyName("shortName")]   public string? ShortName { get; set; }
    [JsonPropertyName("description")] public string? Description { get; set; }
}
```

---

## 4. The validator

Implements the catalogue in `CONFIG-SCHEMA-v2.md` §8. Pure — it reads the config and the
folder listing, and returns diagnostics. No database access, so it can also run offline as a
pre-flight check before the server starts.

```csharp
namespace DRIP.Validation;

public sealed class ConfigValidator(
    IReadOnlySet<string> knownTraderNames,   // "moron", "georgia", + Traders enum names
    IReadOnlySet<string> knownQuestIds)      // quests defined by this content pack
{
    private static readonly string[] Types = ["top", "bottom", "gear"];
    private static readonly string[] Currencies = ["RUB", "USD", "EUR"];

    // null value == the field was dropped outright rather than renamed.
    private static readonly Dictionary<string, string?> RenamedInV2 = new(StringComparer.OrdinalIgnoreCase)
    {
        ["baseItemID"]              = "basedOn",
        ["itemTplToClone"]          = "basedOn",
        ["copyAssort"]              = "copyOriginalOffers",
        ["cloneAssort"]             = "copyOriginalOffers",
        ["weightingMult"]           = "botWeightMultiplier",
        ["childAssorts"]            = "includedParts",
        ["customProperties"]        = "properties / copyPropertiesFrom",
        ["bundlePath"]              = null,   // dropped: bundles are found by co-location
        ["topBundlePath"]           = null,
        ["handsBundlePath"]         = null,
        ["bottomBundlePath"]        = null,
        ["gearDependencies"]        = "bundles",
        ["topDependencies"]         = "bundles",
        ["handsDependencies"]       = "bundles",
        ["bottomDependencies"]      = "bundles",
        ["textureGearDependencies"] = null,
    };

    /// <summary>Field names DRIP knows, for the "did you mean" check.</summary>
    private static readonly string[] KnownFields =
    [
        "type", "id", "name", "shortName", "description", "translations",
        "traderId", "price", "currency", "loyaltyLevel", "profileLevel", "standing",
        "questRequirements", "basedOn", "copyOriginalOffers", "addToBots",
        "botWeightMultiplier", "includedParts", "properties", "copyPropertiesFrom",
        "handbookPrice", "fleaPrice", "bundles",
    ];

    /// <summary>Never a diagnostic: reserved, or meaningful to something other than DRIP.</summary>
    private static readonly HashSet<string> Reserved =
        new(["tags", "$schema", "//", "_comment"], StringComparer.OrdinalIgnoreCase);

    public List<Diagnostic> Validate(ItemConfig c, string file, IReadOnlyCollection<string> bundlesInFolder)
    {
        var d = new List<Diagnostic>();

        ValidateType(c, file, d);
        ValidateText(c, file, d);
        ValidateTrader(c, file, d);
        ValidatePricing(c, file, d);
        ValidateGear(c, file, d);
        ValidateBundles(c, file, bundlesInFolder, d);
        ValidateQuests(c, file, d);
        ValidateUnknownFields(c, file, d);

        return d;
    }

    private static void ValidateType(ItemConfig c, string file, List<Diagnostic> d)
    {
        if (string.IsNullOrWhiteSpace(c.Type))
        {
            d.Add(Diagnostic.Error("DRIP-101", file,
                "'type' is missing.",
                "Add one of:  \"type\": \"top\",  \"type\": \"bottom\",  or  \"type\": \"gear\","));
            return;
        }

        if (!Types.Contains(c.Type, StringComparer.OrdinalIgnoreCase))
        {
            var hint = Suggest(c.Type, Types);
            d.Add(Diagnostic.Error("DRIP-101", file,
                $"'type' is \"{c.Type}\", which isn't a kind of content DRIP knows.",
                hint is null
                    ? "It must be \"top\", \"bottom\" or \"gear\"."
                    : $"Did you mean \"{hint}\"?"));
        }
    }

    private static void ValidateText(ItemConfig c, string file, List<Diagnostic> d)
    {
        if (string.IsNullOrWhiteSpace(c.Name))
            d.Add(Diagnostic.Error("DRIP-104", file,
                "'name' is missing — this is what players see in game.",
                "Add:  \"name\": \"Your item's name\","));

        if (c.IsGear)
        {
            if (string.IsNullOrWhiteSpace(c.ShortName))
                d.Add(Diagnostic.Error("DRIP-105", file,
                    "'shortName' is missing — it's the short label shown on the item in your inventory.",
                    "Add:  \"shortName\": \"6B2\","));
            if (string.IsNullOrWhiteSpace(c.Description))
                d.Add(Diagnostic.Warning("DRIP-106", file,
                    "'description' is missing — the item will have blank flavour text."));
        }
        else if (c.IsClothing && (c.ShortName is not null || c.Description is not null))
        {
            d.Add(Diagnostic.Warning("DRIP-501", file,
                "'shortName' and 'description' aren't shown for clothing.",
                "You can delete them."));
        }
    }

    private void ValidateTrader(ItemConfig c, string file, List<Diagnostic> d)
    {
        if (string.IsNullOrWhiteSpace(c.TraderId))
        {
            d.Add(Diagnostic.Error("DRIP-401", file,
                "'traderId' is missing — nothing will sell this item.",
                "Add:  \"traderId\": \"georgia\","));
            return;
        }

        if (knownTraderNames.Contains(c.TraderId) || IsMongoId(c.TraderId))
            return;

        var hint = Suggest(c.TraderId, knownTraderNames);
        d.Add(Diagnostic.Error("DRIP-401", file,
            $"There's no trader called \"{c.TraderId}\".",
            hint is not null
                ? $"Did you mean \"{hint}\"?"
                : $"Use one of: {string.Join(", ", knownTraderNames.Order())} — or a trader's 24-character ID."));
    }

    private static void ValidatePricing(ItemConfig c, string file, List<Diagnostic> d)
    {
        var needsOwnPrice = c.IsClothing || (c.IsGear && !c.EffectiveCopyOriginalOffers);

        // Presence, not truthiness: price 0 is valid (free quest-reward clothing).
        if (needsOwnPrice && c.Price is null)
        {
            d.Add(Diagnostic.Error("DRIP-301", file,
                c.IsGear
                    ? "'price' is missing. This item has \"copyOriginalOffers\": false, so it needs its own price."
                    : "'price' is missing — clothing is always sold at its own price.",
                "Add:  \"price\": 45000,"
                    + (c.IsGear
                        ? "\nOr set \"copyOriginalOffers\": true to sell it wherever the original is sold."
                        : "")));
        }

        if (c.IsGear && c.EffectiveCopyOriginalOffers && c.Price is not null)
            d.Add(Diagnostic.Warning("DRIP-302", file,
                "'price' is ignored here — with \"copyOriginalOffers\": true the original item's price is used.",
                "Either remove 'price', or set \"copyOriginalOffers\": false to make it apply."));

        if (needsOwnPrice && c.LoyaltyLevel is null)
            d.Add(Diagnostic.Error("DRIP-301", file,
                "'loyaltyLevel' is missing — DRIP needs to know how far in with the trader a player must be.",
                "Add:  \"loyaltyLevel\": 1,"));

        if (c.LoyaltyLevel is < 1 or > 4)
            d.Add(Diagnostic.Error("DRIP-303", file,
                $"'loyaltyLevel' is {c.LoyaltyLevel} — traders only have levels 1 to 4."));

        if (c.Price < 0)
            d.Add(Diagnostic.Error("DRIP-305", file, $"'price' is {c.Price} — it can't be negative."));

        // A zero in a config file is nearly always left over from testing. It loads fine, so
        // this is a warning — but it must name the file, or nobody finds it before release.
        // Note this is NOT the same as NoClothingRequirements zeroing prices, which happens
        // as a runtime transform after loading and is correct.
        if (c.Price == 0)
            d.Add(Diagnostic.Warning("DRIP-307", file,
                "'price' is 0, so this item is free.",
                "If that wasn't deliberate, set a real price. Several items were left at 0 during early testing."));

        if (c.Currency is not null && !Currencies.Contains(c.Currency, StringComparer.OrdinalIgnoreCase))
            d.Add(Diagnostic.Error("DRIP-304", file,
                $"'currency' is \"{c.Currency}\".",
                $"It must be one of: {string.Join(", ", Currencies)}. Leave it out for roubles."));

        if (c.IsGear && (c.ProfileLevel is not null || c.Standing is not null))
            d.Add(Diagnostic.Warning("DRIP-306", file,
                "'profileLevel' and 'standing' only apply to clothing.",
                "You can delete them."));
    }

    private static void ValidateGear(ItemConfig c, string file, List<Diagnostic> d)
    {
        if (!c.IsGear)
        {
            if (c.BasedOn is not null)
                d.Add(Diagnostic.Warning("DRIP-404", file,
                    "'basedOn' only applies to gear — clothing isn't cloned from another item.",
                    "You can delete it."));
            return;
        }

        if (string.IsNullOrWhiteSpace(c.BasedOn))
        {
            d.Add(Diagnostic.Error("DRIP-402", file,
                "'basedOn' is missing — gear needs the ID of the item it's a retexture of.",
                "Add:  \"basedOn\": \"5df8a2ca86f7740bfe6df777\","));
            return;
        }

        if (!IsMongoId(c.BasedOn))
            d.Add(Diagnostic.Error("DRIP-403", file,
                $"'basedOn' is \"{c.BasedOn}\" ({c.BasedOn.Length} characters) — item IDs are 24 characters of 0-9 and a-f.",
                c.BasedOn.Length is 23 or 25
                    ? "That's one character out — check for a typo when you copied it."
                    : "Copy the ID from the item you're retexturing."));

        if (c.EffectiveBotWeight < 0)
            d.Add(Diagnostic.Error("DRIP-405", file,
                $"'botWeightMultiplier' is {c.EffectiveBotWeight} — it can't be negative.",
                "1.0 means as common as the original; 0.5 means half as often."));

        if (c.IncludedParts is not null && c.EffectiveCopyOriginalOffers)
            d.Add(Diagnostic.Warning("DRIP-406", file,
                "'includedParts' is ignored when \"copyOriginalOffers\" is true — the original item's parts are used."));

        foreach (var (slot, tpl) in c.IncludedParts ?? [])
            if (!IsMongoId(tpl))
                d.Add(Diagnostic.Error("DRIP-407", file,
                    $"'includedParts' → \"{slot}\" is \"{tpl}\", which isn't a 24-character item ID."));
    }

    /// <summary>
    /// Pack-level preconditions: one missing thing that makes every item fail for the same
    /// reason. Run these before validating individual items — when one reports, skip the
    /// matching per-item check, or the summary drowns anyway and the exercise is wasted.
    ///
    /// See CONFIG-SCHEMA-v2.md §8 rule 6: diagnose the precondition, not each of its
    /// consequences. Zero items loading is the *correct* outcome here and should read that way.
    /// </summary>
    public static class PackPreconditions
    {
        /// <summary>
        /// Bundles are kept out of git, so a fresh clone has none. Returns false when the pack
        /// looks un-bootstrapped, in which case pass <c>packHasBundles: false</c> to Validate.
        ///
        /// Judged by proportion, NOT by whether any bundle exists: four bundles were committed
        /// before .gitignore covered them, and four are enough to make a 275-item pack look
        /// populated. A Count == 0 check silently never fires.
        /// </summary>
        public static bool BundlesPresent(string packName, int itemCount, int itemsMissingBundles,
                                          List<Diagnostic> into)
        {
            if (itemCount == 0 || itemsMissingBundles <= itemCount / 2) return true;

            into.Add(Diagnostic.Warning("DRIP-200", $"{packName}  (whole content pack)",
                $"{itemsMissingBundles} of {itemCount} items have no bundle on disk, so they can't load yet.",
                "That's normal for a fresh clone — bundles are kept out of git. To populate them:\n"
              + $"  python tools/convert-legacy.py --part 1 --out bundles/ContentPacks/{packName} --bundles link"));
            return false;
        }

        /// <summary>
        /// A pack whose items sell through DRIP's own traders needs those traders defined —
        /// by this pack or by another one loaded alongside it. Vanilla traders need nothing.
        ///
        /// Without this, a pack shipped separately from its traders fails every clothing item
        /// individually with the same message.
        /// </summary>
        public static bool TradersDefined(string packName, IReadOnlyCollection<string> requiredDripTraders,
                                          int affectedItems, bool anyTraderDefinitionsLoaded,
                                          List<Diagnostic> into)
        {
            if (requiredDripTraders.Count == 0 || anyTraderDefinitionsLoaded) return true;

            into.Add(Diagnostic.Warning("DRIP-400", $"{packName}  (whole content pack)",
                $"Nothing defines {string.Join(" or ", requiredDripTraders.Order())}, "
              + $"so {affectedItems} items have nowhere to be sold.",
                "DRIP's own traders are defined by the .json files in a pack's CustomTraders folder.\n"
              + "Either add them here, or install the pack that provides them."));
            return false;
        }
    }

    private static void ValidateBundles(ItemConfig c, string file,
                                        IReadOnlyCollection<string> inFolder, List<Diagnostic> d)
    {
        string[] required = c.Type?.ToLowerInvariant() switch
        {
            "top"    => ["TOP.bundle", "HANDS.bundle"],
            "bottom" => ["BOTTOM.bundle"],
            "gear"   => ["GEAR.bundle"],
            _        => [],
        };

        var have = inFolder.ToHashSet(StringComparer.OrdinalIgnoreCase);

        foreach (var want in required.Where(w => !have.Contains(w)))
            d.Add(Diagnostic.Error("DRIP-201", file,
                $"Expected {want} in this item's folder.",
                have.Count == 0
                    ? "That folder has no .bundle files at all — the bundle needs to sit next to this config."
                    : $"The folder has: {string.Join(", ", have.Order())}. Rename the right one to {want}."));

        foreach (var named in (c.Bundles ?? []).Keys.Where(k => !have.Contains(k)))
            d.Add(Diagnostic.Warning("DRIP-202", file,
                $"'bundles' mentions {named}, but there's no {named} in this folder.",
                "Either the name is misspelled, or the bundle hasn't been copied in yet."));
    }

    private void ValidateQuests(ItemConfig c, string file, List<Diagnostic> d)
    {
        if (knownQuestIds.Count == 0) return;   // pack ships no quests; nothing to check against

        foreach (var q in (c.QuestRequirements ?? []).Where(q => !knownQuestIds.Contains(q)))
            d.Add(Diagnostic.Warning("DRIP-502", file,
                $"'questRequirements' mentions \"{q}\", which no quest in this content pack defines.",
                "The item will never unlock unless another pack provides that quest."));
    }

    private static void ValidateUnknownFields(ItemConfig c, string file, List<Diagnostic> d)
    {
        foreach (var key in c.Extra.Keys)
        {
            if (Reserved.Contains(key)) continue;

            if (RenamedInV2.TryGetValue(key, out var replacement))
            {
                d.Add(Diagnostic.Warning("DRIP-111", file,
                    replacement is null
                        ? $"'{key}' isn't used any more — DRIP finds bundles by looking in this item's folder."
                        : $"'{key}' was renamed to '{replacement}' in the new format.",
                    "Run tools/convert-legacy.py to update this file automatically."));
                continue;
            }

            var hint = Suggest(key, KnownFields);
            d.Add(Diagnostic.Warning("DRIP-110", file,
                $"'{key}' isn't a field DRIP knows, so it's being ignored.",
                hint is not null ? $"Did you mean '{hint}'?" : "Check the spelling against docs/CONFIG-SCHEMA-v2.md."));
        }
    }

    // -- helpers ---------------------------------------------------------------------------

    private static bool IsMongoId(string s) =>
        s.Length == 24 && s.All(ch => ch is >= '0' and <= '9' or >= 'a' and <= 'f');

    /// <summary>Nearest known spelling within edit distance 2, or null.</summary>
    private static string? Suggest(string input, IEnumerable<string> candidates)
    {
        string? best = null;
        var bestDistance = 3;
        foreach (var candidate in candidates)
        {
            var distance = Levenshtein(input.ToLowerInvariant(), candidate.ToLowerInvariant());
            if (distance < bestDistance) { bestDistance = distance; best = candidate; }
        }
        return best;
    }

    private static int Levenshtein(string a, string b)
    {
        var prev = new int[b.Length + 1];
        var cur = new int[b.Length + 1];
        for (var j = 0; j <= b.Length; j++) prev[j] = j;

        for (var i = 1; i <= a.Length; i++)
        {
            cur[0] = i;
            for (var j = 1; j <= b.Length; j++)
            {
                var cost = a[i - 1] == b[j - 1] ? 0 : 1;
                cur[j] = Math.Min(Math.Min(cur[j - 1] + 1, prev[j] + 1), prev[j - 1] + cost);
            }
            (prev, cur) = (cur, prev);
        }
        return prev[b.Length];
    }
}
```

---

## 5. ID collisions

Filename-derived IDs (`CONFIG-SCHEMA-v2.md` §4.1) need exactly one guard, because three
filename stems collide in the legacy corpus — including a Part 1 / Part 3 pair that would let a
later content pack silently overwrite a release item.

```csharp
namespace DRIP.Validation;

/// <summary>
/// Tracks derived item IDs across every content pack loaded this session, so two files that
/// resolve to the same ID are caught rather than one quietly overwriting the other.
/// </summary>
public sealed class IdRegistry
{
    private readonly Dictionary<string, (string File, string ContentHash)> _seen = new();

    /// <summary>Returns false if this item should be skipped.</summary>
    public bool TryClaim(string id, string file, string contentHash, List<Diagnostic> into)
    {
        if (!_seen.TryGetValue(id, out var existing))
        {
            _seen[id] = (file, contentHash);
            return true;
        }

        if (existing.ContentHash == contentHash)
        {
            // Legitimate: Part 3 re-ships a Part 1 item unchanged.
            into.Add(Diagnostic.Info("DRIP-103", file,
                $"Identical to {existing.File}; loading it once."));
            return false;
        }

        into.Add(Diagnostic.Error("DRIP-102", file,
            $"This file and {existing.File} have the same name, so they'd become the same item — "
          + "the second would overwrite the first.",
            "Rename one of them to something unique. The file's name is what gives the item its ID."));
        return false;
    }
}
```

---

## 6. Reporting

```csharp
using SPTarkov.Server.Core.Models.Utils;

namespace DRIP.Validation;

public static class DiagnosticReport
{
    // ISptLogger only exists in its generic form, so the caller's own logger type flows through.
    public static void Write<T>(ISptLogger<T> logger, string packName,
                                IReadOnlyList<Diagnostic> all, int loaded)
    {
        var errors   = all.Count(x => x.Severity == Severity.Error);
        var warnings = all.Count(x => x.Severity == Severity.Warning);

        if (errors == 0 && warnings == 0)
        {
            logger.Success($"[DRIP] {packName}: {loaded} items loaded, no problems found.");
            return;
        }

        foreach (var group in all.Where(x => x.Severity != Severity.Info)
                                 .GroupBy(x => x.File)
                                 .OrderBy(g => g.Key, StringComparer.OrdinalIgnoreCase))
        {
            logger.Warning($"");
            logger.Warning($"[DRIP] {group.Key}");
            foreach (var x in group.OrderBy(x => x.Severity == Severity.Error ? 0 : 1))
            {
                var mark = x.Severity == Severity.Error ? "error  " : "warning";
                logger.Warning($"    {mark}  {x.Code}  {x.Message}");
                foreach (var line in (x.Fix ?? "").Split('\n', StringSplitOptions.RemoveEmptyEntries))
                    logger.Warning($"                        {line}");
            }
        }

        logger.Warning("");
        var summary = $"[DRIP] {packName}: {loaded} items loaded, "
                    + $"{errors} could not be loaded, {warnings} warning(s).";
        if (errors > 0) logger.Error(summary); else logger.Warning(summary);
        logger.Warning("[DRIP] Full field reference: docs/CONFIG-SCHEMA-v2.md");
    }
}
```

---

## 7. Wiring it in

```csharp
var diagnostics = new List<Diagnostic>();
var ids = new IdRegistry();
var validator = new ConfigValidator(knownTraderNames, questIdsInThisPack);
var loaded = 0;

foreach (var file in Directory.EnumerateFiles(itemsRoot, "*.jsonc", SearchOption.AllDirectories))
{
    var relative = Path.GetRelativePath(packRoot, file).Replace('\\', '/');

    if (!ContentPackJson.TryRead<ItemConfig>(file, relative, out var config, out var problem))
    {
        diagnostics.Add(problem!);
        continue;                       // one unreadable file, not one dead content pack
    }

    var folderBundles = Directory.EnumerateFiles(Path.GetDirectoryName(file)!, "*.bundle")
                                 .Select(Path.GetFileName).ToList()!;

    var problems = validator.Validate(config!, relative, folderBundles!);
    diagnostics.AddRange(problems);
    if (problems.Any(p => p.Severity == Severity.Error)) continue;

    var id = config!.Id ?? DeriveId(Path.GetFileNameWithoutExtension(file));
    if (!ids.TryClaim(id, relative, HashOf(config), diagnostics)) continue;

    CreateItem(id, config);
    loaded++;
}

DiagnosticReport.Write(logger, packName, diagnostics, loaded);
```

Two things worth keeping as written:

- **`continue`, never `throw`.** A content pack with one broken file still ships its other 274
  items, and the author sees every problem in one run instead of finding them one restart at a
  time.
- **Validate before claiming an ID.** An item that failed validation shouldn't reserve an ID
  and cause a spurious collision report against the file that actually works.

---

## 8. What this changes for the author

Same mistake — `"type": "TOPP"` with a misspelled `addtoBots` — in a pack of 275 items:

**Before**

```
[DRIP] Error loading configs: 'type' must be 'top' or 'bottom', got 'TOPP'.
```

One item's problem, no filename, 274 other items silently not loaded, and the `addtoBots` typo
never mentioned at all.

**After**

```
[DRIP] CustomClothing/TOPS/GORKA4/SKOL/GORKA4_SKOL_TOP.jsonc
    error    DRIP-101  'type' is "TOPP", which isn't a kind of content DRIP knows.
                       Did you mean "top"?
    warning  DRIP-110  'addtoBots' isn't a field DRIP knows, so it's being ignored.
                       Did you mean 'addToBots'?

[DRIP] Essentials: 274 items loaded, 1 could not be loaded, 1 warning(s).
[DRIP] Full field reference: docs/CONFIG-SCHEMA-v2.md
```

---

## 9. Running it without starting the server

Everything above is pure apart from `knownQuestIds`, so the same validator backs an offline
pre-flight check — the `drip check` half of the one-command goal. A retexture author gets their
mistakes in about a second instead of after a server start, which is the difference between
iterating and giving up.

The remaining half is `drip new <type> <name>`: create the folder, write a commented `.jsonc`
with `$schema` already wired up and the expected bundle filenames named in a comment. Between
the two, an author never starts from a blank file and never waits on a server to find out they
typo'd something.
