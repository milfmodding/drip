#!/usr/bin/env python3
"""
drip - the content author's tool.

    drip new gear ARMOR/6B2/TIGERSTRIPE/ARMOR_6B2_TIGERSTRIPE
    drip new                       (asks you what you're making)
    drip check                     (checks every content pack)
    drip check Essentials          (checks one)
    drip id slick                  (finds a vanilla item's ID from its name)

`new` scaffolds a config with the right fields already filled in and the schema wired up.
`check` finds the mistakes a server restart would otherwise find for you, in about a second.
`id` answers the one question an author can't answer without a programmer.

Standard library only - no install step, nothing to set up.

Field names and shapes are read from docs/drip-item.schema.json rather than repeated here, so
this tool cannot drift away from the published contract. Rules live in docs/CONFIG-SCHEMA-v2.md
section 8.

Most checks read nothing but the content pack. Two things need the game's own database - what
a vanilla item is called, and whether any trader sells it - and those come from sptdb.py,
which finds an SPT install and reads it. When it can't find one, `check` says which check it
skipped rather than reporting a clean run it didn't earn.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

import sptdb

HERE = pathlib.Path(__file__).resolve().parent
MOD_ROOT = HERE.parent
SCHEMA_PATH = MOD_ROOT / "docs" / "drip-item.schema.json"
PACKS_ROOT = MOD_ROOT / "bundles" / "ContentPacks"

TYPE_DIR = {"top": "CustomClothing", "bottom": "CustomClothing", "gear": "CustomItems"}
REQUIRED_BUNDLES = {
    "top": ["TOP.bundle", "HANDS.bundle"],
    "bottom": ["BOTTOM.bundle"],
    "gear": ["GEAR.bundle"],
}

# Legacy spellings -> what they became. None means the field went away entirely.
RENAMED = {
    "baseItemID": "basedOn", "itemTplToClone": "basedOn",
    "copyAssort": "copyOriginalOffers", "cloneAssort": "copyOriginalOffers",
    "weightingMult": "botWeightMultiplier", "childAssorts": "includedParts",
    "customProperties": "properties / copyPropertiesFrom",
    "gearDependencies": "bundles", "topDependencies": "bundles",
    "handsDependencies": "bundles", "bottomDependencies": "bundles",
    "bundlePath": None, "topBundlePath": None, "handsBundlePath": None,
    "bottomBundlePath": None, "textureGearDependencies": None,
    "currencyId": "currency", "locales": "name",
    "translations": "name / shortName / description, which now take a language map directly",
    "overrideProperties": "properties", "bundleDependencies": "bundles",
}

RESERVED = {"tags", "$schema", "//", "_comment"}

# Vanilla traders already exist in the game, so an item naming one needs nothing shipped
# alongside it. Any other accepted trader name is DRIP's own and has to be defined by a
# CustomTraders file somewhere, or there is nowhere for those items to be sold.
# Filenames that betray a file manager rather than a decision. The filename derives the item's
# id, so an accidental name becomes an accidental id — and renaming stops being free once
# players have the item. Deliberately narrow: only names nobody would type on purpose. Naming
# style (_PANTS vs _BOTTOM) is the content owners' call and flagging it would just be noise.
ACCIDENTAL_NAMES = [
    (" - copy", "the name Windows gives a duplicated file"),
    ("copy of ", "the name Windows gives a duplicated file"),
    (" (1)", "the name Windows gives a second copy"),
    (" (2)", "the name Windows gives a second copy"),
    ("untitled", "a placeholder name"),
    ("newfile", "a placeholder name"),
    (" - shortcut", "the name Windows gives a shortcut"),
]

VANILLA_TRADERS = {
    "prapor", "therapist", "fence", "skier", "peacekeeper", "mechanic",
    "ragman", "jaeger", "lighthousekeeper", "btr", "ref",
}

ANSI = {"red": "\033[31m", "yellow": "\033[33m", "green": "\033[32m",
        "dim": "\033[2m", "bold": "\033[1m", "off": "\033[0m"}


def colour(text: str, name: str) -> str:
    if not sys.stdout.isatty():
        return text
    return f"{ANSI[name]}{text}{ANSI['off']}"


# ------------------------------------------------------------------------------------------
# Reading configs
# ------------------------------------------------------------------------------------------

def strip_jsonc(text: str) -> str:
    """Remove comments and trailing commas, respecting string literals."""
    out, i, n, in_str = [], 0, len(text), False
    while i < n:
        c = text[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(text[i + 1]); i += 2; continue
            if c == '"':
                in_str = False
            i += 1; continue
        if c == '"':
            in_str = True; out.append(c); i += 1; continue
        if c == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "*":
            j = text.find("*/", i + 2)
            i = n if j == -1 else j + 2
            continue
        out.append(c); i += 1
    return re.sub(r",(\s*[}\]])", r"\1", "".join(out))


def load_schema() -> dict:
    if not SCHEMA_PATH.exists():
        sys.exit(f"Can't find the schema at {SCHEMA_PATH} - is this tool still in the mod's tools/ folder?")
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


# ------------------------------------------------------------------------------------------
# Diagnostics
# ------------------------------------------------------------------------------------------

class Diag:
    def __init__(self, code, severity, file, message, fix=None):
        self.code, self.severity, self.file = code, severity, file
        self.message, self.fix = message, fix


def levenshtein(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(cur[j - 1] + 1, prev[j] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def suggest(word: str, options) -> str | None:
    best, best_d = None, 3
    for o in options:
        d = levenshtein(word.lower(), o.lower())
        if d < best_d:
            best, best_d = o, d
    return best


def is_mongo_id(s) -> bool:
    return isinstance(s, str) and len(s) == 24 and all(c in "0123456789abcdef" for c in s)


def derive_id(stem: str) -> str:
    """The id an item filename becomes. Same formula as the server's DripIds (no role)."""
    import hashlib
    return hashlib.sha1(stem.encode("utf-8")).hexdigest()[:24].lower()


def derive_quest_id(stem: str) -> str:
    """The id a quest FILENAME becomes: the server's DripIds.Derive(stem, "quest").

    Verified byte-for-byte against the real SPTarkov Server.Core HashUtil on 2026-08-15
    (one-off C# probe over all 18 friendly stems plus the item-role form). If DripIds
    ever changes, this must be re-verified the same way - the flip's gates brick
    silently when the two sides drift. tools/convert-legacy.py carries the same mirror.
    """
    import hashlib
    return hashlib.sha1(f"{stem}:quest".encode("utf-8")).hexdigest()[:24].lower()


def looks_like_pack_item(s) -> bool:
    """SCREAMING_SNAKE_CASE with at least one underscore - the shape every DRIP filename has.

    Only used to decide how to word an error and whether a missing reference is probably
    a cross-pack one, never to change what loads. Mirrors the C# loader's heuristic.
    """
    return (isinstance(s, str) and "_" in s
            and all(c.isascii() and (c.isalnum() or c == "_") for c in s)
            and not any(c.islower() for c in s))


