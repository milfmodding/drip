using System.Reflection;
using System.Text.Json;
using System.Text.Json.Nodes;
using DRIP.Models;
using DRIP.Utils;
using SPTarkov.DI.Annotations;
using SPTarkov.Server.Core.Models.Common;
using SPTarkov.Server.Core.Models.Eft.Common.Tables;
using SPTarkov.Common.Models.Logging;
using SPTarkov.Server.Core.Models.Spt.Tables;
using SPTarkov.Server.Core.Routers;
using SPTarkov.Server.Core.Utils;
using Path = System.IO.Path;

namespace DRIP.Services;

/// <summary>
/// Loads DRIP's quests and their icons.
///
/// A quest config is an object keyed by quest id, matching the shape the game's own quest table uses, so the
/// converted files drop straight in. Quest text lives in the locale files rather than here - the fields on a quest
/// are locale <i>keys</i>, not the strings players read.
/// </summary>
[Injectable(InjectionType.Singleton)]
public class DRIPCustomQuestService(
    ISptLogger<DRIPCustomQuestService> logger,
    TemplateTable templateTable,
    DRIPBundleService bundleService,
    ImageRouter imageRouter,
    HashUtil hashUtil,
    DRIPQuestExpander questExpander,
    SPTarkov.Server.Core.Services.Modding.Custom.CustomQuestService customQuestService
)
{
    /// <summary>Where the client asks for quest icons.</summary>
    private const string QuestIconRoute = "/files/quest/icon";


    /// <summary>
    /// Loads quest configs and icons from one content pack.
    /// </summary>
    /// <param name="assembly">The calling assembly, used to determine the mod folder location</param>
    /// <param name="contentPackPath">
    /// Path to the content pack's CustomQuests directory, relative to the mod folder - already includes "bundles".
    /// </param>
    private readonly List<(string Directory, string ContentPackPath)> _pending = [];

    private readonly List<MongoId> _created = [];

    /// <summary>Quest ids DRIP added, for the verification pass.</summary>
    public IReadOnlyList<MongoId> Created => _created;

    /// <summary>
    /// Notes a content pack's quests to load once every pack's items exist. Quests reference items, and 3.x let them
    /// do so by filename, so resolving those references needs the item table already populated.
    /// </summary>
    public Task CreateCustomQuests(Assembly assembly, string contentPackPath)
    {
        _pending.Add((bundleService.GetModPaths(assembly).Resolve(contentPackPath), contentPackPath));

        return Task.CompletedTask;
    }

    /// <summary>
    /// Loads every recorded pack's quests. Call once, after all content packs have loaded.
    /// </summary>
    public void ApplyAll()
    {

        foreach (var (directory, contentPackPath) in _pending)
        {
            LoadQuestsFrom(directory, contentPackPath);
        }

        _pending.Clear();
    }

    private void LoadQuestsFrom(string finalDir, string contentPackPath)
    {

        var questsAdded = 0;
        var questsFailed = 0;
        var referencesRemapped = 0;

        foreach (var file in DripFiles.EnumerateConfigFiles(finalDir))
        {
            var relativeName = Path.GetRelativePath(finalDir, file).Replace("\\", "/");

            try
            {
                // Two quest formats share this directory while the corpus converts (design step 3):
                // the legacy keyed blob (quest id -> quest) and the friendly one-file-per-quest
                // format. A file that parses as the friendly shape routes to the expander; anything
                // else is legacy. The discriminator is structural - "objectives" exists only in
                // the friendly format - so a legacy blob cannot be mistaken for one.
                var stem = Path.GetFileNameWithoutExtension(file);
                var friendly = TryReadFriendlyQuest(file);

                if (friendly is not null)
                {
                    if (AddFriendlyQuest(friendly, stem, relativeName, ref referencesRemapped))
                    {
                        questsAdded++;
                    }
                    else
                    {
                        questsFailed++;
                    }

                    continue;
                }

                // Bound loosely first so that a friendly trader name can be resolved before the strongly-typed
                // Quest sees it - Quest.TraderId is a MongoId and would reject "moron" outright.
                //
                // Worth knowing that the strong bind is not a safety net here, only a convenience. It catches an
                // unresolved trader on `traderId` because that field is a MongoId; it does *not* catch one on a
                // reward, because Reward.Target is a plain string and an alias binds cleanly and crashes at quest
                // completion instead. See ResolveTraderReferences.
                var raw = DripJson.DeserializeFile<Dictionary<string, JsonElement>>(file);
                if (raw is null)
                {
                    logger.Error($"[DRIP] {relativeName}: file is empty or could not be read.");
                    continue;
                }

                foreach (var (questId, questElement) in raw)
                {
                    // Per quest, not per file: one unreadable quest should cost that quest, not the other eighteen
                    // in the same file.
                    try
                    {
                        if (AddQuest(questId, questElement, relativeName, ref referencesRemapped))
                        {
                            questsAdded++;
                        }
                        else
                        {
                            questsFailed++;
                        }
                    }
                    catch (Exception ex)
                    {
                        logger.Error($"[DRIP] {relativeName}: quest {questId} - {ex.Message}");
                        questsFailed++;
                    }
                }
            }
            catch (Exception ex)
            {
                logger.Error($"[DRIP] {relativeName}: {ex.Message}");
                questsFailed++;
            }
        }

        var iconsAdded = RegisterQuestIcons(finalDir);

        if (questsAdded == 0 && iconsAdded == 0)
        {
            return;
        }

        var summary = $"[DRIP] {contentPackPath}: {questsAdded} quests, {iconsAdded} icons";
        if (referencesRemapped > 0)
        {
            summary += $", {referencesRemapped} item references resolved by name";
        }

        if (questsFailed > 0)
        {
            logger.Error($"{summary}, {questsFailed} failed.");
        }
        else
        {
            logger.Info($"{summary}.");
        }
    }

    /// <summary>
    /// Reads a friendly-format quest file, or returns null when the file is not one. Detection is
    /// structural (an "objectives" member), so it is also the diagnostic for a broken file: a
    /// file that fails to bind to the friendly model while carrying objectives is reported,
    /// not silently routed to the legacy path that would misread it.
    /// </summary>
    private DRIPQuestFormat? TryReadFriendlyQuest(string file)
    {
        try
        {
            var probe = JsonNode.Parse(File.ReadAllText(file), documentOptions: new JsonDocumentOptions
            {
                AllowTrailingCommas = true,
                CommentHandling = JsonCommentHandling.Skip,
            });

            if (probe is not JsonObject obj || !obj.ContainsKey("objectives"))
            {
                return null;
            }

            return DripJson.DeserializeFile<DRIPQuestFormat>(file);
        }
        catch (JsonException)
        {
            // Unparseable JSON is the legacy path's to report (it logs line and column).
            return null;
        }
    }

    /// <summary>
    /// Expands and inserts one friendly-format quest through SPT's CreateQuest.
    ///
    /// Reference resolution happens on the friendly model BEFORE expansion, because the API
    /// validates nothing downstream (measured by disassembly: duplicate ids, empty locales,
    /// side - that is all CreateQuest checks). An unresolved trader on a reward is the exact
    /// georgia/moron crash class the legacy path guards against, so the same guard applies here:
    /// reject at load, naming the file, rather than let a quest that bricks the client on
    /// completion ship.
    /// </summary>
    private bool AddFriendlyQuest(
        DRIPQuestFormat format, string stem, string relativeName, ref int referencesRemapped)
    {
        var resolvedEverything = true;

        if (!DripTraders.TryResolve(format.Trader, out var traderId))
        {
            logger.Error(
                $"[DRIP] {relativeName}: trader \"{format.Trader}\" doesn't resolve. " +
                $"Known names: {string.Join(", ", DripTraders.KnownNames)}. Or use a trader's ID.");
            resolvedEverything = false;
        }
        else
        {
            format.Trader = traderId.ToString();
        }

        foreach (var reward in format.Rewards)
        {
            if (reward.StandingWith is not null)
            {
                if (!DripTraders.TryResolve(reward.StandingWith, out var standingWith))
                {
                    logger.Error(
                        $"[DRIP] {relativeName}: reward names trader \"{reward.StandingWith}\", which doesn't resolve.");
                    resolvedEverything = false;
                }
                else
                {
                    // Guard AND rewrite: the expander copies this value straight into the
                    // TraderStanding target, and CreateQuest validates nothing downstream.
                    reward.StandingWith = standingWith.ToString();
                }
            }

            if (reward.Unlock is not null)
            {
                if (!DripTraders.TryResolve(reward.Unlock, out var unlock))
                {
                    logger.Error(
                        $"[DRIP] {relativeName}: reward names trader \"{reward.Unlock}\", which doesn't resolve.");
                    resolvedEverything = false;
                }
                else
                {
                    reward.Unlock = unlock.ToString();
                }
            }
        }

        // Item references: pack filenames resolve through the same derivation as the legacy
        // path; vanilla ids pass through untouched.
        foreach (var objective in format.Objectives.Where(o => o.Handover is not null))
        {
            objective.Handover = ResolveItemReference(objective.Handover!, relativeName, ref referencesRemapped);
        }

        foreach (var reward in format.Rewards.Where(r => r.Item is not null))
        {
            reward.Item = ResolveItemReference(reward.Item!, relativeName, ref referencesRemapped);
        }

        if (!resolvedEverything)
        {
            return false;
        }

        var (quest, locales) = questExpander.Expand(format, stem, relativeName).GetAwaiter().GetResult();

        var result = customQuestService.CreateQuest(new SPTarkov.Server.Core.Models.Spt.Mod.NewQuestDetails
        {
            NewQuest = quest,
            Locales = locales,
        });

        if (result.Success != true)
        {
            var errors = result.Errors is { Count: > 0 } ? string.Join("; ", result.Errors) : "no reason given";
            logger.Error($"[DRIP] {relativeName}: CreateQuest rejected the quest - {errors}");
            return false;
        }

        _created.Add(new MongoId(quest.Id));

        return true;
    }

    /// <summary>
    /// A reference that is already a MongoId passes through; a pack filename resolves through
    /// the item-id derivation; anything else is left for later validation to name as unresolved.
    /// </summary>
    private string ResolveItemReference(string reference, string relativeName, ref int remapped)
    {
        if (MongoId.IsValidMongoId(reference))
        {
            return reference;
        }

        var derived = DripIds.Derive(hashUtil, reference).GetAwaiter().GetResult();
        if (templateTable.Items.ContainsKey(derived))
        {
            remapped++;
            return derived.ToString();
        }

        // Not a resolvable pack item. If it looks like a filename it is a broken cross-pack
        // reference - say so now rather than letting it fail as an opaque bind error later.
        if (reference.Contains('_') && reference.All(c => char.IsAsciiLetterOrDigit(c) || c == '_')
            && !reference.Any(char.IsLower))
        {
            logger.Error(
                $"[DRIP] {relativeName}: item \"{reference}\" looks like a pack item but no installed pack " +
                "provides it. Either the item belongs in this pack, or the quest belongs in the pack " +
                "that ships the item.");
        }

        return reference;
    }

    private bool AddQuest(string questId, JsonElement questElement, string relativeName, ref int referencesRemapped)
    {
        if (!MongoId.IsValidMongoId(questId))
        {
            logger.Error(
                $"[DRIP] {relativeName}: quest key \"{questId}\" isn't a 24-character ID. " +
                "Quest keys are the quest's own ID.");
            return false;
        }

        var resolved = ResolveTraderReferences(questElement, relativeName, questId);
        if (resolved is null)
        {
            return false;
        }

        resolved = ResolveItemNameReferences(resolved.Value, ref referencesRemapped);

        var unresolved = FindUnresolvedItemNames(resolved.Value);
        if (unresolved.Count > 0)
        {
            logger.Error(
                $"[DRIP] {relativeName}: quest {questId} needs {string.Join(", ", unresolved)}, which no content " +
                "pack installed here provides. Either the item belongs in this pack, or the quest belongs in the " +
                "pack that ships the item.");
            return false;
        }

        var quest = DripJson.BindToSptType<Quest>(resolved.Value);
        if (quest is null)
        {
            logger.Error($"[DRIP] {relativeName}: quest {questId} could not be read.");
            return false;
        }

        MongoId id = questId;

        if (templateTable.Quests.ContainsKey(id))
        {
            logger.Error(
                $"[DRIP] {relativeName}: quest {questId} already exists - another quest has claimed that ID.");
            return false;
        }

        templateTable.Quests[id] = quest;
        _created.Add(id);

        return true;
    }

    /// <summary>
    /// Rewrites friendly trader names such as "moron" into real MongoIds, so quests can be authored with the same
    /// trader names as everything else rather than with an ID nobody can verify by eye.
    /// </summary>
    /// <remarks>
    /// Trader ids appear in a quest in two places, and for a while this only handled the first.
    ///
    /// A quest's own `traderId` is the obvious one. The other is on rewards: 19 of Part 1's rewards name a trader,
    /// and every one kept the literal alias. Nothing complained at load - Reward.Target is a plain string on SPT's
    /// model, so "georgia" binds perfectly happily - and the failure surfaced only when a player hit *complete*, as
    /// an unhandled `ObjectId must be a 24-character hex string (Parameter 'georgia')` inside
    /// /client/game/profile/items/moving. That is a 500 on an item-event route, so the client desynced entirely
    /// rather than failing the one quest: trader tabs stopped responding and exiting to menu did not clear it.
    ///
    /// Hence the shape of this method. An alias that does not resolve rejects the quest *here*, with a message naming
    /// the file, the quest and the field, because a quest that loads and then bricks the client on completion is
    /// strictly worse than a quest that never loads.
    /// </remarks>
    private JsonElement? ResolveTraderReferences(JsonElement questElement, string relativeName, string questId)
    {
        if (JsonNode.Parse(questElement.GetRawText()) is not JsonObject quest)
        {
            // Not an object at all - let the strongly-typed bind report whatever is actually wrong with it.
            return questElement;
        }

        // Deliberately not short-circuiting on the first failure: an author who wrote "georgai" once probably wrote
        // it several times, and one error per run of the server is a slow way to find that out.
        var resolvedEverything = TryResolveField(quest, "traderId", "the quest's own trader", relativeName, questId);

        if (quest["rewards"] is JsonObject rewards)
        {
            // Every bucket, not just Success. Fail rewards are ordinary - vanilla docks standing on failure - and a
            // check that only looked at Success would leave the same crash waiting behind a failed quest.
            foreach (var (bucket, bucketRewards) in rewards)
            {
                if (bucketRewards is not JsonArray rewardList)
                {
                    continue;
                }

                foreach (var reward in rewardList.OfType<JsonObject>())
                {
                    if (reward["type"] is not JsonValue typeValue ||
                        !typeValue.TryGetValue<string>(out var rewardType) ||
                        !DripTraders.TryGetTraderField(rewardType, out var field))
                    {
                        continue;
                    }

                    resolvedEverything &= TryResolveField(
                        reward, field, $"a {rewardType} reward in {bucket}", relativeName, questId);
                }
            }
        }

        return resolvedEverything ? JsonSerializer.SerializeToElement(quest) : null;
    }

    /// <summary>
    /// Resolves one trader-name field in place. Absent or non-string fields are left alone; a present string that
    /// does not name a trader is an error.
    /// </summary>
    private bool TryResolveField(JsonObject owner, string field, string where, string relativeName, string questId)
    {
        if (owner[field] is not JsonValue value || !value.TryGetValue<string>(out var traderName))
        {
            // Missing, null, or not a string. Not our problem to diagnose - the strongly-typed bind reports it.
            return true;
        }

        if (!DripTraders.TryResolve(traderName, out var traderId))
        {
            logger.Error(
                $"[DRIP] {relativeName}: quest {questId} names trader \"{traderName}\" on {where}, which doesn't " +
                $"resolve. Known names: {string.Join(", ", DripTraders.KnownNames)}. Or use a trader's ID.");
            return false;
        }

        // Writing back unconditionally, including when the value was already a real id. The node is a copy, so this
        // costs nothing, and a conditional here is a branch that only ever runs on the path nobody tests.
        owner[field] = traderId.ToString();

        return true;
    }

    /// <summary>
    /// Rewrites item references written as filenames into the ids those filenames now produce.
    /// </summary>
    /// <remarks>
    /// Under 3.x an item's id *was* its config filename, so quests referenced DRIP items directly by name -
    /// `"target": ["COMTAC4_BLACK_HEADSET"]`. Under schema v2 the id is derived from the filename instead, so those
    /// references point at nothing. 13 of them exist across Part 1's quests, in objective targets and rewards.
    ///
    /// A candidate is only rewritten when the id its name derives to is genuinely in the item table. That makes the
    /// check self-validating: ordinary strings like "HandoverItem" or "Pmc" derive to ids that own nothing and are
    /// left untouched, so there is no need to guess which fields are item references and which are not.
    /// </remarks>
    private JsonElement? ResolveItemNameReferences(JsonElement element, ref int remapped)
    {
        switch (element.ValueKind)
        {
            case JsonValueKind.String:
            {
                var value = element.GetString();
                if (string.IsNullOrEmpty(value) || MongoId.IsValidMongoId(value))
                {
                    return element;
                }

                var derived = DripIds.Derive(hashUtil, value).GetAwaiter().GetResult();
                if (!templateTable.Items.ContainsKey(derived))
                {
                    return element;
                }

                remapped++;

                return JsonSerializer.SerializeToElement(derived.ToString());
            }

            case JsonValueKind.Array:
            {
                var items = new List<JsonElement>();
                foreach (var child in element.EnumerateArray())
                {
                    items.Add(ResolveItemNameReferences(child, ref remapped) ?? child);
                }

                return JsonSerializer.SerializeToElement(items);
            }

            case JsonValueKind.Object:
            {
                var properties = new Dictionary<string, JsonElement>();
                foreach (var property in element.EnumerateObject())
                {
                    properties[property.Name] = ResolveItemNameReferences(property.Value, ref remapped) ?? property.Value;
                }

                return JsonSerializer.SerializeToElement(properties);
            }

            default:
                return element;
        }
    }

    /// <summary>
    /// Finds item references that look like DRIP config filenames but resolve to nothing installed.
    /// </summary>
    /// <remarks>
    /// Purely to produce a useful message. Left alone, these reach the strongly-typed bind and surface as
    /// "ObjectId must be a 24-character hex string (Parameter 'SLING_OLIVEDRAB_BAG')", which is true, unhelpful, and
    /// says nothing about the actual problem - that a quest in one content pack needs an item from another.
    ///
    /// The shape test (SCREAMING_SNAKE_CASE) is a heuristic, but it is only ever used to decide how to word an
    /// error, never to change what loads.
    /// </remarks>
    private static List<string> FindUnresolvedItemNames(JsonElement element)
    {
        var found = new List<string>();
        Collect(element, found);

        return found.Distinct().ToList();

        static void Collect(JsonElement node, List<string> into)
        {
            switch (node.ValueKind)
            {
                case JsonValueKind.String:
                {
                    var value = node.GetString();
                    if (!string.IsNullOrEmpty(value) && LooksLikeAContentFilename(value))
                    {
                        into.Add(value);
                    }

                    break;
                }

                case JsonValueKind.Array:
                    foreach (var child in node.EnumerateArray())
                    {
                        Collect(child, into);
                    }

                    break;

                case JsonValueKind.Object:
                    foreach (var property in node.EnumerateObject())
                    {
                        Collect(property.Value, into);
                    }

                    break;
            }
        }
    }

    /// <summary>SCREAMING_SNAKE_CASE with at least one underscore - the shape every DRIP config filename has.</summary>
    private static bool LooksLikeAContentFilename(string value)
    {
        return value.Contains('_')
               && value.All(character => char.IsAsciiLetterOrDigit(character) || character == '_')
               && !value.Any(char.IsLower);
    }

    /// <summary>
    /// Serves the .png files sitting alongside the quest configs.
    /// </summary>
    /// <remarks>
    /// The route is registered without the file extension because the server strips it from the incoming request
    /// before matching - a quest that declares "icon/Boozey.png" resolves against a route of "icon/Boozey".
    /// </remarks>
    private int RegisterQuestIcons(string directory)
    {
        if (!Directory.Exists(directory))
        {
            return 0;
        }

        var added = 0;

        foreach (var image in Directory.EnumerateFiles(directory, "*.png", SearchOption.AllDirectories))
        {
            var iconName = Path.GetFileNameWithoutExtension(image);
            imageRouter.AddRoute($"{QuestIconRoute}/{iconName}", image);
            added++;
        }

        return added;
    }
}
