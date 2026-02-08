using SPTarkov.DI.Annotations;
using SPTarkov.Server.Core.DI;
using SPTarkov.Server.Core.Helpers;
using SPTarkov.Server.Core.Models.Spt.Mod;
using SPTarkov.Server.Core.Models.Utils;
using System.Reflection;

using DRIP.Services;

namespace DRIP
{
    public record ModMetadata : AbstractModMetadata
    {
        public override string Name { get; init; } = "DRIP Core";
        public override string Author { get; init; } = "MILF Modding Team";
        public override List<string>? Contributors { get; init; } =
        [
            "Sophia",
            "Colette Blackpaw",
            "Amber",
            "JustNU",
            "RaiRaiTheRaichu",
            "Virtual"
            // TODO: anyone I missed?
        ];
        public override SemanticVersioning.Version Version { get; init; } = new("2.0.0");
        public override SemanticVersioning.Range SptVersion { get; init; } = new("~4.0.0");


        public override List<string>? Incompatibilities { get; init; }

        public override Dictionary<string, SemanticVersioning.Range>? ModDependencies { get; init; } = new();
        public override string? Url { get; init; }
        public override bool? IsBundleMod { get; init; } = true;
        public override string License { get; init; } = "MIT";
        public override string ModGuid { get; init; } = "gov.milfmodding.drip.core";
    }

    [Injectable(TypePriority = OnLoadOrder.PostSptModLoader + 2)]
    public class DRIP(
        ISptLogger<DRIP> logger,
        ModHelper modHelper,
        DRIPCustomItemService dripCustomItemService,
        //DRIPCustomClothingService dripCustomClothingService,
        DRIPCustomTraderService dripCustomTraderService) : IOnLoad
    {
        public async Task OnLoad()
        {
            var assembly = Assembly.GetExecutingAssembly();

            // Fundamentally, DRIP is a series of Content Packs that assembles itself at runtime, allowing people to
            // determine what items they want in their playthroughs.
            //
            // This also helps immensely with testing and building new items, since DRIP does not need to be re-compiled
            // or adjusted just to add a single new item.
            var assemblyLocation = modHelper.GetAbsolutePathToModFolder(assembly);
            var contentPacksPath = Path.Combine(assemblyLocation, "bundles", "ContentPacks");

            // TODO: error handling?
            foreach (var fullPackPath in Directory.EnumerateDirectories(contentPacksPath))
            {
                var packName = new DirectoryInfo(fullPackPath).Name;
                var packDirectory = Path.GetRelativePath(assemblyLocation, fullPackPath).Replace("\\", "/");
                logger.Info($"[DRIP] Loading Content Pack \"{packName}\"");

                // DRIP-Specific Loaders ///////////////////////////////////////////////////////////////////////////////
                // We need to load the traders first because all our custom items depend on them. :)
                await DoIfPathExists(fullPackPath, "CustomTraders", async () =>
                {
                    await dripCustomTraderService.CreateCustomTraders(assembly, $"{packDirectory}/CustomTraders");
                });

                await DoIfPathExists(fullPackPath, "CustomItems", async () =>
                {
                    await dripCustomItemService.CreateCustomItems(assembly, $"{packDirectory}/CustomItems");
                });

                // DoIfPathExists(fullPackPath, "CustomClothing", async () =>
                // {
                //     await dripCustomClothingService.CreateCustomClothing(assembly, $"{packDirectory}/CustomClothing");
                // });

                // WTT Loaders /////////////////////////////////////////////////////////////////////////////////////////
                // await wttCommon.CustomAchievementService.CreateCustomAchievements(assembly, $"${packDirectory}/CustomAchievements");
                // await wttCommon.CustomAssortSchemeService.CreateCustomAssortSchemes(assembly, $"${packDirectory}/CustomAssortSchemes");
                // await wttCommon.CustomBotLoadoutService.CreateCustomBotLoadouts(assembly, $"${packDirectory}/CustomBotLoadouts");
                // await wttCommon.CustomHideoutRecipeService.CreateHideoutRecipes(assembly, $"${packDirectory}/CustomHideoutRecipes");
                // await wttCommon.CustomLocaleService.CreateCustomLocales(assembly, $"${packDirectory}/CustomLocales");
                // await wttCommon.CustomQuestService.CreateCustomQuests(assembly, $"${packDirectory}/CustomQuests");
            }

            // Clothing Tags Integration ///////////////////////////////////////////////////////////////////////////////
            // TODO: integrate with ICUP :)
        }

        /// <summary>
        /// Conditionally apply a function if the given directory exists. We mostly do this to avoid a ton of confusing
        /// logging if a content pack doesn't have a given thing like CustomBotLoadouts or whatever.
        /// </summary>
        private static Task DoIfPathExists(string basePath, string search, Func<Task> toDo)
        {
            var fullPath = Path.Combine(basePath, search);
            if (Directory.Exists(fullPath))
            {
                toDo();
            }

            return Task.CompletedTask;
        }
    }
}