# ------------------------------------------------------------------------------------------
# check
# ------------------------------------------------------------------------------------------

def quest_ids_in(packs) -> set[str]:
    """Every quest id defined by the packs being checked, from their CustomQuests files.

    Two formats share that folder. A legacy file is a blob keyed by quest id, so its keys
    are ids. A friendly file is one quest whose id DERIVES from its filename - the same
    SHA1 rule the loader uses, verified 2026-08-15 - and a hand-written gate may quote
    either the derived id or the bare filename, so both count. Missing the derivation was
    the flip's regression: every rewritten gate would have read as undefined.
    """
    ids: set[str] = set()
    for pack in packs:
        qdir = pack / "CustomQuests"
        if not qdir.exists():
            continue
        for f in list(qdir.glob("*.jsonc")) + list(qdir.glob("*.json")):
            try:
                data = json.loads(strip_jsonc(f.read_text(encoding="utf-8-sig")))
            except json.JSONDecodeError:
                continue
            if not isinstance(data, dict):
                continue
            if "objectives" in data:            # friendly: id derives from the filename
                ids.add(derive_quest_id(f.stem))
                ids.add(f.stem)                   # may also be named directly
                continue
            ids |= set(data)
            ids |= {v.get("_id") for v in data.values()
                    if isinstance(v, dict) and v.get("_id")}
    return ids


def check_config(data: dict, rel: str, folder: pathlib.Path, schema: dict,
                 pack_has_bundles: bool = True, quest_ids: set[str] | None = None) -> list[Diag]:
    props = schema["properties"]
    known = list(props)
    traders = []
    for branch in props["traderId"].get("anyOf", []):
        traders += branch.get("enum", [])
    currencies = props["currency"]["enum"]
    d: list[Diag] = []

    # -- type ------------------------------------------------------------------------------
    kind = data.get("type")
    if kind is None:
        d.append(Diag("DRIP-101", "error", rel, "'type' is missing.",
                      'Add one of:  "type": "top",  "type": "bottom",  or  "type": "gear",'))
    elif not isinstance(kind, str) or kind.lower() not in TYPE_DIR:
        hint = suggest(str(kind), TYPE_DIR) if isinstance(kind, str) else None
        d.append(Diag("DRIP-101", "error", rel,
                      f'\'type\' is "{kind}", which isn\'t a kind of content DRIP knows.',
                      f'Did you mean "{hint}"?' if hint
                      else 'It must be "top", "bottom" or "gear".'))
        kind = None
    else:
        kind = kind.lower()

    is_gear = kind == "gear"
    is_clothing = kind in ("top", "bottom")

    # -- text ------------------------------------------------------------------------------
    # Text fields take either a plain string or a {language: text} map. A map must carry "en",
    # since that is the fallback every other language resolves through.
    for field in ("name", "shortName", "description"):
        val = data.get(field)
        if isinstance(val, dict) and "en" not in val:
            d.append(Diag("DRIP-107", "error", rel,
                          f"'{field}' gives text per language but has no English.",
                          "English is the fallback for every language you haven't listed. "
                          'Add:  "en": "..."'))

    if not data.get("name"):
        d.append(Diag("DRIP-104", "error", rel,
                      "'name' is missing - this is what players see in game.",
                      'Add:  "name": "Your item\'s name",'))
    if is_gear:
        if not data.get("shortName"):
            d.append(Diag("DRIP-105", "error", rel,
                          "'shortName' is missing - the short label shown on the item in your inventory.",
                          'Add:  "shortName": "6B2",'))
        if not data.get("description"):
            d.append(Diag("DRIP-106", "warning", rel,
                          "'description' is missing - the item will have blank flavour text."))
    elif is_clothing:
        for f in ("shortName", "description"):
            if f in data:
                d.append(Diag("DRIP-501", "warning", rel,
                              f"'{f}' isn't shown for clothing.", "You can delete it."))

    # -- trader ----------------------------------------------------------------------------
    trader = data.get("traderId")
    if not trader:
        d.append(Diag("DRIP-401", "error", rel,
                      "'traderId' is missing - nothing will sell this item.",
                      'Add:  "traderId": "georgia",'))
    elif trader not in traders and not is_mongo_id(trader):
        hint = suggest(trader, traders)
        d.append(Diag("DRIP-401", "error", rel, f'There\'s no trader called "{trader}".',
                      f'Did you mean "{hint}"?' if hint
                      else f"Use one of: {', '.join(traders)} - or a trader's 24-character ID."))

    # -- pricing ---------------------------------------------------------------------------
    copy_offers = data.get("copyOriginalOffers", True)
    needs_price = is_clothing or (is_gear and not copy_offers)
    has_price = "price" in data                      # presence, not truthiness: 0 is valid

    if needs_price and not has_price:
        d.append(Diag("DRIP-301", "error", rel,
                      "'price' is missing. This item has \"copyOriginalOffers\": false, so it needs its own price."
                      if is_gear else
                      "'price' is missing - clothing is always sold at its own price.",
                      'Add:  "price": 45000,' + (
                          '\nOr set "copyOriginalOffers": true to sell it wherever the original is sold.'
                          if is_gear else "")))
    if is_gear and copy_offers and has_price:
        d.append(Diag("DRIP-302", "warning", rel,
                      "'price' is ignored here - with \"copyOriginalOffers\": true the original item's price is used.",
                      'Either remove \'price\', or set "copyOriginalOffers": false to make it apply.'))
    if needs_price and "loyaltyLevel" not in data:
        d.append(Diag("DRIP-301", "error", rel,
                      "'loyaltyLevel' is missing - how far in with the trader a player must be.",
                      'Add:  "loyaltyLevel": 1,'))

    lvl = data.get("loyaltyLevel")
    if isinstance(lvl, int) and not 1 <= lvl <= 4:
        d.append(Diag("DRIP-303", "error", rel,
                      f"'loyaltyLevel' is {lvl} - traders only have levels 1 to 4."))
    if isinstance(data.get("price"), (int, float)) and data["price"] < 0:
        d.append(Diag("DRIP-305", "error", rel, f"'price' is {data['price']} - it can't be negative."))

    # A zero here is almost always left over from early testing rather than a deliberate
    # giveaway. Warn rather than fail: it loads fine, but somebody should look before release.
    # (The NoClothingRequirements option also zeroes clothing prices, but it does that at
    # runtime after loading - a zero written into a file is a different thing.)
    if data.get("price") == 0:
        d.append(Diag("DRIP-307", "warning", rel,
                      "'price' is 0, so this item is free.",
                      "If that wasn't deliberate, set a real price. Several items were left "
                      "at 0 during early testing."))

    cur = data.get("currency")
    if cur is not None and cur not in currencies:
        hint = suggest(str(cur), currencies)
        d.append(Diag("DRIP-304", "error", rel, f"'currency' is \"{cur}\".",
                      f'Did you mean "{hint}"?' if hint
                      else f"It must be one of: {', '.join(currencies)}. Leave it out for roubles."))

    if is_gear and ("profileLevel" in data or "standing" in data):
        d.append(Diag("DRIP-306", "warning", rel,
                      "'profileLevel' and 'standing' only apply to clothing.", "You can delete them."))

    # -- gear ------------------------------------------------------------------------------
    if is_gear:
        based = data.get("basedOn")
        if not based:
            d.append(Diag("DRIP-402", "error", rel,
                          "'basedOn' is missing - gear needs the ID of the item it's a retexture of.",
                          'Add:  "basedOn": "5df8a2ca86f7740bfe6df777",'))
        elif not is_mongo_id(based):
            n = len(based) if isinstance(based, str) else 0
            d.append(Diag("DRIP-403", "error", rel,
                          f"'basedOn' is \"{based}\" ({n} characters) - item IDs are 24 characters of 0-9 and a-f.",
                          "That's one character out - check for a typo when you copied it."
                          if n in (23, 25) else "Copy the ID from the item you're retexturing."))
        for slot, tpl in (data.get("includedParts") or {}).items():
            if not is_mongo_id(tpl):
                d.append(Diag("DRIP-407", "error", rel,
                              f"'includedParts' -> \"{slot}\" is \"{tpl}\", which isn't a 24-character item ID."))
        if data.get("includedParts") and copy_offers:
            d.append(Diag("DRIP-406", "warning", rel,
                          "'includedParts' is ignored when \"copyOriginalOffers\" is true - "
                          "the original item's parts are used."))
    elif "basedOn" in data:
        d.append(Diag("DRIP-404", "warning", rel,
                      "'basedOn' only applies to gear - clothing isn't cloned from another item.",
                      "You can delete it."))

    # -- bundles ---------------------------------------------------------------------------
    # Skipped entirely when the whole pack has no bundles: that's an un-bootstrapped checkout,
    # not 275 broken items, and it's reported once at pack level instead (DRIP-200).
    if pack_has_bundles:
        on_disk = {f.name for f in folder.glob("*.bundle")}
        for want in REQUIRED_BUNDLES.get(kind, []):
            if want not in on_disk:
                d.append(Diag("DRIP-201", "error", rel, f"Expected {want} in this item's folder.",
                              "That folder has no .bundle files at all - the bundle needs to sit next to this config."
                              if not on_disk else
                              f"The folder has: {', '.join(sorted(on_disk))}. Rename the right one to {want}."))
        for named in (data.get("bundles") or {}):
            if named not in on_disk:
                d.append(Diag("DRIP-202", "warning", rel,
                              f"'bundles' mentions {named}, but there's no {named} in this folder.",
                              "Either the name is misspelled, or the bundle hasn't been copied in yet."))

    # -- quest gates -------------------------------------------------------------------------
    # An item locked behind a quest that doesn't exist can never unlock, and nothing at runtime
    # says so - the item simply never becomes available. Only checked when the packs being
    # examined actually ship quests, so a content-only pack isn't told its gates are broken.
    # A gate may quote either spelling of a friendly quest's id - the derived MongoId or the
    # bare filename - and both resolve, because the loader resolves filenames the same way.
    if quest_ids:
        for wanted in data.get("questRequirements") or []:
            resolved = wanted if is_mongo_id(wanted) else derive_quest_id(str(wanted))
            if wanted not in quest_ids and resolved not in quest_ids:
                d.append(Diag("DRIP-502", "error", rel,
                              f"'questRequirements' needs quest \"{wanted}\", which nothing defines.",
                              "This item can never unlock. Either the quest id changed, or the "
                              "pack that provides that quest isn't installed."))

    # -- vanilla origin ----------------------------------------------------------------------
    # Without it the loader can't tell which bots a garment suits. Warned rather than errored:
    # the item still loads and is still buyable, it just won't appear on bots.
    if is_clothing and not data.get("vanillaOrigin"):
        d.append(Diag("DRIP-114", "warning", rel,
                      "'vanillaOrigin' is missing, so bots won't wear this garment.",
                      "Every DRIP garment is a retexture of a vanilla one, so this should "
                      "always be set - a missing one usually means something is wrong rather "
                      "than merely unfilled.\nIt isn't typed by hand. Run:  drip origins"))

    # -- unknown fields --------------------------------------------------------------------
    for key in data:
        if key in props or key in RESERVED:
            continue
        if key in RENAMED:
            new = RENAMED[key]
            d.append(Diag("DRIP-111", "warning", rel,
                          f"'{key}' isn't used any more - DRIP finds bundles by looking in this item's folder."
                          if new is None else
                          f"'{key}' was renamed to '{new}' in the new format.",
                          "Run tools/convert-legacy.py to update this file automatically."))
        else:
            hint = suggest(key, known)
            d.append(Diag("DRIP-110", "warning", rel,
                          f"'{key}' isn't a field DRIP knows, so it's being ignored.",
                          f"Did you mean '{hint}'?" if hint
                          else "Check the spelling against docs/CONFIG-SCHEMA-v2.md."))

    return d


