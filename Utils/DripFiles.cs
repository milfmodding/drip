namespace DRIP.Utils;

public static class DripFiles
{
    private static readonly string[] ConfigExtensions = [".jsonc", ".json5", ".json"];

    /// <summary>
    /// Every content config under a directory, recursively.
    ///
    /// Matched on an explicit extension list rather than a "*.json*" glob, which would also sweep up any stray JSON
    /// that isn't a content config - a report, a manifest, an editor sidecar - and then fail to deserialise it.
    /// </summary>
    public static IEnumerable<string> EnumerateConfigFiles(string directory)
    {
        if (!Directory.Exists(directory))
        {
            return [];
        }

        return Directory
            .EnumerateFiles(directory, "*.*", SearchOption.AllDirectories)
            .Where(file => ConfigExtensions.Contains(Path.GetExtension(file), StringComparer.OrdinalIgnoreCase));
    }
}
