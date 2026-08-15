// DRIP.TexturePreview - a dev-only texture preview loop for DRIP's content authors.
//
// The problem (docs/HOT-RELOAD-DESIGN.md): editing a texture means rebuilding a bundle,
// redeploying, restarting the server and re-entering the raid - minutes per look at work
// that is inherently "look, nudge, look again". This plugin collapses that to: save a PNG
// into the watch folder, and it appears on whatever is on screen.
//
// It is PREVIEW-ONLY by construction: nothing here writes anywhere except its own folder
// (the toast log and the texture-names dump). The bundle rebuild stays the real artifact.
//
// Scoped matching (v2, Sophia's ruling): several DRIP items share texture names - three
// WINTERJACKET variants all ship Top_BOSS_Shturman_d - so matching by name alone recolours
// every variant at once. PNGs therefore live in subfolders naming the item, mirroring the
// bundle path: HotReload/WINTERJACKET/DRIP/Top_BOSS_Shturman_d.png hits only that
// jacket's bundle, and several variants can be edited side by side. A PNG in the folder
// root keeps name-only, all-bundles behaviour - the quick-test case.
//
// How scope is known (measured, 2026-08-15): Unity gives no back-reference from a loaded
// Texture2D to the bundle it came from, and SPT's client BundleManager.Bundles holds only
// manifest metadata (BundleItem: filename/CRC/deps), not AssetBundle instances. So the
// plugin records paths itself - Harmony postfixes on AssetBundle.LoadFromFile/Async
// capture (bundle, path) at load time, engine API, no game internals - and maps textures
// to owning bundles via each bundle's GetAllAssetNames(). If that map comes up empty
// (stripped API, bundles loaded before the plugin), scoped applies say so in the toast
// and fall back to reporting, never to silently global-applying.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using BepInEx;
using BepInEx.Configuration;
using BepInEx.Logging;
using HarmonyLib;
using UnityEngine;

namespace DRIP.TexturePreview
{
    [BepInPlugin(PluginGuid, PluginName, PluginVersion)]
    public class TexturePreviewPlugin : BaseUnityPlugin
    {
        public const string PluginGuid = "gov.milfmodding.drip.texturepreview";
        public const string PluginName = "DRIP.TexturePreview";
        public const string PluginVersion = "0.2.0";

        private ConfigEntry<string> _folder;

        // Watcher thread -> main thread: Unity objects are main-thread-only, and a
        // FileSystemWatcher event is emphatically not the main thread.
        private readonly ConcurrentQueue<string> _pending = new();

        private FileSystemWatcher _watcher;
        private string _toast;
        private float _toastUntil;
        private ManualLogSource _log;

        // Editors sometimes save twice in quick succession (write-then-rename); coalescing
        // events inside this window avoids a double load and a doubled toast.
        private const float DebounceSeconds = 0.2f;
        private readonly Dictionary<string, float> _lastSeen = new();
        private float _now;

        // Texture -> on-disk path of the bundle it came from. Rebuilt lazily: whenever a
        // new async bundle load completes, or on Apply-all (F8). Building it walks every
        // loaded bundle's asset list, which is fine at apply time and too much per frame.
        private Dictionary<Texture2D, string> _texToBundle;
        private int _mapGeneration = -1;

        private void Awake()
        {
            _log = Logger;
            _folder = Config.Bind("General", "Watch folder", "",
                "Where PNGs are dropped. Empty = BepInEx/plugins/DRIP.TexturePreview/HotReload. " +
                "A PNG in a SUBFOLDER applies only to bundles whose path contains the subfolder " +
                "(e.g. HotReload/WINTERJACKET/DRIP/x.png - the item's folder from the bundle path). " +
                "A PNG in the root applies to every loaded texture with that name.");
            Config.Bind("Keys", "Apply all", new KeyboardShortcut(KeyCode.F8),
                "Re-apply every PNG in the watch folder. Use after loading an item that was " +
                "not on screen when you saved.");
            Config.Bind("Keys", "Dump texture names", new KeyboardShortcut(KeyCode.F9),
                "Write texture-names.txt beside the watch folder: every loaded texture's " +
                "name, size and source bundle path, so nobody has to ask what an asset is " +
                "called or where it lives.");

            BundlePaths.Install(_log);
        }

