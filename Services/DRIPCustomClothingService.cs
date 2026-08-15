using System.Reflection;
using System.Text.Json;
using DRIP.Models;
using DRIP.Utils;
using SPTarkov.DI.Annotations;
using SPTarkov.Server.Core.Models.Common;
using SPTarkov.Server.Core.Models.Eft.Common.Tables;
using SPTarkov.Server.Core.Models.Spt.Server;
using SPTarkov.Server.Core.Models.Utils;
using SPTarkov.Server.Core.Services;
using SPTarkov.Server.Core.Utils;
using SPTarkov.Server.Core.Utils.Cloners;
using Path = System.IO.Path;

namespace DRIP.Services;

/// <summary>
/// Creates DRIP's custom clothing - tops (body + hands) and bottoms (feet) - and puts them on sale at a trader.
///
/// Each piece of clothing is three or two database entries: the customization item(s) holding the model, plus a
/// "suite" that binds them together and is what the trader actually sells.
/// </summary>
[Injectable(InjectionType.Singleton)]
public class DRIPCustomClothingService(
    ISptLogger<DRIPCustomClothingService> logger,
    DatabaseService databaseService,
    DRIPBundleService bundleService,
    HashUtil hashUtil,
    ICloner cloner,
    DripConfigService configService
)
{
    // Vanilla customization entries used as templates.
    //
    // These are cloned rather than constructed field-by-field. Cloning inherits every property BSG sets - including
    // ones we don't know about and ones they add later - where hand-construction silently drops them. All five were
    // verified present in 4.0.13, and their parent ids match what a from-scratch implementation would have had to
    // hardcode, so cloning costs nothing and cannot drift.
    private static readonly MongoId TopBodyTemplate = new("5d28adcb86f77429242fc893");
    private static readonly MongoId TopHandsTemplate = new("5d1f5b5386f7744bcc048757");
    private static readonly MongoId TopSuiteTemplate = new("5d1f623e86f7744bce0ef705");
    private static readonly MongoId BottomFeetTemplate = new("5d5e7f4986f7746956659f8a");
    private static readonly MongoId BottomSuiteTemplate = new("5cd946231388ce000d572fe3");

    /// <summary>Scavs wear DRIP too - the vanilla suites are USEC/BEAR only, so this is widened on every suite.</summary>
    private static readonly List<string> AllSides = ["Usec", "Bear", "Savage"];

    /// <summary>
    /// Bot types that wear DRIP clothing.
    ///
    /// Carried over from the 3.x list (collection.ts:540-553), which is deliberately humans-only - bosses have
    /// signature outfits players recognise, and cultists and the infected have their own look. Two names in that
    /// list no longer exist in 4.0.13 ("followertagilla", "followergluharsnipe") and are dropped; "pmcusec" and
    /// "pmcbear" are added because those are what PMCs are called now, where 3.x had only "usec" and "bear".
    ///
    /// CAVEAT, and it matters when reading a raid: five of these are boss escorts - followerbully, the three Gluhar
    /// followers, and followerkojaniy. EFT's AI Amount preset rewrites escort counts client-side. The reported
    /// formula halves the *range* between the database's min and max escort amount using integer division, so it
    /// collapses to zero whenever max - min <= 1 - which is a range condition, not "the amount is a single value".
    /// The client half of that is not something we can verify from here; what we can verify is the database, and it
    /// is where the condition bites:
    ///
    ///   - every escort entry for our five clothed types has max - min <= 1, so all of them zero on Medium
    ///   - across every escort-bearing entry in the vanilla DB, Medium yields 0 or 1 and never more
    ///   - followerkojaniy on Woods is "2,3" - one of our own entries that is NOT a single value but still zeroes
    ///
    /// That last row is why the condition is stated as a range: the flat phrasing sends a reader to check the wrong
    /// thing and clears one of the five types that is actually affected. Escort amounts also live in two places per
    /// spawn - the primary BossEscortType and each entry in Supports - and Supports is where the multi-type escorts
    /// are, so a scan that reads only the primary field undercounts (that is how the three Gluhar followers hide).
    ///
    /// Consequence for testing: on a Medium install these five never spawn no matter what the server did, so a quiet
    /// raid is not evidence against this feature - test on High or AsOnline. Nothing server-side can influence it.
    /// Reserve on High is the best escort raid available: bossGluhar at 50% brings all three Gluhar follower types,
    /// so three clothed escort types in one raid. Customs gives followerbully at 39% ("4"), Woods followerkojaniy
    /// at 50%.
    ///
    /// Reserve on High yields SIX followers, not eight - observed in a raid on 2026-07-29, all six wearing DRIP.
    /// The database cannot tell you this: bossGluhar declares followerGluharSecurity at 2 as its primary
    /// BossEscortType *and* three Supports entries at 2 each, and whether the primary stacks with the Supports or is
    /// superseded by them is client behaviour. It is superseded. Recorded here because it was deliberately left out
    /// as unknowable until a raid settled it, and the next person should not have to re-derive it from a spawn table
    /// that does not contain the answer.
    ///
    /// The escort gate is NOT, however, the whole story, because "assault" is in the list below (Sophia's call).
    /// Sorting all 13 by how they actually spawn in vanilla location data:
    ///
    ///   - wave-spawned, never an escort, so preset-insensitive: assault, marksman. assault does the work here -
    ///     140 wave entries across 17 maps - and is the most numerous bot in any raid.
    ///   - boss- or escort-spawned, so subject to the arithmetic to some degree: the five followers above, plus
    ///     pmcbot, exusec, pmcusec, pmcbear (SPT spawns PMCs through the boss mechanism, not through waves).
    ///   - never spawned at all from vanilla data: usec, bear. Neither has a wave entry or an escort entry anywhere;
    ///     they are the 3.x names, superseded by pmcusec/pmcbear. Harmless to keep and another mod may use them, but
    ///     do not count them as evidence of anything in a raid.
    ///
    /// So this feature is observable on any preset on any map through scavs alone. Read the caveat the right way
    /// round: the preset excuses a raid with no *escort* clothing and excuses nothing else. No DRIP clothing on any
    /// bot at all is a real failure and should be escalated, not attributed to Medium.
    /// </summary>
    private static readonly string[] ClothedBotTypes =
    [
        // Scavs are here (Sophia's call). ~11 Part 1 garments are genuinely scav retextures, including a family
        // literally named SCAVJEANS that no scav could wear across both 3.x and 4.x.
        //
        // They were excluded in 3.x as a workaround for a missing capability, not out of taste: the list used to be
        // applied indiscriminately, so admitting scavs also put modern plate-carrier-era jackets on them. That
        // capability now exists - see MayWear below - so the workaround is retired.
        "assault",

        "marksman",
        "pmcbot",
        "exusec",
        "usec",
        "bear",
        "pmcusec",
        "pmcbear",
        "followerbully",
        "followergluharassault",
        "followergluharscout",
        "followergluharsecurity",
        "followerkojaniy"
    ];

    private DripConfig? _config;

    /// <summary>A garment DRIP registered for bots, kept with the filename that produced it so a debug pin can
    /// name one the way authors name everything else.</summary>
    private record BotGarment(string Stem, MongoId Id, string? VanillaOrigin, List<string>? BotTypes);

    private readonly List<BotGarment> _botBodies = [];
    private readonly List<BotGarment> _botFeet = [];

    private DatabaseTables? _database;

    /// <summary>
    /// Loads clothing configs from one content pack.
    /// </summary>
    /// <param name="assembly">The calling assembly, used to determine the mod folder location</param>
    /// <param name="contentPackPath">
    /// Path to the content pack's CustomClothing directory, relative to the mod folder - already includes "bundles".
    /// </param>
    public async Task CreateCustomClothing(Assembly assembly, string contentPackPath)
    {
        _database ??= databaseService.GetTables();
        _config ??= configService.Get(assembly);

        var paths = bundleService.GetModPaths(assembly);
        var finalDir = paths.Resolve(contentPackPath);

        var created = 0;
        var failed = 0;
        var missingModelBundle = new List<string>();

        foreach (var file in DripFiles.EnumerateConfigFiles(finalDir))
        {
            var configFile = new FileInfo(file);
            var relativeName = Path.GetRelativePath(finalDir, file).Replace("\\", "/");

            try
            {
                var config = DripJson.DeserializeFile<ContentItemConfig>(file);
                if (config is null)
                {
                    logger.Error($"[DRIP] {relativeName}: file is empty or could not be read.");
                    failed++;
                    continue;
                }

                if (await CreateClothing(config, configFile, relativeName, paths, missingModelBundle))
                {
                    created++;
                }
                else
                {
                    failed++;
                }
            }
            catch (Exception ex)
            {
                logger.Error($"[DRIP] {relativeName}: {ex.Message}");
                failed++;
            }
        }

        if (missingModelBundle.Count > 0)
        {
            var (isUnbootstrapped, message) =
                DRIPBundleService.DescribeMissingBundles(missingModelBundle, created + failed, "clothing bundle");

            if (isUnbootstrapped)
            {
                logger.Warning($"[DRIP] {contentPackPath}: {message}");
            }
            else
            {
                logger.Error($"[DRIP] {contentPackPath}: {message}");
            }
        }

        if (failed > 0)
        {
            logger.Error($"[DRIP] {contentPackPath}: {created} new clothing items, {failed} failed.");
        }
        else
        {
            logger.Info($"[DRIP] {contentPackPath}: {created} new clothing items.");
        }
    }

    private async Task<bool> CreateClothing(
        ContentItemConfig config,
        FileInfo configFile,
        string relativeName,
        DRIPBundleService.ModPaths paths,
        List<string> missingModelBundle)
    {
        if (_database is null)
        {
            logger.Error($"[DRIP] {relativeName}: database is not available.");
            return false;
        }

        if (config.HasUnrecognisedType)
        {
            logger.Error($"[DRIP] {relativeName}: 'type' must be \"top\" or \"bottom\" - found \"{config.TypeRaw}\".");
            return false;
        }

        if (config.Type is null)
        {
            logger.Error($"[DRIP] {relativeName}: 'type' is missing - it must be \"top\" or \"bottom\".");
            return false;
        }

        if (config.IsGear)
        {
            logger.Error($"[DRIP] {relativeName}: this is a 'gear' config, but it is in CustomClothing. Move it to CustomItems.");
            return false;
        }

        if (string.IsNullOrWhiteSpace(config.Name))
        {
            logger.Error($"[DRIP] {relativeName}: 'name' is missing - this is what players see in game.");
            return false;
        }

        if (config.HasUnrecognisedCurrency)
        {
            logger.Error($"[DRIP] {relativeName}: 'currency' must be \"RUB\", \"USD\" or \"EUR\" - found \"{config.CurrencyRaw}\".");
            return false;
        }

        // Zero prices are legacy test junk rather than deliberately free items, so this names the file and carries
        // on. The NoClothingRequirements option zeroes prices at runtime and is unaffected by this.
        if (config.Price == 0)
        {
            logger.Warning(
                $"[DRIP] {relativeName}: 'price' is 0, so this is free. If that wasn't intended, give it a price.");
        }

        if (!DripTraders.TryResolve(config.TraderId, out var traderId))
        {
            logger.Error(
                $"[DRIP] {relativeName}: no trader called \"{config.TraderId}\". " +
                $"Known names: {string.Join(", ", DripTraders.KnownNames)}. Or use a trader's ID.");
            return false;
        }

        if (!_database.Traders.TryGetValue(traderId, out var trader))
        {
            logger.Error($"[DRIP] {relativeName}: trader {config.TraderId} resolved to {traderId}, which isn't in the database.");
            return false;
        }

        // Clothing needs several ids where the author supplies at most one, so the rest are derived from it. All are
        // deterministic functions of the filename, so they are stable across restarts and folder moves.
        var stem = config.Id ?? Path.GetFileNameWithoutExtension(configFile.Name);
        var suiteId = await DripIds.Derive(hashUtil, stem, "suite");

        // The trader's offer and the customization entry it sells are separate records with separate ids. Checked
        // against vanilla: all 109 of Ragman's suits have a distinct _id and suiteId, and the 3.x mod did the same.
        var offerId = await DripIds.Derive(hashUtil, stem, "offer");

        var bundles = await bundleService.RegisterBundlesNextTo(configFile, config.Bundles, paths);

        // Only worth saying when some bundles are present. If the folder is empty, the aggregate missing-bundle
        // report already covers it, and repeating it per declared dependency would be two more lines per file.
        if (bundles.Count > 0)
        {
            foreach (var missing in DRIPBundleService.FindDeclaredButMissing(config.Bundles, bundles))
            {
                logger.Warning($"[DRIP] {relativeName}: 'bundles' mentions {missing}, but there's no {missing} in this folder.");
            }
        }

        var suite = config.Type == ContentItemType.Top
            ? await BuildTop(config, stem, suiteId, bundles, relativeName, missingModelBundle)
            : await BuildBottom(config, stem, suiteId, bundles, relativeName, missingModelBundle);

        if (suite is null)
        {
            return false;
        }

        _database.Templates.Customization[suiteId] = suite;

        AddSuiteToTrader(config, trader, traderId, offerId, suiteId);
        AddSuiteLocale(config, suiteId);

        return true;
    }

    /// <summary>
    /// A top is three entries: the body model, the first-person hands model, and the suite tying them together.
    /// </summary>
    private async Task<CustomizationItem?> BuildTop(
        ContentItemConfig config,
        string stem,
        MongoId suiteId,
        Dictionary<string, string> bundles,
        string relativeName,
        List<string> missingModelBundle)
    {
        if (!TryGetBundleKey(bundles, "TOP.bundle", relativeName, missingModelBundle, out var topBundleKey) ||
            !TryGetBundleKey(bundles, "HANDS.bundle", relativeName, missingModelBundle, out var handsBundleKey))
        {
            return null;
        }

        var bodyId = await DripIds.Derive(hashUtil, stem, "body");
        var handsId = await DripIds.Derive(hashUtil, stem, "hands");

        var body = CloneCustomization(TopBodyTemplate, bodyId, $"{stem}_body", topBundleKey);
        var hands = CloneCustomization(TopHandsTemplate, handsId, $"{stem}_hands", handsBundleKey);
        if (body is null || hands is null)
        {
            logger.Error($"[DRIP] {relativeName}: the vanilla clothing templates this clones are missing from the database.");
            return null;
        }

        _database!.Templates.Customization[bodyId] = body;
        _database.Templates.Customization[handsId] = hands;

        // Bots pick a body and a pair of feet independently from weighted pools, so the body id goes in - not the
        // suite. Hands follow whatever body was chosen, so they are not pooled separately.
        _botBodies.Add(new BotGarment(stem, bodyId, config.VanillaOrigin, config.BotTypes));

        var suite = cloner.Clone(_database.Templates.Customization[TopSuiteTemplate]);
        suite.Id = suiteId;
        suite.Name = $"{stem}_suite";
        suite.Properties.Side = AllSides;
        suite.Properties.Body = bodyId;
        suite.Properties.Hands = handsId;

        return suite;
    }

    /// <summary>
    /// A bottom is two entries: the feet model and its suite.
    /// </summary>
    private async Task<CustomizationItem?> BuildBottom(
        ContentItemConfig config,
        string stem,
        MongoId suiteId,
        Dictionary<string, string> bundles,
        string relativeName,
        List<string> missingModelBundle)
    {
        if (!TryGetBundleKey(bundles, "BOTTOM.bundle", relativeName, missingModelBundle, out var bottomBundleKey))
        {
            return null;
        }

        var feetId = await DripIds.Derive(hashUtil, stem, "feet");

        var feet = CloneCustomization(BottomFeetTemplate, feetId, $"{stem}_feet", bottomBundleKey);
        if (feet is null)
        {
            logger.Error($"[DRIP] {relativeName}: the vanilla clothing templates this clones are missing from the database.");
            return null;
        }

        _database!.Templates.Customization[feetId] = feet;

        _botFeet.Add(new BotGarment(stem, feetId, config.VanillaOrigin, config.BotTypes));

        var suite = cloner.Clone(_database.Templates.Customization[BottomSuiteTemplate]);
        suite.Id = suiteId;
        suite.Name = $"{stem}_suite";
        suite.Properties.Side = AllSides;
        suite.Properties.Feet = feetId;

        return suite;
    }

    private CustomizationItem? CloneCustomization(MongoId template, MongoId newId, string name, string bundleKey)
    {
        if (_database is null || !_database.Templates.Customization.TryGetValue(template, out var source))
        {
            return null;
        }

        var clone = cloner.Clone(source);
        clone.Id = newId;
        clone.Name = name;
        clone.Properties.Side = AllSides;
        clone.Properties.Prefab = new Prefab { Path = bundleKey, Rcid = string.Empty };

        return clone;
    }

    private bool TryGetBundleKey(
        Dictionary<string, string> bundles,
        string expected,
        string relativeName,
        List<string> missingModelBundle,
        out string bundleKey)
    {
        if (bundles.TryGetValue(expected, out var found))
        {
            bundleKey = found;
            return true;
        }

        bundleKey = string.Empty;

        // An empty folder is the un-bootstrapped case and is reported once for the whole pack. A folder that has
        // some bundles but not this one is a genuine content bug, so it is named immediately.
        if (bundles.Count == 0)
        {
            missingModelBundle.Add(relativeName);
            return false;
        }

        logger.Error(
            $"[DRIP] {relativeName}: expected {expected} next to this file - the folder has: " +
            $"{string.Join(", ", bundles.Keys)}.");

        return false;
    }

    private void AddSuiteToTrader(
        ContentItemConfig config,
        Trader trader,
        MongoId traderId,
        MongoId offerId,
        MongoId suiteId)
    {
        trader.Base.CustomizationSeller = true;
        trader.Suits ??= [];

        trader.Suits.Add(new Suit
        {
            Id = offerId,
            Tid = traderId,
            SuiteId = suiteId,
            IsActive = true,
            IsHiddenInPVE = false,
            ExternalObtain = false,
            InternalObtain = true,
            // With noClothingRequirements every garment is free and unlocked. Applied here rather than by
            // rewriting configs, so the option can be turned back off without touching content.
            Requirements = _config!.NoClothingRequirements
                ? new SuitRequirements
                {
                    LoyaltyLevel = 1,
                    ProfileLevel = 1,
                    Standing = 0,
                    SkillRequirements = [],
                    QuestRequirements = [],
                    AchievementRequirements = [],
                    ItemRequirements = [],
                    RequiredTid = traderId
                }
                : new SuitRequirements
                {
                    LoyaltyLevel = config.LoyaltyLevel,
                    ProfileLevel = config.ProfileLevel,
                    Standing = config.Standing,
                    SkillRequirements = [],
                    QuestRequirements = config.QuestRequirements ?? [],
                    AchievementRequirements = [],
                    ItemRequirements =
                    [
                        new ItemRequirement
                        {
                            Count = config.Price ?? 0,
                            Tpl = config.CurrencyTpl,
                            OnlyFunctional = true
                        }
                    ],
                    RequiredTid = traderId
                }
        });
    }

    /// <summary>
    /// Lets bots wear DRIP clothing, by adding each garment to the weighted appearance pools bots choose from.
    ///
    /// Without this the 136 clothing items exist and are buyable but are worn by nobody but the player. 3.x did the
    /// same thing (collection.ts:536-566) whenever its tag system was off, which - with tags tabled and moving to
    /// ICUP - is the only path we currently have.
    ///
    /// Deferred to one pass after all packs have loaded, matching the other cross-pack fixups.
    /// </summary>
    public void ApplyBotAppearance()
    {
        if (_database is null || (_botBodies.Count == 0 && _botFeet.Count == 0))
        {
            return;
        }

        if (_config?.AddClothingToBots == false)
        {
            logger.Info("[DRIP] Bot appearance: skipped, 'addClothingToBots' is off.");
            return;
        }

        // Resolved here rather than at boot: the 136 garments are registered *during* load, so a name that is
        // invalid at startup can be perfectly valid by the time this runs.
        var (pinnedTop, pinnedBottom, pinRefused) = ResolvePins();
        if (pinRefused)
        {
            return;
        }

        ReportGarmentsWithoutAnOrigin();

        var missingBotTypes = new List<string>();
        var perType = new List<string>();
        var botsUpdated = 0;

        foreach (var botType in ClothedBotTypes)
        {
            if (!_database.Bots.Types.TryGetValue(botType, out var bot) || bot.BotAppearance is null)
            {
                missingBotTypes.Add(botType);
                continue;
            }

            // Snapshot what this bot wears in vanilla BEFORE adding anything, or we would be testing DRIP garments
            // against a pool DRIP has already contaminated and everything would qualify.
            var vanillaBodies = VanillaPrefabPaths(bot.BotAppearance.Body);
            var vanillaFeet = VanillaPrefabPaths(bot.BotAppearance.Feet);

            var tops = 0;
            var bottoms = 0;

            if (pinnedTop is not null)
            {
                bot.BotAppearance.Body.Clear();
                bot.BotAppearance.Body[pinnedTop.Id] = 1;
                tops = 1;
            }
            else
            {
                foreach (var body in _botBodies.Where(garment => MayWear(garment, botType, vanillaBodies)))
                {
                    bot.BotAppearance.Body[body.Id] = 1;
                    tops++;
                }
            }

            if (pinnedBottom is not null)
            {
                bot.BotAppearance.Feet.Clear();
                bot.BotAppearance.Feet[pinnedBottom.Id] = 1;
                bottoms = 1;
            }
            else
            {
                foreach (var feet in _botFeet.Where(garment => MayWear(garment, botType, vanillaFeet)))
                {
                    bot.BotAppearance.Feet[feet.Id] = 1;
                    bottoms++;
                }
            }

            // Per bot type, not a total. A type dropping to zero is sometimes correct (pmcbot's vanilla pool is one
            // garment, so nothing DRIP retextures is in it) and sometimes a bug, and only a per-type line lets
            // anyone tell those apart.
            perType.Add($"{botType} {tops}/{bottoms}");
            botsUpdated++;
        }

        if (pinnedTop is null && pinnedBottom is null)
        {
            // Stated positively. "Not pinned" has to be a logged fact, or a later reader cannot tell an ordinary
            // run from a pinned one by its absence.
            logger.Info(
                $"[DRIP] Bot appearance (tops/bottoms per bot type): {string.Join(", ", perType)}. " +
                "Not pinned - bots roll normally.");
        }
        else
        {
            var topState = pinnedTop is null
                ? "tops left unpinned"
                : $"exactly 1 top, {pinnedTop.Stem} ({pinnedTop.Id})";

            var bottomState = pinnedBottom is null
                ? "bottoms left unpinned"
                : $"exactly 1 bottom, {pinnedBottom.Stem} ({pinnedBottom.Id})";

            logger.Warning(
                $"[DRIP] Bot appearance PINNED for debugging - {topState} and {bottomState} across " +
                $"{botsUpdated} bot types. Per type (tops/bottoms): {string.Join(", ", perType)}. " +
                "This is not a normal game; turn the pin off in config/config.jsonc.");
        }

        // Named rather than silently skipped: a bot type disappearing from the game is exactly how this feature
        // would quietly stop covering the bots it is supposed to.
        if (missingBotTypes.Count > 0)
        {
            logger.Warning(
                $"[DRIP] These bot types aren't in the database, so they won't wear DRIP clothing: " +
                $"{string.Join(", ", missingBotTypes)}.");
        }
    }

    /// <summary>
    /// Whether a bot type may wear a garment.
    /// </summary>
    /// <remarks>
    /// A bot wears a retexture exactly when it already wears the thing being retextured. That is the same rule
    /// `copyOriginalOffers` and slot-filter inheritance follow, applied to appearance: the original's suitability is
    /// inherited rather than restated.
    ///
    /// It rests on one assumption - that an author clones the base garment matching their intent. A scav-intended
    /// retexture built from a PMC base would be misclassified, which is what `botTypes` exists to correct.
    /// </remarks>
    private static bool MayWear(BotGarment garment, string botType, HashSet<string> vanillaPrefabPaths)
    {
        // An explicit list wins outright, including an empty one - that means "player-only", which is a thing an
        // author may legitimately want and is distinct from not having said anything.
        if (garment.BotTypes is not null)
        {
            return garment.BotTypes.Contains(botType, StringComparer.OrdinalIgnoreCase);
        }

        // No origin means we cannot tell. Excluded rather than included, and reported by name elsewhere - guessing
        // "yes" here is how modern military kit ended up on scavs in the first place.
        return !string.IsNullOrWhiteSpace(garment.VanillaOrigin)
               && vanillaPrefabPaths.Contains(garment.VanillaOrigin.Trim());
    }

    /// <summary>
    /// The vanilla prefab paths behind an appearance pool, resolved through the customization table.
    /// </summary>
    private HashSet<string> VanillaPrefabPaths(Dictionary<MongoId, double> pool)
    {
        var paths = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        foreach (var customizationId in pool.Keys)
        {
            if (!_database!.Templates.Customization.TryGetValue(customizationId, out var entry))
            {
                continue;
            }

            var path = PrefabPathOf(entry.Properties?.Prefab);

            if (!string.IsNullOrWhiteSpace(path))
            {
                paths.Add(path);
            }
        }

        return paths;
    }

    /// <summary>
    /// Extracts a prefab path from <see cref="CustomizationProperties.Prefab"/>.
    /// </summary>
    /// <remarks>
    /// That property is typed <c>object?</c> because BSG's data has it as either an object with a `path` or a bare
    /// string. System.Text.Json therefore materialises it as a <see cref="JsonElement"/> rather than as the `Prefab`
    /// record, so pattern-matching on `Prefab` silently matches nothing and every appearance pool reads as empty -
    /// which is exactly how this failed the first time, with no error and every bot type reporting zero garments.
    ///
    /// The entries DRIP writes itself are real `Prefab` instances, since we construct them, so both shapes are live
    /// in the same dictionary.
    /// </remarks>
    private static string? PrefabPathOf(object? prefab)
    {
        switch (prefab)
        {
            case null:
                return null;

            case Prefab typed:
                return typed.Path;

            case string raw:
                return raw;

            case JsonElement { ValueKind: JsonValueKind.String } element:
                return element.GetString();

            case JsonElement { ValueKind: JsonValueKind.Object } element:
                return element.TryGetProperty("path", out var path) && path.ValueKind == JsonValueKind.String
                    ? path.GetString()
                    : null;

            default:
                return null;
        }
    }

    /// <summary>
    /// Names garments whose origin is unknown, so their absence from every bot is explained rather than mysterious.
    /// </summary>
    /// <remarks>
    /// Loud and by name, deliberately. Silently including them recreates the indiscriminate behaviour this
    /// derivation replaces; silently excluding them makes garments vanish from bots with no explanation. Both are
    /// the "looked fine from the inside" failure this project keeps hitting.
    /// </remarks>
    private void ReportGarmentsWithoutAnOrigin()
    {
        var unknown = _botBodies.Concat(_botFeet)
            .Where(garment => garment.BotTypes is null && string.IsNullOrWhiteSpace(garment.VanillaOrigin))
            .Select(garment => garment.Stem)
            .ToList();

        if (unknown.Count == 0)
        {
            return;
        }

        const int NamesToShow = 5;
        var named = string.Join(", ", unknown.Take(NamesToShow));
        var andMore = unknown.Count > NamesToShow ? $", and {unknown.Count - NamesToShow} more" : string.Empty;

        logger.Error(
            $"[DRIP] {unknown.Count} garments have no 'vanillaOrigin', so DRIP cannot tell which bots should wear " +
            $"them and no bot will: {named}{andMore}. Re-run the converter, or set 'botTypes' on them explicitly.");
    }

    /// <summary>
    /// Resolves the debug appearance pins, if any are configured.
    /// </summary>
    /// <remarks>
    /// Resolution happens here rather than when the config is read, because the garments a pin can name are
    /// registered *during* load - a name that looks invalid at boot may be perfectly valid ten seconds later.
    ///
    /// A pin that names something unknown refuses the entire pin rather than skipping the bad half. A half-applied
    /// fixture is worse than no fixture: it has a name, it looks deliberate, and whoever reads the raid afterwards
    /// has no way to know only part of it took.
    /// </remarks>
    /// <returns>The pinned top and bottom, and whether the pin was refused outright.</returns>
    private (BotGarment? Top, BotGarment? Bottom, bool Refused) ResolvePins()
    {
        var topStem = _config?.DebugPinBotTop;
        var bottomStem = _config?.DebugPinBotBottom;

        if (string.IsNullOrWhiteSpace(topStem) && string.IsNullOrWhiteSpace(bottomStem))
        {
            return (null, null, false);
        }

        var top = Resolve(topStem, _botTopsForPinning, "top", out var topFailed);
        var bottom = Resolve(bottomStem, _botFeetForPinning, "bottom", out var bottomFailed);

        if (topFailed || bottomFailed)
        {
            logger.Error(
                "[DRIP] Bot appearance pin REFUSED - nothing was pinned and no bot appearance was changed at all. " +
                "Fix the name in config/config.jsonc, or clear it to go back to normal bot clothing.");

            return (null, null, true);
        }

        return (top, bottom, false);
    }

    private List<BotGarment> _botTopsForPinning => _botBodies;

    private List<BotGarment> _botFeetForPinning => _botFeet;

    private BotGarment? Resolve(string? stem, List<BotGarment> candidates, string what, out bool failed)
    {
        failed = false;

        if (string.IsNullOrWhiteSpace(stem))
        {
            return null;
        }

        var match = candidates.FirstOrDefault(garment =>
            string.Equals(garment.Stem, stem.Trim(), StringComparison.OrdinalIgnoreCase));

        if (match is null)
        {
            var examples = string.Join(", ", candidates.Take(3).Select(garment => garment.Stem));
            logger.Error(
                $"[DRIP] Bot appearance pin names the {what} \"{stem}\", which isn't a {what} DRIP loaded. " +
                $"Names are config filenames without the extension, for example: {examples}.");

            failed = true;
            return null;
        }

        // Confirm it genuinely landed in the database, rather than trusting that we recorded it.
        if (_database is null || !_database.Templates.Customization.ContainsKey(match.Id))
        {
            logger.Error(
                $"[DRIP] Bot appearance pin names the {what} \"{stem}\", which was loaded but isn't in the " +
                "customization table, so it cannot be worn.");

            failed = true;
            return null;
        }

        return match;
    }

    private void AddSuiteLocale(ContentItemConfig config, MongoId suiteId)
    {
        if (_database is null)
        {
            return;
        }

        foreach (var (localeCode, lazyLocale) in _database.Locales.Global)
        {
            // Captured per locale so the transformer doesn't close over the loop variable.
            var code = localeCode;

            lazyLocale.AddTransformer(localeData =>
            {
                var translated = config.Translations?.GetValueOrDefault(code);
                localeData[$"{suiteId} Name"] = translated?.Name ?? config.Name ?? string.Empty;

                return localeData;
            });
        }
    }
}
