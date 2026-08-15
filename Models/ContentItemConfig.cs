using System.Text.Json;
using System.Text.Json.Serialization;
using DRIP.Utils;
using SPTarkov.Server.Core.Models.Common;
using SPTarkov.Server.Core.Models.Eft.Common.Tables;

namespace DRIP.Models;

/// <summary>
/// The kind of content a config describes. Matched case-insensitively.
/// </summary>
public enum ContentItemType
{
    Top,
    Bottom,
    Gear
}

/// <summary>
/// A single piece of DRIP content, as authored in a Content Pack .jsonc file.
///
/// This is Schema v2 - see docs/CONFIG-SCHEMA-v2.md, which is the contract and takes precedence over this file.
/// If the two disagree, that is a bug in one of them; say so rather than working around it.
///
/// One model covers tops, bottoms and gear. Which fields are legal depends on <see cref="Type"/>, and that is
/// enforced by the validator rather than by the shape of the type, so that a mistyped `type` produces a message
/// instead of a deserialisation failure.
/// </summary>
public class ContentItemConfig
{
    // 4.1 Identity ////////////////////////////////////////////////////////////////////////////////////////////////

    /// <summary>
    /// The raw text the author wrote, kept so diagnostics can quote it back and suggest a correction.
    /// </summary>
    /// <remarks>
    /// Bound as a string rather than through JsonStringEnumConverter deliberately. That converter throws on any
    /// unrecognised value, which would abort deserialisation of the whole file - so a single "TOPP" would surface as
    /// a bogus "this isn't valid JSON" error, prevent DRIP-101 from ever suggesting the right spelling, and stop
    /// [JsonExtensionData] from being populated, hiding every other problem in the file until the typo is fixed and
    /// the author runs again. On a 275-file pack that turns one round-trip into several.
    /// </remarks>
    [JsonPropertyName("type")]
    public string? TypeRaw { get; set; }

    /// <summary>The parsed type, or null if absent <i>or</i> unrecognised. Use <see cref="HasUnrecognisedType"/> to tell those apart.</summary>
    [JsonIgnore]
    public ContentItemType? Type => EnumText.Parse<ContentItemType>(TypeRaw);

    [JsonIgnore]
    public bool HasUnrecognisedType => !string.IsNullOrWhiteSpace(TypeRaw) && Type is null;

    /// <summary>
    /// Optional explicit id. Omitted in almost every case - the loader derives it from the filename.
    /// </summary>
    [JsonPropertyName("id")]
    public string? Id { get; set; }

    // 4.2 Naming and text /////////////////////////////////////////////////////////////////////////////////////////

    /// <summary>English name, and the fallback for every other locale.</summary>
    [JsonPropertyName("name")]
    public string? Name { get; set; }

    /// <summary>Gear only - the game never shows a short name for customization items.</summary>
    [JsonPropertyName("shortName")]
    public string? ShortName { get; set; }

    /// <summary>Gear only - the game never shows a description for customization items.</summary>
    [JsonPropertyName("description")]
    public string? Description { get; set; }

    /// <summary>Per-locale overrides. Purely additive; omit it and every locale gets the English text.</summary>
    [JsonPropertyName("translations")]
    public Dictionary<string, ContentItemTranslation>? Translations { get; set; }

    // 4.3 Where it's sold /////////////////////////////////////////////////////////////////////////////////////////

    /// <summary>DRIP trader name, vanilla trader name, or a raw MongoId. Resolved by DripTraders.</summary>
    [JsonPropertyName("traderId")]
    public string? TraderId { get; set; }

    /// <summary>
    /// What the trader charges.
    /// </summary>
    /// <remarks>
    /// Nullable rather than defaulted so that "missing" means absent and never zero - the two need different
    /// diagnostics.
    ///
    /// A zero price is legacy test junk rather than an intentionally free item (Sophia's call), so it warns and
    /// names the file rather than failing. That is separate from the runtime `NoClothingRequirements` option, which
    /// zeroes every clothing price deliberately and stays valid.
    /// </remarks>
    [JsonPropertyName("price")]
    public int? Price { get; set; }

