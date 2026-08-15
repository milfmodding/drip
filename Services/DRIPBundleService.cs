using System.Reflection;
using SPTarkov.DI.Annotations;
using SPTarkov.Server.Core.Helpers.Server;
using SPTarkov.Server.Core.Loaders;
using SPTarkov.Server.Core.Models.Spt.Bundles;
using SPTarkov.Server.Core.Services.Server;
using Path = System.IO.Path;

namespace DRIP.Services;

/// <summary>
/// Registers the .bundle files that sit alongside a content config.
///
/// DRIP assembles itself at startup rather than shipping a bundles.json manifest, so that adding an item is a matter
/// of dropping a folder in rather than editing a central file. Bundles are therefore discovered by co-location:
/// every .bundle in the same directory as a config belongs to that config.
///
/// Shared by the item and clothing loaders so the two cannot drift apart on dependency defaults or key derivation.
/// </summary>
[Injectable(InjectionType.Singleton)]
public class DRIPBundleService(
    BundleHashCacheService bundleHashCacheService,
    BundleLoader bundleLoader,
    ModHelper modHelper
)
{
    /// <summary>
    /// Applied to every bundle automatically. No DRIP bundle has ever shipped without them, so making authors
    /// declare them would be pure ceremony.
    /// </summary>
    private static readonly string[] DefaultDependencies =
    [
        "shaders",
        "cubemaps",
        "assets/commonassets/physics/physicsmaterials.bundle"
    ];

    /// <summary>
    /// Where the mod lives, in the three forms the loaders need: on disk for enumeration, and relative to the
    /// server's working directory for the bundle loader, which wants both the mod path and the key.
    /// </summary>
    public record ModPaths(string AbsoluteModPath, string ModPath, string ModBundlePath)
    {
        /// <summary>Absolute path to a content pack subdirectory given its mod-relative path.</summary>
        public string Resolve(string modRelativePath)
        {
            return Path.Combine(AbsoluteModPath, modRelativePath);
        }
    }

    public ModPaths GetModPaths(Assembly assembly)
    {
        var assemblyLocation = modHelper.GetAbsolutePathToModFolder(assembly);
        var serverDir = Directory.GetCurrentDirectory();
        var modPath = Path.GetRelativePath(serverDir, assemblyLocation).Replace("\\", "/");
        var modBundlePath = Path.Join(modPath, "bundles").Replace("\\", "/");

        return new ModPaths(assemblyLocation, modPath, modBundlePath);
    }

    /// <summary>
    /// Registers every bundle sitting next to <paramref name="configFile"/>.
    /// </summary>
    /// <param name="extraDependencies">
    /// The config's optional `bundles` block - extra dependency keys per bundle filename, beyond the defaults.
    /// </param>
    /// <returns>Bundle filename (e.g. "TOP.bundle") to the key the game will ask for it by.</returns>
    public async Task<Dictionary<string, string>> RegisterBundlesNextTo(
        FileInfo configFile,
        Dictionary<string, List<string>>? extraDependencies,
        ModPaths paths)
    {
        var registered = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        var configDirectory = configFile.Directory!.FullName;

        foreach (var bundleFile in Directory.EnumerateFiles(configDirectory, "*.bundle"))
        {
            var fullBundleFile = new FileInfo(bundleFile);
            var bundleKey = Path.GetRelativePath(paths.ModBundlePath, fullBundleFile.FullName).Replace("\\", "/");
            var bundleLocalPath = Path.Join(paths.ModBundlePath, bundleKey).Replace("\\", "/");
            // 4.1: hash is async and takes a token; bundle registration carries none, so None here means
            // "not cancellable", same as the 4.0 synchronous call it replaces.
            var bundleHash = await bundleHashCacheService.CalculateMatchAndStoreHashAsync(
                bundleLocalPath, CancellationToken.None);

            var dependencies = new List<string>(DefaultDependencies);
            if (extraDependencies is not null && extraDependencies.TryGetValue(fullBundleFile.Name, out var extra))
            {
                dependencies = [.. dependencies.Concat(extra).Distinct()];
            }

            // 4.1: BundleInfo has no constructor - populate its properties instead.
            bundleLoader.AddBundle(bundleKey, new BundleInfo
            {
                ModPath = paths.ModPath,
                Crc = bundleHash,
                Bundle = new BundleManifestEntry
                {
                    Key = bundleKey,
                    DependencyKeys = dependencies,
                },
            });

            registered[fullBundleFile.Name] = bundleKey;
        }

        NoteIfSiblingsAreUndeclared(configFile, registered, extraDependencies, paths);

        return registered;
    }

    /// <summary>
    /// A content directory holding more than one bundle where no config declares a dependency between them.
    /// </summary>
    public record UndeclaredSiblings(string Directory, string PrimaryBundle, IReadOnlyList<string> SiblingKeys);

    private readonly Dictionary<string, UndeclaredSiblings> _undeclared = new(StringComparer.OrdinalIgnoreCase);

    private readonly HashSet<string> _declared = new(StringComparer.OrdinalIgnoreCase);

    /// <summary>Directories whose sibling bundles nothing depends on, for the verification pass.</summary>
    public IReadOnlyCollection<UndeclaredSiblings> Undeclared => _undeclared.Values;

    /// <summary>
    /// Records a directory holding several bundles that declares no dependency between them.
    /// </summary>
    /// <remarks>
    /// Caught: four half-masks rendering magenta and two helmets rendering white, all six shipping a model bundle
    /// whose material lives in a sibling that the client was never told to load. DRIP *registers* every bundle beside
    /// a config but only *depends* on the ones a `bundles` block names, so the sibling exists, is served on request,
    /// and is never requested.
    ///
    /// Measured across the pack on 2026-07-31: 88 directories hold more than one bundle and 86 already declare a
    /// dependency. That 86 is the argument for this check - it stays silent on the overwhelming majority of real
    /// content and fired on exactly the six that were broken. The 188 single-bundle directories cannot reach it.
    ///
    /// Recorded here rather than swept from disk later because this method is already standing in the directory with
    /// the config's `bundles` block in hand, so it cannot disagree with what was actually registered.
    ///
    /// Two things this deliberately does NOT do, both learned the expensive way:
    ///
    ///   * It does not say "add a bundles block". On a half-mask that is the whole fix; on the two helmets it was
    ///     necessary and changed nothing until an externals entry inside the bundle binary was repointed. A message
    ///     promising a fix would have sent the next person round the same evening. Hence the second clause.
    ///   * It does not open the bundles. Whether anything actually points at the sibling is the better question and
    ///     the server cannot answer it - it registers keys and never reads the files. That check needs UnityPy and
    ///     lives in tools/bundles/ instead.
    ///
    /// It should flag nothing on a healthy tree. **That is the success condition, not evidence it is dead weight.**
    /// </remarks>
    private void NoteIfSiblingsAreUndeclared(
        FileInfo configFile,
        Dictionary<string, string> registered,
        Dictionary<string, List<string>>? extraDependencies,
        ModPaths paths)
    {
        if (registered.Count < 2)
        {
            return;
        }

        var directory = configFile.Directory!.FullName;
        var relative = Path.GetRelativePath(paths.ModBundlePath, directory).Replace("\\", "/");

        // Several configs can share a directory and any one of them declaring the dependency is enough. Tracking the
        // declared set separately rather than just removing makes that order-independent: a directory whose
        // declaring config happens to load second would otherwise be recorded and never cleared.
        if (extraDependencies is { Count: > 0 })
        {
            _declared.Add(relative);
            _undeclared.Remove(relative);
            return;
        }

        if (_declared.Contains(relative))
        {
            return;
        }

        // The model bundle is the one an item points at; the rest are the siblings it would need to depend on.
        var primary = registered.Keys.FirstOrDefault(name => name.Contains("GEAR", StringComparison.OrdinalIgnoreCase))
                      ?? registered.Keys.First();

        _undeclared[relative] = new UndeclaredSiblings(
            relative,
            primary,
            registered.Where(entry => entry.Key != primary).Select(entry => entry.Value).ToList());
    }

    /// <summary>
    /// Describes a set of configs whose model bundle is absent, as one message rather than one per config.
    ///
    /// A couple of these is a content bug and reads like one - the files are named. Nearly all of them is an
    /// un-bootstrapped checkout, which is an expected state for a developer and should say so instead of scrolling
    /// the same line past hundreds of times.
    /// </summary>
    /// <returns>
    /// Whether this looks like an un-bootstrapped checkout (report as a warning) rather than a content bug (report
    /// as an error), and the message to log.
    /// </returns>
    public static (bool IsUnbootstrappedCheckout, string Message) DescribeMissingBundles(
        List<string> missing,
        int totalConfigs,
        string expectedBundleName)
    {
        const int NamesToShow = 5;

        // "Nearly all" rather than "all", because a handful of bundles committed before the git policy changed would
        // otherwise mask this for everyone who clones the repo.
        if (totalConfigs > 0 && missing.Count >= totalConfigs * 0.9)
        {
            return (true,
                $"{missing.Count} of {totalConfigs} have no bundle, so almost nothing here can load. That normally " +
                "means bundles haven't been fetched - they aren't kept in git. See docs/AUTHORING.md for how to " +
                "populate them.");
        }

        var named = string.Join(", ", missing.Take(NamesToShow));
        var andMore = missing.Count > NamesToShow ? $", and {missing.Count - NamesToShow} more" : string.Empty;

        return (false, $"{missing.Count} are missing their {expectedBundleName}: {named}{andMore}.");
    }

    /// <summary>
    /// Names a `bundles` entry that doesn't correspond to a file on disk. Almost always a typo, and silently does
    /// nothing, so it is worth saying out loud.
    /// </summary>
    public static IEnumerable<string> FindDeclaredButMissing(
        Dictionary<string, List<string>>? extraDependencies,
        Dictionary<string, string> registered)
    {
        return extraDependencies is null
            ? []
            : extraDependencies.Keys.Where(name => !registered.ContainsKey(name));
    }
}
