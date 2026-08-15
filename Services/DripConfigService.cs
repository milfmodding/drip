using System.Reflection;
using DRIP.Models;
using DRIP.Utils;
using SPTarkov.DI.Annotations;
using SPTarkov.Server.Core.Helpers;
using SPTarkov.Server.Core.Models.Common;
using SPTarkov.Server.Core.Models.Enums;
using SPTarkov.Server.Core.Models.Utils;
using SPTarkov.Server.Core.Services;
using Path = System.IO.Path;

namespace DRIP.Services;

/// <summary>
/// Reads the mod's global options once and applies the ones that transform the game database rather than gate a
/// loader.
/// </summary>
[Injectable(InjectionType.Singleton)]
public class DripConfigService(
    ISptLogger<DripConfigService> logger,
    DatabaseService databaseService,
    ModHelper modHelper
)
{
    private const string ConfigFileName = "config.jsonc";

    private DripConfig? _config;

    /// <summary>
    /// The loaded options. Falls back to defaults - a player who has deleted or broken their config should get a
    /// working mod and one clear message, not a dead one.
    /// </summary>
    public DripConfig Get(Assembly assembly)
    {
        if (_config is not null)
        {
            return _config;
        }

        var path = Path.Combine(modHelper.GetAbsolutePathToModFolder(assembly), "config", ConfigFileName);

        if (!File.Exists(path))
        {
            logger.Warning($"[DRIP] No config/{ConfigFileName}, so DRIP is using its default options.");
            return _config = new DripConfig();
        }

        try
        {
            _config = DripJson.DeserializeFile<DripConfig>(path) ?? new DripConfig();
        }
        catch (Exception ex)
        {
            logger.Error(
                $"[DRIP] config/{ConfigFileName} could not be read, so DRIP is using its default options: {ex.Message}");
            _config = new DripConfig();
        }

        return _config;
    }

    /// <summary>
    /// Rescales what Ragman charges for vanilla clothing.
    /// </summary>
    /// <remarks>
    /// Vanilla only, deliberately - it runs against Ragman's suit list, which DRIP's own clothing is not part of.
    /// A percentage below zero is clamped rather than refused; the intent of a negative number is unambiguous and
    /// failing a whole load over it would be disproportionate.
    /// </remarks>
    public void ApplyVanillaClothingPrices(Assembly assembly)
    {
        var percentage = Get(assembly).VanillaClothingPricePercentage;

        if (percentage == 100)
        {
            return;
        }

        if (percentage < 0)
        {
            logger.Warning(
                $"[DRIP] 'vanillaClothingPricePercentage' is {percentage}, which isn't a meaningful price. " +
                "Treating it as 0, so vanilla clothing is free.");
            percentage = 0;
        }

        var database = databaseService.GetTables();
        if (!database.Traders.TryGetValue(Traders.RAGMAN, out var ragman) || ragman.Suits is null)
        {
            logger.Warning("[DRIP] Ragman has no clothing list, so 'vanillaClothingPricePercentage' did nothing.");
            return;
        }

        var repriced = 0;

        foreach (var requirement in ragman.Suits
                     .Select(suit => suit.Requirements?.ItemRequirements)
                     .Where(requirements => requirements is { Count: > 0 })
                     .Select(requirements => requirements![0]))
        {
            requirement.Count = Math.Round((requirement.Count ?? 0) * percentage / 100.0);
            repriced++;
        }

        logger.Info($"[DRIP] Vanilla clothing: {repriced} outfits repriced to {percentage}% of the original.");
    }
}