    /// <summary>
    /// Raw currency text. String-bound for the same reason as <see cref="TypeRaw"/> - "ROUBLES" should produce
    /// DRIP-304 naming the value, not a JSON parse failure that buries the rest of the file.
    /// </summary>
    [JsonPropertyName("currency")]
    public string? CurrencyRaw { get; set; }

    /// <summary>The parsed currency, or null if absent <i>or</i> unrecognised.</summary>
    [JsonIgnore]
    public DripCurrency? Currency => EnumText.Parse<DripCurrency>(CurrencyRaw);

    [JsonIgnore]
    public bool HasUnrecognisedCurrency => !string.IsNullOrWhiteSpace(CurrencyRaw) && Currency is null;

    [JsonPropertyName("loyaltyLevel")] public int? LoyaltyLevel { get; set; }

    /// <summary>Clothing only.</summary>
    [JsonPropertyName("profileLevel")] public int? ProfileLevel { get; set; }

    /// <summary>Clothing only.</summary>
    [JsonPropertyName("standing")] public double? Standing { get; set; }

    [JsonPropertyName("questRequirements")] public List<string>? QuestRequirements { get; set; }

    // 4.4 Other prices ////////////////////////////////////////////////////////////////////////////////////////////

    /// <summary>Catalogue valuation. Defaults to the cloned item's.</summary>
    [JsonPropertyName("handbookPrice")] public int? HandbookPrice { get; set; }

    /// <summary>Flea market valuation. Defaults to the cloned item's.</summary>
    [JsonPropertyName("fleaPrice")] public int? FleaPrice { get; set; }

    // 4.5 Gear-only ///////////////////////////////////////////////////////////////////////////////////////////////

    /// <summary>The item this one is a retexture of. Required for gear.</summary>
    [JsonPropertyName("basedOn")]
    public string? BasedOn { get; set; }

    /// <summary>Sell this wherever the original is sold, inheriting its price and loyalty level.</summary>
    [JsonPropertyName("copyOriginalOffers")]
    public bool? CopyOriginalOffers { get; set; }

    [JsonPropertyName("addToBots")] public bool? AddToBots { get; set; }

    /// <summary>
    /// Scales how often bots spawn with this item, relative to the item it retextures.
    /// </summary>
    /// <remarks>
    /// Deliberately a real knob rather than a vestigial field (Sophia's call). Unset means 1.0 - the same spawn rate
    /// as the original - which is right for most retextures, and no config in the corpus sets it. But a rarer item
    /// is a thing an author should be able to ask for, so the first person to write 0.5 will genuinely get one.
    /// </remarks>
    [JsonPropertyName("botWeightMultiplier")] public double? BotWeightMultiplier { get; set; }

    /// <summary>Slot name to the item filling it - armour plates, in practice. Only meaningful with own-price gear.</summary>
    [JsonPropertyName("includedParts")]
    public Dictionary<string, string>? IncludedParts { get; set; }

    /// <summary>
    /// Direct property overrides layered onto the cloned item, using raw BSG property names.
    ///
    /// Held as raw JSON rather than bound directly to <see cref="TemplateItemProperties"/> because that type must be
    /// deserialised case-<i>sensitively</i> - it declares both `ShotgunDispersion` and `shotgunDispersion`, and the
    /// case-insensitive options DRIP's own fields use cannot construct it at all. Call
    /// <see cref="MaterializeProperties"/> to bind it.
    /// </summary>
    [JsonPropertyName("properties")]
    public JsonElement? Properties { get; set; }

    /// <summary>
    /// Bind <see cref="Properties"/> onto SPT's item property model, with the exact-match options that type needs.
    /// </summary>
    public TemplateItemProperties? MaterializeProperties()
    {
        return Properties is null ? null : DripJson.BindToSptType<TemplateItemProperties>(Properties.Value);
    }

    /// <summary>Pull named properties off another item template - armour stats, in practice.</summary>
    [JsonPropertyName("copyPropertiesFrom")]
    public Dictionary<string, List<string>>? CopyPropertiesFrom { get; set; }