def cmd_check(args) -> int:
    schema = load_schema()

    if args.path:
        base = pathlib.Path(args.path).resolve()
        if not base.exists():
            sys.exit(f"No such folder: {base}")
        packs = [base]
    else:
        if not PACKS_ROOT.exists():
            sys.exit(f"No content packs found at {PACKS_ROOT}")
        packs = [PACKS_ROOT / args.pack] if args.pack else sorted(
            p for p in PACKS_ROOT.iterdir() if p.is_dir())
        packs = [p for p in packs if p.exists()]
        if not packs:
            sys.exit(f"No content pack called {args.pack!r} in {PACKS_ROOT}")

    all_diags: list[Diag] = []
    checked = 0
    ids: dict[str, str] = {}
    known_quests = quest_ids_in(packs)
    every_item: list[tuple[str, dict]] = []
    every_quest: list[tuple[pathlib.Path, str, dict, pathlib.Path]] = []

    # Trader definitions are gathered across every pack being checked, not per pack: one pack
    # may legitimately sell through traders another one defines.
    trader_files = [t for p in packs for t in (p / "CustomTraders").glob("*.json")] \
        if not args.path else []

    for pack in packs:
        # Read everything first, so the bundle situation can be judged across the whole pack
        # before deciding how to report it.
        items = []
        # Normally the item folders; for a loose folder (--path, test fixtures) scan it whole.
        roots = [pack / s for s in ("CustomItems", "CustomClothing")]
        roots = [r for r in roots if r.exists()] or [pack]
        base = PACKS_ROOT if PACKS_ROOT in pack.parents or pack == PACKS_ROOT else pack.parent

        for root in roots:
            # .json5 is scanned too, so a leftover old-format file is reported rather than
            # ignored. An ignored one is worse than it sounds: the loader may well read it
            # alongside its converted replacement and define everything twice.
            for f in sorted(list(root.rglob("*.jsonc")) + list(root.rglob("*.json5"))):
                rel = f.relative_to(base).as_posix()
                try:
                    data = json.loads(strip_jsonc(f.read_text(encoding="utf-8-sig")))
                except json.JSONDecodeError as e:
                    all_diags.append(Diag("DRIP-001", "error", rel,
                                          f"This file isn't valid JSON - line {e.lineno}, character {e.colno}.",
                                          "A missing comma, a missing quote, or a stray bracket is the usual cause."))
                    continue
                if f.suffix == ".json5":
                    all_diags.append(Diag("DRIP-112", "warning", rel,
                                          "This is an old-format .json5 file.",
                                          "Convert it with tools/convert-legacy.py and delete the original - "
                                          "if both remain, the item can end up defined twice."))

                low = f.stem.lower()
                for needle, why in ACCIDENTAL_NAMES:
                    if needle in low:
                        all_diags.append(Diag(
                            "DRIP-113", "warning", rel,
                            f"The filename contains '{needle.strip()}' - {why}.",
                            "This file's name becomes the item's ID, so rename it to something "
                            "deliberate.\nDo it before release: renaming is free now, but once "
                            "players have the item it can't change."))
                        break
                items.append((f, rel, data))

        # "Most of the pack has no bundle" means an un-bootstrapped checkout - bundles are
        # deliberately kept out of git - and deserves one message. "A few are missing" means
        # genuine content bugs and deserves one message each. Same condition, opposite meanings,
        # so the volume is what tells them apart. Judging by proportion rather than by whether
        # any bundle exists at all keeps a handful of stray bundles from hiding the bootstrap
        # case.
        missing = sum(
            1 for f, _, data in items
            if any(want not in {b.name for b in f.parent.glob("*.bundle")}
                   for want in REQUIRED_BUNDLES.get(str(data.get("type", "")).lower(), []))
        )
        unbootstrapped = items and missing > len(items) / 2
        if unbootstrapped:
            all_diags.append(Diag(
                "DRIP-200", "warning", f"{pack.name}  (whole content pack)",
                f"{missing} of {len(items)} items have no bundle on disk, so they can't load yet.",
                "That's normal for a fresh clone - bundles are kept out of git. To populate them:\n"
                f"  python tools/convert-legacy.py --part 1 --out bundles/ContentPacks/{pack.name} --bundles link\n"
                "Everything else is still checked below."))

        # Same shape as the bundle case: if nothing anywhere defines DRIP's own traders, every
        # item that sells through one fails for one reason. Report the reason, once.
        needs_drip_traders = sorted({
            str(d.get("traderId")) for _, _, d in items
            if d.get("traderId") and str(d["traderId"]).lower() not in VANILLA_TRADERS
            and not is_mongo_id(str(d["traderId"]))
        })
        if needs_drip_traders and not trader_files and not args.path:
            affected = sum(1 for _, _, d in items
                           if str(d.get("traderId", "")).lower() in
                           {t.lower() for t in needs_drip_traders})
            all_diags.append(Diag(
                "DRIP-400", "warning", f"{pack.name}  (whole content pack)",
                f"Nothing defines {' or '.join(needs_drip_traders)}, so {affected} items have "
                "nowhere to be sold.",
                "DRIP's own traders are defined by the .json files in a pack's CustomTraders "
                "folder.\nEither add them here, or install the pack that provides them."))

        for f, rel, data in items:
            checked += 1
            all_diags += check_config(data, rel, f.parent, schema, not unbootstrapped,
                                      known_quests)

            stem = f.stem
            if stem in ids and ids[stem] != rel:
                all_diags.append(Diag("DRIP-102", "error", rel,
                                      f"This file and {ids[stem]} have the same name, so they'd become "
                                      "the same item - the second would overwrite the first.",
                                      "Rename one of them. The file's name is what gives the item its ID."))
            ids.setdefault(stem, rel)
            every_item.append((rel, data))

        # Friendly quest files: one quest per file, checked after the items exist because
        # their references resolve against the item table. The legacy blob (DRIP.jsonc and
        # its kind) is the loader's business - a hand-written one is a converter step, not
        # an authoring mistake, and its gates are already covered by DRIP-502 above.
        qdir = pack / "CustomQuests"
        if qdir.exists():
            for f in sorted(list(qdir.glob("*.jsonc")) + list(qdir.glob("*.json"))):
                rel = f.relative_to(base).as_posix()
                try:
                    data = json.loads(strip_jsonc(f.read_text(encoding="utf-8-sig")))
                except json.JSONDecodeError:
                    continue              # the item scan above already reports JSON errors
                if isinstance(data, dict) and "objectives" in data:
                    checked += 1
                    every_quest.append((f, rel, data, pack))

    traders: list[str] = []
    for branch in schema["properties"]["traderId"].get("anyOf", []):
        traders += branch.get("enum", [])

    game_diags, notes = game_checks(every_item, every_quest, set(ids), known_quests, traders)
    all_diags += game_diags

    return report(all_diags, checked, notes)