        private void Start()
        {
            var folder = ResolveFolder();
            Directory.CreateDirectory(folder);
            _watcher = new FileSystemWatcher(folder, "*.png")
            {
                // Editors commonly save via write-temp-then-rename; renamed events catch
                // that where plain Created/Changed miss it. Subdirectories carry the scope.
                NotifyFilter = NotifyFilters.LastWrite | NotifyFilters.FileName,
                IncludeSubdirectories = true,
                EnableRaisingEvents = true,
            };
            _watcher.Created += (_, e) => _pending.Enqueue(e.FullPath);
            _watcher.Changed += (_, e) => _pending.Enqueue(e.FullPath);
            _watcher.Renamed += (_, e) => _pending.Enqueue(e.FullPath);
            _log.LogInfo($"watching {folder} - drop PNGs named after texture assets; " +
                         "subfolders scope to an item's bundle path");
        }

        private string ResolveFolder()
        {
            var configured = _folder.Value;
            if (!string.IsNullOrWhiteSpace(configured))
            {
                return configured;
            }

            var here = Path.GetDirectoryName(Info.Location)
                       ?? Path.Combine(Paths.PluginPath, PluginName);
            return Path.Combine(here, "HotReload");
        }

        private void Update()
        {
            _now = Time.unscaledTime;

            // Async bundle loads complete out of band; harvest finished ones so the map (and
            // its Generation) reflect them before any apply this frame uses it.
            BundlePaths.Harvest();

            DrainQueue();

            if (KeyPressed("Apply all"))
            {
                ApplyEverythingInFolder();
            }

            if (KeyPressed("Dump texture names"))
            {
                DumpTextureNames();
            }
        }

        private bool KeyPressed(string keyName)
        {
            var entry = (ConfigEntry<KeyboardShortcut>)Config["Keys", keyName];
            return entry.Value.IsDown();
        }

        private void DrainQueue()
        {
            var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            while (_pending.TryDequeue(out var path))
            {
                if (!seen.Add(path))
                {
                    continue; // one apply per file per frame, however many events arrived
                }

                if (_now - (_lastSeen.TryGetValue(path, out var t) ? t : float.MinValue) < DebounceSeconds)
                {
                    continue;
                }

                _lastSeen[path] = _now;
                ApplyOne(path);
            }
        }

        private void ApplyOne(string fullPath)
        {
            byte[] bytes;
            try
            {
                // The editor may still hold the file open; a brief failure is normal and
                // the watcher fires again when the write completes.
                bytes = File.ReadAllBytes(fullPath);
            }
            catch (IOException)
            {
                return;
            }

            var root = ResolveFolder();
            var name = Path.GetFileNameWithoutExtension(fullPath);
            var scope = ScopeOf(root, fullPath);

            var changed = Apply(name, bytes, scope);

            if (changed > 0)
            {
                Toast(scope.Length == 0
                    ? $"{name}: {changed} texture(s) updated (all bundles)"
                    : $"{scope}/{name}: {changed} texture(s) updated");
            }
            else if (scope.Length == 0)
            {
                Toast($"{name}: no loaded texture with that name - is the item on screen? " +
                      "(name-dump key lists what is loaded)");
            }
            else
            {
                Toast($"{scope}/{name}: no texture with that name in a bundle matching " +
                      $"'{scope}' - check the folder name against the name-dump's bundle paths");
            }
        }

        private void ApplyEverythingInFolder()
        {
            var root = ResolveFolder();
            var applied = 0;
            var missing = 0;

            foreach (var file in Directory.Exists(root)
                         ? Directory.EnumerateFiles(root, "*.png", SearchOption.AllDirectories)
                         : Enumerable.Empty<string>())
            {
                byte[] bytes;
                try
                {
                    bytes = File.ReadAllBytes(file);
                }
                catch (IOException)
                {
                    continue;
                }

                if (Apply(Path.GetFileNameWithoutExtension(file), bytes, ScopeOf(root, file)) > 0)
                {
                    applied++;
                }
                else
                {
                    missing++;
                }
            }

            Toast(applied + missing == 0
                ? "Apply all: the watch folder has no PNGs"
                : $"Apply all: {applied} applied, {missing} with no matching loaded texture");
        }

        /// <summary>The scope a PNG's subfolder path names, relative to the watch root,
        /// "/"-separated and lowercased for matching. Empty = the folder root = all bundles.</summary>
        private static string ScopeOf(string root, string fullPath)
        {
            var dir = Path.GetDirectoryName(fullPath)!;
            if (!dir.StartsWith(root, StringComparison.OrdinalIgnoreCase))
            {
                return "";
            }

            var rel = dir.Substring(root.Length).TrimStart('\\', '/');
            return rel.Replace('\\', '/').ToLowerInvariant();
        }

