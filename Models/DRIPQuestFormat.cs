// Quest authoring format: Models/DRIPQuestFormat.cs
// The friendly format from docs/QUEST-LAYER-DESIGN.md and QUEST-FORMAT-PROPOSAL.md.
// One file per quest under CustomQuests/; the filename derives the quest id.

using System.Text.Json.Serialization;

namespace DRIP.Models;

/// <summary>
/// A quest as an author writes it: decisions only, no bookkeeping.
///
/// Every id is derived (the filename gives the quest id; condition and reward ids derive from
/// quest id + position), the condition grouping (AvailableForStart/Finish) follows from each
/// condition's own type — measured 66/66 across the corpus with no exceptions — and six
/// top-level fields that are identical in every quest the mod has ever shipped are simply
/// defaulted. The loader expands this into a fully-built <see cref="Quest"/> and inserts it
/// through SPT's CustomQuestService.CreateQuest.
/// </summary>
public class DRIPQuestFormat
{
    /// <summary>What players see in the quest log's title. The file's name is the quest's ID.</summary>
    public string Name { get; set; } = "";

    /// <summary>Who hands the quest out. A friendly trader name ('moron', 'georgia', 'ragman') or a raw id.</summary>
    public string Trader { get; set; } = "";

    /// <summary>Quest icon, by filename of a .png beside this config. Optional.</summary>
    public string? Image { get; set; }

    /// <summary>The quest-giver's pitch, shown before accepting.</summary>
    public string? Description { get; set; }

    /// <summary>What the trader says on completion. Optional; description is used if absent.</summary>
    public string? OnSuccess { get; set; }

    /// <summary>What the trader says when the quest is accepted. Optional.</summary>
    public string? OnStart { get; set; }

    /// <summary>What the trader says on failure. Optional.</summary>
    public string? OnFail { get; set; }

    /// <summary>Gates on starting the quest at all.</summary>
    public QuestRequirements? Requires { get; set; }

    /// <summary>What the player must do. Order within the list does not matter.</summary>
    public List<QuestObjective> Objectives { get; set; } = [];

    /// <summary>What the player gets. Order within the list does not matter.</summary>
    public List<QuestReward> Rewards { get; set; } = [];
}

public class QuestRequirements
{
    /// <summary>Minimum player level to start.</summary>
    [JsonPropertyName("playerLevel")]
    public int? PlayerLevel { get; set; }

    /// <summary>A quest (by filename, e.g. "GLOCK_WICK") that must be done first.</summary>
    public string? Quest { get; set; }
}

public class QuestObjective
{
    /// <summary>Hand items to the trader: which item (pack filename or vanilla id), how many, found-in-raid or not.</summary>
    public string? Handover { get; set; }
    public int? Count { get; set; }
    [JsonPropertyName("foundInRaid")]
    public bool? FoundInRaid { get; set; }

    /// <summary>Kill things: who ("AnyPmc", "Scav", a base name), how many, optionally where and with what.</summary>
    public string? Kill { get; set; }
    public string? At { get; set; }
    public string? With { get; set; }

    /// <summary>The text the player reads for this objective. The one field with no mechanical meaning and the one authors most need to control.</summary>
    public string? Text { get; set; }
}

public class QuestReward
{
    /// <summary>XP awarded on completion.</summary>
    public double? Experience { get; set; }

    /// <summary>Reputation with the quest's own trader.</summary>
    public double? Standing { get; set; }

    /// <summary>Reputation with a named trader, when it is not the quest's own.</summary>
    public string? StandingWith { get; set; }

    /// <summary>Unlock a trader's higher loyalty tier.</summary>
    public string? Unlock { get; set; }

    /// <summary>Give items: which (pack filename or vanilla id) and how many.</summary>
    public string? Item { get; set; }
    [JsonPropertyName("itemCount")]
    public int? ItemCount { get; set; }
}