def game_checks(items: list, quests: list | None = None,
                item_stems: set[str] | None = None,
                known_quests: set[str] | None = None,
                traders: list[str] | None = None) -> tuple[list[Diag], list[str]]:
    """The checks that need the game's own database rather than just the schema.

    Opened once and shared, so a missing install produces one honest "not checked" note
    instead of the same apology twice. The quest checks still run their schema-only half
    (traders, filenames, images, objective text) when there is no database - only the
    MongoId-into-the-game half waits.
    """
    quests = quests or []
    item_stems = item_stems or set()
    known_quests = known_quests or set()
    traders = traders or []
    try:
        db = sptdb.open_database()
    except sptdb.NoDatabase as why:
        diags = quest_checks(quests, item_stems, known_quests, None, traders)
        return diags, ["Not checked: whether the game actually sells the items these are based "
                      f"on, whether the parts listed for them fit, and whether quest ids point "
                      f"into the game's own quests.\n{why}"]
    diags, notes = seller_check(items, db)
    diags += parts_check(items, db)
    diags += quest_checks(quests, item_stems, known_quests, db, traders)
    return diags, notes


def quest_checks(quests: list, item_stems: set[str], known_quests: set[str], db,
                 traders: list[str]):
    """Validate friendly-format quest files the way the item checks validate item files.

    A broken quest reference doesn't crash - it produces a quest nobody can complete or an
    item nobody can unlock, which a player discovers halfway through (QUEST-FORMAT-PROPOSAL
    section 6). These run before the server ever starts.

    Returns (diags, cross-pack-aggregated-packs) - the aggregation is finished by the
    caller because the pack-level message needs the pack name, which lives one frame up.
    """
    diags: list[Diag] = []
    # pack name -> list of (quest file, reference) that looks like a pack item no
    # checked pack ships. One message per pack at the end (CONFIG-SCHEMA-v2 section 8,
    # rule 6), not one per quest - a quest depending on another pack is normal.
    cross_pack: dict[str, list[tuple[str, str]]] = {}
    derived_items = {derive_id(s) for s in item_stems}

    for f, rel, data, pack in quests:
        stem = f.stem
        own_ids = {derive_quest_id(stem), stem}

        # -- trader --------------------------------------------------------------------
        # Same names the item check accepts, read from the same schema so the two cannot
        # drift. A quest's trader is SPT's MongoId field, so an unresolved alias is a load
        # failure - error, not warning.
        named = data.get("trader")
        if not named:
            diags.append(Diag("DRIP-503", "error", rel,
                              "'trader' is missing - nobody offers this quest.",
                              'Add:  "trader": "georgia",'))
        elif named not in traders and not is_mongo_id(named):
            hint = suggest(str(named), traders)
            diags.append(Diag("DRIP-503", "error", rel,
                              f'There\'s no trader called "{named}".',
                              f'Did you mean "{hint}"?' if hint
                              else f"Use one of: {', '.join(traders)} - or a trader's "
                                   "24-character ID."))

        for reward in data.get("rewards") or []:
            for field, label in (("standingWith", "a standing reward"),
                                 ("unlock", "an unlock reward")):
                named = reward.get(field)
                if named and named not in traders and not is_mongo_id(named):
                    hint = suggest(str(named), traders)
                    diags.append(Diag("DRIP-503", "error", rel,
                                      f'The quest gives {label} naming trader "{named}", which '
                                      "doesn't resolve.",
                                      f'Did you mean "{hint}"?' if hint
                                      else "Use one of the trader names, or a trader's ID."))

        # -- item references (handover targets, item rewards) ---------------------------
        refs: list[tuple[str, str]] = []
        for obj in data.get("objectives") or []:
            if obj.get("handover"):
                refs.append(("handover", str(obj["handover"])))
        for reward in data.get("rewards") or []:
            if reward.get("item"):
                refs.append(("item reward", str(reward["item"])))

        for kind, ref in refs:
            if is_mongo_id(ref):
                if ref in derived_items:
                    continue
                if db is None:
                    continue          # noted at pack level once - cannot check ids without it
                if ref in db.items:
                    continue
                diags.append(Diag(
                    "DRIP-504", "error", rel,
                    f'The {kind} names item "{ref}", which is neither a DRIP item nor one the '
                    "game knows.",
                    "A 24-character ID that resolves nowhere is usually a character out - "
                    "re-copy it, or write the DRIP item's filename instead."))
            elif ref in item_stems:
                continue
            elif looks_like_pack_item(ref):
                cross_pack.setdefault(pack.name, []).append((rel, ref))
            else:
                diags.append(Diag(
                    "DRIP-504", "error", rel,
                    f'The {kind} names "{ref}", which is neither an item ID nor a DRIP '
                    "filename.",
                    "Write the DRIP item's filename (they look like THIS_ONE) or a vanilla "
                    "item's 24-character ID."))

        # -- prerequisite quest ---------------------------------------------------------
        prereq = (data.get("requires") or {}).get("quest")
        if prereq is not None:
            if prereq in own_ids:
                diags.append(Diag(
                    "DRIP-505", "error", rel,
                    "This quest requires itself, so no player could ever start it.",
                    "Name a DIFFERENT quest, or delete 'requires.quest' if this one starts "
                    "freely."))
            elif is_mongo_id(prereq):
                if prereq not in known_quests and db is not None and prereq not in db.quests:
                    diags.append(Diag(
                        "DRIP-505", "error", rel,
                        f"This quest requires quest \"{prereq}\", which nothing defines - not "
                        "these packs, not the game.",
                        "A quest nobody can complete gating this one makes both unplayable. "
                        "Check the ID."))
            elif prereq not in known_quests:
                hint = None
                stems = {q for q in known_quests if not is_mongo_id(q)}
                if stems:
                    hint = suggest(str(prereq), stems)
                diags.append(Diag(
                    "DRIP-505", "error", rel,
                    f'This quest requires \"{prereq}\", which is not a quest filename any pack '
                    "here ships.",
                    f'Did you mean "{hint}"?' if hint
                    else 'Quest filenames are the .jsonc names in CustomQuests - e.g. "A_WILD_NIGHT".'))

        # -- image -----------------------------------------------------------------------
        # "image" either names one of the pack's own icons (a .png beside the quest
        # configs) or quotes a VANILLA icon - which is a MongoId stem resolved by the
        # client from its own files, nothing the pack ships. Only the first kind is
        # checkable here; warning about a vanilla reference would be noise.
        image = data.get("image")
        if image:
            wanted = pathlib.Path(str(image)).stem
            icons = {p.stem for p in (pack / "CustomQuests").rglob("*.png")} \
                if (pack / "CustomQuests").exists() else set()
            if wanted not in icons and not is_mongo_id(wanted):
                diags.append(Diag(
                    "DRIP-506", "warning", rel,
                    f'"image" names "{image}", but there is no {wanted}.png anywhere under '
                    "this pack's CustomQuests.",
                    "The quest loads and plays fine - the journal just shows a missing "
"picture.\nDrop the .png in beside the quest configs, or fix the name."))

        # -- objective text ----------------------------------------------------------------
        # The expander generates a sensible sentence when text is missing, so this is a
        # warning, not an error: players would read words nobody wrote.
        for obj in data.get("objectives") or []:
            if obj.get("text"):
                continue
            what = obj.get("handover") or obj.get("kill") or "?"
            count = obj.get("count", 1)
            verb = "Hand over" if obj.get("handover") else "Eliminate"
            diags.append(Diag(
                "DRIP-507", "warning", rel,
                f"An objective has no text, so players would read the auto-generated "
                f'"{verb} {count} x {what}."',
                'Add:  "text": "Hand over 2 Glock 17s.",  - the sentence players see in the journal.'))

    # -- cross-pack, aggregated to one message per pack (section 8, rule 6) --------------
    for pack_name, entries in cross_pack.items():
        missing = sorted({ref for _, ref in entries})
        files = sorted({rel for rel, _ in entries})
        diags.append(Diag(
            "DRIP-508", "warning", f"{pack_name}  (whole content pack)",
            f"{len(files)} quest(s) hand over or reward items no pack being checked ships: "
            f"{', '.join(missing)}.",
            "Either those items belong in this pack, or the pack that ships them isn't "
            "installed here.\nA quest depending on another pack is normal - it only breaks "
            "when that pack is missing. Checking all packs together clears this if they "
            "resolve."))

    return diags


