using System.Text.Json.Serialization;
using SPTarkov.Server.Core.Models.Common;
using SPTarkov.Server.Core.Models.Eft.Common;
using SPTarkov.Server.Core.Models.Eft.Common.Tables;
using SPTarkov.Server.Core.Models.Enums;
using SPTarkov.Server.Core.Models.Spt.Mod;

namespace DRIP.Models;

/// <summary>
/// This is a modified version of WTT's CustomItemConfig that includes DRIP-specific functionality.
/// </summary>
// TODO: look into upstreaming this
public class CustomItemConfig
{
    [JsonPropertyName("itemTplToClone")] public required string ItemTplToClone { get; set; }

    [JsonPropertyName("parentId")] public string? ParentId { get; set; }

    [JsonPropertyName("handbookParentId")] public string? HandbookParentId { get; set; }

    [JsonPropertyName("overrideProperties")]
    public required TemplateItemProperties OverrideProperties { get; set; }

    [JsonPropertyName("locales")] public required Dictionary<string, LocaleDetails> Locales { get; set; }

    [JsonPropertyName("fleaPriceRoubles")] public int? FleaPriceRoubles { get; set; }

    [JsonPropertyName("handbookPriceRoubles")]
    public int? HandbookPriceRoubles { get; set; }

    [JsonPropertyName("addtoInventorySlots")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public List<string>? AddToInventorySlots { get; set; }

    [JsonPropertyName("addtoModSlots")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? AddToModSlots { get; set; }

    [JsonPropertyName("modSlot")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public List<string>? ModSlot { get; set; }

    [JsonPropertyName("addtoTraders")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? AddToTraders { get; set; }

    [JsonPropertyName("traders")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public Dictionary<string, Dictionary<MongoId, ConfigTraderScheme>>? Traders { get; set; }

    [JsonPropertyName("addtoBots")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? AddToBots { get; set; }

    [JsonPropertyName("addtoStaticLootContainers")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? AddToStaticLootContainers { get; set; }

    [JsonPropertyName("staticLootContainers")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public List<ConfigStaticLootContainer>? StaticLootContainers { get; set; }

    [JsonPropertyName("masteries")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? Masteries { get; set; }

    [JsonPropertyName("masterySections")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public List<Mastering>? MasterySections { get; set; }

    [JsonPropertyName("addWeaponPreset")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? AddWeaponPreset { get; set; }

    [JsonPropertyName("weaponPresets")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public List<Preset>? WeaponPresets { get; set; }

    [JsonPropertyName("addtoHallOfFame")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? AddToHallOfFame { get; set; }

    [JsonPropertyName("hallOfFameSlots")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public List<string>? HallOfFameSlots { get; set; }

    [JsonPropertyName("addtoSpecialSlots")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? AddToSpecialSlots { get; set; }

    [JsonPropertyName("addtoGeneratorAsFuel")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? AddToGeneratorAsFuel { get; set; }

    [JsonPropertyName("generatorFuelSlotStages")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public List<string>? GeneratorFuelSlotStages { get; set; }

    [JsonPropertyName("addtoHideoutPosterSlots")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? AddToHideoutPosterSlots { get; set; }

    [JsonPropertyName("addPosterToMaps")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? AddPosterToMaps { get; set; }

    [JsonPropertyName("posterSpawnProbability")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public int? PosterSpawnProbability { get; set; }

    [JsonPropertyName("addtoStatuetteSlots")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? AddToStatuetteSlots { get; set; }

    [JsonPropertyName("addCaliberToAllCloneLocations")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? AddCaliberToAllCloneLocations { get; set; }

    [JsonPropertyName("addtoStaticAmmo")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? AddToStaticAmmo { get; set; }

    [JsonPropertyName("staticAmmoProbability")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public int? StaticAmmoProbability { get; set; }

    [JsonPropertyName("addtoEmptyPropSlots")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? AddToEmptyPropSlots { get; set; }
        
    [JsonPropertyName("emptyPropSlot")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public EmptySlotScheme? EmptyPropSlot { get; set; }
    
    [JsonPropertyName("addtoSecureFilters")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? AddToSecureFilters { get; set; }
    
    // DRIP-Specific Fields ////////////////////////////////////////////////////////////////////////////////////////////
    [JsonPropertyName("cloneAssort")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? CloneAssort { get; set; }
    
    [JsonPropertyName("traderId")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? TraderId { get; set; }
    
    [JsonPropertyName("bundleDependencies")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public Dictionary<string, List<string>>? BundleDependencies { get; set; }

    ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

    public void Validate()
    {
        // ---------- Required checks ----------
        if (string.IsNullOrWhiteSpace(ItemTplToClone))
            throw new InvalidDataException("itemTplToClone is required");

        if (string.IsNullOrWhiteSpace(ParentId))
            throw new InvalidDataException("parentId is required");

        if (string.IsNullOrWhiteSpace(HandbookParentId))
            throw new InvalidDataException("handbookParentId is required");

        if (OverrideProperties == null)
            throw new InvalidDataException("overrideProperties is required");

        if (Locales == null || Locales.Count == 0)
            throw new InvalidDataException("locales is required and must contain at least one locale");

        if (FleaPriceRoubles < 0)
            throw new InvalidDataException("fleaPriceRoubles must be >= 0");

        if (HandbookPriceRoubles < 0)
            throw new InvalidDataException("handbookPriceRoubles must be >= 0");

        if (AddToTraders == true && Traders != null)
        {
            if (Traders.Count == 0)
                throw new InvalidDataException("traders was provided but is empty");

            foreach (var traderEntry in Traders)
            {
                var traderKey = traderEntry.Key;
                var schemes = traderEntry.Value;

                if (string.IsNullOrWhiteSpace(traderKey))
                    throw new InvalidDataException("traders contains an empty trader key");

                if (schemes == null || schemes.Count == 0)
                    throw new InvalidDataException($"traders['{traderKey}'] must contain at least one scheme");

                foreach (var schemeEntry in schemes)
                {
                    var schemeKey = schemeEntry.Key;
                    var scheme = schemeEntry.Value;

                    if (string.IsNullOrWhiteSpace(schemeKey))
                        throw new InvalidDataException($"traders['{traderKey}'] contains an empty scheme key");

                    if (scheme == null)
                        throw new InvalidDataException($"traders['{traderKey}']['{schemeKey}'] is null");

                    if (scheme.ConfigBarterSettings == null)
                        throw new InvalidDataException(
                            $"traders['{traderKey}']['{schemeKey}'].barterSettings is required");

                    if (scheme.ConfigBarterSettings.LoyalLevel < 0)
                        throw new InvalidDataException(
                            $"traders['{traderKey}']['{schemeKey}'].barterSettings.loyalLevel must be >= 0");

                    if (scheme.ConfigBarterSettings.StackObjectsCount < 0)
                        throw new InvalidDataException(
                            $"traders['{traderKey}']['{schemeKey}'].barterSettings.stackObjectsCount must be >= 0");

                    if (scheme.Barters == null || scheme.Barters.Count == 0)
                        throw new InvalidDataException(
                            $"traders['{traderKey}']['{schemeKey}'] must include at least one barter");

                    for (var i = 0; i < scheme.Barters.Count; i++)
                    {
                        var barter = scheme.Barters[i];
                        if (barter == null)
                            throw new InvalidDataException(
                                $"traders['{traderKey}']['{schemeKey}'].barters[{i}] is null");

                        if (string.IsNullOrWhiteSpace(barter.Template))
                            throw new InvalidDataException(
                                $"traders['{traderKey}']['{schemeKey}'].barters[{i}].template is required");

                        if (barter.Count <= 0)
                            throw new InvalidDataException(
                                $"traders['{traderKey}']['{schemeKey}'].barters[{i}].count must be > 0");
                    }
                }
            }
        }

        if (AddToInventorySlots != null && AddToInventorySlots.Count > 0)
            for (var i = 0; i < AddToInventorySlots.Count; i++)
                if (string.IsNullOrWhiteSpace(AddToInventorySlots[i]))
                    throw new InvalidDataException($"addtoInventorySlots[{i}] must be a non-empty string");

        if (AddToModSlots != null && AddToModSlots == true && ModSlot != null)
        {
            if (ModSlot.Count == 0)
                throw new InvalidDataException("modSlot was provided but is empty");

            for (var i = 0; i < ModSlot.Count; i++)
                if (string.IsNullOrWhiteSpace(ModSlot[i]))
                    throw new InvalidDataException($"modSlot[{i}] must be a non-empty string");
        }

        if (HallOfFameSlots != null && AddToHallOfFame == true)
        {
            if (HallOfFameSlots.Count == 0)
                throw new InvalidDataException("hallOfFameSlots was provided but is empty");

            for (var i = 0; i < HallOfFameSlots.Count; i++)
                if (string.IsNullOrWhiteSpace(HallOfFameSlots[i]))
                    throw new InvalidDataException($"hallOfFameSlots[{i}] must be a non-empty string");
        }

        if (AddToStaticLootContainers == true && StaticLootContainers != null)
        {
            if (StaticLootContainers.Count == 0)
                throw new InvalidDataException("staticLootContainers was provided but is empty");

            for (var i = 0; i < StaticLootContainers.Count; i++)
            {
                var c = StaticLootContainers[i];
                if (c == null)
                    throw new InvalidDataException($"staticLootContainers[{i}] is null");

                if (string.IsNullOrWhiteSpace(c.ContainerName))
                    throw new InvalidDataException($"staticLootContainers[{i}].containerName is required");

                if (c.Probability < 0)
                    throw new InvalidDataException($"staticLootContainers[{i}].probability must be >= 0");
            }
        }

        if (Masteries == true && MasterySections != null)
        {
            if (MasterySections.Count == 0)
                throw new InvalidDataException("masterySections was provided but is empty");

            for (var i = 0; i < MasterySections.Count; i++)
            {
                var m = MasterySections[i];
                if (m == null)
                    throw new InvalidDataException($"masterySections[{i}] is null");

                if (m.Templates == null)
                    throw new InvalidDataException($"masterySections[{i}].templates is required");
                if (m.Name == null)
                    throw new InvalidDataException($"masterySections[{i}].name is required");
                if (m.Level2 < 0)
                    throw new InvalidDataException($"masterySections[{i}].level2 is required");
                if (m.Level3 < 0)
                    throw new InvalidDataException($"masterySections[{i}].level3 is required");
            }
        }

        if (AddToStaticAmmo == true && StaticAmmoProbability == null)
            throw new InvalidDataException(
                "locationStaticAmmoProbability is required when addToLocationStaticAmmo is true");

        if (StaticAmmoProbability is < 0)
            throw new InvalidDataException("locationStaticAmmoProbability must be >= 0");

        if (AddToEmptyPropSlots == true && EmptyPropSlot == null)
            throw new InvalidDataException("emptyPropSlot is required when addToEmptyPropSlots is true");

        if (AddWeaponPreset == true && WeaponPresets != null)
        {
            if (WeaponPresets.Count == 0)
                throw new InvalidDataException("weaponPresets was provided but is empty");

            for (var i = 0; i < WeaponPresets.Count; i++)
            {
                var p = WeaponPresets[i];
                if (p == null)
                    throw new InvalidDataException($"weaponPresets[{i}] is null");

                if (string.IsNullOrWhiteSpace(p.Id.ToString()))
                    throw new InvalidDataException($"weaponPresets[{i}]._id is required");

                if (string.IsNullOrWhiteSpace(p.Type))
                    throw new InvalidDataException($"weaponPresets[{i}]._type is required");

                if (string.IsNullOrWhiteSpace(p.Name))
                    throw new InvalidDataException($"weaponPresets[{i}]._name is required");

                if (string.IsNullOrWhiteSpace(p.Parent.ToString()))
                    throw new InvalidDataException($"weaponPresets[{i}]._parent is required");

                if (p.Items == null || p.Items.Count == 0)
                    throw new InvalidDataException($"weaponPresets[{i}] must include at least one item");

                for (var j = 0; j < p.Items.Count; j++)
                {
                    var item = p.Items[j];
                    if (item == null)
                        throw new InvalidDataException($"weaponPresets[{i}].items[{j}] is null");

                    if (item.Id == null || string.IsNullOrWhiteSpace(item.Id.ToString()))
                        throw new InvalidDataException($"weaponPresets[{i}].items[{j}]._id is required");

                    if (item.Template == null || string.IsNullOrWhiteSpace(item.Template.ToString()))
                        throw new InvalidDataException($"weaponPresets[{i}].items[{j}]._tpl is required");

                    if (!string.IsNullOrWhiteSpace(item.ParentId) && string.IsNullOrWhiteSpace(item.SlotId))
                        throw new InvalidDataException(
                            $"weaponPresets[{i}].items[{j}] has a parentId but no slotId");

                    if (!string.IsNullOrWhiteSpace(item.SlotId) && string.IsNullOrWhiteSpace(item.ParentId))
                        throw new InvalidDataException(
                            $"weaponPresets[{i}].items[{j}] has a slotId but no parentId");
                }
            }
        }
    }
}

public class ConfigTraderScheme
{
    [JsonPropertyName("barterSettings")] public required ConfigBarterSettings ConfigBarterSettings { get; set; }

    [JsonPropertyName("barters")] public required List<ConfigBarterScheme> Barters { get; set; } = new();
    
}

public class ConfigBarterSettings
{
    [JsonPropertyName("loyalLevel")] public required int LoyalLevel { get; set; }

    [JsonPropertyName("unlimitedCount")] public required bool UnlimitedCount { get; set; }

    [JsonPropertyName("stackObjectsCount")] public required int StackObjectsCount { get; set; }

    [JsonPropertyName("buyRestrictionMax")] public int? BuyRestrictionMax { get; set; }
    
}

public class ConfigBarterScheme
{
    [JsonPropertyName("count")] public virtual double? Count { get; set; }

    [JsonPropertyName("_tpl")] public virtual string Template { get; set; }

    [JsonPropertyName("onlyFunctional")] public virtual bool? OnlyFunctional { get; set; }

    [JsonPropertyName("sptQuestLocked")] public virtual bool? SptQuestLocked { get; set; }

    [JsonPropertyName("level")] public virtual int? Level { get; set; }

    [JsonPropertyName("side")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public virtual DogtagExchangeSide? Side { get; set; }
}

public class ConfigStaticLootContainer
{
    [JsonPropertyName("containerName")] public required string ContainerName { get; set; } = string.Empty;

    [JsonPropertyName("probability")] public required int Probability { get; set; }
}

public class EmptySlotScheme
{
    [JsonPropertyName("itemToAddTo")]
    public string ItemToAddTo { get; set; } = string.Empty;
        
    [JsonPropertyName("modSlot")]
    public string ModSlot { get; set; } = string.Empty;
}