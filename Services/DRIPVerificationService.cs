using System.Diagnostics;
using System.Reflection;
using DRIP.Utils;
using SPTarkov.DI.Annotations;
using SPTarkov.Server.Core.DI;
using SPTarkov.Server.Core.Models.Common;
using SPTarkov.Server.Core.Models.Eft.Common;
using SPTarkov.Server.Core.Models.Eft.Common.Tables;
using SPTarkov.Common.Models.Logging;
using SPTarkov.Server.Core.Models.Spt.Tables;

namespace DRIP.Services;

/// <summary>
/// Checks, after everything has loaded, that the database DRIP built is actually coherent.
///
/// Every assertion here corresponds to a bug that reached us once. The point is not to find those bugs again - they
/// are fixed - but to make their recurrence impossible rather than merely unlikely, particularly when Parts 2 and 3
/// land and nobody remembers why any of this mattered.
///
/// It runs on every load rather than behind a switch. A check that only runs when someone remembers to ask is a
/// check that does not run.
/// </summary>
[Injectable(InjectionType.Singleton)]
public class DRIPVerificationService(
    ISptLogger<DRIPVerificationService> logger,
    TemplateTable templateTable,
    TradersTable tradersTable,
    GlobalTable globalTable,
    LocaleTable localeTable,
    DRIPCustomItemService itemService,
    DRIPCustomQuestService questService,
    DRIPTraderAssortService assortService,
    DRIPBundleService bundleService
)
{
    /// <summary>How many offending items to name before summarising the rest.</summary>
    private const int NamesToShow = 5;


    public void VerifyAll()
    {
        if (itemService.Created.Count == 0)
        {
            return;
        }



        var stopwatch = Stopwatch.StartNew();
        var problems = new List<string>();

        // Each check is isolated, because a bug in a *check* must never be worse than the bug it looks for.
        // Learned the hard way: an unguarded `new MongoId(...)` in the quest-gate check threw on the very input it
        // existed to catch, and took the whole server down with it - a diagnostic that killed the thing it was
        // diagnosing. Nothing here is worth a failed startup.
        Run(nameof(VerifyEveryItemIsSoldSomewhere), () => VerifyEveryItemIsSoldSomewhere(problems), problems);
        Run(nameof(VerifyNoItemWearsItsBaseItemsModel), () => VerifyNoItemWearsItsBaseItemsModel(problems), problems);
        Run(nameof(VerifySuitsHaveDistinctOfferAndSuiteIds), () => VerifySuitsHaveDistinctOfferAndSuiteIds(problems), problems);
        Run(nameof(VerifyQuestItemReferencesResolve), () => VerifyQuestItemReferencesResolve(problems), problems);
        Run(nameof(VerifyQuestTraderReferencesResolve), () => VerifyQuestTraderReferencesResolve(problems), problems);
        Run(nameof(VerifyArmourHasAFleaPreset), () => VerifyArmourHasAFleaPreset(problems), problems);
        Run(nameof(VerifyTraderOffersCanBeEquipped), () => VerifyTraderOffersCanBeEquipped(problems), problems);
        Run(nameof(VerifySiblingBundlesAreDeclared), () => VerifySiblingBundlesAreDeclared(problems), problems);
        Run(nameof(VerifyEveryItemHasAHandbookPrice), () => VerifyEveryItemHasAHandbookPrice(problems), problems);
        Run(nameof(VerifyNoDuplicateIds), () => VerifyNoDuplicateIds(problems), problems);
        Run(nameof(VerifyEveryItemHasAName), () => VerifyEveryItemHasAName(problems), problems);
        Run(nameof(VerifyNoTwoItemsShareOneModel), () => VerifyNoTwoItemsShareOneModel(problems), problems);
        Run(nameof(VerifySuitQuestGatesResolve), () => VerifySuitQuestGatesResolve(problems), problems);
        Run(nameof(VerifyWeLoadBeforeProfileValidation), () => VerifyWeLoadBeforeProfileValidation(problems), problems);

        stopwatch.Stop();

        if (problems.Count == 0)
        {
            logger.Info($"[DRIP] Self-check passed ({stopwatch.ElapsedMilliseconds}ms).");
            return;
        }

        logger.Error($"[DRIP] Self-check found {problems.Count} problem(s):");
        foreach (var problem in problems)
        {
            logger.Error($"[DRIP]   {problem}");
        }
    }

    /// <summary>
    /// Caught: every profile owning DRIP content was marked invalid on the next start, because DRIP registered its
    /// templates at PostSptModLoader - 400,000 priority units *after* SaveCallbacks runs profile validation.
    ///
    /// This is the one check here that cannot prevent the bug it looks for. If the order is wrong, validation has
    /// already run and already condemned the profile by the time this executes. What it does is put the cause in the
    /// same log as the effect: `InvalidModdedClothingException` names an id and nothing else, and working back from
    /// that id to a load-order constant cost real hours. Reading our own attribute is the only way to check this -
    /// there is no hook that reports what priority we were actually given.
    /// </summary>
    private void VerifyWeLoadBeforeProfileValidation(List<string> problems)
    {
        var injectable = typeof(global::DRIP.DRIP)
            .GetCustomAttributesData()
            .FirstOrDefault(attribute => attribute.AttributeType.Name.StartsWith("Injectable"));

        var priority = injectable?.NamedArguments
            .Where(argument => argument.MemberName == "TypePriority")
            .Select(argument => (long?)Convert.ToInt64(argument.TypedValue.Value))
            .FirstOrDefault();

        if (priority is null)
        {
            problems.Add(
                "could not read DRIP's own load priority, so it is unknown whether the database is populated before " +
                "SPT validates profiles. If the [Injectable] attribute on the DRIP class was renamed or its " +
                "TypePriority removed, restore it - see the comment there.");
            return;
        }

        if (priority >= OnLoadOrder.SaveCallbacks)
        {
            problems.Add(
                $"DRIP loads at priority {priority:N0}, which is at or after SaveCallbacks " +
                $"({OnLoadOrder.SaveCallbacks:N0}) where SPT validates every profile against the item database. " +
                "Any profile owning DRIP items or clothing will have been marked invalid on this start, and the " +
                "remedy SPT suggests for that error deletes the player's DRIP gear. Move the [Injectable] " +
                $"TypePriority on the DRIP class back into the pre-SaveCallbacks window (see " +
                "docs/SPT-4.1-MIGRATION.md) - see the comment there for why.");
            return;
        }

        // Passing the check above does NOT mean the load order is "correct" - it means the profile half is safe.
        // There are three consumers and no single slot satisfies all of them, so state where we actually sit rather
        // than let a green assertion imply more than it checked. Being before TraderCallbacks is a deliberate trade:
        // Fence's assort is generated there, so DRIP cannot mirror Fence's offers, and that is the accepted cost of
        // profiles that survive a restart. See the comment on the DRIP class.
        // Each stage is described by what the relationship *means*, not by which side of it we are on. Being before
        // TraderCallbacks is good for one reason and bad for another, and a reader deserves both halves.
        var profiles = priority < OnLoadOrder.SaveCallbacks
            ? "validated against our templates (good)"
            : "ALREADY RAN - profiles owning DRIP content are invalid";
        var traders = priority < OnLoadOrder.TraderCallbacks
            ? "runs after us, so our traders get resupply timestamps, but Fence's assort is generated there and so " +
              "is invisible to us - copyOriginalOffers cannot mirror Fence"
            : "already ran, so Fence's assort is visible to us, but our own traders missed resupply and price setup";
        var flea = priority < OnLoadOrder.RagfairCallbacks
            ? "generated after us, so our items get static prices (good)"
            : "already generated, so our items have no static flea price";

        logger.Info($"[DRIP] Load order {priority:N0}. Profile validation ({OnLoadOrder.SaveCallbacks:N0}): {profiles}. " +
                    $"Trader init ({OnLoadOrder.TraderCallbacks:N0}): {traders}. " +
                    $"Flea static prices ({OnLoadOrder.RagfairCallbacks:N0}): {flea}.");
    }

    /// <summary>
    /// Runs one check, converting a crash in it into a reported problem rather than a dead server.
    /// </summary>
    private void Run(string name, Action check, List<string> problems)
    {
        try
        {
            check();
        }
        catch (Exception ex)
        {
            problems.Add($"the '{name}' check itself failed and could not run: {ex.Message}");
        }
    }

    /// <summary>
    /// Caught: traders logging `no assort found` because nothing put items on sale.
    /// </summary>
    private void VerifyEveryItemIsSoldSomewhere(List<string> problems)
    {
        var soldTemplates = tradersTable.Values
            .Where(trader => trader.Assort?.Items is not null)
            .SelectMany(trader => trader.Assort!.Items)
            .Select(item => item.Template)
            .ToHashSet();

        var unsold = itemService.Created
            .Where(item => !soldTemplates.Contains(item.Id))
            .Select(item => item.RelativeName)
            .ToList();

        if (unsold.Count == 0)
        {
            return;
        }

        // Split by reason. An item declined because every original offer is quest-locked is the loader working, and
        // reporting correct behaviour as a problem is how an assertion becomes one nobody reads - the failure mode
        // this whole class exists to avoid. So gated items are stated, not counted against us.
        //
        // Detection stays database-derived above; this only *explains* what was found. An item that is unsold and has
        // no recorded reason is the interesting case and stays a problem, because it means something failed silently
        // somewhere other than the copy path.
        var gated = assortService.Unsold.Where(item => item.GatedByQuest).Select(item => item.RelativeName).ToHashSet();

        var actionable = unsold.Where(name => !gated.Contains(name)).ToList();
        var declined = unsold.Where(gated.Contains).ToList();

        if (declined.Count > 0)
        {
            logger.Info(
                $"[DRIP] {declined.Count} item(s) are not sold by any trader because every offer of the original is " +
                "quest-locked. This is deliberate: copying one would make quest-gated gear freely available. They " +
                "remain lootable and wearable by bots. " + Describe(declined, "gated"));
        }

        if (actionable.Count > 0)
        {
            problems.Add(Describe(actionable, "no trader sells"));
        }
    }

    /// <summary>
    /// Caught: items created without a model bundle, which silently kept the cloned item's model and shipped as
    /// visual duplicates of the vanilla item they retexture. Nothing errored; they simply looked wrong.
    /// </summary>
    private void VerifyNoItemWearsItsBaseItemsModel(List<string> problems)
    {
        var wearingVanilla = new List<string>();

        foreach (var created in itemService.Created)
        {
            if (!templateTable.Items.TryGetValue(created.Id, out var item) ||
                !templateTable.Items.TryGetValue(created.BaseTpl, out var baseItem))
            {
                continue;
            }

            var path = item.Properties?.Prefab?.Path;
            var basePath = baseItem.Properties?.Prefab?.Path;

            if (!string.IsNullOrEmpty(path) && path == basePath)
            {
                wearingVanilla.Add(created.RelativeName);
            }
        }

        if (wearingVanilla.Count > 0)
        {
            problems.Add(Describe(wearingVanilla, "uses the same model as the item it retextures, so it will look vanilla in game -"));
        }
    }

    /// <summary>
    /// Caught: giving a suit the same id for the trader's offer and the customization record. It loaded perfectly;
    /// vanilla uses distinct ids for all 109 of Ragman's suits.
    /// </summary>
    private void VerifySuitsHaveDistinctOfferAndSuiteIds(List<string> problems)
    {
        var collisions = new List<string>();

        foreach (var traderId in new[] { DripTraders.Moron, DripTraders.Georgia })
        {
            if (!tradersTable.TryGetValue(traderId, out var trader) || trader.Suits is null)
            {
                continue;
            }

            collisions.AddRange(trader.Suits
                .Where(suit => suit.Id == suit.SuiteId)
                .Select(suit => suit.Id.ToString()));
        }

        if (collisions.Count > 0)
        {
            problems.Add(Describe(collisions, "has one id doing two jobs (offer and suite) -"));
        }
    }

    /// <summary>
    /// Caught: a Part 1 quest requiring an item that only ships in Part 3.
    /// </summary>
    private void VerifyQuestItemReferencesResolve(List<string> problems)
    {
        var dangling = new List<string>();

        foreach (var questId in questService.Created)
        {
            if (!templateTable.Quests.TryGetValue(questId, out var quest))
            {
                continue;
            }

            foreach (var target in ItemTargetsOf(quest))
            {
                if (!templateTable.Items.ContainsKey(target))
                {
                    dangling.Add($"{quest.QuestName ?? questId.ToString()} -> {target}");
                }
            }
        }

        if (dangling.Count > 0)
        {
            problems.Add(Describe(dangling, "needs an item that isn't installed -"));
        }
    }

    /// <summary>
    /// Caught: 19 quest rewards naming a trader by its friendly alias, because the loader only ever rewrote the
    /// quest's own `traderId`. No DRIP quest could be completed.
    /// </summary>
    /// <remarks>
    /// This one earns its place more than most, because nothing else can see it. Reward.Target is a plain string on
    /// SPT's model, so "georgia" binds cleanly, loads cleanly, and sits in the database looking correct until a
    /// player presses *complete* - at which point RewardHelper casts it to a MongoId and throws inside
    /// /client/game/profile/items/moving. A 500 on an item-event route desyncs the whole client, so the symptom is
    /// "trader tabs stopped working", several screens away from the cause.
    ///
    /// So this deliberately re-derives from the built database rather than trusting that the loader's rewrite ran.
    /// The loader rejects a quest whose alias will not resolve; this asserts the surviving quests actually point at
    /// traders that exist, which additionally catches the case the loader cannot see - a syntactically valid id for a
    /// trader nobody installed.
    /// </remarks>
    private void VerifyQuestTraderReferencesResolve(List<string> problems)
    {
        var dangling = new List<string>();

        foreach (var questId in questService.Created)
        {
            if (!templateTable.Quests.TryGetValue(questId, out var quest))
            {
                continue;
            }

            var name = quest.QuestName ?? questId.ToString();

            // The quest's own trader. A MongoId on the model, so it cannot be malformed by the time it gets here -
            // only pointed at a trader that does not exist.
            if (!tradersTable.ContainsKey(quest.TraderId))
            {
                dangling.Add($"{name} is sold by {quest.TraderId}, which isn't a trader here");
            }

            foreach (var (bucket, rewards) in quest.Rewards ?? [])
            {
                foreach (var reward in rewards ?? [])
                {
                    var reference = TraderReferenceOf(reward);
                    if (reference is null)
                    {
                        continue;
                    }

                    // Validate before constructing, for the same reason VerifySuitQuestGatesResolve does: MongoId's
                    // constructor throws on anything that isn't 24 hex characters, and an unresolved alias is
                    // precisely what this check exists to find.
                    if (!MongoId.IsValidMongoId(reference))
                    {
                        dangling.Add($"{name} rewards {reward.Type} in {bucket} to \"{reference}\" (not an ID at all)");
                        continue;
                    }

                    if (!tradersTable.ContainsKey(new MongoId(reference)))
                    {
                        dangling.Add($"{name} rewards {reward.Type} in {bucket} to {reference}, which isn't a trader here");
                    }
                }
            }
        }

        if (dangling.Count > 0)
        {
            problems.Add(Describe(dangling,
                "quest trader references don't resolve, which crashes the client on quest completion rather than " +
                "failing here -"));
        }
    }

    /// <summary>
    /// Caught: DRIP armour bought from the flea arriving with empty required slots, unequippable, while the same
    /// item bought from a trader arrived fully fitted.
    /// </summary>
    /// <remarks>
    /// Worth stating what this does and does not prove, because the honest scope is narrow. It asserts that every
    /// DRIP item whose base has a default preset has one of its own, and that the preset's root names the DRIP item
    /// rather than the item it was cloned from - the second being the failure that would be worse than the bug,
    /// since a preset registered against the wrong template sells the wrong armour rather than none.
    ///
    /// It does not prove the offer is wearable in game. SPT gates equipment presets on
    /// ItemHelper.ArmorItemCanHoldMods, and whether the flea then fills the slots is client-side. That half is smoke
    /// test material, not something the server can answer.
    /// </remarks>
    private void VerifyArmourHasAFleaPreset(List<string> problems)
    {
        var presets = globalTable.ItemPresets;
        if (presets is null)
        {
            problems.Add("globals has no ItemPresets table, so nothing sold on the flea can carry its plates.");
            return;
        }

        // Re-derived from the database rather than from the preset service's own record of what it created, so this
        // measures the built result rather than our bookkeeping about it.
        var presetByTpl = new Dictionary<MongoId, Preset>();
        foreach (var preset in presets.Values)
        {
            if (preset.Encyclopedia is { } encyclopedia)
            {
                presetByTpl.TryAdd(encyclopedia, preset);
            }
        }

        var missing = new List<string>();
        var mistargeted = new List<string>();

        foreach (var item in itemService.Created)
        {
            if (!presetByTpl.ContainsKey(item.BaseTpl))
            {
                // The base has no default preset either, so vanilla sells it bare on the flea too. Not our bug.
                continue;
            }

            if (!presetByTpl.TryGetValue(item.Id, out var ours))
            {
                missing.Add(item.RelativeName);
                continue;
            }

            var root = ours.Items?.FirstOrDefault();
            if (root is null || root.Template != item.Id)
            {
                mistargeted.Add($"{item.RelativeName} -> {root?.Template.ToString() ?? "no root item"}");
            }
        }

        if (missing.Count > 0)
        {
            problems.Add(Describe(missing,
                "have a base with a default preset but none of their own, so buying them from the flea gives an " +
                "empty shell that cannot be equipped -"));
        }

        if (mistargeted.Count > 0)
        {
            problems.Add(Describe(mistargeted,
                "have a preset whose root is not the item itself, so the flea would sell the wrong armour -"));
        }
    }

    /// <summary>
    /// A content directory shipping several bundles with no dependency declared between them.
    /// </summary>
    /// <remarks>
    /// The detection is <see cref="DRIPBundleService.Undeclared"/>, recorded during registration where the config's
    /// `bundles` block is actually in hand. This only decides how it is said, and the wording is Sophia's decision
    /// and Echo's refinement rather than mine:
    ///
    ///   * **Not fatal, but eye-catching.** Sophia's call - she wanted something she can point Colette and Amber at
    ///     ("look at the server logs") without it stopping anyone's game. She was ambivalent because it can bite an
    ///     ordinary player, and decided for it because it makes the right thing the easiest thing for the people
    ///     authoring content. So it goes in the self-check block, which is prominent and does not halt.
    ///   * **It names the line to add.** A message that only states the problem becomes something they screenshot
    ///     and send her, which is the outcome she is trying to avoid.
    ///   * **Two clauses, not one.** Echo's, and it is the difference between a message that helps and one that
    ///     misleads: "declare it" is the whole fix for a half-mask and did nothing for the two helmets until an
    ///     externals entry inside the bundle was repointed. So the second clause asks the question instead -
    ///     *if nothing reads from the other bundle, why does it ship?* - which is what would have caught the helmets
    ///     honestly.
    /// </remarks>
    private void VerifySiblingBundlesAreDeclared(List<string> problems)
    {
        var undeclared = bundleService.Undeclared;
        if (undeclared.Count == 0)
        {
            return;
        }

        var example = undeclared.First();
        var siblings = string.Join(", ", example.SiblingKeys.Select(key => $"\"{key}\""));

        var opening = undeclared.Count == 1
            ? $"{example.Directory} ships more than one bundle but declares no dependency between them"
            : $"{undeclared.Count} content folders ship more than one bundle but declare no dependency between them";

        // The example line is built from the keys actually registered for that folder, so it can be pasted rather
        // than adapted. Naming the line is Sophia's condition: a message that only states the problem becomes a
        // screenshot sent to her, which is the thing it exists to prevent.
        var line = $"\"bundles\": {{ \"{example.PrimaryBundle}\": [ {siblings} ] }}";

        var alsoAffected = undeclared.Count > 1
            ? " " + Describe(undeclared.Select(entry => entry.Directory).ToList(), "folders affected:")
            : string.Empty;

        problems.Add(
            $"{opening}, so the game is never told to " +
            "load the second one. If one bundle reads from another - a model whose material or texture lives in a " +
            "sibling - the item renders wrong with nothing in the log. Add this to the config" +
            $"{(undeclared.Count > 1 ? $" (example, for {example.Directory})" : string.Empty)}:  {line}  - and if " +
            $"nothing reads from the other bundle, ask why it ships at all.{alsoAffected}");
    }

    /// <summary>
    /// An item a trader sells that arrives with a required slot empty, so it is buyable and cannot be equipped.
    /// </summary>
    /// <remarks>
    /// Echo and Sophia's, and it is the one check here written *before* the bug rather than after it.
    ///
    /// A trader offer gets its children one of two ways: copyOriginalOffers brings them with the copied offer, or
    /// `includedParts` fits them explicitly. Nothing else does. So an item given its own price, whose base has
    /// required slots and which declares no includedParts, ships a bare shell - it appears in the trader's list, it
    /// costs money, and it will not go on. Nothing errors.
    ///
    /// Today it flags nothing. **That is its success condition, not evidence it is dead weight** - do not delete it
    /// for being quiet. Where it earns its place is the 13-item reprice worklist in CONTENT-ISSUES: those items are
    /// on that list precisely because no reachable trader sells the original, so an own price is their only route,
    /// and **12 of the 13 have required slots and no includedParts.** If prices are set and nothing else, twelve
    /// items become unwearable in one edit. Verified 2026-07-31 against the server's own worklist; the 13th
    /// (HELMET_TKHEAVYTROOPER_BLACK) has no required slots and is safe to reprice alone.
    ///
    /// Deliberately derived from the built assort rather than from the configs. The config version answers "did the
    /// author write includedParts"; this answers "does the thing on sale have its parts", which is the question, and
    /// it catches a copyOriginalOffers that copied nothing or an includedParts that resolved to nothing as well.
    ///
    /// It reports and does not repair. The vanilla default preset would fill every one of these exactly - one preset
    /// per base, no ambiguity - but that preset also carries ballistic plates (the THOR's come to ~618,000 roubles),
    /// so auto-filling would silently decide whether every purchase ships free plates. That is a balance call for
    /// Colette and Amber, not a default for a verification pass to pick.
    /// </remarks>
    private void VerifyTraderOffersCanBeEquipped(List<string> problems)
    {
        var dripItems = itemService.Created.ToDictionary(item => item.Id, item => item.RelativeName);
        var bare = new List<string>();

        foreach (var (traderId, trader) in tradersTable)
        {
            var assort = trader.Assort?.Items;
            if (assort is null)
            {
                continue;
            }

            // Children by parent, built once per trader rather than rescanned per offer.
            var childSlotsByParent = new Dictionary<string, HashSet<string>>(StringComparer.OrdinalIgnoreCase);
            foreach (var entry in assort.Where(entry => entry.ParentId is not null && entry.SlotId is not null))
            {
                if (!childSlotsByParent.TryGetValue(entry.ParentId!, out var slots))
                {
                    slots = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
                    childSlotsByParent[entry.ParentId!] = slots;
                }

                slots.Add(entry.SlotId!);
            }

            foreach (var offer in assort)
            {
                // Root offers only. A child entry has its own template and is not the thing being bought.
                if (offer.ParentId != "hideout" || offer.SlotId != "hideout")
                {
                    continue;
                }

                if (!dripItems.TryGetValue(offer.Template, out var relativeName))
                {
                    continue;
                }

                var missing = RequiredSlotsOf(offer.Template);
                if (missing.Count == 0)
                {
                    continue;
                }

                if (childSlotsByParent.TryGetValue(offer.Id.ToString(), out var filled))
                {
                    missing.ExceptWith(filled);
                }

                if (missing.Count > 0)
                {
                    bare.Add($"{relativeName} at {traderId} (empty: {string.Join(", ", missing.Order())})");
                }
            }
        }

        if (bare.Count > 0)
        {
            problems.Add(Describe(bare,
                "trader offers arrive with a required slot empty, so they can be bought and cannot be equipped. " +
                "Fill them with 'includedParts', or leave the item on copyOriginalOffers -"));
        }
    }

    /// <summary>
    /// The names of a template's required slots. Case-insensitive because the game's own data is not consistent -
    /// `Soft_armor_left` and `soft_armor_right` sit in the same item.
    /// </summary>
    private HashSet<string> RequiredSlotsOf(MongoId template)
    {
        var slots = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        if (!templateTable.Items.TryGetValue(template, out var item))
        {
            return slots;
        }

        foreach (var slot in item.Properties?.Slots ?? [])
        {
            if (slot.Required == true && !string.IsNullOrEmpty(slot.Name))
            {
                slots.Add(slot.Name!);
            }
        }

        return slots;
    }

    /// <summary>
    /// The trader id a reward refers to, or null if this kind of reward does not refer to one.
    /// </summary>
    /// <remarks>
    /// Which reward types carry a trader, and in which field, is <see cref="DripTraders.TryGetTraderField"/> - shared
    /// with the loader so the two cannot disagree. All this adds is the mapping from that JSON field name onto SPT's
    /// bound property, which is only interesting because the two fields have different types: Target is a string,
    /// TraderId is `object` (ProductionScheme puts an integer there, which is why it is not in the table).
    /// </remarks>
    private static string? TraderReferenceOf(Reward reward)
    {
        if (!DripTraders.TryGetTraderField(reward.Type?.ToString(), out var field))
        {
            return null;
        }

        return field switch
        {
            "target" => reward.Target,
            "traderId" => reward.TraderId?.ToString(),
            _ => null
        };
    }

    /// <summary>
    /// Item templates a quest's objectives point at. Deliberately narrow - only the condition types whose target is
    /// unambiguously an item template, so this cannot mistake a location or a quest id for a missing item.
    /// </summary>
    private static IEnumerable<MongoId> ItemTargetsOf(Quest quest)
    {
        var conditions = new[]
            {
                quest.Conditions?.AvailableForFinish,
                quest.Conditions?.AvailableForStart
            }
            .Where(list => list is not null)
            .SelectMany(list => list!);

        foreach (var condition in conditions)
        {
            if (condition.ConditionType is not ("HandoverItem" or "FindItem"))
            {
                continue;
            }

            if (condition.Target?.IsList != true)
            {
                continue;
            }

            foreach (var target in condition.Target.List!.Where(MongoId.IsValidMongoId))
            {
                yield return new MongoId(target);
            }
        }
    }

    /// <summary>
    /// Caught: every item being given a hardcoded 69420 handbook and flea price.
    /// </summary>
    private void VerifyEveryItemHasAHandbookPrice(List<string> problems)
    {
        var handbookIds = templateTable.Handbook.Items
            .Where(entry => entry.Price is > 0)
            .Select(entry => entry.Id)
            .ToHashSet();

        var unpriced = itemService.Created
            .Where(item => !handbookIds.Contains(item.Id))
            .Select(item => item.RelativeName)
            .ToList();

        if (unpriced.Count > 0)
        {
            problems.Add(Describe(unpriced, "has no handbook price, so it will be worthless in the catalogue -"));
        }
    }

    /// <summary>
    /// Two configs deriving one id would mean the second silently replaces the first. The loader rejects that as it
    /// happens; this confirms it across every pack at once.
    /// </summary>
    private void VerifyNoDuplicateIds(List<string> problems)
    {
        var duplicates = itemService.Created
            .GroupBy(item => item.Id)
            .Where(group => group.Count() > 1)
            .Select(group => $"{group.Key} claimed by {string.Join(" and ", group.Select(item => item.RelativeName))}")
            .ToList();

        if (duplicates.Count > 0)
        {
            problems.Add(Describe(duplicates, "share one item id -"));
        }
    }

    /// <summary>
    /// Caught: locale transformer wiring. An item whose name in game is its own 24-character id means the locale
    /// never reached it.
    /// </summary>
    /// <remarks>
    /// The only assertion here that costs anything - reading the English locale forces it to materialise, which is a
    /// full deserialise. Worth it: this is the one check that verifies text end-to-end rather than checking our own
    /// inputs back to ourselves.
    /// </remarks>
    private void VerifyEveryItemHasAName(List<string> problems)
    {
        if (!localeTable.Global.TryGetValue("en", out var english))
        {
            return;
        }

        var locale = english.Value;
        if (locale is null)
        {
            return;
        }

        var nameless = itemService.Created
            .Where(item =>
            {
                var key = $"{item.Id} Name";
                return !locale.TryGetValue(key, out var name)
                       || string.IsNullOrWhiteSpace(name)
                       || name == item.Id.ToString();
            })
            .Select(item => item.RelativeName)
            .ToList();

        if (nameless.Count > 0)
        {
            problems.Add(Describe(nameless, "has no name in game -"));
        }
    }

    /// <summary>
    /// Two items pointing at the same model bundle render identically, with nothing to say why.
    /// </summary>
    /// <remarks>
    /// This is the server-side half of a problem whose other half we cannot see from here. Bundles are discovered by
    /// co-location, so two configs in one folder both claim its bundle - that is this check, and it is catchable.
    ///
    /// The half we cannot check is that many DRIP bundles declare the *same internal vanilla path* as each other
    /// (79 paths are claimed by more than one bundle). That is invisible to the server, which registers bundle keys
    /// and never opens the files, and it is tracked as smoke test 6.7 instead.
    /// </remarks>
    private void VerifyNoTwoItemsShareOneModel(List<string> problems)
    {
        var byModelPath = new Dictionary<string, List<string>>();

        foreach (var created in itemService.Created)
        {
            if (!templateTable.Items.TryGetValue(created.Id, out var item))
            {
                continue;
            }

            var path = item.Properties?.Prefab?.Path;
            if (string.IsNullOrEmpty(path))
            {
                continue;
            }

            if (!byModelPath.TryGetValue(path, out var sharers))
            {
                sharers = [];
                byModelPath[path] = sharers;
            }

            sharers.Add(created.RelativeName);
        }

        var shared = byModelPath
            .Where(entry => entry.Value.Count > 1)
            .Select(entry => $"{string.Join(" and ", entry.Value)} all use {entry.Key}")
            .ToList();

        if (shared.Count > 0)
        {
            problems.Add(Describe(shared, "sets of items share one model, so they will look identical -"));
        }
    }

    /// <summary>
    /// A clothing gate pointing at a quest that does not exist.
    /// </summary>
    /// <remarks>
    /// The 3.x mod shipped this for years: 68 configs named quests as `DRIP_1`, `DRIP_12` and so on, while every
    /// real quest was keyed by a MongoId, so nothing resolved. Whether that made those garments unobtainable or
    /// silently free is client behaviour - the server records the requirement and never evaluates it, and SPT strips
    /// unresolvable quest conditions in exactly one place, for prestige, not for suits.
    ///
    /// Tau's converter now remaps the old names, and all 15 references resolve. This asserts it stays that way, and
    /// catches the cross-pack case on the way: a Part 2 garment gated behind a Part 1 quest that isn't installed.
    /// </remarks>
    private void VerifySuitQuestGatesResolve(List<string> problems)
    {
        var dangling = new List<string>();

        foreach (var traderId in new[] { DripTraders.Moron, DripTraders.Georgia })
        {
            if (!tradersTable.TryGetValue(traderId, out var trader) || trader.Suits is null)
            {
                continue;
            }

            foreach (var suit in trader.Suits)
            {
                var required = suit.Requirements?.QuestRequirements;
                if (required is null)
                {
                    continue;
                }

                foreach (var questId in required.Where(id => !string.IsNullOrWhiteSpace(id)))
                {
                    // Validate before constructing. MongoId's constructor throws on anything that isn't 24 hex
                    // characters, and a gate naming "DRIP_1" is exactly the case this check exists to find - so
                    // constructing one unguarded turns the report into a crash.
                    if (!MongoId.IsValidMongoId(questId))
                    {
                        dangling.Add($"{suit.SuiteId} -> \"{questId}\" (not even a quest ID)");
                        continue;
                    }

                    if (!templateTable.Quests.ContainsKey(new MongoId(questId)))
                    {
                        dangling.Add($"{suit.SuiteId} -> {questId}");
                    }
                }
            }
        }

        if (dangling.Count > 0)
        {
            problems.Add(Describe(dangling,
                "clothing gates name a quest that isn't installed, so the garment may be permanently unobtainable -"));
        }
    }

    private static string Describe(List<string> offenders, string what)
    {
        var named = string.Join(", ", offenders.Take(NamesToShow));
        var andMore = offenders.Count > NamesToShow ? $", and {offenders.Count - NamesToShow} more" : string.Empty;

        return $"{offenders.Count} {what} {named}{andMore}.";
    }
}