        /// <summary>
        /// Applies PNG bytes to the loaded textures they name. Scoped (subfolder) applies
        /// only touch textures whose source bundle path contains the scope; root applies
        /// touch every loaded texture with the name. Returns how many changed.
        /// </summary>
        private int Apply(string name, byte[] bytes, string scope)
        {
            var changed = 0;

            if (scope.Length == 0)
            {
                foreach (var tex in Resources.FindObjectsOfTypeAll<Texture2D>())
                {
                    if (string.Equals(tex.name, name, StringComparison.OrdinalIgnoreCase))
                    {
                        tex.LoadImage(bytes);
                        changed++;
                    }
                }

                return changed;
            }

            var map = TextureBundleMap();
            foreach (var entry in map)
            {
                var tex = entry.Key;
                var bundlePath = entry.Value;
                if (!string.Equals(tex.name, name, StringComparison.OrdinalIgnoreCase))
                {
                    continue;
                }

                if (bundlePath != null && Normalise(bundlePath).Contains(scope))
                {
                    tex.LoadImage(bytes);
                    changed++;
                }
            }

            return changed;
        }

        private static string Normalise(string path)
        {
            return path.Replace('\\', '/').ToLowerInvariant();
        }

        /// <summary>
        /// Texture -> bundle path, over bundles this session loaded from file. Bundles that
        /// predate the plugin (or loaded from memory) map to null and are skipped by scoped
        /// applies - stated in the toast, not hidden.
        /// </summary>
        private Dictionary<Texture2D, string> TextureBundleMap()
        {
            var generation = BundlePaths.Generation;
            if (_texToBundle != null && generation == _mapGeneration)
            {
                return _texToBundle;
            }

            var map = new Dictionary<Texture2D, string>();
            foreach (var bundle in Resources.FindObjectsOfTypeAll<AssetBundle>())
            {
                if (!BundlePaths.PathOf(bundle, out var path))
                {
                    continue;
                }

                string[] assetNames;
                try
                {
                    assetNames = bundle.GetAllAssetNames();
                }
                catch (Exception e)
                {
                    _log.LogWarning($"GetAllAssetNames failed on {path}: {e.Message} - " +
                                    "its textures are unavailable to scoped applies");
                    continue;
                }

                foreach (var assetName in assetNames)
                {
                    if (!assetName.EndsWith(".png", StringComparison.OrdinalIgnoreCase))
                    {
                        continue;
                    }

                    Texture2D tex = null;
                    try
                    {
                        tex = bundle.LoadAsset<Texture2D>(assetName);
                    }
                    catch
                    {
                        // A non-texture asset named *.png, or an unloadable one: skip it.
                    }

                    if (tex != null)
                    {
                        map[tex] = path;
                    }
                }
            }

            _texToBundle = map;
            _mapGeneration = generation;
            _log.LogInfo($"texture->bundle map rebuilt: {map.Count} textures from " +
                         $"{BundlePaths.Count} pathed bundles");
            return map;
        }

        /// <summary>
        /// Writes every loaded texture's name, size and source bundle beside the watch
        /// folder, so an author can find what an asset is called - and which subfolder
        /// scopes it - without asking a programmer.
        /// </summary>
        private void DumpTextureNames()
        {
            var root = ResolveFolder();
            var path = Path.Combine(Path.GetDirectoryName(root) ?? root, "texture-names.txt");

            var map = TextureBundleMap();
            var lines = Resources.FindObjectsOfTypeAll<Texture2D>()
                .OrderBy(t => t.name, StringComparer.OrdinalIgnoreCase)
                .Select(t => map.TryGetValue(t, out var bundle) && bundle != null
                    ? $"{t.name}  {t.width}x{t.height}  {bundle}"
                    : $"{t.name}  {t.width}x{t.height}")
                .ToList();

            File.WriteAllLines(path, lines);
            Toast($"Wrote {lines.Count} texture names to {path}");
        }

        private void Toast(string message)
        {
            _toast = message;
            _toastUntil = Time.unscaledTime + 5f;
            _log.LogInfo(message);
        }

