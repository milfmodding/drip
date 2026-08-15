// DRIP.TexturePreview - a dev-only texture preview loop for DRIP's content authors.
//
// The problem (docs/HOT-RELOAD-DESIGN.md): editing a texture means rebuilding a bundle,
// redeploying, restarting the server and re-entering the raid - minutes per look at work
// that is inherently "look, nudge, look again". This plugin collapses that to: save a PNG
// into the watch folder, and it appears on whatever is on screen.
//
// It is PREVIEW-ONLY by construction: nothing here writes anywhere except its own folder
// (the toast log and the texture-names dump). The bundle rebuild stays the real artifact.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using BepInEx;
using BepInEx.Configuration;
using UnityEngine;

namespace DRIP.TexturePreview
{
    [BepInPlugin(PluginGuid, PluginName, PluginVersion)]
    public class TexturePreviewPlugin : BaseUnityPlugin
    {
        public const string PluginGuid = "gov.milfmodding.drip.texturepreview";
        public const string PluginName = "DRIP.TexturePreview";
        public const string PluginVersion = "0.1.0";

        // Where the watch folder and the texture-names dump live. Default sits under this
        // plugin's own folder so everything the tool touches is in one place; settable in
        // ConfigurationManager (F7 in game) if someone prefers another location.
        private ConfigEntry<string> _folder;

        // The watcher thread hands file paths to the main thread through this queue:
        // Unity objects may only be touched from the main thread, and a FileSystemWatcher
        // event is emphatically not the main thread.
        private readonly ConcurrentQueue<string> _pending = new();

        private FileSystemWatcher _watcher;
        private string _toast;
        private float _toastUntil;

        // Editor windows sometimes save twice in quick succession (write-then-rename);
        // coalescing events inside this window avoids a double load and a doubled toast.
        private const float DebounceSeconds = 0.2f;
        private readonly Dictionary<string, float> _lastSeen = new();
        private float _now;

        private void Awake()
        {
            _folder = Config.Bind("General", "Watch folder", "",
                "Where PNGs are dropped. Empty = BepInEx/plugins/DRIP.TexturePreview/HotReload. " +
                "Name each PNG after the texture asset it replaces (press the name-dump key to " +
                "list them). Applies to every loaded texture with that name.");
            Config.Bind("Keys", "Apply all", new KeyboardShortcut(KeyCode.F8),
                "Re-apply every PNG in the watch folder. Use after loading an item that was " +
                "not on screen when you saved.");
            Config.Bind("Keys", "Dump texture names", new KeyboardShortcut(KeyCode.F9),
                "Write texture-names.txt into the watch folder: every loaded texture's name " +
                "and size, so nobody has to ask what an asset is called.");
        }

        private void Start()
        {
            var folder = ResolveFolder();
            Directory.CreateDirectory(folder);
            EnsureWatchers(folder);
            Debug.Log($"[{PluginName}] watching {folder} - drop a PNG named after a texture asset");
        }

        private string ResolveFolder()
        {
            var configured = _folder.Value;
            if (!string.IsNullOrWhiteSpace(configured))
            {
                return configured;
            }

            // BepInEx 5 hands plugin instances their own directory - the cleanest anchor
            // for a sibling HotReload folder. The fallback covers unusual setups.
            var here = Path.GetDirectoryName(Info.Location)
                       ?? Path.Combine(Paths.PluginPath, PluginName);
            return Path.Combine(here, "HotReload");
        }

        private void EnsureWatchers(string folder)
        {
            _watcher = new FileSystemWatcher(folder, "*.png")
            {
                // Editors commonly save via write-temp-then-rename; renamed events catch
                // that where plain Created/Changed miss it.
                NotifyFilter = NotifyFilters.LastWrite | NotifyFilters.FileName,
                IncludeSubdirectories = false,
                EnableRaisingEvents = true,
            };
            _watcher.Created += (_, e) => Enqueue(e.FullPath);
            _watcher.Changed += (_, e) => Enqueue(e.FullPath);
            _watcher.Renamed += (_, e) => Enqueue(e.FullPath);
        }

        private void Enqueue(string path)
        {
            _pending.Enqueue(path);
        }

        private void Update()
        {
            _now = Time.unscaledTime;

            DrainQueue();

            if (WasKeyPressed("Apply all"))
            {
                ApplyEverythingInFolder();
            }

            if (WasKeyPressed("Dump texture names"))
            {
                DumpTextureNames();
            }
        }

