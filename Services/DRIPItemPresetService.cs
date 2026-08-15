using DRIP.Utils;
using SPTarkov.DI.Annotations;
using SPTarkov.Server.Core.Models.Common;
using SPTarkov.Server.Core.Models.Eft.Common;
using SPTarkov.Common.Models.Logging;
using SPTarkov.Server.Core.Models.Spt.Tables;
using SPTarkov.Server.Core.Utils;
using SPTarkov.Server.Core.Utils.Cloners;

namespace DRIP.Services;

/// <summary>
/// Gives every DRIP item a default preset, so armour bought from the flea arrives wearable.
/// </summary>
/// <remarks>
/// Sophia found this: a DRIP armour bought from a trader comes with its soft armour and plates, and the same item
/// bought on the flea arrives with empty required slots and cannot be equipped at all.
///
/// The two paths differ because only one of them was ever implemented. Traders work by accident of
/// copyOriginalOffers, which copies the original offer's children; the flea does not copy anything. It builds its
/// armour offers from globals.ItemPresets, and DRIP never wrote to that table, so a DRIP clone had no preset and the
/// flea emitted a bare root item.
///
/// What SPT actually requires, read out of 4.0.13 rather than assumed - three facts, each of which is easy to get
/// wrong and none of which is visible from the JSON:
///
///   1. RagfairAssortGenerator.GetPresetsToAdd reads ragfair.json's dynamic.showDefaultPresetsOnly (true by default)
///      and, when set, takes PresetHelper.GetDefaultPresets() rather than every preset.
///   2. The equipment half of that is filtered by
///          preset.Encyclopedia.HasValue &amp;&amp; itemHelper.ArmorItemCanHoldMods(preset.Encyclopedia.Value)
///      Note it tests _encyclopedia, NOT the root of _items. So _encyclopedia is not bookkeeping - it is the field
///      that decides whether a preset reaches the flea at all, and it has to name the DRIP item.
///   3. PresetHelper.GetDefaultPresetsByTplKey keys on _items.First().Template, and GetBaseItemTpl finds the root by
///      _id == _parent. So the root entry must stay first in the array and _parent must point at it.
///
/// Timing is not a concern: presets are cached at PresetCallbacks (900,000) via PresetController.Initialize, and
/// DRIP writes them at 400,002.
/// </remarks>
[Injectable(InjectionType.Singleton)]
public class DRIPItemPresetService(
    ISptLogger<DRIPItemPresetService> logger,
    TemplateTable templateTable,
    GlobalTable globalTable,
    DRIPCustomItemService itemService,
    HashUtil hashUtil,
    ICloner cloner
)
{
    /// <summary>A preset DRIP added, for the verification pass.</summary>
    public record CreatedPreset(MongoId PresetId, MongoId ItemTpl, MongoId BaseTpl, string RelativeName);

    private readonly List<CreatedPreset> _created = [];

    public IReadOnlyList<CreatedPreset> Created => _created;

    /// <summary>
    /// Items whose base has a default preset carrying required slots, but which we could not give one.
    /// </summary>
    public IReadOnlyList<string> Failed => _failed;

    private readonly List<string> _failed = [];

    /// <summary>
    /// Clones the default preset of every DRIP item's base onto the DRIP item. Call once, after all content packs
    /// have loaded.
    /// </summary>
    public async Task ApplyAll()
    {
        var presets = globalTable.ItemPresets;

        if (presets is null || presets.Count == 0)
        {
            logger.Error(
                "[DRIP] globals has no ItemPresets table, so no DRIP armour can be given a flea preset. Armour " +
                "bought from the flea will arrive with empty plate slots and cannot be equipped.");
            return;
        }

        // Index vanilla's defaults by the item they are the preset *for*. Keyed on _encyclopedia rather than on the
        // root of _items because that is the field SPT filters on - see the class remarks. In 4.0.13 the two agree
        // for all 254 default presets, and each tpl has exactly one, so this cannot silently pick a loser.
        var defaultByTpl = new Dictionary<MongoId, Preset>();
        foreach (var preset in presets.Values)
        {
            if (preset.Encyclopedia is { } encyclopedia)
            {
                defaultByTpl.TryAdd(encyclopedia, preset);
            }
        }

        var created = 0;
        var skippedNoPreset = 0;

        foreach (var item in itemService.Created)
        {
            if (!defaultByTpl.TryGetValue(item.BaseTpl, out var basePreset))
            {
                // The base has no default preset, so vanilla sells it bare on the flea too. Nothing to mirror.
                skippedNoPreset++;
                continue;
            }

            if (await BuildPresetFor(item, basePreset, presets))
            {
                created++;
            }
            else
            {
                _failed.Add(item.RelativeName);
            }
        }

        if (created == 0 && _failed.Count == 0)
        {
            return;
        }

        var summary =
            $"[DRIP] Flea presets: {created} created for {itemService.Created.Count} items " +
            $"({skippedNoPreset} bases have no default preset, so vanilla sells those bare too)";

        if (_failed.Count > 0)
        {
            logger.Error($"{summary}, {_failed.Count} failed.");
        }
        else
        {
            logger.Info($"{summary}.");
        }
    }

    /// <summary>
    /// Clones one vanilla default preset onto one DRIP item and registers it.
    /// </summary>
    private async Task<bool> BuildPresetFor(
        DRIPCustomItemService.CreatedItem item,
        Preset basePreset,
        Dictionary<MongoId, Preset> presets)
    {
        if (basePreset.Items is not { Count: > 0 })
        {
            logger.Error(
                $"[DRIP] {item.RelativeName}: the default preset of {item.BaseTpl} has no items, so it cannot be " +
                "cloned. This item will arrive from the flea with empty slots.");
            return false;
        }

        var stem = Path.GetFileNameWithoutExtension(item.RelativeName);

        // Everything is derived, nothing is generated. A preset id that changes between builds is the same failure
        // as an item id that changes between builds, which cost a bricked profile on 2026-07-31 - so the rule that
        // came out of that applies here unchanged. See DripIds.
        var presetId = await DripIds.Derive(hashUtil, stem, "preset");

        if (presets.ContainsKey(presetId) || templateTable.Items.ContainsKey(presetId))
        {
            logger.Error(
                $"[DRIP] {item.RelativeName}: preset ID {presetId} is already taken. Two configs with the same " +
                "filename derive the same IDs - rename one of them.");
            return false;
        }

        var preset = cloner.Clone(basePreset);

        // Re-id every entry. Without this, DRIP's preset and the vanilla preset it was cloned from share item ids,
        // and both live in the same table. Derived per position so they are stable across builds, and the mapping is
        // built first so parentId references can be rewritten to match.
        var newIdByOldId = new Dictionary<MongoId, MongoId>();
        for (var index = 0; index < preset.Items!.Count; index++)
        {
            newIdByOldId[preset.Items[index].Id] = await DripIds.Derive(hashUtil, stem, $"preset-item-{index}");
        }

        foreach (var entry in preset.Items)
        {
            entry.Id = newIdByOldId[entry.Id];

            // A parentId that isn't in the map would be a reference out of the preset, which vanilla never does.
            // Leaving it as-is is the safe reading: it is not ours to invent a target for.
            if (entry.ParentId is not null &&
                MongoId.IsValidMongoId(entry.ParentId) &&
                newIdByOldId.TryGetValue(new MongoId(entry.ParentId), out var newParentId))
            {
                entry.ParentId = newParentId.ToString();
            }
        }

        // The root is the entry with no parent - and it must stay first, because GetDefaultPresetsByTplKey keys the
        // whole cache on _items.First().Template. Vanilla always puts it first; assert rather than assume, because
        // if that ever stops being true the preset silently registers against the wrong template.
        var root = preset.Items[0];
        if (root.ParentId is not null)
        {
            logger.Error(
                $"[DRIP] {item.RelativeName}: the default preset of {item.BaseTpl} does not have its root item " +
                "first, which is the order SPT indexes presets by. Skipping rather than registering it against the " +
                "wrong item.");
            return false;
        }

        root.Template = item.Id;

        preset.Id = presetId;
        preset.Parent = root.Id;

        // The field that decides whether this reaches the flea at all. See the class remarks.
        preset.Encyclopedia = item.Id;

        // Distinct and greppable in a globals dump. Nothing reads it - GetDefaultPresets never looks at _name - but
        // leaving 59 presets all called "LBT-6094A Slick Plate Carrier" is a debugging tax for no gain.
        preset.Name = stem;

        presets[presetId] = preset;
        _created.Add(new CreatedPreset(presetId, item.Id, item.BaseTpl, item.RelativeName));

        return true;
    }
}
