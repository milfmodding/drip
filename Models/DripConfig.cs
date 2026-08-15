using System.Text.Json;
using System.Text.Json.Serialization;

namespace DRIP.Models;

/// <summary>
/// The mod's global options, from `config/config.jsonc`.
///
/// Every option here is one a player might reasonably want to change, so each has a sane default and a missing
/// config file is not an error - DRIP runs with defaults and says so once.
/// </summary>
/// <remarks>
/// Schema v2 §6. Two 3.x options are deliberately absent: `UseDRIPTagSystem` and `vanillaclothing` both configured
/// the clothing tag system, which is tabled and moving to ICUP. Names are normalised to camelCase and read
/// case-insensitively, so the 3.x PascalCase spellings still bind.
/// </remarks>
public class DripConfig
{
    /// <summary>Make all DRIP clothing free and requirement-free.</summary>
    [JsonPropertyName("noClothingRequirements")]
    public bool NoClothingRequirements { get; set; }

    /// <summary>Let bots wear DRIP clothing.</summary>
    [JsonPropertyName("addClothingToBots")]
    public bool AddClothingToBots { get; set; } = true;

    /// <summary>Let bots spawn with DRIP gear.</summary>
    [JsonPropertyName("addEquipmentToBots")]
    public bool AddEquipmentToBots { get; set; } = true;

    /// <summary>
    /// Rescale what Ragman charges for *vanilla* clothing, as a percentage of the original. 40 makes everything 40%
    /// of its usual price; 0 makes it free. Does not affect DRIP's own clothing.
    /// </summary>
    [JsonPropertyName("vanillaClothingPricePercentage")]
    public int VanillaClothingPricePercentage { get; set; } = 100;

    /// <summary>Note which content pack an item came from at the end of its description.</summary>
    [JsonPropertyName("collectionInDescription")]
    public bool CollectionInDescription { get; set; } = true;

    /// <summary>Prefix every item's name with its content pack. For debugging, not for playing.</summary>
    [JsonPropertyName("debugNames")]
    public bool DebugNames { get; set; }

    // Debugging ///////////////////////////////////////////////////////////////////////////////////////////////////

    /// <summary>
    /// Make every bot wear one specific top, named by its config filename without the extension.
    /// </summary>
    /// <remarks>
    /// For reproducing appearance bugs, not for playing. Bots normally roll a garment from a weighted pool, which
    /// makes "I did not see the bug" and "I did not roll the bug" indistinguishable. Pinning removes the dice.
    /// </remarks>
    [JsonPropertyName("debugPinBotTop")]
    public string? DebugPinBotTop { get; set; }

    /// <summary>Make every bot wear one specific bottom. See <see cref="DebugPinBotTop"/>.</summary>
    [JsonPropertyName("debugPinBotBottom")]
    public string? DebugPinBotBottom { get; set; }

    /// <summary>Anything unrecognised - notably the two dropped tag options - kept rather than rejected.</summary>
    [JsonExtensionData]
    public Dictionary<string, JsonElement> Extra { get; set; } = new();
}
