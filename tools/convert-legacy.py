#!/usr/bin/env python3
"""
Convert legacy DRIP 3.x content packs (.json5) to schema v2 (.jsonc).

    python convert-legacy.py --part 1 --out ..\\bundles\\ContentPacks\\Essentials

The conversion is mechanical and re-runnable: it never edits the source tree, and running it
twice over the same input produces the same output. Bundles can be hard-linked (instant, no
extra disk) rather than copied.

See docs/CONFIG-SCHEMA-v2.md for what each transformation is doing and why.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import pathlib
import re
import shutil
import sys

# --------------------------------------------------------------------------------------------
# Constants drawn from the legacy loader (collection.ts) and the corpus survey.
# --------------------------------------------------------------------------------------------

LEGACY_ROOT = pathlib.Path(r"F:\SPT\Mods\DRIP-3.x-main\ContentPacks")

PARTS = {
    "1": "DRIP Part 1 (Essentials)",
    "2": "DRIP Part 2",
    "3": "DRIP Part 3",
}

# Applied to every bundle automatically by the v2 loader, so they never need declaring.
DEFAULT_BUNDLE_DEPS = {
    "shaders",
    "cubemaps",
    "assets/commonassets/physics/physicsmaterials.bundle",
}

# Legacy dependency field -> the bundle filename it actually described.
DEP_FIELD_TO_BUNDLE = {
    "gearDependencies": "GEAR.bundle",
    "topDependencies": "TOP.bundle",
    "handsDependencies": "HANDS.bundle",
    "bottomDependencies": "BOTTOM.bundle",
}

TYPE_MAP = {"TOP": "top", "BOTTOM": "bottom", "RETEXTURE": "gear", "CUSTOM": "gear"}

# Raw trader IDs that have a friendly name in v2.
# Values taken from SPTarkov.Server.Core.Models.Enums.Traders — do not hand-write these.
# Note 579dc571d53a0658a154fbec is FENCE, not Ragman; 28 legacy configs use it.
TRADER_NAMES = {
    "54cb50c76803fa8b248b4571": "prapor",
    "54cb57776803fa99248b456e": "therapist",
    "579dc571d53a0658a154fbec": "fence",
    "58330581ace78e27b8b10cee": "skier",
    "5935c25fb3acc3127c3d8cd9": "peacekeeper",
    "5a7c2eca46aef81a7ca2145d": "mechanic",
    "5ac3b934156ae10c4430e83c": "ragman",
    "5c0647fdd443bc2504c2d371": "jaeger",
    "638f541a29ffd1183d187f57": "lighthousekeeper",
    "656f0f98d80a697f855d34b1": "btr",
    "6617beeaa9cfa777ca915b7c": "ref",
}

# --------------------------------------------------------------------------------------------
# Decisions made on top of the 3.x source.
#
# The 3.x tree is a read-only reference corpus, so corrections cannot be made there. They live
# here instead: without that, re-running the converter silently reverts every decision already
# taken, and the revert looks exactly like a successful conversion.
# --------------------------------------------------------------------------------------------

# stem -> {field: value}. Read from tools/price-overrides.json, which the price review tool
# writes, so a reviewed price is not quietly reverted the next time this script runs.
def _load_overrides() -> dict:
    f = pathlib.Path(__file__).resolve().parent / "price-overrides.json"
    if not f.exists():
        return {}
    data = json.loads(f.read_text(encoding="utf-8")).get("overrides", {})
    return {stem: {k: v for k, v in fields.items() if k != "why"}
            for stem, fields in data.items()}


OVERRIDES = _load_overrides()

# stem in the 3.x tree -> stem it should ship under.
#
# The filename derives the item's id, so an accidental filename becomes an accidental id.
# Renaming is free while profiles are a blank slate and permanent once players have the item
# in a stash, so accidents get corrected before release, here rather than in the corpus.
#
# Only genuine accidents belong here. Naming-style inconsistencies (_PANTS vs _BOTTOM, and
# similar) are for the content owners to decide, not something to quietly normalise.
RENAMES = {
    # Windows' name for a duplicated file. It is the only config in its folder, so this is
    # not a stray copy left beside an original - the accident *is* the item.
    "COMBAT_PANTS_URBANREED_BOTTOM - Copy": "COMBAT_PANTS_URBANREED_BOTTOM",
}

# Old quest id -> the quest that replaced it.
#
# 3.x allowed any alphanumeric quest id; 4.x requires MongoId format, matching BSG's change in
# Live. The quests were renumbered and the item configs that gate on them were not, so 68 Part 1
# items reference quests that no longer exist and can never unlock. The bug predates the port —
# the same mismatch is in the 3.x source.
#
# Recovered rather than guessed: the renumbering left BOTH key styles in the locale file, so
# each old id was matched to a new one by its four text fields together (name, description,
# successMessageText, failMessageText). 19/19 resolved, none ambiguous, and the result is
# sequential by quest id order — two independent derivations agreeing.
#
# WARNING: those old locale keys are now the only record of this mapping. They look like dead
# weight and are the sort of thing a tidy-up would delete. This table is the durable copy;
# do not remove it just because the locale keys survive today.
QUEST_ID_MAP = {
    "DRIP_0": "669a1606666bd606fa3f897a",   # A Wild Night
    "DRIP_1": "669cdb5039f39e1bd6019b56",   # The Morning After
    "DRIP_2": "669f74d7e7211bf21d8af254",   # Material Handler
    "DRIP_3": "669f759a1c5ee26e33c5afb2",   # Glock Wick: Part 1
    "DRIP_4": "669f76cb1fec55b3413b554c",   # Glock Wick: Part 2
    "DRIP_5": "669f775edfe50ca330aaa91d",   # Glock Wick: Part 3
    "DRIP_6": "669f77bd952e94e100e88847",   # Full Life Consequences
    "DRIP_7": "669f78036d104f2127da9a3b",   # Shock and Awe
    "DRIP_8": "669f78477ebc9a09e44cbd6d",   # Lack of Lubrication
    "DRIP_9": "669f78890cf4da93267775f6",   # Junker
    "DRIP_10": "669f78e3ea69f9bde9904a1b",  # Party City
    "DRIP_11": "669f795b4657ccef2265f1be",  # System Destroyer: Part 1
    "DRIP_12": "669f79c7f8b1f185365997e3",  # System Destroyer: Part 2
    "DRIP_13": "669f7a04a6bd56d17bae1089",  # Head, eyes
    "DRIP_14": "669f7a46a33b9e7cbda18b33",  # Mosin Man
    "DRIP_15": "669f7a86fd2585b9526ea0ed",  # Power Supply and Demand
    "DRIP_16": "669f7ab67cf81b4cfa87028f",  # First Impressions
    "DRIP_17": "669f7af0dec2d6cd48b2bf1d",  # The Best Defense
    "DRIP_18": "669f7b28d1dbbbdb0475e7be",  # Friendly Feud
}

# stem -> (part it lives in, part it should ship in).
# Converting the destination part pulls the item in; converting the source part leaves it out,
# so a combined run cannot collide with itself.
PROMOTIONS = {
    # A Part 1 quest hands this over, but it only ever shipped in Part 3, so the quest could
    # not load. Sophia approved the move.
    "SLING_OLIVEDRAB_BAG": ("3", "1"),
}

# (base item, slot) -> the item that actually belongs in it.
#
# Eight files across all three parts put the ID of the FRONT insert into the "Soft_armor_back"
# slot. Every other slot in those files matches vanilla exactly, which is the signature of a
# duplicated line with the slot renamed and the ID left behind. It is easy to write because
# the two inserts share a name - both are called "Aramid insert", and they differ only in
# which part of the body their colliders cover.
#
# **The carriers were not mis-covered, they were uncovered.** Each of these slots accepts
# exactly one item and it is not the one named, so the game refused to fit the part and left
# the slot empty. These eight have had no back armour at all since 3.x. This is a repair, not
# a balance change, and anyone reading it later should not mistake it for one.
#
# Keyed by base item rather than by filename so it covers Parts 2 and 3 the first time they
# are converted, instead of being found and fixed twice. Sophia approved the fix.
#
# `drip check` reports the same condition as DRIP-410 by deriving it from the game's slot
# filters. That stays the safety net; this table stays the record. A converter that silently
# rewrote author data to match the game database would fix these eight and document nothing.
SLOT_FIXES = {
    # BNTI Zhuk body armor (EMR) - 1 file. Back slot held 65764275..., the front insert.
    ("5c0e625a86f7742d77340f62", "Soft_armor_back"): "657642b0e6d5dd75f40688a5",
    # Crye Precision AVS plate carrier (Tagilla Edition) - 7 files across all three parts.
    # Back slot held 6575f5cb..., the front one.
    ("609e860ebd219504d8507525", "Soft_armor_back"): "6575f5e1da698a4e98067869",
}

def dependencies_at_risk(dest_file: pathlib.Path, new_config: dict) -> list[str]:
    """Bundle dependencies the destination declares that this run would not re-emit.

    A stripped bundle borrows its geometry from another bundle, and that needs two things:
    the externals table inside the .bundle names it, and the config declares a dependency so
    the client actually loads it. The first is safe from this script. **The second lives in
    the file this script overwrites.**

    So a conversion can silently delete the second half of a working arrangement. The symptom
    is not a crash and not magenta - it is an item that renders as nothing at all, and the
    conversion reports success. That is the same shape as the back-armour bug it just fixed:
    a real thing quietly missing, with nothing anywhere saying so.

    This only detects. It cannot re-emit them, because the information is not in the 3.x
    source - it is a fact about the bundles on disk, which is why deriving it belongs in a
    tool that can open one.
    """
    if not dest_file.is_file():
        return []
    try:
        existing = json.loads(strip_json5(dest_file.read_text(encoding="utf-8-sig")))
    except Exception:
        return []                       # unreadable destination is the stale-output check's job
    was = existing.get("bundles") or {}
    now = new_config.get("bundles") or {}
    lost = []
    for key, paths in was.items():
        for path in (paths or []):
            if path not in (now.get(key) or []):
                lost.append(f"{key} -> {path}")
    return lost


# Fields the v2 schema drops entirely. See CONFIG-SCHEMA-v2.md sections 2.1 and 2.2.
DROPPED = {
    "bundlePath",          # decorative: never read, always the constant the loader assumed
    "topBundlePath",
    "handsBundlePath",
    "bottomBundlePath",
}

# Field order in the emitted file. Readability matters more than diff-minimalism here:
# identity first, then what players see, then what it costs, then the fiddly bits.
FIELD_ORDER = [
    "$schema", "type",
    "name", "shortName", "description", "translations",
    "traderId", "copyOriginalOffers",
    "price", "currency", "loyaltyLevel", "profileLevel", "standing", "questRequirements",
    "basedOn", "addToBots", "botWeightMultiplier", "includedParts",
    "properties", "copyPropertiesFrom", "handbookPrice", "fleaPrice",
    "vanillaOrigin", "bundles",
    "tags",
]

# Comments attached to fields in the output, so a converted file still teaches.
FIELD_COMMENTS = {
    "traderId": "Who sells this. 'moron' and 'georgia' are DRIP's own traders.",
    "copyOriginalOffers": (
        "true  = sold wherever the original item is sold, at the original price.\n"
        "false = sold by the trader above, at the price below."
    ),
    "bundles": (
        "Extra dependencies beyond the automatic ones (shaders, cubemaps, physics materials).\n"
        "Bundles next to this file are found automatically — you only list extras here."
    ),
    "tags": "Outfit-matching tags. Not read by DRIP right now; kept for ICUP.",
}


# --------------------------------------------------------------------------------------------
# Vanilla origin
#
# Every DRIP bundle carries an AssetBundle object naming the vanilla bundle it was cloned from.
# The loader registers bundles by key and never opens them, so it cannot see this — but the
# converter already walks every bundle, so it surfaces the fact as a config field.
#
# Emitted RAW, deliberately. The converter could resolve which bot types a garment suits, but
# that would freeze the answer against whatever game version happened to be installed when it
# ran. Resolving at runtime against the live database is what lets this self-correct when BSG
# changes a bot's wardrobe. The converter's job is to surface, not to decide.
# --------------------------------------------------------------------------------------------

VANILLA_ORIGINS_FILE = pathlib.Path(__file__).resolve().parent / "vanilla-origins.json"

# The bundle whose origin decides what a garment *is*, per clothing type. A top also has a
# HANDS bundle with its own origin; it is a companion, not the garment.
GARMENT_BUNDLE = {"top": "TOP.bundle", "bottom": "BOTTOM.bundle"}

try:
    import UnityPy
    _UNITYPY = True
except ImportError:
    _UNITYPY = False

_origins: dict[str, str] = {}
_origins_dirty = False


def origin_key(stem: str, kind: str) -> str:
    """Identity of a garment, independent of where its files live.

    Verified unique across all 270 clothing configs in all three parts: 267 keys, and the three
    that repeat agree on their origin. Filename alone is not enough — a Part 2 top and bottom
    share the stem INFILTRATOR_NIGHTGREY_PANTS and have different origins.
    """
    return f"{stem}|{kind}"


def load_origins() -> None:
    global _origins
    if VANILLA_ORIGINS_FILE.exists():
        _origins = json.loads(VANILLA_ORIGINS_FILE.read_text(encoding="utf-8")).get("origins", {})


def save_origins() -> None:
    if not _origins_dirty:
        return
    VANILLA_ORIGINS_FILE.write_text(json.dumps({
        "_README": [
            "The vanilla garment each DRIP garment was cloned from. Keyed by <filename>|<type>.",
            "",
            "This is a RECORD, not a cache. It is read in preference to the bundles and is not",
            "expected to be re-derivable: today the value can be read back out of a bundle's",
            "AssetBundle name, but the Unity rebuild constructs bundles that reference vanilla",
            "assets instead of copying them, so their internal names will no longer carry it.",
            "",
            "Every DRIP garment is a retexture of a vanilla one - none has ever been made from",
            "scratch - so a garment with no entry here is an alarm, not an unset option.",
            "",
            "Captured while it was still readable. Do not delete entries. If a garment is",
            "genuinely retired, remove its config and this line together.",
            "",
            "COUNTING: entries are not garments. A renamed garment is deliberately recorded",
            "under BOTH names (see RENAMES in convert-legacy.py) so the record answers whether",
            "you look it up by the name on disk or the name it ships under. 270 clothing",
            "configs -> 268 distinct garment keys -> 269 entries, the extra being one rename",
            "alias. Quote the garment count, not the line count.",
            "",
            "KNOWN LIMIT: two garments with the same filename AND the same type, differing only",
            "by folder, collapse to one key. That is real in Part 3 - two TSHIRT_KHAKI.json5",
            "tops at different prices with different bundles - and the record happens to be",
            "right there only because both share a vanilla origin. It is not a live problem:",
            "the pair already hard-errors on conversion as an id collision, so it cannot reach",
            "a release unresolved. Folder is deliberately NOT in the key, because the key must",
            "survive a file being moved.",
            "",
            "Regenerate or extend with:  python convert-legacy.py --capture-origins",
        ],
        "origins": dict(sorted(_origins.items())),
    }, indent=1) + "\n", encoding="utf-8")


def resolve_origin(stem: str, kind: str, folder: pathlib.Path) -> tuple[str | None, str | None]:
    """Recorded origin first, bundle second. Returns (origin, problem); one is always None."""
    global _origins_dirty
    key = origin_key(stem, kind)
    if key in _origins:
        return _origins[key], None

    origin, problem = read_bundle_origin(folder / GARMENT_BUNDLE[kind])
    if origin:
        _origins[key] = origin
        _origins_dirty = True
    return origin, problem


def read_bundle_origin(bundle: pathlib.Path) -> tuple[str | None, str | None]:
    if not bundle.exists():
        return None, f"{bundle.name} is not on disk and no origin is recorded for this garment"
    if not _UNITYPY:
        return None, ("UnityPy is not installed, so bundle origins can't be read "
                      "(pip install UnityPy) and this garment has no recorded origin")
    try:
        env = UnityPy.load(str(bundle))
        for obj in env.objects:
            if obj.type.name == "AssetBundle":
                origin = obj.read().m_Name
                if not origin:
                    return None, f"{bundle.name} names an empty vanilla origin"
                return origin, None
        return None, f"{bundle.name} carries no AssetBundle object naming its vanilla origin"
    except Exception as exc:
        return None, f"{bundle.name} could not be read: {type(exc).__name__}: {exc}"


def capture_origins() -> int:
    """Walk every part and record every garment's origin, while the bundles still carry it."""
    global _origins_dirty
    load_origins()
    found = missing = 0
    for part_dir in PARTS.values():
        root = LEGACY_ROOT / part_dir / "items"
        if not root.exists():
            continue
        for f in sorted(root.rglob("*.json5")):
            try:
                data, _ = read_legacy(f)
            except Exception:
                continue
            kind = TYPE_MAP.get(data.get("type"))
            if kind not in GARMENT_BUNDLE:
                continue

            bundle = f.parent / GARMENT_BUNDLE[kind]
            note = ""
            if not bundle.exists():
                # A garment whose bundle is misnamed still has a lineage worth keeping, and
                # after the rebuild it is unrecoverable. One unambiguous bundle is enough.
                others = list(f.parent.glob("*.bundle"))
                if len(others) == 1:
                    bundle, note = others[0], f" (read from {others[0].name}, not {GARMENT_BUNDLE[kind]})"

            origin, problem = read_bundle_origin(bundle)
            # A renamed garment is recorded under both names on purpose: capture sees the name
            # on disk, the converter looks it up by the name it ships under. Recording only one
            # leaves the other lookup falling back to reading a bundle — which works today and
            # will not after the rebuild.
            keys = {origin_key(f.stem, kind)}
            if f.stem in RENAMES:
                keys.add(origin_key(RENAMES[f.stem], kind))
            if origin:
                for key in keys:
                    if _origins.get(key) != origin:
                        _origins[key] = origin
                        _origins_dirty = True
                found += 1
                if note:
                    print(f"    {f.stem}{note}")
            else:
                missing += 1
                print(f"    NOT RECORDED  {f.stem}: {problem}")

    save_origins()
    print(f"\n  recorded {found} garment origins, "
          f"{len(set(_origins.values()))} distinct")
    if missing:
        print(f"  {missing} could not be read")
    print(f"  -> {VANILLA_ORIGINS_FILE}\n")
    return 1 if missing else 0


