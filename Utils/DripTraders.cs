using SPTarkov.Server.Core.Models.Common;
using SPTarkov.Server.Core.Models.Enums;

namespace DRIP.Utils;

/// <summary>
/// Resolves the author-facing `traderId` field to a real trader MongoId.
///
/// Resolution order, all matched case-insensitively:
///   1. DRIP trader names  - "moron", "georgia"
///   2. Vanilla trader names - "fence", "ragman", "prapor", ...
///   3. A raw 24-character MongoId, passed straight through
///
/// Friendly names are load-bearing, not sugar: 515 of 543 legacy configs use them. Vanilla names are new, and exist
/// because 28 configs hardcode a raw id that nobody can verify by eye - during the schema pass that very id was
/// mis-read as Ragman when it is in fact Fence, which would have silently relocated 28 items to the wrong trader.
///
/// Vanilla ids come from the server's Traders enum and are never hand-written here, so they cannot drift.
/// </summary>
public static class DripTraders
{
    /// <summary>Tupitsa, aka "moron".</summary>
    public static readonly MongoId Moron = new("cd736677c3b1b0c7baf04f25");

    /// <summary>Georgia.</summary>
    public static readonly MongoId Georgia = new("d6f8d358252b59ba5784e89c");

    private static readonly Dictionary<string, MongoId> ByName = new(StringComparer.OrdinalIgnoreCase)
    {
        ["moron"] = Moron,
        ["georgia"] = Georgia,

        ["prapor"] = Traders.PRAPOR,
        ["therapist"] = Traders.THERAPIST,
        ["fence"] = Traders.FENCE,
        ["skier"] = Traders.SKIER,
        ["peacekeeper"] = Traders.PEACEKEEPER,
        ["mechanic"] = Traders.MECHANIC,
        ["ragman"] = Traders.RAGMAN,
        ["jaeger"] = Traders.JAEGER,
        ["lighthousekeeper"] = Traders.LIGHTHOUSEKEEPER,
        ["btr"] = Traders.BTR,
        ["ref"] = Traders.REF
    };

    /// <summary>The names DRIP recognises, for use in error messages.</summary>
    public static IEnumerable<string> KnownNames => ByName.Keys;

    /// <summary>
    /// Reward fields that hold a trader id, keyed by the reward type that owns them. Nothing outside this table is a
    /// trader reference.
    /// </summary>
    /// <remarks>
    /// Lives here rather than beside either of its two users so there is exactly one copy. It is read by
    /// DRIPCustomQuestService, which rewrites these fields at load, and by DRIPVerificationService, which asserts
    /// afterwards that they all point at a real trader. Two copies of this set would drift, and the direction it
    /// would drift is a reward type the loader resolves but the check does not look at.
    ///
    /// Why it has to be keyed by reward type at all: `target` is a different kind of id on almost every reward type -
    /// an item template on Item, an achievement on Achievement, a pocket template on Pockets, a skill *name* on Skill
    /// - so "resolve every target" would be wrong even though <see cref="TryResolve"/> passes a 24-character id
    /// through unchanged. It would also teach the next reader that targets are trader-shaped, which is the more
    /// expensive mistake.
    ///
    /// Where each pair comes from, so it can be rechecked rather than trusted:
    ///   * TraderStanding and TraderUnlock are proven. RewardHelper.ApplyRewards casts `target` to MongoId and hands
    ///     it to TraderHelper.AddStandingToTrader and SetTraderUnlockedState respectively.
    ///   * TraderStandingReset and TraderStandingRestore are by name and by vanilla data, not by code - 4.0.13's
    ///     ApplyRewards has no branch for either, so both currently fall through to its "unhandled reward type"
    ///     error. Listed because the day SPT implements them, an alias there would throw exactly as this bug did.
    ///   * AssortmentUnlock carries its trader in `traderId`, not `target` - 236 vanilla rewards do this. Note that
    ///     field is typed `object` on SPT's model because ProductionScheme puts an *integer* in the same key; keying
    ///     off the reward type is what keeps us away from that.
    /// </remarks>
    private static readonly Dictionary<string, string> TraderFieldByRewardType = new(StringComparer.OrdinalIgnoreCase)
    {
        ["TraderStanding"] = "target",
        ["TraderUnlock"] = "target",
        ["TraderStandingReset"] = "target",
        ["TraderStandingRestore"] = "target",
        ["AssortmentUnlock"] = "traderId"
    };

    /// <summary>
    /// Which field of a quest reward holds a trader id, if any.
    /// </summary>
    /// <param name="rewardType">The reward's `type`, as authored or as SPT's RewardType enum names it.</param>
    /// <param name="field">The JSON field name - "target" or "traderId".</param>
    public static bool TryGetTraderField(string? rewardType, out string field)
    {
        field = string.Empty;

        return rewardType is not null && TraderFieldByRewardType.TryGetValue(rewardType, out field!);
    }

    public static bool TryResolve(string? traderId, out MongoId resolved)
    {
        resolved = default;

        if (string.IsNullOrWhiteSpace(traderId))
        {
            return false;
        }

        var trimmed = traderId.Trim();

        if (ByName.TryGetValue(trimmed, out var known))
        {
            resolved = known;
            return true;
        }

        if (MongoId.IsValidMongoId(trimmed))
        {
            resolved = new MongoId(trimmed);
            return true;
        }

        return false;
    }
}