        // ConfigEntry<KeyboardShortcut>.Value.IsDown exists on newer BepInEx builds; this
        // reads the same entry without assuming it, so the plugin survives BepInEx minor
        // version drift (the survey pinned 5.4.23, but installs drift).
        private bool WasKeyPressed(string keyName)
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

                if (_now - GetLastSeen(path) < DebounceSeconds)
                {
                    continue;
                }

                _lastSeen[path] = _now;
                ApplyOne(path);
            }
        }

        private float GetLastSeen(string path)
        {
            return _lastSeen.TryGetValue(path, out var t) ? t : float.MinValue;
        }

        private void ApplyOne(string path)
        {
            byte[] bytes;
            try
            {
                // The editor may still hold the file open; a brief failure is normal and
                // the watcher will fire again when the write completes.
                bytes = File.ReadAllBytes(path);
            }
            catch (IOException)
            {
                return;
            }

            // The texture's asset name is the PNG's filename without extension.
            var name = Path.GetFileNameWithoutExtension(path);
            var changed = ApplyToLoadedTextures(name, bytes);

            if (changed > 0)
            {
                Toast($"{name}: {changed} texture(s) updated");
            }
            else
            {
                // The single most likely confusion: the file saved fine but nothing with
                // that name is loaded. Name the cause rather than letting it read as a no-op.
                Toast($"{name}: no loaded texture with that name - is the item on screen? (name-dump key lists what is loaded)");
            }
        }

        private void ApplyEverythingInFolder()
        {
            var folder = ResolveFolder();
            var applied = 0;
            var missing = 0;

            foreach (var file in Directory.Exists(folder)
                         ? Directory.EnumerateFiles(folder, "*.png")
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

                var name = Path.GetFileNameWithoutExtension(file);
                if (ApplyToLoadedTextures(name, bytes) > 0)
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
                : $"Apply all: {applied} applied, {missing} with no loaded texture");
        }

        /// <summary>
        /// Loads <paramref name="bytes"/> into every loaded Texture2D whose name matches.
        /// Returns how many changed.
        /// </summary>
        /// <remarks>
        /// "Every" is load-bearing, not a compromise: several DRIP items share one texture
        /// name (three WINTERJACKET variants all ship Top_BOSS_Shturman_d), so there is no
        /// single correct target - and for a PREVIEW tool, recolouring each loaded copy of
        /// the name is visible, harmless and reversible. Scoped-per-bundle matching is the
        /// v2 idea if the sharing ever annoys in practice (design doc, "The collision").
        /// </remarks>
        private static int ApplyToLoadedTextures(string name, byte[] bytes)
        {
            var changed = 0;
            // FindObjectsOfTypeAll reaches textures with no scene presence - exactly what
            // bundle-loaded Texture2Ds are.
            foreach (var tex in Resources.FindObjectsOfTypeAll<Texture2D>())
            {
                if (!string.Equals(tex.name, name, StringComparison.OrdinalIgnoreCase))
                {
                    continue;
                }

                // LoadImage replaces the texture's pixels from PNG/JPEG bytes. Mipmaps:
                // the new data may carry fewer mips than the original, which can shimmer
                // slightly at distance - a preview-fidelity note, recorded in the design
                // doc, not worth blocking the loop over.
                tex.LoadImage(bytes);
                changed++;
            }

            return changed;
        }

        /// <summary>
        /// Writes every loaded texture's name and size next to the watch folder, so an
        /// author can find what an asset is called without asking a programmer. This is
        /// the piece that makes the whole tool usable alone.
        /// </summary>
        private void DumpTextureNames()
        {
            var folder = ResolveFolder();
            var path = Path.Combine(Path.GetDirectoryName(folder) ?? folder, "texture-names.txt");

            var lines = Resources.FindObjectsOfTypeAll<Texture2D>()
                .OrderBy(t => t.name, StringComparer.OrdinalIgnoreCase)
                .Select(t => $"{t.name}  {t.width}x{t.height}")
                .ToList();

            File.WriteAllLines(path, lines);
            Toast($"Wrote {lines.Count} texture names to {path}");
        }

        private void Toast(string message)
        {
            _toast = message;
            _toastUntil = Time.unscaledTime + 5f;
            Debug.Log($"[{PluginName}] {message}");
        }

        private void OnGUI()
        {
            if (string.IsNullOrEmpty(_toast) || Time.unscaledTime > _toastUntil)
            {
                return;
            }

            // Plain but legible: a black box bottom-centre. This is a dev tool; the bar is
            // "readable over any scene", not styled.
            const int width = 620;
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
}
