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


# ------------------------------------------------------------------------------------------
# check
# ------------------------------------------------------------------------------------------

def quest_ids_in(packs) -> set[str]:
    """Every quest id defined by the packs being checked, from their CustomQuests files."""
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
            if isinstance(data, dict):
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
    if quest_ids:
        for wanted in data.get("questRequirements") or []:
            if wanted not in quest_ids:
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

    game_diags, notes = game_checks(every_item)
    all_diags += game_diags

    return report(all_diags, checked, notes)


def game_checks(items: list) -> tuple[list[Diag], list[str]]:
    """The checks that need the game's own database rather than just the schema.

    Opened once and shared, so a missing install produces one honest "not checked" note
    instead of the same apology twice.
    """
    try:
        db = sptdb.open_database()
    except sptdb.NoDatabase as why:
        return [], ["Not checked: whether the game actually sells the items these are based "
                    f"on, and whether the parts listed for them fit.\n{why}"]
    diags, notes = seller_check(items, db)
    diags += parts_check(items, db)
    return diags, notes


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
        diags.append(Diag(
            "DRIP-408", "error", rel,
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
        print("    4. Read the instructions")
        print("    5. Exit")
        print()
        try:
            choice = input("  Type a number and press Enter: ").strip()
        except (EOFError, KeyboardInterrupt):
            # Closing the window is a fine way to leave.
            return 0
        if choice in ("5", "q", "quit", "exit"):
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
            print(__doc__)
            print("  Full instructions: docs/AUTHORING.md")
        else:
            print("  Pick a number from 1 to 5 (5 to exit).")


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