# --------------------------------------------------------------------------------------------
# Tolerant JSON5 reading
# --------------------------------------------------------------------------------------------

def repair_control_chars(text: str) -> tuple[str, int]:
    """Replace raw control characters inside strings — invalid in JSON and JSON5 alike.

    One file in the corpus (MARKSGORKA_BEREZKA_TOP) has a literal tab in its name.
    """
    out, i, n, in_str, fixed = [], 0, len(text), False, 0
    while i < n:
        c = text[i]
        if in_str:
            if c == "\\" and i + 1 < n:
                out.append(c)
                out.append(text[i + 1])
                i += 2
                continue
            if c == '"':
                in_str = False
            elif ord(c) < 0x20 and c not in "\r\n":
                out.append(" ")
                fixed += 1
                i += 1
                continue
        elif c == '"':
            in_str = True
        out.append(c)
        i += 1
    return "".join(out), fixed


def strip_json5(text: str) -> str:
    """Remove // and /* */ comments and trailing commas, respecting string literals."""
    out, i, n, in_str = [], 0, len(text), False
    while i < n:
        c = text[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
            out.append(c)
            i += 1
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "*":
            j = text.find("*/", i + 2)
            i = n if j == -1 else j + 2
            continue
        out.append(c)
        i += 1
    return re.sub(r",(\s*[}\]])", r"\1", "".join(out))


def read_legacy(path: pathlib.Path) -> tuple[dict, list[str]]:
    notes = []
    raw = path.read_text(encoding="utf-8-sig")
    raw, fixed = repair_control_chars(raw)
    if fixed:
        notes.append(f"repaired {fixed} stray control character(s) inside a string")
    return json.loads(strip_json5(raw)), notes


# --------------------------------------------------------------------------------------------
# JSONC writing
# --------------------------------------------------------------------------------------------

def dump_value(value, indent: int) -> str:
    """Compact-but-readable JSON. Short arrays stay on one line; objects always expand."""
    pad = "  " * indent
    inner = "  " * (indent + 1)

    if isinstance(value, dict):
        if not value:
            return "{}"
        parts = [f'{inner}{json.dumps(k)}: {dump_value(v, indent + 1)}'
                 for k, v in value.items()]
        return "{\n" + ",\n".join(parts) + f"\n{pad}}}"

    if isinstance(value, list):
        if not value:
            return "[]"
        flat = json.dumps(value)
        if len(flat) <= 70 and not any(isinstance(x, (dict, list)) for x in value):
            return flat
        parts = [f"{inner}{dump_value(v, indent + 1)}" for v in value]
        return "[\n" + ",\n".join(parts) + f"\n{pad}]"

    return json.dumps(value)


def dump_jsonc(config: dict, header: list[str]) -> str:
    lines = [f"// {h}" for h in header]
    lines.append("{")

    keys = [k for k in FIELD_ORDER if k in config]
    keys += [k for k in config if k not in FIELD_ORDER]  # anything unexpected, kept at the end

    for idx, key in enumerate(keys):
        if key in FIELD_COMMENTS:
            if idx:
                lines.append("")
            for c in FIELD_COMMENTS[key].split("\n"):
                lines.append(f"  // {c}")
        comma = "," if idx < len(keys) - 1 else ""
        lines.append(f"  {json.dumps(key)}: {dump_value(config[key], 1)}{comma}")

    lines.append("}")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------------------------
# The conversion itself
# --------------------------------------------------------------------------------------------

class Report:
    """Records everything the conversion did, per file.

    A conversion nobody can audit is a conversion nobody trusts, so every alteration is
    recorded against the file it happened to — not just counted. Three levels:

      change  routine and expected (a field renamed, a price flattened)
      repair  the converter altered content to fix a defect in the source file
      warning something a human should look at; the file still converted
    """

    def __init__(self):
        self.converted = 0
        self.changes: dict[str, list[str]] = collections.defaultdict(list)
        self.repairs: list[tuple[str, str]] = []
        self.warnings: list[tuple[str, str]] = []
        self.errors: list[tuple[str, str]] = []
        self.ids: dict[str, list[tuple[str, str]]] = collections.defaultdict(list)
        self.written: set[pathlib.Path] = set()
        self.at_risk: list[tuple[str, str]] = []
        self.stats = collections.Counter()

    def change(self, path, msg, category: str | None = None):
        """`msg` goes in the per-file report; `category` is what the console tallies."""
        self.changes[path].append(msg)
        self.stats[category or msg] += 1

    def repair(self, path, msg):
        self.repairs.append((path, msg))
        self.changes[path].append(f"REPAIRED — {msg}")

    def warn(self, path, msg):
        self.warnings.append((path, msg))
        self.changes[path].append(f"warning — {msg}")

    def error(self, path, msg):
        self.errors.append((path, msg))


def derive_id(stem: str) -> str:
    return hashlib.sha1(stem.encode("utf-8")).hexdigest()[:24].lower()


def find_mod_root(out_root: pathlib.Path) -> pathlib.Path | None:
    """Walk up from the output folder looking for the mod root (the folder holding docs/)."""
    for candidate in [out_root, *out_root.resolve().parents]:
        if (candidate / "docs" / "drip-item.schema.json").exists():
            return candidate
    return None


def schema_ref(dest_file: pathlib.Path, out_root: pathlib.Path) -> str:
    """Relative path from a config file to the shared schema, for editor autocomplete.

    Derived from where the schema actually is rather than assuming a fixed nesting depth,
    so moving content packs around doesn't silently break every file's autocomplete.
    """
    mod_root = find_mod_root(out_root)
    if mod_root is None:
        # No schema in reach: emit a path that at least reads correctly, and say so once.
        return "../" * (len(dest_file.relative_to(out_root).parts) - 1) + "drip-item.schema.json"
    schema = mod_root / "docs" / "drip-item.schema.json"
    import os
    return pathlib.PurePath(
        os.path.relpath(schema, dest_file.parent)
    ).as_posix()


def convert_one(legacy: dict, src: pathlib.Path, rel: str, rpt: Report) -> dict | None:
    out: dict = {}

    legacy_type = legacy.get("type")
    kind = TYPE_MAP.get(legacy_type)
    if kind is None:
        rpt.error(rel, f"unknown type {legacy_type!r} — skipped")
        return None
    out["type"] = kind
    is_gear = kind == "gear"

    # --- text -------------------------------------------------------------------------------
    out["name"] = legacy["name"]
    for field in ("shortName", "description"):
        if field in legacy:
            if is_gear:
                out[field] = legacy[field]
            else:
                rpt.warn(rel, f"dropped '{field}' — not shown for clothing")

    # --- trader -----------------------------------------------------------------------------
    trader = legacy["traderId"]
    if trader in TRADER_NAMES:
        rpt.change(rel, f"traderId: replaced raw ID {trader} with '{TRADER_NAMES[trader]}'",
                   "traderId de-mongo'd")
        trader = TRADER_NAMES[trader]
    out["traderId"] = trader

    # --- gear structure ---------------------------------------------------------------------
    if is_gear:
        if "baseItemID" not in legacy:
            rpt.error(rel, "no 'baseItemID' — cannot tell what this is a retexture of")
            return None
        copy_offers = bool(legacy.get("copyAssort", True))
        # Always explicit: it decides whether a price is required, so hiding it hurts readers.
        out["copyOriginalOffers"] = copy_offers

    # --- price ------------------------------------------------------------------------------
    price = legacy.get("price")
    currency = legacy.get("currency", "RUB")
    if isinstance(price, dict):
        # gear's nested {currency, amount} form -> flat
        currency = price.get("currency", "RUB")
        price = price.get("amount")
        rpt.change(rel, f"price: flattened {{currency, amount}} to price {price} + currency {currency}",
                   "nested price flattened")
    if price is not None:
        out["price"] = price
        if currency and currency != "RUB":
            out["currency"] = currency

    for field in ("loyaltyLevel", "profileLevel", "standing"):
        if field in legacy:
            if is_gear and field in ("profileLevel", "standing"):
                rpt.warn(rel, f"dropped '{field}' — gear doesn't use it")
                continue
            out[field] = legacy[field]

    if legacy.get("questRequirements"):
        gates = []
        for wanted in legacy["questRequirements"]:
            replacement = QUEST_ID_MAP.get(wanted)
            if replacement:
                gates.append(replacement)
                rpt.change(rel, f"questRequirements: '{wanted}' -> '{replacement}' "
                                f"(the quest was renumbered; see QUEST_ID_MAP)",
                           "quest gate remapped")
            else:
                gates.append(wanted)
        out["questRequirements"] = gates

    # --- gear extras ------------------------------------------------------------------------
    if is_gear:
        out["basedOn"] = legacy["baseItemID"]

        if legacy.get("addToBots") is False:
            out["addToBots"] = False  # true is the default, so only false is worth writing
        mult = legacy.get("weightingMult", 1.0)
        if mult != 1.0:
            out["botWeightMultiplier"] = mult

        if legacy.get("childAssorts"):
            parts = dict(legacy["childAssorts"])
            for slot, tpl in list(parts.items()):
                right = SLOT_FIXES.get((out["basedOn"], slot))
                if right and tpl != right:
                    parts[slot] = right
                    rpt.repair(rel, f'includedParts["{slot}"] was {tpl}, which the game will '
                                    f"not fit there - the slot was left empty. Now {right}. "
                                    "See SLOT_FIXES in this script.")
            out["includedParts"] = parts

        custom = legacy.get("customProperties") or {}
        props = custom.get("props") or {}
        if props.get("changeProps"):
            out["properties"] = props["changeProps"]
        if props.get("copyPropsFrom"):
            out["copyPropertiesFrom"] = props["copyPropsFrom"]
        cprice = custom.get("price") or {}
        if "handbook" in cprice:
            out["handbookPrice"] = cprice["handbook"]
        if "flea" in cprice:
            out["fleaPrice"] = cprice["flea"]

    # --- bundles ----------------------------------------------------------------------------
    # Legacy *BundlePath fields are dropped: every value in the corpus is the constant the
    # loader hardcoded, so they carried no information. Dependencies keep only the non-default
    # entries; textureGearDependencies* are dropped entirely (always empty — they existed only
    # to flag an extra co-located TEXTURE bundle, which v2 discovers on its own).
    on_disk = {f.name for f in src.parent.glob("*.bundle")}
    ship_as = RENAMES.get(src.stem, src.stem)

    # --- vanilla origin (clothing only) -------------------------------------------------------
    # Which bots may wear a garment is derived at runtime from the vanilla garment it was cloned
    # from — BSG already decided that, and a retexture inherits it. Surfaced here because the
    # loader never opens bundles. Omitted rather than guessed when it can't be read: including a
    # garment blindly recreates the every-bot-wears-everything behaviour this replaces.
    if kind in GARMENT_BUNDLE:
        origin, problem = resolve_origin(ship_as, kind, src.parent)
        if origin:
            out["vanillaOrigin"] = origin
            rpt.change(rel, f"vanillaOrigin: {origin}", "vanilla origin read")
        else:
            rpt.warn(rel, f"no 'vanillaOrigin' emitted - {problem}. Bots will not be able to "
                          f"tell whether this garment suits them.")

    bundles: dict[str, list[str]] = {}
    for dep_field, bundle_name in DEP_FIELD_TO_BUNDLE.items():
        deps = legacy.get(dep_field)
        if not deps:
            continue
        dropped = [d for d in deps if d in DEFAULT_BUNDLE_DEPS]
        extra = [d for d in deps if d not in DEFAULT_BUNDLE_DEPS]
        if extra:
            bundles[bundle_name] = extra
        rpt.change(rel, f"bundles: '{dep_field}' -> bundles['{bundle_name}']"
                        + (f", dropped {len(dropped)} dependency(ies) now applied automatically"
                           if dropped else ""),
                   "dependencies moved into 'bundles'")
    if bundles:
        out["bundles"] = bundles
    else:
        rpt.stats["no bundles block needed"] += 1

    # The legacy *BundlePath fields were never read by the loader — but where one disagrees
    # with what is actually on disk, the author has been looking at a lie, so say so.
    for path_field in ("bundlePath", "topBundlePath", "handsBundlePath", "bottomBundlePath"):
        declared = legacy.get(path_field)
        if declared is None:
            continue
        if declared in on_disk:
            rpt.change(rel, f"dropped '{path_field}' — bundles are found by co-location now",
                       "decorative *BundlePath dropped")
        else:
            rpt.repair(rel,
                       f"'{path_field}' declared {declared!r}, which is not in this folder "
                       f"(found: {sorted(on_disk) or 'no bundles at all'}). The old loader "
                       f"ignored this field and looked for the co-located bundle regardless, "
                       f"so this item may never have worked.")

    for key in sorted(legacy):
        if key.startswith("textureGearDependencies"):
            rpt.change(rel, f"dropped '{key}' — it was always empty; the co-located "
                            f"TEXTURE bundle is discovered automatically",
                       "textureGearDependencies dropped")

    # --- renames worth naming individually ---------------------------------------------------
    for old, new in (("baseItemID", "basedOn"), ("copyAssort", "copyOriginalOffers"),
                     ("weightingMult", "botWeightMultiplier"), ("childAssorts", "includedParts")):
        if old in legacy:
            rpt.change(rel, f"renamed '{old}' to '{new}'", "fields renamed")
    if "customProperties" in legacy:
        rpt.change(rel, "split 'customProperties' into properties / copyPropertiesFrom / "
                        "handbookPrice / fleaPrice", "customProperties split")

    # --- passthrough ------------------------------------------------------------------------
    # tags must survive byte-for-byte: ICUP picks them up later. See schema section 4.7.
    if "tags" in legacy:
        out["tags"] = legacy["tags"]
        rpt.change(rel, "kept 'tags' unchanged (reserved for ICUP)", "tags preserved")

    # --- decisions taken on top of the source ------------------------------------------------
    for field, value in OVERRIDES.get(src.stem, {}).items():
        was = out.get(field)
        out[field] = value
        rpt.change(rel, f"override: {field} {was!r} -> {value!r} (see OVERRIDES in this script)",
                   "overrides applied")

    known = (
        set(DROPPED) | set(DEP_FIELD_TO_BUNDLE) | {
            "name", "type", "traderId", "shortName", "description", "baseItemID",
            "copyAssort", "addToBots", "weightingMult", "currency", "price",
            "loyaltyLevel", "profileLevel", "standing", "questRequirements",
            "tags", "childAssorts", "customProperties",
        }
    )
    for key in legacy:
        if key not in known and not key.startswith("textureGearDependencies"):
            out[key] = legacy[key]
            rpt.warn(rel, f"unrecognised field '{key}' carried over untouched")

    # --- sanity checks the author would otherwise hit at runtime ----------------------------
    expected = {"top": ["TOP.bundle", "HANDS.bundle"],
                "bottom": ["BOTTOM.bundle"],
                "gear": ["GEAR.bundle"]}[kind]
    for want in expected:
        if want not in on_disk:
            rpt.warn(rel, f"expected {want} beside this config; folder has "
                          f"{sorted(on_disk) or 'no bundles'}")

    if is_gear and not out["copyOriginalOffers"] and "price" not in out:
        rpt.error(rel, "sold by our own trader but has no price")

    return out


def dest_for(rel_parts: tuple[str, ...], kind: str) -> pathlib.PurePath:
    """items/CLOTHING/TOP/A/B -> CustomClothing/TOPS/A/B ; items/GEAR/A/B -> CustomItems/A/B

    Placed by the item's declared `type`, not by which folder it was filed in. The two disagree
    at least once in the corpus - a top with TOP.bundle and HANDS.bundle sits under
    CLOTHING/BOTTOM - and following the folder would carry that mistake into the output. The
    type field is what the loader acts on, so it is the honest thing to organise by.
    """
    parts = list(rel_parts)
    if parts[:1] == ["items"]:
        parts = parts[1:]
    if parts[:1] == ["CLOTHING"]:
        parts = parts[2:] if parts[1:2] in (["TOP"], ["BOTTOM"]) else parts[1:]
    elif parts[:1] == ["GEAR"]:
        parts = parts[1:]

    if kind == "top":
        return pathlib.PurePath("CustomClothing", "TOPS", *parts)
    if kind == "bottom":
        return pathlib.PurePath("CustomClothing", "BOTTOMS", *parts)
    return pathlib.PurePath("CustomItems", *parts)


def place_bundle(src: pathlib.Path, dst: pathlib.Path, mode: str):
    if mode == "none" or dst.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if mode == "link":
        try:
            import os
            os.link(src, dst)
            return
        except OSError:
            pass  # different volume or no privilege — fall back
    shutil.copy2(src, dst)


def convert_part(part: str, out_root: pathlib.Path, bundle_mode: str,
                 dry_run: bool, rpt: Report):
    src_root = LEGACY_ROOT / PARTS[part]
    items_root = src_root / "items"
    if not items_root.exists():
        rpt.error(str(src_root), "no items/ directory")
        return

    # Items promoted INTO this part are converted alongside its own, keeping their folder
    # layout so they land where their siblings already are.
    sources = [(src, src_root) for src in sorted(items_root.rglob("*.json5"))]
    for stem, (from_part, to_part) in PROMOTIONS.items():
        if to_part != part:
            continue
        other_root = LEGACY_ROOT / PARTS[from_part]
        for extra in sorted((other_root / "items").rglob(f"{stem}.json5")):
            sources.append((extra, other_root))

    for src, this_root in sources:
        # ...and left out of the part they live in, so a combined run can't collide with itself.
        promo = PROMOTIONS.get(src.stem)
        if promo and promo[1] != part:
            rpt.change(str(src.relative_to(LEGACY_ROOT)),
                       f"not emitted with Part {promo[0]}: promoted to Part {promo[1]}",
                       "promoted between parts")
            continue

        rel_parts = src.relative_to(this_root).parent.parts
        rel = str(src.relative_to(LEGACY_ROOT))
        if promo:
            rpt.change(rel, f"pulled into Part {promo[1]} from Part {promo[0]} "
                            f"(see PROMOTIONS in this script)", "promoted between parts")
        try:
            legacy, notes = read_legacy(src)
        except Exception as exc:
            rpt.error(rel, f"could not be read: {exc}")
            continue
        for n in notes:
            rpt.repair(rel, n)

        config = convert_one(legacy, src, rel, rpt)
        if config is None:
            continue

        ship_as = RENAMES.get(src.stem, src.stem)
        if ship_as != src.stem:
            rpt.repair(rel, f"filename looks accidental; shipping as '{ship_as}'. "
                            f"The filename derives the item id, so this corrects the id too - "
                            f"free now, permanent once players have the item.")

        dest_dir = out_root / dest_for(rel_parts, config["type"])
        dest_file = dest_dir / f"{ship_as}.jsonc"

        item_id = derive_id(ship_as)
        body = json.dumps(config, sort_keys=True)
        rpt.ids[item_id].append((rel, hashlib.sha1(body.encode()).hexdigest()))

        config = {"$schema": schema_ref(dest_file, out_root), **config}

        text = dump_jsonc(config, [
            f"{config['name']}",
            f"Converted from {src.name} — see docs/CONFIG-SCHEMA-v2.md",
        ])

        rpt.written.add(dest_file.resolve())
        for what in dependencies_at_risk(dest_file, config):
            rpt.at_risk.append((rel, what))
        if not dry_run:
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_file.write_text(text, encoding="utf-8")
            for bundle in src.parent.glob("*.bundle"):
                place_bundle(bundle, dest_dir / bundle.name, bundle_mode)

        rpt.converted += 1
        rpt.stats[f"type={config['type']}"] += 1

    # quests, quest images and locales travel with the pack
    for sub, dest, pattern in (
        ("quests", "CustomQuests", "*.json5"),
        ("quests", "CustomQuests", "*.png"),
        ("locales/en", "CustomLocales", "*.json5"),
    ):
        srcdir = src_root / sub
        if not srcdir.exists():
            continue
        for f in sorted(srcdir.glob(pattern)):
            target = out_root / dest / (f.stem + (".jsonc" if f.suffix == ".json5" else f.suffix))
            if dest == "CustomLocales":
                target = out_root / dest / "en.json"
            if dry_run:
                rpt.stats[f"{dest} files"] += 1
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            if f.suffix == ".json5":
                data, _ = read_legacy(f)
                if dest == "CustomLocales" and target.exists():
                    data = {**json.loads(target.read_text(encoding="utf-8")), **data}
                target.write_text(json.dumps(data, indent=2, ensure_ascii=False),
                                  encoding="utf-8")
            else:
                shutil.copy2(f, target)
            rpt.stats[f"{dest} files"] += 1


def write_report(path: pathlib.Path, parts: list[str], rpt: Report, dry_run: bool):
    """Per-file record of everything the conversion touched, so the result can be audited."""
    lines = [
        "# DRIP legacy -> v2 conversion report",
        "",
        f"Parts converted: {', '.join(parts)}{'  (DRY RUN — nothing written)' if dry_run else ''}",
        f"Files converted: {rpt.converted}",
        "",
        "Every alteration is listed against the file it happened to. `REPAIRED` marks a case",
        "where the converter changed content to fix a defect in the source file — those are",
        "worth reading. See docs/CONFIG-SCHEMA-v2.md for why each transformation happens.",
        "",
    ]

    if rpt.repairs:
        lines += ["## Repairs", "",
                  "The converter altered content to fix a problem in the original file.", ""]
        for p, m in rpt.repairs:
            lines += [f"- **{p}**", f"  - {m}", ""]

    collisions = {i: f for i, f in rpt.ids.items() if len(f) > 1}
    if collisions:
        lines += ["## ID collisions", "",
                  "Two files whose names produce the same item ID.", ""]
        for item_id, files in collisions.items():
            identical = len({h for _, h in files}) == 1
            lines.append(f"- `{item_id}` — "
                         + ("identical content, safe to delete one"
                            if identical else
                            "**different content: one would overwrite the other, rename one**"))
            lines += [f"  - {f}" for f, _ in files]
        lines.append("")

    if rpt.warnings:
        lines += ["## Warnings", ""]
        for p, m in rpt.warnings:
            lines += [f"- **{p}**", f"  - {m}", ""]

    if rpt.errors:
        lines += ["## Errors — did not convert", ""]
        for p, m in rpt.errors:
            lines += [f"- **{p}**", f"  - {m}", ""]

    lines += ["## Every file", ""]
    for f in sorted(rpt.changes):
        lines.append(f"### {f}")
        lines += [f"- {c}" for c in rpt.changes[f]]
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--part", action="append", choices=sorted(PARTS),
                    help="which legacy part to convert (repeatable); default: 1")
    ap.add_argument("--out", type=pathlib.Path,
                    help="destination content pack folder (not needed with --capture-origins)")
    ap.add_argument("--bundles", choices=["link", "copy", "none"], default="link",
                    help="hard-link (default, instant), copy, or skip .bundle files")
    ap.add_argument("--dry-run", action="store_true", help="report only, write nothing")
    ap.add_argument("--allow-dependency-loss", action="store_true",
                    help="write even if it would drop bundle dependency declarations that "
                         "this run cannot reproduce (they are not in the 3.x source)")
    ap.add_argument("--capture-origins", action="store_true",
                    help="record every garment's vanilla origin from its bundle and exit")
    ap.add_argument("--report", type=pathlib.Path, default=None,
                    help="where to write the per-file change report "
                         "(default: CONVERSION-REPORT.md beside --out)")
    args = ap.parse_args()

    if args.capture_origins:
        print("\n  Recording vanilla origins from the 3.x bundles...\n")
        return capture_origins()

    if args.out is None:
        ap.error("--out is required unless you're using --capture-origins")

    parts = args.part or ["1"]
    load_origins()

    # Probe first, write second. A conversion overwrites the file that carries a bundle's
    # dependency declarations, and those are not derivable from the 3.x source - they are
    # facts about the bundles on disk. Losing them does not break the build or turn anything
    # magenta; it makes items render as nothing, and the conversion reports success.
    #
    # So the run is done twice: once with nothing written, to find out what it would cost.
    # Converting is fast and the alternative is a silent, invisible regression.
    if not args.dry_run:
        probe = Report()
        for part in parts:
            convert_part(part, args.out, args.bundles, True, probe)
        if probe.at_risk and not args.allow_dependency_loss:
            files = {rel for rel, _ in probe.at_risk}
            print(f"\n  STOPPED - nothing was written.\n")
            print(f"  {len(probe.at_risk)} bundle dependency declaration(s) across "
                  f"{len(files)} file(s) exist in\n  {args.out}\n"
                  "  and this run would not re-emit them.\n")
            print("  Those declarations are what tells the client to load the bundle a")
            print("  stripped bundle borrows its geometry from. Without them the items load")
            print("  with no geometry and render as nothing at all - and no error is raised.\n")
            for rel, what in probe.at_risk[:8]:
                print(f"    {rel}\n        {what}")
            if len(probe.at_risk) > 8:
                print(f"    ... and {len(probe.at_risk) - 8} more")
            print("\n  Re-derive them after converting, or pass --allow-dependency-loss if")
            print("  you have a copy and intend to restore them yourself.\n")
            return 1

    rpt = Report()
    for part in parts:
        convert_part(part, args.out, args.bundles, args.dry_run, rpt)

    # A config sitting in the output that this run did not write is stale — most often a file
    # whose source was renamed. Left alone it loads as a second, duplicate item, and nothing
    # downstream would notice: it is a perfectly valid config with a valid id of its own.
    stale = []
    if not args.dry_run:
        for sub in ("CustomItems", "CustomClothing"):
            root = args.out / sub
            if root.exists():
                stale += [f for f in sorted(root.rglob("*.jsonc"))
                          if f.resolve() not in rpt.written]

    print(f"\n{'=' * 78}")
    print(f"DRIP legacy -> v2   part(s) {', '.join(parts)}"
          f"{'   [DRY RUN]' if args.dry_run else ''}")
    print("=" * 78)
    print(f"  converted : {rpt.converted}")
    for k, v in sorted(rpt.stats.items()):
        print(f"    {v:5d}  {k}")

    collisions = {i: f for i, f in rpt.ids.items() if len(f) > 1}
    if collisions:
        print(f"\n  ID COLLISIONS ({len(collisions)}) — two files sharing one item ID:")
        for item_id, files in collisions.items():
            identical = len({h for _, h in files}) == 1
            verdict = "identical content, safe to delete one" if identical \
                else "DIFFERENT content — one will overwrite the other, rename one"
            print(f"    {item_id}  ({verdict})")
            for f, _ in files:
                print(f"        {f}")

    if stale:
        print(f"\n  STALE OUTPUT ({len(stale)}) — present in the destination but not produced")
        print("  by this run. Usually a file whose source was renamed. Left in place it loads")
        print("  as a duplicate item. Delete if you're satisfied it's superseded:")
        for f in stale:
            print(f"    {f.relative_to(args.out)}")

    if rpt.repairs:
        print(f"\n  REPAIRS ({len(rpt.repairs)}) — content was altered to fix a problem:")
        for path, msg in rpt.repairs:
            print(f"    {path}\n        {msg}")

    if rpt.warnings:
        print(f"\n  warnings ({len(rpt.warnings)}):")
        for path, msg in rpt.warnings[:40]:
            print(f"    {path}\n        {msg}")
        if len(rpt.warnings) > 40:
            print(f"    … and {len(rpt.warnings) - 40} more")

    if rpt.errors:
        print(f"\n  ERRORS ({len(rpt.errors)}) — these did not convert:")
        for path, msg in rpt.errors:
            print(f"    {path}\n        {msg}")

    save_origins()

    report_path = args.report or (args.out / "CONVERSION-REPORT.md")
    write_report(report_path, parts, rpt, args.dry_run)
    print(f"\n  per-file report: {report_path}")

    print()
    return 1 if rpt.errors else 0


if __name__ == "__main__":
    sys.exit(main())
