using System.Reflection;
using DRIP.Utils;
using SPTarkov.DI.Annotations;
using SPTarkov.Server.Core.Models.Spt.Server;
using SPTarkov.Server.Core.Models.Utils;
using SPTarkov.Server.Core.Services;
using Path = System.IO.Path;

namespace DRIP.Services;

/// <summary>
/// Loads the text players actually read - quest names, descriptions and objectives.
///
/// One file per locale, named for its locale code: `en.json`, `ru.json`. English is the fallback for every locale
/// that has no file of its own, which is currently all sixteen of them.
/// </summary>
[Injectable(InjectionType.Singleton)]
public class DRIPCustomLocaleService(
    ISptLogger<DRIPCustomLocaleService> logger,
    DatabaseService databaseService,
    DRIPBundleService bundleService
)
{
    private const string FallbackLocale = "en";

    private DatabaseTables? _database;

    /// <summary>
    /// Loads locale files from one content pack.
    /// </summary>
    /// <param name="assembly">The calling assembly, used to determine the mod folder location</param>
    /// <param name="contentPackPath">
    /// Path to the content pack's CustomLocales directory, relative to the mod folder - already includes "bundles".
    /// </param>
    public Task CreateCustomLocales(Assembly assembly, string contentPackPath)
    {
        _database ??= databaseService.GetTables();

        var finalDir = bundleService.GetModPaths(assembly).Resolve(contentPackPath);
        if (!Directory.Exists(finalDir))
        {
            return Task.CompletedTask;
        }

        // Read every locale file up front. The transformers below run lazily, potentially long after this method has
        // returned, so they must close over data rather than over file paths.
        var byLocale = new Dictionary<string, Dictionary<string, string>>(StringComparer.OrdinalIgnoreCase);

        foreach (var file in DripFiles.EnumerateConfigFiles(finalDir))
        {
            var localeCode = Path.GetFileNameWithoutExtension(file);

            try
            {
                var entries = DripJson.DeserializeFile<Dictionary<string, string>>(file);
                if (entries is null || entries.Count == 0)
                {
                    logger.Warning($"[DRIP] Locale file {localeCode} is empty.");
                    continue;
                }

                byLocale[localeCode] = entries;
            }
            catch (Exception ex)
            {
                logger.Error($"[DRIP] Locale file {localeCode} could not be read: {ex.Message}");
            }
        }

        if (byLocale.Count == 0)
        {
            return Task.CompletedTask;
        }

        byLocale.TryGetValue(FallbackLocale, out var fallback);
        if (fallback is null)
        {
            logger.Warning(
                $"[DRIP] {contentPackPath}: no {FallbackLocale}.json, so locales with no file of their own will " +
                "show raw IDs in game.");
        }

        var localesTouched = 0;

        foreach (var (localeCode, lazyLocale) in _database.Locales.Global)
        {
            // Fall back to English rather than leaving a locale untouched: a Russian player seeing English quest
            // text is a far better outcome than seeing a raw MongoId.
            var entries = byLocale.GetValueOrDefault(localeCode) ?? fallback;
            if (entries is null)
            {
                continue;
            }

            lazyLocale.AddTransformer(localeData =>
            {
                foreach (var (key, value) in entries)
                {
                    localeData[key] = value;
                }

                return localeData;
            });

            localesTouched++;
        }

        var authored = string.Join(", ", byLocale.Keys.Order());
        logger.Info(
            $"[DRIP] {contentPackPath}: {fallback?.Count ?? 0} strings across {localesTouched} locales " +
            $"(authored: {authored}).");

        return Task.CompletedTask;
    }
}