    // 4.8 Bot suitability /////////////////////////////////////////////////////////////////////////////////////////

    /// <summary>
    /// The vanilla bundle this garment is a retexture of, e.g.
    /// "assets/content/characters/character/prefabs/pants_wild_victory.bundle".
    /// </summary>
    /// <remarks>
    /// Written by the converter, read from the bundle's own AssetBundle object - the loader never opens bundles, so
    /// it cannot discover this itself.
    ///
    /// It decides which bots may wear the garment: a bot wears a retexture exactly when it already wears the thing
    /// being retextured. Same principle as `copyOriginalOffers` and slot-filter inheritance - a retexture behaves
    /// like its original.
    ///
    /// Resolved against the live database rather than pre-computed into a bot list by the converter, so it
    /// self-corrects when BSG changes an appearance pool.
    ///
    /// TODO(Tau): field name proposed, not agreed. Matches the `vanillaOrigin` key already used in the art library
    /// manifest, which is where the value comes from. Rename freely - this is the only place it is read.
    /// </remarks>
    [JsonPropertyName("vanillaOrigin")]
    public string? VanillaOrigin { get; set; }

    /// <summary>
    /// Bot types that may wear this garment, overriding what <see cref="VanillaOrigin"/> would decide.
    /// </summary>
    /// <remarks>
    /// The escape hatch for the one assumption the derivation rests on: that an author clones the base garment
    /// matching their intent. A scav-intended retexture built from a PMC base would be misclassified, and this is
    /// how that gets corrected - deliberately per-garment rather than a global switch.
    ///
    /// An empty list is meaningful and distinct from omitting the field: it means "no bot wears this", i.e.
    /// player-only.
    /// </remarks>
    [JsonPropertyName("botTypes")]
    public List<string>? BotTypes { get; set; }

    // 4.6 Bundles - PROVISIONAL ///////////////////////////////////////////////////////////////////////////////////

    /// <summary>
    /// Extra dependency keys per co-located bundle, keyed by bundle filename. Omit entirely and you get co-location
    /// plus the default dependencies, which is correct for most of the corpus.
    /// </summary>
    /// <remarks>
    /// PROVISIONAL - the bundle workstream may reshape this, and is moving toward less author-facing surface, so it
    /// may become optional-to-absent. Deliberately isolated under one key: keep bundle concerns out of other fields
    /// so that change stays a single-object edit.
    /// </remarks>
    [JsonPropertyName("bundles")]
    public Dictionary<string, List<string>>? Bundles { get; set; }

    // 4.7 Passthrough /////////////////////////////////////////////////////////////////////////////////////////////

    /// <summary>
    /// Everything this model does not bind - `tags`, `$schema`, and anything a future field group adds.
    ///
    /// `tags` in particular must round-trip untouched: 268 configs carry it and it moves to ICUP later. This is also
    /// what feeds the "did you mean" typo check, so unknown fields are surfaced rather than silently vanishing.
    /// </summary>
    [JsonExtensionData]
    public Dictionary<string, JsonElement> Extra { get; set; } = new();

    // Derived /////////////////////////////////////////////////////////////////////////////////////////////////////

    public bool IsClothing => Type is ContentItemType.Top or ContentItemType.Bottom;

    public bool IsGear => Type is ContentItemType.Gear;

    /// <summary>Gear sells wherever the original does unless the author says otherwise.</summary>
    public bool ShouldCopyOriginalOffers => CopyOriginalOffers ?? true;

    public bool ShouldAddToBots => AddToBots ?? true;

    public double EffectiveBotWeightMultiplier => BotWeightMultiplier ?? 1.0;

    public MongoId CurrencyTpl => (Currency ?? DripCurrency.RUB).ToTemplateId();
}

public class ContentItemTranslation
{
    [JsonPropertyName("name")] public string? Name { get; set; }

    [JsonPropertyName("shortName")] public string? ShortName { get; set; }

    [JsonPropertyName("description")] public string? Description { get; set; }
}
