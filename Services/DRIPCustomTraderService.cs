using System.Reflection;
using DRIP.Models;
using DRIP.Utils;
using SPTarkov.DI.Annotations;
using SPTarkov.Server.Core.Helpers;
using SPTarkov.Server.Core.Models.Common;
using SPTarkov.Server.Core.Models.Eft.Common.Tables;
using SPTarkov.Server.Core.Models.Spt.Server;
using SPTarkov.Server.Core.Models.Utils;
using SPTarkov.Server.Core.Services;
using Path = System.IO.Path;
using SPTarkov.Server.Core.Utils;
using SPTarkov.Server.Core.Routers;
using SPTarkov.Server.Core.Servers;
using SPTarkov.Server.Core.Models.Spt.Config;
using SPTarkov.Server.Core.Utils.Cloners;

namespace DRIP.Services;

[Injectable(InjectionType.Singleton)]
public class DRIPCustomTraderService(
    ISptLogger<DRIPCustomTraderService> logger,
    DatabaseService databaseService,
    ImageRouter imageRouter,
    TimeUtil timeUtil,
    ModHelper modHelper,
    ICloner cloner,
    ConfigServer configServer
)
{
    private DatabaseTables? _database;
    // TODO: use the new config injection system
    private readonly TraderConfig _traderConfig = configServer.GetConfig<TraderConfig>();
    private readonly RagfairConfig _ragfairConfig = configServer.GetConfig<RagfairConfig>();

    /// <summary>
    /// Loads custom trader configs from JSON/JSONC files and registers them to the game database.
    /// </summary>
    /// <param name="assembly">The calling assembly, used to determine the mod folder location</param>
    /// <param name="contentPackPath">
    /// Path to the content pack's CustomTraders directory, relative to the mod folder - for example
    /// "bundles/ContentPacks/Essentials/CustomTraders". Already includes the "bundles" segment.
    /// </param>
    public async Task CreateCustomTraders(Assembly assembly, string contentPackPath)
    {
        if (_database == null) _database = databaseService.GetTables();

        var pathToMod = modHelper.GetAbsolutePathToModFolder(assembly);
        var customTradersDirectory = Path.Combine(pathToMod, contentPackPath);

        foreach (var traderFile in Directory.EnumerateFiles(customTradersDirectory, "*.json"))
        {
            var traderId = Path.GetFileNameWithoutExtension(traderFile);
            var traderImagePath = Path.Combine(customTradersDirectory, $"{traderId}.jpeg");
            var traderBase = DripJson.DeserializeFile<CustomTraderConfig>(traderFile);
            if (traderBase is null)
            {
                logger.Error($"[DRIP] Trader config {traderId}.json deserialised to null, skipping.");
                continue;
            }

            // TODO: hard set the trader avatar, since we have everything we need for it. 
            imageRouter.AddRoute(traderBase.Avatar.Replace(".jpg", ""), traderImagePath);

            // Base Config /////////////////////////////////////////////////////////////////////////////////////////
            var traderDataToAdd = new Trader
            {
                // Use an empty assort for now as the content packs will create them.
                Assort = new TraderAssort
                {
                    Items = [],
                    BarterScheme = new Dictionary<MongoId, List<List<BarterScheme>>>(),
                    LoyalLevelItems = new Dictionary<MongoId, int>()
                },
                Base = cloner.Clone(traderBase),
                // These keys MUST be lowercase. The server indexes them unguarded - see
                // PostDbLoadService.ValidateQuestAssortUnlocksExist, which does QuestAssort["started"] for every
                // trader in the database - so capitalised keys are a KeyNotFoundException waiting for a load-order
                // change. Vanilla traders and the 3.x mod both use lowercase.
                QuestAssort = new()
                {
                    { "started", new() },
                    { "success", new() },
                    { "fail", new() }
                },
                Dialogue = []
            };

            databaseService.GetTables().Traders.Add(traderBase.Id, traderDataToAdd);

            // Add a refresh timer for this trader.
            // TODO: load this from the config file?
            var traderRefreshRecord = new UpdateTime
            {
                TraderId = traderBase.Id,
                Seconds = new MinMax<int>(timeUtil.GetHoursAsSeconds(1), timeUtil.GetHoursAsSeconds(2))
            };

            _traderConfig.UpdateTime.Add(traderRefreshRecord);

            // Add this trader to the flea market.
            _ragfairConfig.Traders.TryAdd(traderBase.Id, true);

            // Add the necessary locale strings for the trader.
            var locales = databaseService.GetTables().Locales.Global;
            foreach (var (localeKey, localeKvP) in locales)
            {
                localeKvP.AddTransformer(lazyloadedLocaleData =>
                {
                    // TODO: full name creation from name and surname
                    lazyloadedLocaleData.Add($"{traderBase.Id} FullName", traderBase.Name);
                    lazyloadedLocaleData.Add($"{traderBase.Id} FirstName", traderBase.Name);
                    lazyloadedLocaleData.Add($"{traderBase.Id} Nickname", traderBase.Nickname);
                    lazyloadedLocaleData.Add($"{traderBase.Id} Location", traderBase.Location);
                    lazyloadedLocaleData.Add($"{traderBase.Id} Description", traderBase.Description);
                    return lazyloadedLocaleData;
                });
            }
        }
    }
}