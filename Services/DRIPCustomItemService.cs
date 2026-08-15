using System.Reflection;
using System.Text.Json.Serialization;
using DRIP.Models;
using DRIP.Utils;
using SPTarkov.DI.Annotations;
using SPTarkov.Server.Core.Helpers;
using SPTarkov.Server.Core.Loaders;
using SPTarkov.Server.Core.Models.Common;
using SPTarkov.Server.Core.Models.Eft.Common;
using SPTarkov.Server.Core.Models.Eft.Common.Tables;
using SPTarkov.Server.Core.Models.Spt.Mod;
using SPTarkov.Server.Core.Models.Spt.Server;
using SPTarkov.Server.Core.Models.Utils;
using SPTarkov.Server.Core.Servers;
using SPTarkov.Server.Core.Services;
using SPTarkov.Server.Core.Services.Mod;
using SPTarkov.Server.Core.Utils;
using SPTarkov.Server.Core.Utils.Cloners;
using Path = System.IO.Path;

namespace DRIP.Services;

[Injectable(InjectionType.Singleton)]
public class DRIPCustomItemService(
    ISptLogger<DRIPCustomItemService> logger,
    CustomItemService customItemService,
    DatabaseServer databaseServer,
    DRIPBundleService bundleService,
    DRIPTraderAssortService assortService,
    HashUtil hashUtil,
    ICloner cloner,
    DripConfigService configService
)
{
    private DatabaseTables? _database;

    private DripConfig? _config;

    /// <summary>
    /// Base template id to the new items cloned from it, accumulated across every content pack.
    ///
    /// This exists so slot filters and conflicts can be fixed up in one pass over the item database at the end,
    /// rather than the 3.x approach of walking every template once per item. See
    /// <see cref="ApplyInheritedSlotFiltersAndConflicts"/>.
    /// </summary>
    private readonly Dictionary<MongoId, List<Retexture>> _retexturesByBase = new();

    /// <summary>An item DRIP created, and what the base item's bot weightings should become for it.</summary>
    private record Retexture(MongoId Id, bool AddToBots, double WeightMultiplier);

    /// <summary>An item DRIP created, for the verification pass to check over.</summary>
    public record CreatedItem(MongoId Id, MongoId BaseTpl, string RelativeName);

    private readonly List<CreatedItem> _created = [];

    /// <summary>Everything this loader created, in load order.</summary>
    public IReadOnlyList<CreatedItem> Created => _created;

    /// <summary>
    /// Loads item configs from one content pack, registering their co-located bundles and creating each item.
    /// </summary>
    /// <param name="assembly">The calling assembly, used to determine the mod folder location</param>
    /// <param name="contentPackPath">
    /// Path to the content pack's CustomItems directory, relative to the mod folder - already includes "bundles".
    /// </param>
    public async Task CreateCustomItems(Assembly assembly, string contentPackPath)
    {
        _database ??= databaseServer.GetTables();
        _config ??= configService.Get(assembly);

        var paths = bundleService.GetModPaths(assembly);
        var finalDir = paths.Resolve(contentPackPath);

        // "bundles/ContentPacks/Essentials/CustomItems" -> "Essentials". This is what players are told an item
        // belongs to, so it comes from the folder rather than being configured anywhere.
        var packName = Path.GetFileName(Path.GetDirectoryName(contentPackPath.Replace('/', Path.DirectorySeparatorChar)))
                       ?? contentPackPath;

        var itemsCreated = 0;
        var itemsFailed = 0;
        var missingModelBundle = new List<string>();

        // Each config is loaded in isolation. A single malformed file should cost us that one item, not the rest of
        // the content pack - one bad file must not cost the author the other 274.
        foreach (var file in DripFiles.EnumerateConfigFiles(finalDir))
        {
            var fullFile = new FileInfo(file);
            var relativeName = Path.GetRelativePath(finalDir, file).Replace("\\", "/");

            try
            {
                var config = DripJson.DeserializeFile<ContentItemConfig>(file);
                if (config is null)
                {
                    logger.Error($"[DRIP] {relativeName}: file is empty or could not be read.");
                    itemsFailed++;
                    continue;
                }

                if (await CreateItem(config, fullFile, relativeName, paths, packName, missingModelBundle))
                {
                    itemsCreated++;
                }
                else
                {
                    itemsFailed++;
                }
            }
            catch (Exception ex)
            {
                logger.Error($"[DRIP] {relativeName}: {ex.Message}");
                itemsFailed++;
            }
        }

        if (missingModelBundle.Count > 0)
        {
            var (isUnbootstrapped, message) =
                DRIPBundleService.DescribeMissingBundles(missingModelBundle, itemsCreated + itemsFailed, "GEAR.bundle");

            if (isUnbootstrapped)
            {
                logger.Warning($"[DRIP] {contentPackPath}: {message}");
            }
            else
            {
                logger.Error($"[DRIP] {contentPackPath}: {message}");
            }
        }


        if (itemsFailed > 0)
        {
            logger.Error($"[DRIP] {contentPackPath}: {itemsCreated} new items, {itemsFailed} failed.");
        }
        else
        {
            logger.Info($"[DRIP] {contentPackPath}: {itemsCreated} new items.");
        }
    }

    private async Task<bool> CreateItem(
        ContentItemConfig config,
        FileInfo configFile,
        string relativeName,
        DRIPBundleService.ModPaths paths,
        string packName,
        List<string> missingModelBundle)
    {
        if (_database is null)
        {
            logger.Error($"[DRIP] {relativeName}: database is not available.");
            return false;
        }

        if (config.HasUnrecognisedType)
        {
            var hint = config.TypeRaw!.Trim().ToLower() switch
            {
                "retexture" or "custom" =>
                    $"'{config.TypeRaw}' was the 3.x name - it's called \"gear\" in v2.",
                _ => $"'type' must be \"top\", \"bottom\" or \"gear\" - found \"{config.TypeRaw}\"."
            };

            logger.Error($"[DRIP] {relativeName}: {hint}");
            return false;
        }

        if (config.Type is null)
        {
            logger.Error($"[DRIP] {relativeName}: 'type' is missing - it must be \"top\", \"bottom\" or \"gear\".");
            return false;
        }

        if (config.IsClothing)
        {
            logger.Error(
                $"[DRIP] {relativeName}: this is a '{config.Type.ToString()?.ToLower()}' config, but it is in " +
                "CustomItems. Move it to CustomClothing.");
            return false;
        }

        if (config.HasUnrecognisedCurrency)
        {
            logger.Error(
                $"[DRIP] {relativeName}: 'currency' must be \"RUB\", \"USD\" or \"EUR\" - found \"{config.CurrencyRaw}\".");
            return false;
        }

        if (string.IsNullOrWhiteSpace(config.BasedOn))
        {
            logger.Error($"[DRIP] {relativeName}: 'basedOn' is missing - gear needs the ID of the item it's a retexture of.");
            return false;
        }

        if (!MongoId.IsValidMongoId(config.BasedOn))
        {
            logger.Error(
                $"[DRIP] {relativeName}: 'basedOn' is \"{config.BasedOn}\" ({config.BasedOn.Length} characters) - " +
                "item IDs are 24. Check for a missing character.");
            return false;
        }

        if (string.IsNullOrWhiteSpace(config.Name))
        {
            logger.Error($"[DRIP] {relativeName}: 'name' is missing - this is what players see in game.");
            return false;
        }

        // Zero prices are legacy test junk rather than deliberately free items, so this names the file and carries
        // on. The NoClothingRequirements option zeroes prices at runtime and is unaffected by this.
        if (config.Price == 0)
        {
            logger.Warning(
                $"[DRIP] {relativeName}: 'price' is 0, so this is free. If that wasn't intended, give it a price.");
        }

        MongoId baseTpl = config.BasedOn;
        if (!_database.Templates.Items.TryGetValue(baseTpl, out var baseItem))
        {
            logger.Error($"[DRIP] {relativeName}: 'basedOn' item {baseTpl} is not in the item database.");
            return false;
        }

        // The author never writes an ID. It is derived from the filename so that it is deterministic across
        // restarts and unaffected by reorganising folders.
        var newItemId = config.Id is not null
            ? new MongoId(config.Id)
            : await DripIds.Derive(hashUtil, Path.GetFileNameWithoutExtension(configFile.Name));

        if (_database.Templates.Items.ContainsKey(newItemId))
        {
            logger.Error(
                $"[DRIP] {relativeName}: item ID {newItemId} already exists. Another file with the same name has " +
                "already claimed it - rename one of them.");
            return false;
        }

        var overrideProperties = await RegisterBundlesAndBuildOverrides(config, configFile, relativeName, paths, missingModelBundle);
        if (overrideProperties is null)
        {
            // No model bundle. Creating the item anyway would leave it pointing at the cloned item's model, so it
            // would look exactly like the vanilla item it retextures - a silent wrong-content bug, which is worse
            // than not existing.
            return false;
        }

        var baseHandbookEntry = _database.Templates.Handbook.Items.FirstOrDefault(entry => entry.Id == baseTpl);
        if (baseHandbookEntry is null && (config.HandbookPrice is null || config.CopyOriginalOffers is not false))
        {
            logger.Warning(
                $"[DRIP] {relativeName}: the item it is based on has no handbook entry, so it has no catalogue " +
                "category or price. Set 'handbookPrice' explicitly if it shows up wrong.");
        }

        _database.Templates.Prices.TryGetValue(baseTpl, out var baseFleaPrice);

        var itemDetails = new NewItemFromCloneDetails
        {
            ItemTplToClone = baseTpl,
            NewId = newItemId,

            // Neither of these is author-facing. Both default from the cloned item, which is what 3.x got for free
            // by cloning the whole template and only rewriting its id.
            ParentId = baseItem.Parent.ToString(),
            HandbookParentId = baseHandbookEntry?.ParentId.ToString(),

            HandbookPriceRoubles = config.HandbookPrice ?? baseHandbookEntry?.Price,
            FleaPriceRoubles = config.FleaPrice ?? baseFleaPrice,

            Locales = BuildLocales(config, packName),
            OverrideProperties = overrideProperties
        };

        var result = customItemService.CreateItemFromClone(itemDetails);
        if (result.Success != true)
        {
            var errors = result.Errors is { Count: > 0 } ? string.Join("; ", result.Errors) : "no reason given";
            logger.Error($"[DRIP] {relativeName}: could not create item from {baseTpl} - {errors}");
            return false;
        }

        ApplyCopiedProperties(config, newItemId, relativeName);

        // Putting it on sale is deferred: it needs an index over every trader's assort, and that should be built
        // once for the whole load rather than once per item.
        if (DripTraders.TryResolve(config.TraderId, out var traderId))
        {
            assortService.Record(newItemId, baseTpl, traderId, config, relativeName);
        }
        else
        {
            logger.Error(
                $"[DRIP] {relativeName}: no trader called \"{config.TraderId}\". " +
                $"Known names: {string.Join(", ", DripTraders.KnownNames)}. Or use a trader's ID. " +
                "The item exists but nothing sells it.");
        }

        // Remember the lineage so slot filters and conflicts can be fixed up in one pass later.
        if (!_retexturesByBase.TryGetValue(baseTpl, out var siblings))
        {
            siblings = [];
            _retexturesByBase[baseTpl] = siblings;
        }

        siblings.Add(new Retexture(newItemId, config.ShouldAddToBots, config.EffectiveBotWeightMultiplier));
        _created.Add(new CreatedItem(newItemId, baseTpl, relativeName));

        return true;
    }

    /// <summary>
    /// Registers every bundle sitting next to the config and returns the property overrides to apply to the new
    /// item, including the model path pointing at the discovered bundle.
    /// </summary>
    private async Task<TemplateItemProperties?> RegisterBundlesAndBuildOverrides(
        ContentItemConfig config,
        FileInfo configFile,
        string relativeName,
        DRIPBundleService.ModPaths paths,
        List<string> missingModelBundle)
    {
        // Start from the author's own property overrides, if any, so the model path is layered on top rather than
        // replacing them.
        var overrides = config.MaterializeProperties() ?? new TemplateItemProperties();

        var bundles = await bundleService.RegisterBundlesNextTo(configFile, config.Bundles, paths);

        var modelBundleKey = ResolveModelBundle(bundles, relativeName, missingModelBundle);
        if (modelBundleKey is null)
        {
            return null;
        }

        overrides.Prefab = new Prefab { Path = modelBundleKey, Rcid = string.Empty };

        // Only worth saying when some bundles are present - if the folder is empty the missing-model report above
        // already covers it, and repeating it per declared dependency is pure noise.
        if (bundles.Count > 0)
        {
            foreach (var missing in DRIPBundleService.FindDeclaredButMissing(config.Bundles, bundles))
            {
                logger.Warning($"[DRIP] {relativeName}: 'bundles' mentions {missing}, but there's no {missing} in this folder.");
            }
        }

        return overrides;
    }

    /// <summary>
    /// Picks the bundle holding the item's model. TEXTURE bundles are dependencies of the model, never the model.
    /// </summary>
    private string? ResolveModelBundle(Dictionary<string, string> bundles, string relativeName, List<string> missingModelBundle)
    {
        var candidates = bundles
            .Where(entry => !entry.Key.StartsWith("TEXTURE", StringComparison.OrdinalIgnoreCase))
            .ToList();

        if (candidates.Count == 0)
        {
            // Recorded rather than logged: when a checkout has not been bootstrapped this is true of every config in
            // the pack, and 271 identical lines bury anything else worth reading. Reported in aggregate afterwards.
            missingModelBundle.Add(relativeName);
            return null;
        }

        var canonical = candidates.FirstOrDefault(entry =>
            entry.Key.Equals("GEAR.bundle", StringComparison.OrdinalIgnoreCase));

        if (canonical.Value is not null)
        {
            return canonical.Value;
        }

        // Not the canonical name. Accept it when unambiguous so pre-conversion content still loads, but say so -
        // the converter normalises these to GEAR.bundle.
        if (candidates.Count > 1)
        {
            logger.Error(
                $"[DRIP] {relativeName}: expected GEAR.bundle next to this file, and there is more than one " +
                $"candidate so DRIP can't guess: {DescribeBundleList(candidates.Select(entry => entry.Key))}.");
            return null;
        }

        logger.Warning(
            $"[DRIP] {relativeName}: using {candidates[0].Key} as the model, but the expected name is GEAR.bundle.");

        return candidates[0].Value;
    }

    private static string DescribeBundleList(IEnumerable<string> bundleNames)
    {
        var names = bundleNames.ToList();

        return names.Count == 0 ? "no bundles at all" : string.Join(", ", names);
    }

    /// <summary>
    /// The English text is the fallback for every locale; `translations` layers over it where supplied.
    /// </summary>
    private Dictionary<string, LocaleDetails> BuildLocales(ContentItemConfig config, string packName)
    {
        var fallback = Decorate(new LocaleDetails
        {
            Name = config.Name,
            ShortName = config.ShortName,
            Description = config.Description
        }, packName);

        var locales = new Dictionary<string, LocaleDetails> { ["en"] = fallback };

        if (config.Translations is null)
        {
            return locales;
        }

        foreach (var (locale, translation) in config.Translations)
        {
            locales[locale] = Decorate(new LocaleDetails
            {
                Name = translation.Name ?? config.Name,
                ShortName = translation.ShortName ?? config.ShortName,
                Description = translation.Description ?? config.Description
            }, packName);
        }

        return locales;
    }

    /// <summary>
    /// Applies the two presentation options: naming the content pack in an item's description, and - for debugging
    /// only - prefixing its name so DRIP items are obvious at a glance.
    /// </summary>
    private LocaleDetails Decorate(LocaleDetails locale, string packName)
    {
        if (_config?.CollectionInDescription == true)
        {
            locale.Description = $"{locale.Description}{Environment.NewLine}{Environment.NewLine}" +
                                 $"This item is part of the {packName} content pack.";
        }

        if (_config?.DebugNames == true)
        {
            locale.Name = $"{packName} | {locale.Name}";
        }

        return locale;
    }

    /// <summary>
    /// Copies named properties off other item templates - armour stats, in practice. Property names are the raw BSG
    /// names authors see in the item database, matched against the serialised names of the model.
    /// </summary>
    private void ApplyCopiedProperties(ContentItemConfig config, MongoId newItemId, string relativeName)
    {
        if (config.CopyPropertiesFrom is null || _database is null)
        {
            return;
        }

        if (!_database.Templates.Items.TryGetValue(newItemId, out var newItem) || newItem.Properties is null)
        {
            return;
        }

        foreach (var (sourceTpl, propertyNames) in config.CopyPropertiesFrom)
        {
            if (!MongoId.IsValidMongoId(sourceTpl) ||
                !_database.Templates.Items.TryGetValue(new MongoId(sourceTpl), out var sourceItem) ||
                sourceItem.Properties is null)
            {
                logger.Warning(
                    $"[DRIP] {relativeName}: 'copyPropertiesFrom' mentions {sourceTpl}, which isn't an item in the " +
                    "database. Skipping it.");
                continue;
            }

            foreach (var propertyName in propertyNames)
            {
                var property = FindPropertyBySerialisedName(propertyName);
                if (property is null)
                {
                    logger.Warning(
                        $"[DRIP] {relativeName}: 'copyPropertiesFrom' asks for '{propertyName}', which isn't a " +
                        "property items have. Skipping it.");
                    continue;
                }

                property.SetValue(newItem.Properties, property.GetValue(sourceItem.Properties));
            }
        }
    }

    /// <summary>
    /// Exact match first, and only fall back to a case-insensitive match when it is unambiguous.
    ///
    /// BSG ships property pairs that differ only by case - `ShotgunDispersion` and `shotgunDispersion` both exist -
    /// so a blanket case-insensitive lookup would silently copy whichever one reflection happened to return first.
    /// </summary>
    private static PropertyInfo? FindPropertyBySerialisedName(string serialisedName)
    {
        var properties = typeof(TemplateItemProperties).GetProperties(BindingFlags.Public | BindingFlags.Instance);

        var exact = properties.FirstOrDefault(property => SerialisedNameOf(property) == serialisedName);
        if (exact is not null)
        {
            return exact;
        }

        var caseInsensitiveMatches = properties
            .Where(property => string.Equals(SerialisedNameOf(property), serialisedName, StringComparison.OrdinalIgnoreCase))
            .ToList();

        return caseInsensitiveMatches.Count == 1 ? caseInsensitiveMatches[0] : null;
    }

    private static string SerialisedNameOf(PropertyInfo property)
    {
        return property.GetCustomAttribute<JsonPropertyNameAttribute>()?.Name ?? property.Name;
    }

    /// <summary>
    /// Teaches the rest of the item database about the items DRIP added: anywhere a base item is accepted by a slot
    /// filter, or conflicts with something, its retextures now do too.
    ///
    /// Without this, retextured armour will not fit in rigs and plate slots reject retextured plates - the failure
    /// is silent and looks like a broken item rather than a missing step.
    ///
    /// This is one pass over the item database for all content packs combined. The 3.x version
    /// (collection.ts:304-334) walked every template once per item, which at 271 items would be roughly 271 times
    /// this much work.
    /// </summary>
    public void ApplyInheritedSlotFiltersAndConflicts()
    {
        if (_database is null || _retexturesByBase.Count == 0)
        {
            return;
        }

        var conflictsUpdated = 0;
        var filtersUpdated = 0;

        foreach (var item in _database.Templates.Items.Values)
        {
            var properties = item.Properties;
            if (properties is null)
            {
                continue;
            }

            if (properties.ConflictingItems is not null)
            {
                foreach (var newId in properties.ConflictingItems
                             .SelectMany(GetRetexturesOf)
                             .ToList())
                {
                    if (properties.ConflictingItems.Add(newId))
                    {
                        conflictsUpdated++;
                    }
                }
            }

            if (properties.Slots is null)
            {
                continue;
            }

            foreach (var filter in properties.Slots
                         .Select(slot => slot.Properties?.Filters)
                         .Where(filters => filters is not null)
                         .SelectMany(filters => filters!)
                         .Where(filter => filter.Filter is not null))
            {
                foreach (var newId in filter.Filter!.SelectMany(GetRetexturesOf).ToList())
                {
                    if (filter.Filter.Add(newId))
                    {
                        filtersUpdated++;
                    }
                }
            }
        }

        logger.Info(
            $"[DRIP] Inherited compatibility for {_retexturesByBase.Values.Sum(list => list.Count)} items: " +
            $"{filtersUpdated} slot filter entries, {conflictsUpdated} conflict entries.");
    }

    private IEnumerable<MongoId> GetRetexturesOf(MongoId baseId)
    {
        return _retexturesByBase.TryGetValue(baseId, out var retextures)
            ? retextures.Select(retexture => retexture.Id)
            : [];
    }

    /// <summary>
    /// Gives DRIP items the same chance of spawning on a bot as the item they retexture, scaled by the config's
    /// `botWeightMultiplier`.
    ///
    /// Bots pick equipment from weighted pools keyed by template id, so a retexture that isn't in those pools simply
    /// never spawns - which is how 274 of 275 configs setting `addToBots: true` currently produces no bots wearing
    /// DRIP at all.
    ///
    /// One pass over every bot type for the whole load, rather than the 3.x approach of walking all bot types once
    /// per item (collection.ts:336-372). With ~90 bot types and 139 items that is the difference between one sweep
    /// and 139 of them.
    /// </summary>
    public void ApplyBotWeightings()
    {
        if (_database is null || _retexturesByBase.Count == 0)
        {
            return;
        }

        if (_config?.AddEquipmentToBots == false)
        {
            logger.Info("[DRIP] Bot loadouts: skipped, 'addEquipmentToBots' is off.");
            return;
        }

        var equipmentEntries = 0;
        var lootEntries = 0;
        var modEntries = 0;

        foreach (var bot in _database.Bots.Types.Values)
        {
            var inventory = bot?.BotInventory;
            if (inventory is null)
            {
                continue;
            }

            if (inventory.Equipment is not null)
            {
                foreach (var slot in inventory.Equipment.Values)
                {
                    equipmentEntries += AddWeightedRetextures(slot, scale: true);
                }
            }

            foreach (var pool in LootPoolsOf(inventory))
            {
                lootEntries += AddWeightedRetextures(pool, scale: false);
            }

            modEntries += AddModCompatibility(inventory.Mods);
        }

        logger.Info(
            $"[DRIP] Bot loadouts: {equipmentEntries} equipment entries, {lootEntries} loot entries, " +
            $"{modEntries} attachment entries.");
    }

    private static IEnumerable<Dictionary<MongoId, double>?> LootPoolsOf(BotTypeInventory inventory)
    {
        var pools = inventory.Items;
        if (pools is null)
        {
            yield break;
        }

        yield return pools.Backpack;
        yield return pools.Pockets;
        yield return pools.SecuredContainer;
        yield return pools.SpecialLoot;
        yield return pools.TacticalVest;
    }

    /// <summary>
    /// Copies each base item's weight onto its retextures. Equipment weights are scaled by the config's multiplier;
    /// loot weights are copied as-is, matching 3.x, where the multiplier only ever applied to worn equipment.
    /// </summary>
    private int AddWeightedRetextures(Dictionary<MongoId, double>? pool, bool scale)
    {
        if (pool is null)
        {
            return 0;
        }

        var added = 0;

        // Materialised first: we are adding to the dictionary we are reading.
        foreach (var (baseId, weight) in pool.ToList())
        {
            if (!_retexturesByBase.TryGetValue(baseId, out var retextures))
            {
                continue;
            }

            foreach (var retexture in retextures.Where(retexture => retexture.AddToBots))
            {
                pool[retexture.Id] = scale
                    ? Math.Round(weight * retexture.WeightMultiplier)
                    : weight;

                added++;
            }
        }

        return added;
    }

    /// <summary>
    /// Makes retextures usable wherever their base item is - both as an attachment on something else, and as a
    /// host that accepts the same attachments.
    /// </summary>
    // The server calls this shape GlobalMods, but that name is a `global using` alias internal to its assembly and
    // isn't visible to mods, so it has to be spelled out here: host item -> slot name -> permitted attachments.
    private int AddModCompatibility(Dictionary<MongoId, Dictionary<string, HashSet<MongoId>>>? mods)
    {
        if (mods is null)
        {
            return 0;
        }

        var added = 0;

        foreach (var slots in mods.Values)
        {
            foreach (var candidates in slots.Values)
            {
                foreach (var retexture in candidates
                             .ToList()
                             .SelectMany(GetBotRetexturesOf))
                {
                    if (candidates.Add(retexture))
                    {
                        added++;
                    }
                }
            }
        }

        // A retexture accepts whatever its base accepts. Done after the loop above so we are not adding keys to the
        // dictionary we are enumerating.
        foreach (var (baseId, slots) in mods.ToList())
        {
            if (!_retexturesByBase.TryGetValue(baseId, out var retextures))
            {
                continue;
            }

            foreach (var retexture in retextures.Where(retexture => retexture.AddToBots))
            {
                mods.TryAdd(retexture.Id, cloner.Clone(slots));
            }
        }

        return added;
    }

    private IEnumerable<MongoId> GetBotRetexturesOf(MongoId baseId)
    {
        return _retexturesByBase.TryGetValue(baseId, out var retextures)
            ? retextures.Where(retexture => retexture.AddToBots).Select(retexture => retexture.Id)
            : [];
    }
}
