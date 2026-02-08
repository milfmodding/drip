using System.Reflection;
using DRIP.Models;
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
    /// 
    /// Traders are loaded from the mod's "db/CustomTraders" directory (or a custom path if specified).
    /// </summary>
    /// <param name="assembly">The calling assembly, used to determine the mod folder location</param>
    /// <param name="relativePath">(OPTIONAL) Custom path relative to the mod folder</param>
    public async Task CreateCustomTraders(Assembly assembly, string contentPackPath)
    {
        if (_database == null) _database = databaseService.GetTables();

        var pathToMod = modHelper.GetAbsolutePathToModFolder(assembly);
        var customTradersDirectory = $"{pathToMod}/bundles/${contentPackPath}";

        foreach (var traderFile in Directory.EnumerateFiles(customTradersDirectory, "*.json"))
        {
            var traderId = Path.GetFileNameWithoutExtension(traderFile);
            var traderImagePath = Path.Combine(customTradersDirectory, $"{traderId}.jpeg");
            var traderBase = modHelper.GetJsonDataFromFile<CustomTraderConfig>(customTradersDirectory, $"{traderId}.json");

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
                QuestAssort = new()
                {
                    { "Started", new() },
                    { "Success", new() },
                    { "Fail", new() }
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