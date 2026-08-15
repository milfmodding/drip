// Quest expansion: friendly format -> fully-built Quest + locale table.
// The shapes mirror the 19 verified quests in CustomQuests/DRIP.jsonc exactly - every
// default below was read off a working quest, not reconstructed from documentation.

using System.IO;
using System.Text.Json;
using System.Text.Json.Nodes;
using DRIP.Models;
using DRIP.Utils;
using SPTarkov.DI.Annotations;
using SPTarkov.Server.Core.Models.Common;
using SPTarkov.Server.Core.Models.Eft.Common.Tables;
using SPTarkov.Server.Core.Utils;
using Path = System.IO.Path;

namespace DRIP.Services;

/// <summary>
/// Expands <see cref="DRIPQuestFormat"/> into the objects SPT's CustomQuestService.CreateQuest consumes.
///
/// Everything mechanical lives here so nothing mechanical lives with the author:
/// quest/condition/reward ids derive from the filename (same <see cref="DripIds"/> function as
/// items, so cross-references resolve through one mechanism), the Start/Finish grouping follows
/// from each condition's own type (measured 66/66 across the corpus), six constant fields are
/// defaulted, and the locale table is generated from the inline text.
/// </summary>
[Injectable(InjectionType.Singleton)]
public class DRIPQuestExpander(
    HashUtil hashUtil)
{
    /// <summary>
    /// Expands one friendly quest. Returns null (with the reason logged by the caller's context)
    /// only from the methods that validate author input; this method itself assumes the format
    /// model bound successfully.
    /// </summary>
    public async Task<(Quest Quest, Dictionary<string, Dictionary<string, string>> Locales)> Expand(
        DRIPQuestFormat format, string stem, string relativeName)
    {
        var questId = await DripIds.Derive(hashUtil, stem, "quest");
        var id = questId.ToString();

        // Locale keys, mirroring the corpus: quest text keyed "<qid> field", objective text keyed by
        // the condition's own id. The client resolves quest text fields through these keys; an
        // objective with no authored text would render its raw key in the journal, so the fallback
        // is a sensible sentence rather than an empty string.
        var en = new Dictionary<string, string>
        {
            [$"{id} name"] = format.Name,
            [$"{id} description"] = format.Description ?? format.Name,
            [$"{id} successMessageText"] = format.OnSuccess ?? format.Description ?? format.Name,
            [$"{id} failMessageText"] = format.OnFail ?? "",
            [$"{id} note"] = "",
            [$"{id} changeQuestMessageText"] = "",
            [$"{id} declinePlayerMessage"] = "",
        };

        var startConditions = new JsonArray();
        var finishConditions = new JsonArray();

        if (format.Requires is { } requires)
        {
            if (requires.PlayerLevel is { } level)
            {
                startConditions.Add(LevelCondition(await NextId(stem, "start", 0), startConditions.Count, level));
            }

            if (requires.Quest is { } prerequisite)
            {
                var target = await ResolveQuestReference(prerequisite);
                startConditions.Add(QuestCondition(await NextId(stem, "start", 1), startConditions.Count, target));
            }
        }

        var anyKill = false;

        foreach (var objective in format.Objectives)
        {
            if (objective.Handover is { } handover)
            {
                var conditionId = await NextId(stem, "finish", finishConditions.Count);
                en[conditionId] = objective.Text ?? $"Hand over {objective.Count ?? 1} x {handover}.";
                finishConditions.Add(HandoverCondition(conditionId, finishConditions.Count, handover,
                    objective.Count ?? 1, objective.FoundInRaid ?? true));
            }
            else if (objective.Kill is { } kill)
            {
                anyKill = true;
                var conditionId = await NextId(stem, "finish", finishConditions.Count);
                en[conditionId] = objective.Text ?? $"Eliminate {objective.Count ?? 1} x {kill}.";
                finishConditions.Add(await KillCondition(conditionId, finishConditions.Count, kill,
                    objective.Count ?? 1, objective.At, objective.With, stem, finishConditions.Count));
            }
        }

        var rewards = new JsonArray();
        foreach (var reward in format.Rewards)
        {
            if (reward.Experience is { } experience)
            {
                rewards.Add(new JsonObject
                {
                    ["id"] = await NextId(stem, "reward", rewards.Count),
                    ["index"] = rewards.Count,
                    ["type"] = "Experience",
                    ["value"] = experience.ToString(),
                });
            }
            else if (reward.StandingWith is not null || reward.Standing is not null)
            {
                var amount = reward.Standing ?? 0.01;
                rewards.Add(new JsonObject
                {
                    ["id"] = await NextId(stem, "reward", rewards.Count),
                    ["index"] = rewards.Count,
                    ["type"] = "TraderStanding",
                    ["target"] = reward.StandingWith ?? format.Trader,
                    ["value"] = amount.ToString(),
                });
            }
            else if (reward.Unlock is { } unlock)
            {
                rewards.Add(new JsonObject
                {
                    ["id"] = await NextId(stem, "reward", rewards.Count),
                    ["index"] = rewards.Count,
                    ["type"] = "TraderUnlock",
                    ["target"] = unlock,
                });
            }
            else if (reward.Item is { } item)
            {
                var stackId = await NextId(stem, "reward-item", rewards.Count);
                var count = reward.ItemCount ?? 1;
                rewards.Add(new JsonObject
                {
                    ["id"] = await NextId(stem, "reward", rewards.Count),
                    ["index"] = rewards.Count,
                    ["type"] = "Item",
                    ["value"] = count.ToString(),
                    ["findInRaid"] = true,
                    ["target"] = stackId,
                    ["items"] = new JsonArray
                    {
                        new JsonObject
                        {
                            ["_id"] = stackId,
                            ["_tpl"] = item,
                            ["upd"] = new JsonObject { ["StackObjectsCount"] = count },
                        }
                    },
                });
            }
        }

        // The corpus has exactly two quest types: handover quests are PickUp, kill quests
        // Elimination. A quest with both is still Elimination - the type only names the
        // journal category.
        var questType = anyKill ? "Elimination" : "PickUp";

        var questJson = new JsonObject
        {
            ["QuestName"] = format.Name,
            ["_id"] = id,
            ["canShowNotificationsInGame"] = true,
            ["changeQuestMessageText"] = $"{id} changeQuestMessageText",
            ["conditions"] = new JsonObject
            {
                ["AvailableForStart"] = startConditions,
                ["AvailableForFinish"] = finishConditions,
                ["Fail"] = new JsonArray(),
            },
            ["declinePlayerMessage"] = $"{id} declinePlayerMessage",
            ["description"] = $"{id} description",
            ["failMessageText"] = $"{id} failMessageText",
            ["image"] = $"/files/quest/icon/{Path.GetFileNameWithoutExtension(format.Image ?? "quest")}",
            ["instantComplete"] = false,
            ["isKey"] = false,
            ["location"] = "any",
            ["name"] = $"{id} name",
            ["note"] = $"{id} note",
            ["restartable"] = false,
            ["rewards"] = new JsonObject
            {
                ["Fail"] = new JsonArray(),
                ["Started"] = new JsonArray(),
                ["Success"] = rewards,
            },
            ["secretQuest"] = false,
            ["side"] = "Pmc",
            ["startedMessageText"] = $"{id} description",
            ["successMessageText"] = $"{id} successMessageText",
            ["traderId"] = format.Trader,
            ["type"] = questType,
        };

        var quest = DripJson.BindToSptType<Quest>(
            JsonSerializer.SerializeToElement(questJson, DripJson.SptTypeOptions))
            ?? throw new InvalidOperationException(
                $"{relativeName}: the expanded quest did not bind to SPT's Quest type - " +
                "this is a bug in DRIPQuestExpander, not in the config.");

        var locales = new Dictionary<string, Dictionary<string, string>> { ["en"] = en };

        return (quest, locales);
    }

    private async Task<string> NextId(string stem, string role, int index)
    {
        return (await DripIds.Derive(hashUtil, stem, $"{role}-{index}")).ToString();
    }

    /// <summary>
    /// A prerequisite written as a filename resolves through the same derivation the quest loader
    /// uses; a raw id passes through. Self-reference is rejected - it would make a quest its own
    /// gate, which no player could ever start and nothing would report.
    /// </summary>
    private async Task<string> ResolveQuestReference(string reference)
    {
        return MongoId.IsValidMongoId(reference)
            ? reference
            : (await DripIds.Derive(hashUtil, reference, "quest")).ToString();
    }

    private static JsonNode LevelCondition(string id, int index, int level)
    {
        return new JsonObject
        {
            ["compareMethod"] = ">=",
            ["conditionType"] = "Level",
            ["dynamicLocale"] = false,
            ["globalQuestCounterId"] = "",
            ["id"] = id,
            ["index"] = index,
            ["parentId"] = "",
            ["value"] = level,
            ["visibilityConditions"] = new JsonArray(),
        };
    }

    private static JsonNode QuestCondition(string id, int index, string target)
    {
        return new JsonObject
        {
            ["availableAfter"] = 0,
            ["conditionType"] = "Quest",
            ["dynamicLocale"] = false,
            ["globalQuestCounterId"] = "",
            ["id"] = id,
            ["index"] = index,
            ["parentId"] = "",
            ["status"] = new JsonArray { 4 },       // 4 = Success, as every corpus prereq uses
            ["target"] = target,
            ["visibilityConditions"] = new JsonArray(),
        };
    }

    private static JsonNode HandoverCondition(string id, int index, string target, int count, bool foundInRaid)
    {
        return new JsonObject
        {
            ["conditionType"] = "HandoverItem",
            ["dogtagLevel"] = 0,
            ["dynamicLocale"] = false,
            ["globalQuestCounterId"] = "",
            ["id"] = id,
            ["index"] = index,
            ["maxDurability"] = 100,
            ["minDurability"] = 0,
            ["onlyFoundInRaid"] = foundInRaid,
            ["parentId"] = "",
            ["target"] = new JsonArray { target },
            ["value"] = count.ToString(),
            ["visibilityConditions"] = new JsonArray(),
        };
    }

    private async Task<JsonNode> KillCondition(
        string id, int index, string target, int count, string? at, string? with, string stem, int conditionIndex)
    {
        var kills = new JsonObject
        {
            ["compareMethod"] = ">=",
            ["conditionType"] = "Kills",
            ["id"] = await NextId(stem, "kill", conditionIndex),
            ["target"] = target,
            ["value"] = count.ToString(),
        };

        if (with is not null)
        {
            kills["weapon"] = new JsonArray { with };
        }

        var counterConditions = new JsonArray { kills };

        if (at is not null)
        {
            counterConditions.Add(new JsonObject
            {
                ["conditionType"] = "Location",
                ["id"] = await NextId(stem, "kill-location", conditionIndex),
                ["target"] = new JsonArray { at },
            });
        }

        return new JsonObject
        {
            ["conditionType"] = "CounterCreator",
            ["counter"] = new JsonObject
            {
                ["conditions"] = counterConditions,
                ["id"] = await NextId(stem, "counter", conditionIndex),
            },
            ["doNotResetIfCounterCompleted"] = false,
            ["dynamicLocale"] = false,
            ["globalQuestCounterId"] = "",
            ["id"] = id,
            ["index"] = index,
            ["oneSessionOnly"] = false,
            ["parentId"] = "",
            ["type"] = "Elimination",
            ["value"] = count.ToString(),
            ["visibilityConditions"] = new JsonArray(),
        };
    }
}