def parts_check(items: list, db) -> list[Diag]:
    """Whether every part an item lists is one the game will actually accept.

    'includedParts' names what fills each slot of a cloned item. The slots are the game's,
    not ours, and each one carries its own list of what fits. Across every vanilla armour
    carrier, all 275 required soft-armour slots accept exactly one item - so a wrong ID in
    one is never a judgement someone made, it is a typo.

    It is worth catching because of how it fails: the game does not complain, it declines
    to fit the part. The slot ends up empty, the armour has a hole in it exactly where the
    author thought they had covered, and nothing anywhere says so.
    """
    diags: list[Diag] = []
    for rel, data in items:
        parts = data.get("includedParts") or {}
        if not parts:
            continue
        base = data.get("basedOn")
        if not is_mongo_id(str(base or "")) or base not in db.items:
            continue                      # already reported by the basedOn checks
        for slot, tpl in parts.items():
            if not is_mongo_id(str(tpl or "")):
                continue                  # already reported by DRIP-407
            allowed = db.slot_filter(base, slot)
            if allowed is None:
                names = db.slot_names(base)
                hint = suggest(str(slot), names)
                diags.append(Diag(
                    "DRIP-409", "error", rel,
                    f"{db.name_of(base)} has no slot called \"{slot}\", so this part has "
                    "nowhere to go and is ignored.",
                    f'Did you mean "{hint}"?' if hint else
                    ("The slots it does have are: " + ", ".join(names) if names else
                     "That item takes no parts at all - you can delete 'includedParts'.")))
                continue
            if tpl in allowed:
                continue
            # Where does the named part actually belong? Nearly always another slot of this
            # same item - the line was copied from the slot above and the ID left behind.
            belongs = [s for s in db.slot_names(base)
                       if s != slot and tpl in (db.slot_filter(base, s) or [])]

            if len(allowed) == 1:
                only = allowed[0]
                fix = (f'Only one part fits there. Change it to:\n  "{slot}": "{only}",')
                # Armour inserts routinely share a name with the one next to them, which is
                # how this gets written in the first place. Saying so beats a message that
                # looks like it is arguing with itself.
                if db.name_of(only) == db.name_of(tpl):
                    fix += (f'\nBoth parts are called "{db.name_of(tpl)}" - only the ID tells '
                            "them apart.")
            else:
                fix = ("What fits there is:\n  " +
                       "\n  ".join(f'"{a}"  ({db.name_of(a)})' for a in allowed[:8]) +
                       ("\n  ..." if len(allowed) > 8 else ""))

            if belongs:
                message = (f"'includedParts' puts the \"{belongs[0]}\" part into the "
                           f"\"{slot}\" slot, so \"{slot}\" is left empty and that part of "
                           f"the {db.name_of(base)} is unprotected.")
            else:
                message = (f"'includedParts' puts {db.name_of(tpl)} in the \"{slot}\" slot, "
                           f"but {db.name_of(base)} does not accept it there, so that slot "
                           "is left empty.")
            diags.append(Diag("DRIP-410", "error", rel, message, fix))
    return diags


