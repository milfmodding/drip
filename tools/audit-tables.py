#!/usr/bin/env python3
"""Check that every hand-written repair in convert-legacy.py still matches something.

Read-only. Writes nothing, changes nothing, and exits 1 if it finds a dead entry.

WHY THIS EXISTS
---------------
convert-legacy.py carries four tables of deliberate repairs, each keyed by a value someone
typed by hand: OVERRIDES, RENAMES, PROMOTIONS and SLOT_FIXES. An entry whose key matches no
source file does not fail. It does not warn. It matches nothing, repairs nothing, and the
conversion reports success -- so the item it was written to fix goes out broken, and the table
still reads as though the fix is in place.

That is not hypothetical. During development a base-item ID was typed for the wrong armour and
would have silently repaired nothing; it was caught by checking the entry against the game's
slot filters, not by reading it.

Renaming or removing a source file has the same effect, which is the more likely way this bites
someone in the future: the table entry survives its subject.

WHAT IT DELIBERATELY DOES NOT CHECK
-----------------------------------
QUEST_ID_MAP is excluded, and that exclusion is the point rather than an oversight.

The four tables above are *repair* tables: each entry asserts "a specific broken thing exists,
and here is its correction". An entry matching nothing is therefore a defect.

QUEST_ID_MAP is a *reference* table: it maps all 19 DRIP quest IDs to their renumbered form.
Only 15 are currently used to gate an item. The other 4 are not dead -- completeness is the
property you want in a lookup map, so that an item gated on any quest resolves without anyone
having to extend the table first. Auditing it would report 4 problems that are not problems,
every run, forever, and the first person to "fix" the noise would delete four correct entries.

Repair tables want every entry used. Reference tables want every case covered. Do not merge
these two ideas into one check.

USAGE
    python tools/audit-tables.py
"""

import importlib.util
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
LEGACY_ROOT = HERE.parent.parent / "DRIP-3.x-main" / "ContentPacks"
PARTS = ["DRIP Part 1 (Essentials)", "DRIP Part 2", "DRIP Part 3"]


def load_converter():
    """convert-legacy.py has a hyphen in its name, so it cannot be imported normally."""
    spec = importlib.util.spec_from_file_location("convert_legacy", HERE / "convert-legacy.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_corpus(conv):
    """Every legacy config across all three parts, plus a note for any that would not parse."""
    configs, unreadable = {}, []
    for part in PARTS:
        root = LEGACY_ROOT / part
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.json5")):
            try:
                configs[path] = conv.read_legacy(path)[0]
            except Exception as why:
                unreadable.append((path, why))
    return configs, unreadable


def main() -> int:
    if not LEGACY_ROOT.is_dir():
        print(f"\n  Can't audit: the 3.x source tree isn't at\n  {LEGACY_ROOT}\n")
        print("  This tool compares the repair tables against the files they repair, so it")
        print("  needs that tree. Nothing is wrong with your install; there is just nothing")
        print("  here to check against.\n")
        return 0

    conv = load_converter()
    configs, unreadable = read_corpus(conv)

    stems = {path.stem for path in configs}
    bases = {cfg.get("baseItemID") for cfg in configs.values()}

    # A population that came out empty would make every entry look dead. Say so instead.
    if not stems:
        print(f"\n  Read 0 configs from {LEGACY_ROOT}. Not reporting anything as dead;\n"
              "  an empty corpus makes every table entry look unused.\n")
        return 1

    tables = [
        ("OVERRIDES", "a field this file corrects", list(conv.OVERRIDES),
         lambda key: key in stems, "no source config with that name"),
        ("RENAMES", "a file that ships under a different name", list(conv.RENAMES),
         lambda key: key in stems, "no source config with that name"),
        ("PROMOTIONS", "a file that moves between parts", list(conv.PROMOTIONS),
         lambda key: key in stems, "no source config with that name"),
        ("SLOT_FIXES", "a part put in the wrong slot", list(conv.SLOT_FIXES),
         lambda key: key[0] in bases, "no source config is based on that item"),
    ]

    print(f"\n  Checked against {len(configs)} source configs "
          f"({len(stems)} names, {len(bases)} base items).\n")

    dead_total = 0
    for name, what, keys, matches, why_dead in tables:
        dead = [key for key in keys if not matches(key)]
        dead_total += len(dead)
        state = "OK" if not dead else f"{len(dead)} DEAD"
        print(f"  {name:<12} {len(keys):>3} entries, each naming {what:<38} {state}")
        for key in dead:
            print(f"      {key!r}\n          {why_dead}")

    if unreadable:
        print(f"\n  {len(unreadable)} source file(s) could not be read, so any table entry")
        print("  pointing at one of them was not checked:")
        for path, why in unreadable:
            print(f"      {path.name}: {why}")

    print()
    if dead_total:
        print(f"  {dead_total} entry(ies) repair nothing.\n")
        print("  An entry that matches nothing is not harmless. It reads like a fix that is")
        print("  in place, so whatever it was written to correct is going out uncorrected.")
        print("  Either the key is wrong, or the file it named has been renamed or removed.\n")
        return 1

    print("  Every repair still has something to repair.\n")
    print("  Not checked: whether each repair is the RIGHT value -- only that its subject")
    print("  exists. A correctly-spelled key holding a wrong ID passes this and still\n"
          "  repairs the wrong thing. 'drip check' derives some of those independently.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
