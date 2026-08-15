namespace DRIP.Utils;

/// <summary>
/// Parses author-written enum values without ever throwing.
///
/// Content configs never bind enums through JsonStringEnumConverter, because that converter throws on an
/// unrecognised value and takes the whole file down with it - the author gets a misleading "invalid JSON" error, the
/// validator never gets to suggest the right spelling, and [JsonExtensionData] is left unpopulated so no other
/// problem in the file can be reported either. A misspelled field must produce a message, never a failure that
/// hides the next nine.
/// </summary>
public static class EnumText
{
    /// <summary>
    /// Parse case-insensitively, tolerating surrounding whitespace. Returns null for absent, empty, or
    /// unrecognised input - the caller distinguishes those by looking at the raw text.
    /// </summary>
    public static T? Parse<T>(string? raw) where T : struct, Enum
    {
        if (string.IsNullOrWhiteSpace(raw))
        {
            return null;
        }

        // Reject numeric input: Enum.TryParse happily accepts "7" and yields an undefined value.
        var trimmed = raw.Trim();
        if (!char.IsLetter(trimmed[0]))
        {
            return null;
        }

        return Enum.TryParse<T>(trimmed, ignoreCase: true, out var parsed) && Enum.IsDefined(parsed)
            ? parsed
            : null;
    }
}