def seller_check(items: list, db) -> tuple[list[Diag], list[str]]:
    """Which items the game has nowhere to sell.

    Three outcomes, and they need three different responses, which is the whole reason this
    is worth reading the game database for:

      sold          the original is on a trader's shelf - copying its offer works.
      quest-locked  the original is sold, but only after a quest. DRIP deliberately does not
                    copy those offers, so the item correctly has no shelf of its own. Nothing
                    to fix, and no message: warning about it would be a flag that fires on
                    healthy data.
      unsold        nothing sells the original at all, so copying its offer copies nothing
                    and the item can never be bought. That one is a real content bug.

    Kappa's server-side self-check sees all of this too, but at the point where it can only
    say "something is wrong" in a log. The author needs to know which of their files to open
    and what to type in it, which is the difference between an assertion and a work list.
    """
    diags: list[Diag] = []
    notes: list[str] = []

    unsold, quest_locked = [], 0
    for rel, data in items:
        if str(data.get("type", "")).lower() != "gear":
            continue
        # Absent means true - an item with no opinion is sold wherever the original is.
        if not data.get("copyOriginalOffers", True):
            continue
        base = data.get("basedOn")
        if not is_mongo_id(str(base or "")):
            continue                      # already reported by the basedOn checks
        verdict = db.traders.classify(base)
        if verdict == "quest-locked":
            quest_locked += 1
        elif verdict == "unsold":
            unsold.append((rel, base, db.name_of(base)))

    for rel, base, name in unsold:
        # Severity is Sophia's call, 2026-08-15: a warning, so the first releases can be cut
        # while the pricing queue waits for Colette and Amber - visible in every check, never
        # blocking a build, and no longer the first thing a fresh author sees as an "error".
        diags.append(Diag(
            "DRIP-408", "warning", rel,
            f"No trader sells {name}, so copying its offers gives this item nowhere to be "
            "sold and nobody can buy it.",
            'Give it a price of its own: set "copyOriginalOffers" to false, then add '
            '"price" and "loyaltyLevel".\n'
            "Prices for the rest of the set are in the spreadsheet - "
            'double-click "Review Prices.cmd".'))

    scope = f"game data: SPT {db.version} at {db.root}"
    if quest_locked:
        notes.append(
            f"{quest_locked} more item(s) are based on something a trader only sells after a "
            "quest.\n  DRIP leaves those alone on purpose, so they have no shelf either - "
            "that is correct and needs\n  no action. The server log counts them together with "
            f"the {len(unsold)} above.\n  ({scope})")
    else:
        notes.append(f"Checked against {scope}.")
    return diags, notes


def report(diags: list[Diag], checked: int, notes: list[str] | None = None) -> int:
    errors = [x for x in diags if x.severity == "error"]
    warnings = [x for x in diags if x.severity == "warning"]

    def print_notes():
        for note in notes or []:
            head, *rest = note.split("\n")
            print(colour(f"  Note: {head}", "dim"))
            for line in rest:
                print(colour(f"        {line.strip()}", "dim"))
            print()

    if not errors and not warnings:
        print(colour(f"\n  All good - {checked} item(s) checked, nothing to fix.\n", "green"))
        print_notes()
        return 0

    by_file: dict[str, list[Diag]] = {}
    for x in diags:
        by_file.setdefault(x.file, []).append(x)

    print()
    for file in sorted(by_file):
        print(colour(f"  {file}", "bold"))
        for x in sorted(by_file[file], key=lambda x: x.severity != "error"):
            mark = colour("error  ", "red") if x.severity == "error" else colour("warning", "yellow")
            print(f"    {mark}  {colour(x.code, 'dim')}  {x.message}")
            for line in (x.fix or "").split("\n"):
                if line:
                    print(f"                        {colour(line, 'dim')}")
        print()

    summary = (f"  {checked} item(s) checked - "
               f"{len(errors)} error(s), {len(warnings)} warning(s).")
    print(colour(summary, "red" if errors else "yellow"))
    print(colour("  Errors mean the item won't work as intended and need fixing. "
                 "Warnings are worth a look.", "dim"))
    print(colour("  Field reference: docs/CONFIG-SCHEMA-v2.md\n", "dim"))
    print_notes()
    return 1 if errors else 0


# ------------------------------------------------------------------------------------------
# new
# ------------------------------------------------------------------------------------------

