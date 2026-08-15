using System.Text.Json;
using System.Text.Json.Serialization;
using SPTarkov.Server.Core.Utils;

namespace DRIP.Utils;

/// <summary>
/// Reads DRIP's own Content Pack config files.
///
/// DRIP deliberately does not use <see cref="ModHelper.GetJsonDataFromFile{T}"/> for these. That helper uses the
/// server's shared serializer options, which are tuned for the server's own data files and are stricter than the
/// format DRIP content is authored in:
///
///   - No <c>AllowTrailingCommas</c>. Content is authored as .json5/.jsonc where a trailing comma is idiomatic;
///     279 of the 546 legacy Content Pack configs contain one. Every one of them throws under the server options.
///   - <c>JsonUnmappedMemberHandling.Disallow</c> in DEBUG builds, so on a debug server any config carrying a key we
///     have not modelled throws. 269 configs currently carry a "tags" key destined for ICUP.
///
/// The server's options are used as the base so that all of its registered converters (MongoId and friends) still
/// apply - only the reader strictness is relaxed.
/// </summary>
public static class DripJson
{
    private static JsonSerializerOptions? _options;
    private static JsonSerializerOptions? _sptTypeOptions;

    /// <summary>
    /// For DRIP's own config models. Forgiving: author-facing field names bind case-insensitively.
    /// </summary>
    public static JsonSerializerOptions Options => _options ??= Build(caseInsensitive: true);

    /// <summary>
    /// For binding raw config fragments onto SPT's own model types. Case-<b>sensitive</b>, deliberately.
    ///
    /// SPT's models mirror BSG's data, which ships pairs of fields that differ only by case - notably
    /// <c>TemplateItemProperties.ShotgunDispersion</c> and <c>TemplateItemProperties.shotgunDispersion</c>, both of
    /// which exist and mean different things. Case-insensitive matching does not merely risk picking the wrong one:
    /// System.Text.Json refuses to build metadata for such a type at all and throws
    /// "The JSON property name for '...shotgunDispersion' collides with another property."
    ///
    /// So case-insensitivity stops at the DRIP/BSG boundary. Our field names are forgiving because authors type
    /// them; BSG property names are exact because BSG chose them.
    /// </summary>
    public static JsonSerializerOptions SptTypeOptions => _sptTypeOptions ??= Build(caseInsensitive: false);

    private static JsonSerializerOptions Build(bool caseInsensitive)
    {
        var serverOptions = JsonUtil.JsonSerializerOptionsNoIndent
                            ?? throw new InvalidOperationException(
                                "JsonUtil has not been constructed yet, so its converters are unavailable. " +
                                "DripJson must only be used from OnLoad or later.");

        return new JsonSerializerOptions(serverOptions)
        {
            AllowTrailingCommas = true,
            ReadCommentHandling = JsonCommentHandling.Skip,
            UnmappedMemberHandling = JsonUnmappedMemberHandling.Skip,

            // Without this, a field whose casing doesn't match the model binds differently depending on how the
            // server was built: silently ignored in Release, throws in Debug (see UnmappedMemberHandling above).
            // Behaviour that varies by build configuration is worse than either failure on its own.
            PropertyNameCaseInsensitive = caseInsensitive
        };
    }

    /// <summary>
    /// Deserialise a Content Pack config file from its full path.
    /// </summary>
    public static T? DeserializeFile<T>(string fullPath)
    {
        return JsonSerializer.Deserialize<T>(File.ReadAllText(fullPath), Options);
    }

    /// <summary>
    /// Bind a raw fragment of an author's config onto one of SPT's model types. See <see cref="SptTypeOptions"/>
    /// for why this does not share the forgiving options.
    /// </summary>
    public static T? BindToSptType<T>(JsonElement element)
    {
        return element.Deserialize<T>(SptTypeOptions);
    }
}
