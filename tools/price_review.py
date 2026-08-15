#!/usr/bin/env python3
"""
Price review: put every price in a spreadsheet, take the edits back safely.

    python price_review.py export         make the review spreadsheet
    python price_review.py apply          read it back, show a diff, then write

Normally driven by "Review Prices.cmd" in the mod folder, so the people who own this content
never touch a terminal.

Two things this must never do: change anything without showing what changed first, and let a
reviewed price be silently reverted later. The second is why edits land in
tools/price-overrides.json, which the converter also reads, rather than only in the config
files the converter regenerates.
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import xlsx_lite
from xlsx_lite import Cell, EDIT, FLAG, HEADER, LOCKED, MONEY

MOD_ROOT = pathlib.Path(__file__).resolve().parent.parent
PACKS_ROOT = MOD_ROOT / "bundles" / "ContentPacks"
OVERRIDES_FILE = MOD_ROOT / "tools" / "price-overrides.json"
DEFAULT_SHEET = MOD_ROOT / "Prices to review.xlsx"

COLUMNS = [
    ("Item", 30), ("What it is", 34), ("Set", 16), ("Kind", 8), ("Sold by", 10),
    ("Level", 9), ("Price now", 13), ("Currency", 10), ("Comes with", 26),
    ("NEW PRICE", 13), ("Others in this set", 26), ("Worth a look?", 18), ("Why", 52),
]
LEVEL_COL = 5
NEW_PRICE_COL = 9

# 20 of the 171 priced items are in dollars or euros, and a bare number cannot say which.
# The number typed into NEW PRICE is written straight back into "price" without touching
# "currency", so a rouble-shaped edit to a dollar item is a silent 120x error - and the two
# it would most likely hit are armour priced at 1,360 and 2,450, which look far too cheap
# next to a set priced in roubles and are not.
#
# No set mixes currencies, so "Others in this set" and the "Odd for the set" flag compare
# like with like and were never wrong. This column exists for the comparison a person makes
# across sets, and for the unit they are typing in.

# Numbers that read as someone having fun rather than pricing an item. Flagged gently -
# several are almost certainly deliberate, and it is not this tool's place to decide.
NOVELTY_NUMBERS = {1337, 6969, 42069, 69420, 69696, 80085, 420666, 420690, 421337}

# Gear and clothing gate on different fields, and the sheet used to show only one of them:
# 'profileLevel' is clothing's, and gear never has it (drip check warns if it does). So the
# Level column was blank for all 35 priced gear rows and nobody noticed, because a blank
# cell in a column that is often blank looks like data.
LEVEL_FIELD = {"gear": "loyaltyLevel"}
DEFAULT_LOYALTY = 1


def level_field_for(data: dict) -> str:
    return LEVEL_FIELD.get(str(data.get("type", "")).lower(), "profileLevel")


# ------------------------------------------------------------------------------------------
# Reading the content packs
# ------------------------------------------------------------------------------------------

def strip_jsonc(text: str) -> str:
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


def load_items(include_unpriced: frozenset = frozenset()) -> list[dict]:
    """Every priced item across every content pack, with its folder 'set' for comparison.

    `include_unpriced` adds items that have no price *and need one* - the ones whose original
    nothing sells, so "sold wherever the original is sold" sells them nowhere. They are the
    reason this sheet exists right now, and without them it cannot ask the question.
    """
    items = []
    if not PACKS_ROOT.exists():
        sys.exit(f"No content packs at {PACKS_ROOT}")
    for pack in sorted(p for p in PACKS_ROOT.iterdir() if p.is_dir()):
        for sub in ("CustomItems", "CustomClothing"):
            root = pack / sub
            if not root.exists():
                continue
            for f in sorted(root.rglob("*.jsonc")):
                try:
                    data = json.loads(strip_jsonc(f.read_text(encoding="utf-8-sig")))
                except json.JSONDecodeError:
                    continue
                if "price" not in data and f.stem not in include_unpriced:
                    continue  # sold at the original item's price; nothing to review
                # Group by the model folder, which is what makes two prices comparable:
                #   CustomClothing/BOTTOMS/GORKA4/SKOL/FILE   -> GORKA4
                #   CustomItems/ARMOR/6B23/CLEARSKY/FILE      -> 6B23
                # The level above is only a category (ARMOR, FACE) and lumps together items
                # that have no business being priced alike.
                rel = f.relative_to(root).parts
                group = rel[1] if len(rel) > 2 else (rel[0] if len(rel) > 1 else "-")
                items.append({
                    "stem": f.stem, "path": f, "pack": pack.name, "data": data, "set": group,
                    "unpriced": "price" not in data,
                })
    return items


# ------------------------------------------------------------------------------------------
# What the game knows: which items have no seller, and what ships inside each one
# ------------------------------------------------------------------------------------------

def from_game_database() -> tuple[frozenset, dict, list[str]]:
    """Returns (stems needing a price, stem -> what ships with it, notes).

    Two things the content files cannot answer on their own:

    **Which items have no seller.** Identical rule to `drip check`'s DRIP-408 - gear, copying
    the original's offers, and no reachable trader selling that original. Deliberately derived
    rather than listed, so this sheet and that check can never drift apart about which items
    are affected.

    **What comes inside each one.** The anchor a reviewer reaches for is the vanilla handbook
    price, and for a plate carrier that is the price of the *bare shell* - the assembled item
    is 28x to 50x more. Someone pricing a 360,000-rouble carrier at 12,710 has done something
    reasonable with the number in front of them, and nothing afterwards looks wrong. That is
    the failure this column exists to make impossible, without telling anyone what to charge.

    Degrades to an empty answer with a note. A sheet that quietly omitted the 13 would look
    exactly like a sheet that had nothing to ask.
    """
    try:
        import sptdb
        db = sptdb.open_database()
    except Exception as why:
        return frozenset(), {}, [
            "Could not read the game's files, so this sheet is missing two things:",
            "  - the items that have no seller yet (they are the ones that need a price most)",
            "  - the 'Comes with' column, which says what ships inside each item",
            f"  {str(why).splitlines()[0] if str(why) else why}",
        ]

    handbook = {e["Id"]: e["Price"] for e in json.loads(
        (db.db / "templates" / "handbook.json").read_text(encoding="utf-8"))["Items"]}
    presets = json.loads(
        (db.db / "globals.json").read_text(encoding="utf-8"))["ItemPresets"]
    default_preset = {}
    for p in presets.values():
        root = p["_items"][0]
        if p.get("_encyclopedia") == root["_tpl"]:
            default_preset[root["_tpl"]] = {
                i.get("slotId"): i["_tpl"] for i in p["_items"][1:]
                if i.get("parentId") == root["_id"]}

    def required_slots(tpl):
        props = (db.items.get(tpl) or {}).get("_props") or {}
        return {s["_name"] for s in (props.get("Slots") or []) if s.get("_required")}

    needs, comes = set(), {}
    for it in load_items(include_unpriced=ALL_STEMS):
        data, base = it["data"], it["data"].get("basedOn")
        if not base or base not in db.items:
            continue
        copy_offers = data.get("copyOriginalOffers", True)
        if it["unpriced"] and copy_offers and db.traders.classify(base) == "unsold":
            needs.add(it["stem"])

        # What will ship inside it: its own parts list if it has one, otherwise vanilla's.
        parts = data.get("includedParts") or (
            default_preset.get(base, {}) if it["unpriced"] else {})
        if not parts:
            continue
        req = required_slots(base)
        total = sum(handbook.get(t, 0) for t in parts.values())
        plates = sum(handbook.get(t, 0) for s, t in parts.items() if s not in req)
        comes[it["stem"]] = (total, plates, handbook.get(base, 0))
    return frozenset(needs), comes, []


class _All(frozenset):
    """`stem in ALL_STEMS` is always true - lets one loader serve both passes."""
    def __contains__(self, item):  # noqa: D105
        return True


ALL_STEMS = _All()


# ------------------------------------------------------------------------------------------
# "Worth a look?" — placeholder detection
# ------------------------------------------------------------------------------------------

def add_flags(items: list[dict]) -> None:
    """Flag prices that look like template leftovers rather than decisions.

    Zero was findable because it's conspicuous. These are the ones that aren't: a level no
    sibling uses, a price well outside its set, a set that prices by level with one member
    that doesn't fit.
    """
    by_set = collections.defaultdict(list)
    for it in items:
        by_set[(it["set"], it["data"].get("type"))].append(it)

    for it in items:
        price = it["data"].get("price")
        level = it["data"].get("profileLevel")
        siblings = [s for s in by_set[(it["set"], it["data"].get("type"))]
                    if s is not it and isinstance(s["data"].get("price"), (int, float))]
        sib_prices = sorted(s["data"]["price"] for s in siblings)
        it["siblings"] = sib_prices

        flags, why = [], []

        if it.get("unpriced"):
            flags.append("Needs a price")
            why.append("Nothing in the game sells the item this is a retexture of, so it has "
                       "no shelf and nobody can buy it. A price here is what fixes that.")
            total, plates = it.get("comes_with") or (0, 0)
            if total:
                why.append(f"Careful with the obvious anchor: the plain item is worth "
                           f"{it.get('shell_price', 0):,} in the handbook, but this ships "
                           f"with {total:,} of armour inside it"
                           + (f" ({plates:,} of that in plates)." if plates else "."))

        if price == 0:
            flags.append("Free")
            why.append("Priced at 0, so players get it for nothing.")

        if sib_prices and isinstance(price, (int, float)) and price:
            med = statistics.median(sib_prices)
            if med and (price > med * 1.75 or price < med * 0.55):
                flags.append("Odd for the set")
                why.append(f"The rest of {it['set']} sits around {med:,.0f}, "
                           f"this one is {price:,.0f}.")

        if isinstance(price, (int, float)) and int(price) in NOVELTY_NUMBERS:
            flags.append("Joke number")
            why.append("Looks like a placeholder someone typed for fun - "
                       "fine if it's deliberate.")

        it["flags"] = " / ".join(flags)
        it["why"] = " ".join(why)

        # Deliberately NOT flagged: a profileLevel no sibling uses. In a set that prices by
        # level, every rung is the only one at its level, so that fires on all of them and
        # says nothing. The "Others in this set" column already gives the reviewer the range
        # they need to judge it. A flag that cries wolf is worse than no flag.


# ------------------------------------------------------------------------------------------
# export
# ------------------------------------------------------------------------------------------

def cmd_export(args) -> int:
    needs_price, comes_with, notes = from_game_database()
    items = load_items(include_unpriced=needs_price)
    if not items:
        sys.exit("No priced items found. Has the content been converted yet?")
    for it in items:
        total, plates, shell = comes_with.get(it["stem"]) or (0, 0, 0)
        it["comes_with"], it["shell_price"] = (total, plates), shell
    add_flags(items)

    # The ones that cannot be bought at all come first: they are the question being asked.
    items.sort(key=lambda i: (not i["unpriced"], not i["flags"], i["set"], i["stem"]))

    rows = [[Cell(name, HEADER) for name, _ in COLUMNS]]
    for it in items:
        d = it["data"]
        sib = it["siblings"]
        sib_text = "-" if not sib else (
            f"{sib[0]:,}" if len(set(sib)) == 1 and len(sib) > 1 and sib[0] == sib[-1]
            else f"{min(sib):,} - {max(sib):,}" if min(sib) != max(sib) else f"{sib[0]:,}")
        if sib and len(set(sib)) == 1:
            sib_text = f"all {sib[0]:,}"
        if not sib and it["unpriced"]:
            # Every one of the 13 sits in a set where nothing else is priced either, so this
            # column - normally the most useful one - has nothing to offer them. Say that,
            # rather than showing a dash that reads as missing data.
            sib_text = "none priced yet"
        total, plates = it["comes_with"]
        comes_text = "-" if not total else (
            f"{total:,} of armour" + (f" ({plates:,} in plates)" if plates else ""))

        # An item with no price yet needs a loyalty level too, or it fails to load. That is a
        # judgement about how far in with the trader it sits, so it is asked rather than
        # assumed - a second yellow cell, pre-filled with the answer most people want.
        level_value = d.get(level_field_for(d), "")
        level_cell = (Cell(DEFAULT_LOYALTY, EDIT) if it["unpriced"]
                      else Cell(level_value if level_value is not None else "", LOCKED))

        rows.append([
            Cell(it["stem"], LOCKED),
            Cell(d.get("name", ""), LOCKED),
            Cell(it["set"], LOCKED),
            Cell(str(d.get("type", "")), LOCKED),
            Cell(str(d.get("traderId", "")), LOCKED),
            level_cell,
            Cell("not sold yet", LOCKED) if it["unpriced"] else Cell(d.get("price"), MONEY),
            Cell(str(d.get("currency") or "roubles"), LOCKED),
            Cell(comes_text, LOCKED),
            Cell(None, EDIT),                     # the column they fill in
            Cell(sib_text, LOCKED),
            Cell(it["flags"], FLAG if it["flags"] else LOCKED),
            Cell(it["why"], LOCKED),
        ])

    out = pathlib.Path(args.out) if args.out else DEFAULT_SHEET
    xlsx_lite.write(out, rows, [w for _, w in COLUMNS], sheet_name="Prices")

    flagged = sum(1 for i in items if i["flags"])
    unpriced = sum(1 for i in items if i["unpriced"])
    print(f"\n  Made:  {out.name}")
    print(f"  {len(items)} items, {flagged} worth a look.")
    if unpriced:
        print(f"  {unpriced} of them have no price at all yet and are listed first - "
              "nothing sells them.")
    for note in notes:
        print(f"  {note}")
    print()
    print("  Open it, put new numbers in the NEW PRICE column (the yellow one),")
    print("  leave everything else alone, save, and run this again to apply.\n")
    if unpriced:
        # For whoever is about to send this on, not for the people filling it in - which is
        # why it prints here and appears nowhere in the sheet.
        print("  Before sending: the wording in this sheet has not had Sophia's Gate 1 pass.")
        print("  Rows with no price also need a trader level; theirs is the second yellow "
              "cell,\n  filled in with 1 already.\n")
    return 0


# ------------------------------------------------------------------------------------------
# apply
# ------------------------------------------------------------------------------------------

def parse_price(text: str):
    """Accept 45000, 45,000, '45 000', £45000 — people type prices in all sorts of ways."""
    if text is None:
        return None
    cleaned = re.sub(r"[^\d.\-]", "", str(text).strip())
    if cleaned in ("", "-", "."):
        return None
    try:
        value = float(cleaned)
    except ValueError:
        return None
    return int(round(value))


def cmd_apply(args) -> int:
    sheet = pathlib.Path(args.file) if args.file else DEFAULT_SHEET
    if not sheet.exists():
        sys.exit(f"\n  Can't find {sheet.name}. Run the export step first.\n")

    try:
        rows = (xlsx_lite.read(sheet) if sheet.suffix.lower() == ".xlsx"
                else [line.split(",") for line in
                      sheet.read_text(encoding="utf-8-sig").splitlines()])
    except Exception as exc:
        sys.exit(f"\n  Couldn't read {sheet.name}: {exc}\n"
                 "  If you saved it in a different format, save it as .xlsx and try again.\n")

    # Load the unpriced ones too, or a sheet that asked about them cannot be read back.
    needs_price, _, _ = from_game_database()
    items = {i["stem"]: i for i in load_items(include_unpriced=needs_price)}
    changes, problems = [], []

    for n, row in enumerate(rows[1:], start=2):
        if not row or not row[0].strip():
            continue
        stem = row[0].strip()
        it = items.get(stem)
        if it is None:
            problems.append(f"row {n}: no item called '{stem}' - was the Item column edited?")
            continue
        if len(row) <= NEW_PRICE_COL:
            continue
        new = parse_price(row[NEW_PRICE_COL])
        if new is None:
            continue
        if new < 0:
            problems.append(f"row {n}: {stem} - a price can't be negative ({new})")
            continue
        old = it["data"].get("price")
        if old == new:
            continue

        # An item with no price also needs a loyalty level and needs to stop deferring to the
        # original's offer. Without all three it loads as an error rather than as an item.
        loyalty = None
        if it["unpriced"]:
            loyalty = parse_price(row[LEVEL_COL]) if len(row) > LEVEL_COL else None
            if loyalty is None:
                loyalty = DEFAULT_LOYALTY
            if not 1 <= loyalty <= 4:
                problems.append(f"row {n}: {stem} - Level is {loyalty}, but traders only have "
                                "levels 1 to 4.")
                continue
        changes.append((stem, old, new, it, loyalty))

    if problems:
        print("\n  Problems in the spreadsheet:\n")
        for p in problems:
            print(f"    {p}")
        print("\n  Nothing has been changed. Fix those and run again.\n")
        return 1

    if not changes:
        print("\n  No new prices filled in - nothing to change.\n")
        return 0

    # Show everything before touching anything.
    print(f"\n  {len(changes)} price(s) to change:\n")
    print(f"    {'item':<36} {'from':>12} {'to':>12}")
    for stem, old, new, _, loyalty in changes:
        old_text = "not sold yet" if old is None else f"{old:,}"
        extra = f"   (goes on sale at trader level {loyalty})" if loyalty is not None else ""
        print(f"    {stem:<36} {old_text:>12} {new:>12,}{extra}")

    if not args.yes:
        print()
        answer = input("  Apply these? [y/N] ").strip().lower()
        if answer not in ("y", "yes"):
            print("\n  Left alone. Nothing changed.\n")
            return 0

    # 1. Record in the overrides file, so the converter can't revert them.
    doc = json.loads(OVERRIDES_FILE.read_text(encoding="utf-8")) if OVERRIDES_FILE.exists() \
        else {"overrides": {}}
    doc.setdefault("overrides", {})
    for stem, old, new, _, loyalty in changes:
        fields = {"price": new, "why": "set during price review"}
        if loyalty is not None:
            # All three, or the converter regenerates an item that still has no seller.
            fields |= {"loyaltyLevel": loyalty, "copyOriginalOffers": False}
        doc["overrides"][stem] = fields
    OVERRIDES_FILE.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")

    # 2. Write into the config files themselves, so the change takes effect now.
    written = 0
    for stem, old, new, it, loyalty in changes:
        text = it["path"].read_text(encoding="utf-8")
        if loyalty is None:
            updated, count = re.subn(r'("price"\s*:\s*)-?[\d.]+', rf"\g<1>{new}", text, count=1)
        else:
            # No price line to replace - this item deferred to the original's offer and has
            # to stop. Anchor on copyOriginalOffers so the new lines land beside the comment
            # that explains what they mean.
            updated, count = re.subn(
                r'("copyOriginalOffers"\s*:\s*)true',
                lambda m: (f'{m.group(1)}false,\n'
                           f'  "price": {new},\n'
                           f'  "loyaltyLevel": {loyalty}'),
                text, count=1)
        if count != 1:
            problems.append(f"{stem}: couldn't find the line to update - left alone")
            continue
        it["path"].write_text(updated, encoding="utf-8")
        written += 1

    print(f"\n  Updated {written} item(s), and recorded them in {OVERRIDES_FILE.name}")
    if problems:
        print("\n  But these need a look:")
        for p in problems:
            print(f"    {p}")
    print("\n  Run 'drip check' if you'd like to confirm everything still looks right.\n")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)

    e = sub.add_parser("export", help="make the review spreadsheet")
    e.add_argument("--out", default=None)
    e.set_defaults(func=cmd_export)

    a = sub.add_parser("apply", help="read the spreadsheet back and write the changes")
    a.add_argument("--file", default=None)
    a.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
    a.set_defaults(func=cmd_apply)

    args = ap.parse_args()
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\n  Stopped. Nothing changed.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