        private void OnGUI()
        {
            if (string.IsNullOrEmpty(_toast) || Time.unscaledTime > _toastUntil)
            {
                return;
            }

            // Plain but legible: a black box bottom-centre. This is a dev tool; the bar is
            // "readable over any scene", not styled.
            const int width = 680;
            const int height = 46;
            var area = new Rect((Screen.width - width) / 2, Screen.height - height - 90, width, height);
            var previous = GUI.color;
            GUI.color = new Color(0f, 0f, 0f, 0.82f);
            GUI.Box(area, GUIContent.none);
            GUI.color = previous;
            GUI.Label(new Rect(area.x + 10, area.y + 6, area.width - 20, area.height - 12),
                _toast, new GUIStyle(GUI.skin.label) { alignment = TextAnchor.MiddleCenter });
        }

        private void OnDestroy()
        {
            _watcher?.Dispose();
        }
    }

    /// <summary>
    /// Records which on-disk path each AssetBundle loaded from, via Harmony postfixes on
    /// the engine's own load calls. SPT's client BundleManager tracks only manifest
    /// metadata (measured: Bundles is BundleItem - filename/CRC/deps), and Unity offers no
    /// bundle back-reference on a texture, so this is the one place the information exists.
    /// </summary>
    /// <remarks>
    /// Async loads hand over an AssetBundleCreateRequest; the bundle inside it is not ready
    /// at postfix time, so requests are parked and harvested on the main thread later -
    /// which is also what bumps <see cref="Generation"/> and invalidates consumers' caches.
    /// </remarks>
    [HarmonyPatch]
    internal static class BundlePaths
    {
        private static readonly Dictionary<AssetBundle, string> Paths = new();
        private static readonly List<AssetBundleCreateRequest> Pending = new();
        private static ManualLogSource _log;
        private static int _generation;

        /// <summary>Bumped whenever a new (bundle, path) pair becomes known, so caches
        /// built over the map know to rebuild.</summary>
        public static int Generation => _generation;

        public static int Count => Paths.Count;

        public static void Install(ManualLogSource log)
        {
            _log = log;
            new Harmony(TexturePreviewPlugin.PluginGuid).PatchAll(typeof(BundlePaths));
        }

        public static bool PathOf(AssetBundle bundle, out string path)
        {
            lock (Paths)
            {
                return Paths.TryGetValue(bundle, out path);
            }
        }

        /// <summary>Move completed async loads into the map. Main thread only.</summary>
        public static void Harvest()
        {
            lock (Pending)
            {
                for (var i = Pending.Count - 1; i >= 0; i--)
                {
                    var request = Pending[i];
                    if (!request.isDone || request.assetBundle == null)
                    {
                        continue;
                    }

                    Record(request.assetBundle, _pathByRequest[request]);
                    _pathByRequest.Remove(request);
                    Pending.RemoveAt(i);
                }
            }
        }

        private static readonly Dictionary<AssetBundleCreateRequest, string> _pathByRequest = new();

        private static void Record(AssetBundle bundle, string path)
        {
            if (bundle == null || string.IsNullOrEmpty(path))
            {
                return;
            }

            lock (Paths)
            {
                if (Paths.ContainsKey(bundle))
                {
                    return;
                }

                Paths[bundle] = Path.GetFullPath(path);
            }

            _generation++;
            _log?.LogInfo($"tracking bundle {Paths.Count}: {path}");
        }

        [HarmonyPostfix]
        [HarmonyPatch(typeof(AssetBundle), nameof(AssetBundle.LoadFromFile), new[] { typeof(string) })]
        [HarmonyPatch(typeof(AssetBundle), nameof(AssetBundle.LoadFromFile), new[] { typeof(string), typeof(uint) })]
        [HarmonyPatch(typeof(AssetBundle), nameof(AssetBundle.LoadFromFile),
            new[] { typeof(string), typeof(uint), typeof(ulong) })]
        private static void AfterLoadFromFile(AssetBundle __result, string path)
        {
            Record(__result, path);
        }

        [HarmonyPostfix]
        [HarmonyPatch(typeof(AssetBundle), nameof(AssetBundle.LoadFromFileAsync), new[] { typeof(string) })]
        [HarmonyPatch(typeof(AssetBundle), nameof(AssetBundle.LoadFromFileAsync), new[] { typeof(string), typeof(uint) })]
        [HarmonyPatch(typeof(AssetBundle), nameof(AssetBundle.LoadFromFileAsync),
            new[] { typeof(string), typeof(uint), typeof(ulong) })]
        private static void AfterLoadFromFileAsync(AssetBundleCreateRequest __result, string path)
        {
            if (__result == null)
            {
                return;
            }

            lock (Pending)
            {
                Pending.Add(__result);
                _pathByRequest[__result] = path;
            }
        }
    }
}