TEMPLATES = {
    "gear": """// {name}
{{
  "$schema": "{schema}",
  "type": "gear",

  "name": "{name}",
  "shortName": "SHORT",
  "description": "Describe the item here.",

  // The item you're retexturing. `drip new` looks this ID up from the name you gave it;
  // to change it later, run `drip id <name>` to find the right one.
  "basedOn": "{based_on}",

  // Who sells this. 'moron' and 'georgia' are DRIP's own traders.
  "traderId": "{trader}",

  // true  = sold wherever the original item is sold, at the original price.
  // false = sold by the trader above, at your own price (then add "price" and "loyaltyLevel").
  "copyOriginalOffers": true
}}
""",
    "top": """// {name}
{{
  "$schema": "{schema}",
  "type": "top",

  "name": "{name}",

  // Who sells this. 'moron' and 'georgia' are DRIP's own traders.
  "traderId": "{trader}",

  "price": 50000,
  "loyaltyLevel": 1,
  "profileLevel": 1,
  "standing": 0
}}
""",
    "bottom": """// {name}
{{
  "$schema": "{schema}",
  "type": "bottom",

  "name": "{name}",

  // Who sells this. 'moron' and 'georgia' are DRIP's own traders.
  "traderId": "{trader}",

  "price": 50000,
  "loyaltyLevel": 1,
  "profileLevel": 1,
  "standing": 0
}}
""",
}


def ask(prompt: str, default: str | None = None, options=None) -> str:
    while True:
        suffix = f" [{default}]" if default else ""
        answer = input(f"  {prompt}{suffix}: ").strip() or (default or "")
        if not answer:
            print("     (needed)")
            continue
        if options and answer.lower() not in options:
            hint = suggest(answer, options)
            print(f"     must be one of: {', '.join(options)}"
                  + (f" - did you mean '{hint}'?" if hint else ""))
            continue
        return answer


def cmd_origins(args) -> int:
    """Read each garment's vanilla origin out of its bundle and write it into the config.

    Separate from `check` because it needs UnityPy, which `check` and `new` deliberately do
    not - those two must run with nothing installed.
    """
    # The recorded origins come first: tools/vanilla-origins.json is the source of truth, and
    # after the bundle rebuild it will be the ONLY source — rebuilt bundles won't carry their
    # vanilla lineage internally any more. Reading a bundle is the fallback for a garment
    # nobody has recorded yet.
    record_file = MOD_ROOT / "tools" / "vanilla-origins.json"
    record: dict[str, str] = {}
    if record_file.exists():
        record = json.loads(record_file.read_text(encoding="utf-8")).get("origins", {})

    UnityPy = None
    try:
        import UnityPy  # noqa: F811
    except ImportError:
        pass

    garment_bundle = {"top": "TOP.bundle", "bottom": "BOTTOM.bundle"}
    roots = ([PACKS_ROOT / args.pack] if args.pack
             else [p for p in PACKS_ROOT.iterdir() if p.is_dir()])

    filled, already, problems = 0, 0, []
    for pack in roots:
        for f in sorted((pack / "CustomClothing").rglob("*.jsonc")
                        if (pack / "CustomClothing").exists() else []):
            raw = f.read_text(encoding="utf-8-sig")
            try:
                data = json.loads(strip_jsonc(raw))
            except json.JSONDecodeError:
                continue
            kind = str(data.get("type", "")).lower()
            if kind not in garment_bundle:
                continue
            if data.get("vanillaOrigin"):
                already += 1
                continue

            origin = record.get(f"{f.stem}|{kind}")
            source = "recorded"

            if not origin:
                bundle = f.parent / garment_bundle[kind]
                if not bundle.exists():
                    problems.append(f"{f.stem}: nothing recorded for it, and no {bundle.name} "
                                    f"beside it to read one from")
                    continue
                if UnityPy is None:
                    problems.append(f"{f.stem}: nothing recorded for it, and reading it from "
                                    f"{bundle.name} needs UnityPy (pip install UnityPy)")
                    continue
                try:
                    origin = next((o.read().m_Name for o in UnityPy.load(str(bundle)).objects
                                   if o.type.name == "AssetBundle"), None)
                except Exception as exc:
                    problems.append(f"{f.stem}: couldn't read {bundle.name} "
                                    f"({type(exc).__name__})")
                    continue
                if not origin:
                    problems.append(f"{f.stem}: {bundle.name} doesn't name a vanilla origin")
                    continue
                source = f"read from {bundle.name}"

            # Insert before "bundles" if present, else before the closing brace.
            line = f'  "vanillaOrigin": {json.dumps(origin)},'
            lines = raw.splitlines()
            at = next((i for i, l in enumerate(lines) if l.strip().startswith('"bundles"')), None)
            if at is None:
                at = max(i for i, l in enumerate(lines) if l.strip() == "}")
                lines[at - 1] = lines[at - 1].rstrip() + ","
            lines.insert(at, line)
            f.write_text("\n".join(lines) + "\n", encoding="utf-8")
            filled += 1
            print(f"  {f.stem}\n      {origin}")

    print(f"\n  filled in {filled}, already had one {already}")
    if problems:
        print(f"  couldn't do {len(problems)}:")
        for p in problems:
            print(f"      {p}")
    print()
    return 1 if problems else 0


PLACEHOLDER_ID = "PUT_THE_24_CHARACTER_ID_HERE"


def resolve_base_item(given: str | None, interactive: bool) -> str:
    """Turn "slick" into 5e4abb5086f77406975c9342.

    This is the one question in the whole tool that a content author genuinely could not
    answer on their own - the 24-character ID isn't written anywhere they'd look, so the
    honest instruction used to be "ask a programmer". That is the exact dependency the mod
    exists to remove, so it is worth reading the game's item database to answer it.

    Always prints what it resolved to. A name search can land on something reasonable but
    wrong - "vest" is a real short name belonging to one specific armour - and a silent
    correct-looking answer is worse than a question.
    """
    try:
        db = sptdb.open_database()
    except sptdb.NoDatabase as why:
        if given and is_mongo_id(given.lower()):
            return given.lower()
        print(colour(f"\n  I can't look item names up right now.\n  {why}\n", "yellow"))
        if not interactive:
            return PLACEHOLDER_ID
        typed = ask("ID of the item you're retexturing", PLACEHOLDER_ID)
        return typed

    while True:
        typed = given or ask("Which item are you retexturing? (its name, e.g. Slick)")
        given = None
        found, matches = db.resolve_item(typed)

        if found:
            print(colour(f"     -> {db.name_of(found)}  ({found})", "dim"))
            return found

        if not matches:
            print(f"     Nothing wearable is called '{typed}'. Try fewer words, or part of "
                  "the name as it\n     appears in game - 'fast' rather than 'FAST MT "
                  "Super High Cut'.")
            if not interactive:
                return PLACEHOLDER_ID
            continue

        print(f"\n     {len(matches)} items match '{typed}':")
        for i, (tpl, name) in enumerate(matches[:12], 1):
            print(f"       {i:2d}. {name}")
        if len(matches) > 12:
            print(f"       ... and {len(matches) - 12} more - use more of the name to narrow it.")
        if not interactive:
            return PLACEHOLDER_ID

        pick = input("\n     Which one? (number, or type a better name): ").strip()
        if pick.isdigit() and 1 <= int(pick) <= min(len(matches), 12):
            tpl = matches[int(pick) - 1][0]
            print(colour(f"     -> {db.name_of(tpl)}  ({tpl})", "dim"))
            return tpl
        given = pick or None


