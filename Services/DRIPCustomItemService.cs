using System.Reflection;
using SPTarkov.DI.Annotations;
using SPTarkov.Server.Core.Helpers;
using SPTarkov.Server.Core.Loaders;
using SPTarkov.Server.Core.Models.Eft.Common;
using SPTarkov.Server.Core.Models.Spt.Mod;
using SPTarkov.Server.Core.Models.Spt.Server;
using SPTarkov.Server.Core.Models.Utils;
using SPTarkov.Server.Core.Servers;
using SPTarkov.Server.Core.Services;
using SPTarkov.Server.Core.Services.Mod;
using SPTarkov.Server.Core.Utils;
using Path = System.IO.Path;

namespace DRIP.Services;

[Injectable(InjectionType.Singleton)]
public class DRIPCustomItemService(
    ISptLogger<DRIPCustomItemService> logger,
    CustomItemService customItemService,
    DatabaseServer databaseServer,
    ModHelper modHelper,
    BundleHashCacheService bundleHashCacheService,
    HashUtil hashUtil,
    JsonUtil jsonUtil,
    BundleLoader bundleLoader
)
{
    private DatabaseTables? _database;

    /// <summary>
    /// Loads custom item configurations from JSON/JSONC files and creates items with all associated properties.
    ///
    /// Items are loaded from the mod's "db/CustomItems" directory (or a custom path if specified).
    /// Each item is cloned from a base template and can be configured with traders, presets, masteries, slots, loot tables, and more.
    ///
    /// </summary>
    /// <param name="assembly">The calling assembly, used to determine the mod folder location</param>
    /// <param name="relativePath">(OPTIONAL) Custom path relative to the mod folder</param>
    public async Task CreateCustomItems(Assembly assembly, string contentPackPath)
    {
        if (_database == null) _database = databaseServer.GetTables();

        // These paths are required to assemble the full path to the bundles for that loader.
        var assemblyLocation = modHelper.GetAbsolutePathToModFolder(assembly);
        var serverDir = Directory.GetCurrentDirectory();
        var modPath = Path.GetRelativePath(serverDir, assemblyLocation).Replace("\\", "/");
        var modBundlePath = Path.Join(modPath, "bundles").Replace("\\", "/");

        try
        {
            var itemsCreated = 0;
            var finalDir = Path.Combine(assemblyLocation, contentPackPath);
            foreach (var file in Directory.EnumerateFiles(finalDir, "*.json*", SearchOption.AllDirectories))
            {
                var fullFile = new FileInfo(file);
                // We need to remove the file extension to get the real name of the item.
                var rawFilename = fullFile.Name.Replace(fullFile.Extension, "");
                var itemMongoId = (await hashUtil.GenerateHashForDataAsync(HashingAlgorithm.SHA1, rawFilename))[..24].ToLower();
                var thisPath = fullFile.Directory.FullName;
                var serverRelativePath = Path.GetRelativePath(serverDir, thisPath);

                // TODO: error handling?
                var thisItemConfig = modHelper.GetJsonDataFromFile<Models.CustomItemConfig>(thisPath, file);

                // Load in all the bundles from the same directory.
                // This allows us to not have to specify a bundles.json with the mod so DRIP can assemble itself at startup.
                foreach (var bundleFile in Directory.EnumerateFiles(thisPath, "*.bundle"))
                {
                    var fullBundleFile = new FileInfo(bundleFile);
                    var bundleKey = Path.GetRelativePath(modBundlePath, fullBundleFile.FullName).Replace("\\", "/");

                    var bundleLocalPath = Path.Join(modBundlePath, bundleKey).Replace("\\", "/");
                    var bundleHash = await bundleHashCacheService.CalculateMatchAndStoreHash(bundleLocalPath);
                    var bundleManifest = new BundleManifestEntry
                    {
                        Key = bundleKey,
                        // We always include the default dependencies since no bundle is ever going to ship without them.
                        DependencyKeys = [
                            "shaders",
                            "cubemaps",
                            "assets/commonassets/physics/physicsmaterials.bundle"
                        ],
                    };

                    if (thisItemConfig.BundleDependencies is not null && thisItemConfig.BundleDependencies.TryGetValue(fullBundleFile.Name, out List<string>? value))
                    {
                        bundleManifest.DependencyKeys = [.. bundleManifest.DependencyKeys.Concat(value).Distinct()];
                    }

                    // TODO: better error handling?
                    bundleLoader.AddBundle(bundleKey, new BundleInfo(modPath, bundleManifest, bundleHash));
                }

                // TODO: validate config
                if (CreateItemFromConfig(itemMongoId, thisItemConfig))
                {
                    itemsCreated++;
                }
            }

            logger.Info($"[DRIP] {contentPackPath}: {itemsCreated} new items.");
        }
        catch (Exception ex)
        {
            logger.Error($"Error loading configs: {ex.Message}");
        }
    }

    private bool CreateItemFromConfig(string newItemId, Models.CustomItemConfig config)
    {
        try
        {
            var itemDetails = new NewItemFromCloneDetails
            {
                ItemTplToClone = config.ItemTplToClone,
                ParentId = "5448e53e4bdc2d60728b4567",
                HandbookParentId = "5b5f6f6c86f774093f2ecf0b",
                NewId = newItemId,

                // TODO: lookup the existing FleaPriceRoubles and HandbookPriceRoubles
                FleaPriceRoubles = 69420,
                HandbookPriceRoubles = 69420,
                // TODO: "en" special processing
                Locales = config.Locales,
                OverrideProperties = config.OverrideProperties
            };

            customItemService.CreateItemFromClone(itemDetails);
            logger.Info($"Created item {newItemId}"); // TODO: debug

            // ProcessAdditionalProperties(newItemId, config);

            return true;
        }
        catch (Exception ex)
        {
            logger.Error($"Failed to create item {newItemId}: {ex.Message}");
            return false;
        }
    }

    /*private void ProcessAdditionalProperties(string newItemId, CustomItemConfig config)
    {
        if (_database == null) return;
        if (config is { AddToTraders: true, Traders: not null })
            traderItemHelper.AddItem(config, newItemId);

        if (config.AddWeaponPreset == true)
            weaponPresetHelper.ProcessWeaponPresets(config, newItemId);

        if (config is { Masteries: true, MasterySections: not null })
            masteryHelper.AddOrUpdateMasteries(config.MasterySections, newItemId);

        if (config.AddToModSlots == true)
            AddDeferredModSlot(newItemId, config);

        if (config.AddToInventorySlots != null)
            inventorySlotHelper.ProcessInventorySlots(config, newItemId);

        if (config.AddToHallOfFame == true)
            hallOfFameHelper.AddToHallOfFame(config, newItemId);

        if (config.AddToSpecialSlots == true)
            specialSlotsHelper.AddToSpecialSlots(config, newItemId);

        if (config is { AddToStaticLootContainers: true, StaticLootContainers: not null })
            staticLootHelper.ProcessStaticLootContainers(config, newItemId);

        if (config.AddToBots == true)
            botLootHelper.AddToBotLoot(config, newItemId);

        if (config.AddCaliberToAllCloneLocations == true)
            caliberHelper.AddNewCaliberToItems(config, newItemId);

        if (config is { AddToGeneratorAsFuel: true, GeneratorFuelSlotStages: not null })
            generatorFuelHelper.AddGeneratorFuel(config, newItemId);

        if (config.AddToHideoutPosterSlots == true)
            hideoutPosterHelper.AddToPosterSlot(newItemId);

        if (config is { AddPosterToMaps: true, PosterSpawnProbability: not null })
            posterLootHelper.ProcessPosterLoot(config, newItemId);

        if (config.AddToStatuetteSlots == true)
            hideoutStatuetteHelper.AddToStatuetteSlot(newItemId);

        if (config.AddToStaticAmmo == true)
            staticAmmoHelper.AddAmmoToLocationStaticAmmo(config, newItemId);

        if (config.AddToEmptyPropSlots == true)
            emptyPropSlotHelper.AddCustomSlots(config, newItemId);
        if (config.AddToSecureFilters == true)
            AddDeferredSecureFilters(newItemId, config);

        // TODO: copyAssort
        // TODO: traderId
    }

    private void AddDeferredModSlot(string newItemId, CustomItemConfig config)
    {
        if (_deferredModSlotConfigs.Any(d => d.newItemId == newItemId))
        {
            logger.Warning($"Deferred modslot for {newItemId} already exists, skipping.");
            return;
        }

        _deferredModSlotConfigs.Add((newItemId, config));
    }

    public void ProcessDeferredModSlots()
    {
        if (_deferredModSlotConfigs.Count == 0)
        {
            LogHelper.Debug(logger, "No deferred modslots to process");
            return;
        }

        LogHelper.Debug(logger, $"Processing {_deferredModSlotConfigs.Count} deferred modslots...");

        foreach (var (newItemId, config) in _deferredModSlotConfigs)
            try
            {
                if (_database == null) return;
                modSlotHelper.ProcessModSlots(config, newItemId);

                if (logger.IsLogEnabled(LogLevel.Debug)) LogHelper.Debug(logger, $"Processed modslots for {newItemId}");
            }
            catch (Exception ex)
            {
                logger.Critical($"Failed processing modslots for {newItemId}", ex);
            }

        _deferredModSlotConfigs.Clear();

        LogHelper.Debug(logger, "Finished processing deferred modslots");
    }

    private void AddDeferredSecureFilters(string newItemId, CustomItemConfig config)
    {
        if (_deferredSecureFilterConfigs.Any(d => d.newItemId == newItemId))
        {
            logger.Warning($"Deferred secure filters for {newItemId} already exists, skipping.");
            return;
        }

        _deferredSecureFilterConfigs.Add((newItemId, config));
    }

    public void ProcessDeferredSecureFilters()
    {
        if (_deferredSecureFilterConfigs.Count == 0)
        {
            LogHelper.Debug(logger, "No deferred secure filters to process");
            return;
        }

        LogHelper.Debug(logger, $"Processing {_deferredSecureFilterConfigs.Count} deferred secure filters...");

        foreach (var (newItemId, config) in _deferredSecureFilterConfigs)
            try
            {
                if (_database == null) return;
                secureFiltersHelper.AddToSecureFilters(config, newItemId);

                if (logger.IsLogEnabled(LogLevel.Debug))
                    LogHelper.Debug(logger, $"Processed secure filters for {newItemId}");
            }
            catch (Exception ex)
            {
                logger.Critical($"Failed processing secure filters for {newItemId}", ex);
            }

        _deferredSecureFilterConfigs.Clear();

        LogHelper.Debug(logger, "Finished processing deferred secure filters");
    }*/
}
