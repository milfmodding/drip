using SPTarkov.Server.Core.Models.Common;
using SPTarkov.Server.Core.Utils;

namespace DRIP.Utils;

/// <summary>
/// Derives item ids from filenames.
///
/// Authors never write an id. It is a deterministic function of the config's filename, which means it survives
/// restarts and folder reorganisation, and two people adding content in parallel cannot collide unless they pick
/// the same filename - in which case the loader says so.
/// </summary>
public static class DripIds
{
    /// <summary>
    /// Derive an id from a filename stem, optionally for a specific role.
    ///
    /// Clothing needs several ids where the author supplies at most one - a top is a body, a pair of hands and a
    /// suite - so the role distinguishes them. It is folded into the hash input rather than into the resulting id,
    /// because the id must stay a valid 24-character MongoId.
    /// </summary>
    public static async Task<MongoId> Derive(HashUtil hashUtil, string stem, string? role = null)
    {
        var input = role is null ? stem : $"{stem}:{role}";
        var hash = await hashUtil.GenerateHashForDataAsync(HashingAlgorithm.SHA1, input);

        return new MongoId(hash[..24].ToLower());
    }
}