def cmd_id(args) -> int:
    """Look up a vanilla item's ID by name, for editing a config that already exists.

    `drip new` asks for this as part of scaffolding, but the far more common case is opening
    a config written months ago and wanting to point it at a different vanilla item. Without
    this that means asking a programmer, which is the thing worth removing.
    """
    try:
        db = sptdb.open_database()
    except sptdb.NoDatabase as why:
        print(colour(f"\n  {why}\n", "yellow"))
        return 1

    text = " ".join(args.words)
    found, matches = db.resolve_item(text)
    if found:
        print(f"\n  {db.name_of(found)}")
        print(colour(f"  {found}\n", "bold"))
        return 0
    if not matches:
        print(f"\n  Nothing wearable is called '{text}'.")
        print("  Try fewer words, or part of the name as it appears in game.\n")
        return 1
    print(f"\n  {len(matches)} items match '{text}':\n")
    for tpl, name in matches[:20]:
        print(f"  {colour(tpl, 'bold')}  {name}")
    if len(matches) > 20:
        print(f"  ... and {len(matches) - 20} more.")
    print()
    return 0


def cmd_new(args) -> int:
    interactive = not args.where
    if interactive:
        print("\n  Making a new DRIP item. Press Ctrl-C to stop.\n")

    kind = (args.type or ask("What kind? (gear / top / bottom)", "gear", TYPE_DIR)).lower()
    where = args.where or ask("Where does it go? e.g. ARMOR/6B2/TIGERSTRIPE/ARMOR_6B2_TIGERSTRIPE")
    pack = args.pack or (ask("Which content pack?", "Essentials") if interactive else "Essentials")
    trader = args.trader or (ask("Which trader?", "georgia") if interactive else "georgia")
    name = args.name or (ask("What's it called in game?", pathlib.Path(where).stem.replace("_", " ").title())
                         if interactive else pathlib.Path(where).stem.replace("_", " ").title())
    based_on = PLACEHOLDER_ID
    if kind == "gear":
        based_on = resolve_base_item(args.based_on, interactive)

    sub = TYPE_DIR[kind]
    if kind in ("top", "bottom") and not where.upper().startswith(("TOPS/", "BOTTOMS/")):
        where = f"{'TOPS' if kind == 'top' else 'BOTTOMS'}/{where}"

    dest = PACKS_ROOT / pack / sub / f"{where}.jsonc"
    if dest.exists():
        sys.exit(f"\n  {dest.relative_to(MOD_ROOT)} already exists - pick another name.\n")

    import os
    schema_rel = pathlib.PurePath(
        os.path.relpath(SCHEMA_PATH, dest.parent)).as_posix()

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(TEMPLATES[kind].format(
        name=name, trader=trader, schema=schema_rel, based_on=based_on), encoding="utf-8")

    print(colour(f"\n  Created  {dest.relative_to(MOD_ROOT)}", "green"))
    print(f"\n  Next:")
    print(f"    1. Put {' and '.join(REQUIRED_BUNDLES[kind])} in the same folder:")
    print(colour(f"       {dest.parent.relative_to(MOD_ROOT)}", "dim"))
    print(f"    2. Fill in the config - your editor will autocomplete and flag mistakes.")
    print(f"    3. Run  drip check  before starting the server.\n")
    return 0


# ------------------------------------------------------------------------------------------

def cmd_menu(_args):
    """The double-click entry point: ask what you want, run it.

    Each choice re-enters main() with a real argv, so the menu goes through the
    identical parsing and validation as the command line - there is no second
    implementation of anything to drift. Nothing here writes on its own.
    """
    while True:
        print()
        print("  What would you like to do?")
        print()
        print("    1. Check my content packs for mistakes")
        print("    2. Make a new item")
        print("    3. Find a vanilla item's ID from its name")
        print("    4. Build a release zip (for players to download)")
        print("    5. Read the instructions")
        print("    6. Exit")
        print()
        try:
            choice = input("  Type a number and press Enter: ").strip()
        except (EOFError, KeyboardInterrupt):
            # Closing the window is a fine way to leave.
            return 0
        if choice in ("6", "q", "quit", "exit"):
            return 0
        def run(argv):
            """Dispatch one menu action; EOF or Ctrl-C comes back to the menu."""
            sys.argv = argv
            try:
                main()
            except (EOFError, KeyboardInterrupt):
                print("\n  Stopped - back to the menu.\n")

        if choice == "1":
            run(["drip", "check"])
        elif choice == "2":
            kind = input("  Making gear, a top, or a bottom? ").strip().lower()
            run(["drip", "new"] + ([kind] if kind else []))
        elif choice == "3":
            words = input("  Part of the item's in-game name (e.g. slick): ").strip()
            if words:
                run(["drip", "id"] + words.split())
            else:
                print("  Nothing typed - back to the menu.")
        elif choice == "4":
            # The real build tool, run as itself - the menu never reimplements it.
            # It checks content and release-readiness first, so a broken pack stops
            # here with a work list rather than shipping.
            import subprocess
            print("\n  Building release archives (this checks everything first)...\n")
            try:
                subprocess.run([sys.executable, str(HERE / "build-release.py"), "--all"])
            except KeyboardInterrupt:
                print("\n  Stopped - back to the menu.\n")
            print("\n  Output lands in the dist/ folder when it succeeds.\n")
        elif choice == "5":
            print(__doc__)
            print("  Full instructions: docs/AUTHORING.md")
        else:
            print("  Pick a number from 1 to 6 (6 to exit).")


def main() -> int:
    ap = argparse.ArgumentParser(
        prog="drip", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)

    c = sub.add_parser("check", help="check content packs for mistakes")
    c.add_argument("pack", nargs="?", help="one content pack; omit to check all")
    c.add_argument("--path", default=None,
                   help="check a folder outside the content packs (test fixtures, "
                        "or a pack before you copy it in)")
    c.set_defaults(func=cmd_check)

    o = sub.add_parser("origins",
                       help="fill in 'vanillaOrigin' for clothing that's missing it")
    o.add_argument("pack", nargs="?", help="one content pack; omit for all")
    o.set_defaults(func=cmd_origins)

    i = sub.add_parser("id", help="find a vanilla item's ID from its name")
    i.add_argument("words", nargs="+", help="part of the item's in-game name")
    i.set_defaults(func=cmd_id)

    n = sub.add_parser("new", help="scaffold a new item config")
    n.add_argument("type", nargs="?", choices=sorted(TYPE_DIR), help="gear, top or bottom")
    n.add_argument("where", nargs="?", help="path within the pack, without the extension")
    n.add_argument("--pack", default=None, help="content pack (default: Essentials)")
    n.add_argument("--trader", default=None, help="who sells it (default: georgia)")
    n.add_argument("--name", default=None, help="in-game name")
    n.add_argument("--based-on", default=None, metavar="NAME_OR_ID",
                   help="the item being retextured - its name ('slick') or its 24-character ID")
    n.set_defaults(func=cmd_new)

    m = sub.add_parser("menu",
                       help="interactive menu (what you get on a double-click)")
    m.set_defaults(func=cmd_menu)

    args = ap.parse_args()
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\n  Stopped.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
