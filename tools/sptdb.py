#!/usr/bin/env python3
"""
Reads the game's own database, so DRIP's tools can answer two questions an author
otherwise has to ask a programmer:

    "what's the 24-character ID for the Slick?"      -> resolve_item("slick")
    "which of my items has no trader to sell it?"    -> TraderIndex

Standard library only, like the rest of the tools. Everything here is READ-ONLY -
nothing in this file ever writes to an SPT install.

Why this exists at all, given `drip check` was deliberately built not to need the game
database: the two questions above are the ones the content owners cannot answer without a
coder, which is the exact dependency DRIP exists to remove. The check that reads this is
additive and degrades to a printed note when no install is configured - a missing database
is never reported as the author's mistake.

The database is read at the state DRIP actually sees it. DRIP loads at PostDBModLoader + 2
(400,002) and Fence's assort is generated at TraderCallbacks (800,000), so Fence has no
assort when DRIP looks - and Fence's on-disk assort.json is empty, so reading from disk
agrees with the running server rather than contradicting it. Verified, not assumed.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import unicodedata

HERE = pathlib.Path(__file__).resolve().parent
MOD_ROOT = HERE.parent
PATH_FILE = HERE / "spt-path.txt"

MONGO_ID = re.compile(r"^[a-f0-9]{24}$")

# The categories a DRIP retexture can belong to, used to keep a name search over 4,500 items
# from returning ammunition when someone types "vest".
#
# Named rather than hard-coded by ID, and there are three of them rather than one, because
# the obvious single-root guess is wrong: rigs and backpacks hang off `SearchableItem`, not
# off `Equipment`, so filtering on `Equipment` alone silently drops every TacTec, A18 and
# bag in the game - a third of what DRIP retextures - and returns a confident "no matches".
WEARABLE_ROOTS = ("Equipment", "Vest", "Backpack")


# Cyrillic letters that are drawn identically to a Latin one. The game's own item names
# contain a few, some of them BSG's typos - three keys are spelt "Сity key" with a Cyrillic
# C. Transliterating those would give "Sity key"; they are lookalikes, so map them across.
LOOKALIKES = str.maketrans({
    "А": "A", "В": "B", "Е": "E", "К": "K", "М": "M",
    "Н": "H", "О": "O", "Р": "P", "С": "C", "Т": "T",
    "Х": "X", "а": "a", "е": "e", "о": "o", "р": "p",
    "с": "c", "у": "y", "х": "x",
    "’": "'", "‘": "'", "“": '"', "”": '"',
    "–": "-", "—": "-", "…": "...", " ": " ",
})


def ascii_only(text: str) -> str:
    """Fold text that came out of the game into something a Windows console can print.

    Not cosmetic. `sys.stdout` on a stock Windows console is cp1252, and printing the
    Cyrillic T in "7.62x25mm TT FMJ43" raises UnicodeEncodeError - so a game name reaching
    the screen unfolded does not look wrong, it ends the run in a Python traceback. Ten of
    the 5,155 item names are affected, and any of them can turn up in a search result or a
    list of what fits a slot.

    Folding here, where game text enters, rather than at each print, because the rule is
    about the source of the text and not about any one message.
    """
    if text.isascii():
        return text
    swapped = text.translate(LOOKALIKES)
    decomposed = unicodedata.normalize("NFKD", swapped)
    return "".join(c for c in decomposed if c.isascii())


class NoDatabase(Exception):
    """Raised with a message written for someone who has never seen a config file."""


# ------------------------------------------------------------------------------------------
# Finding an install


def database_under(install: pathlib.Path):
    """The database folder for an install root, or None if that isn't one.

    Two layouts are accepted because both are real: a normal SPT install keeps the server in
    a `SPT/` subfolder next to EscapeFromTarkov.exe, but the server can also be unpacked on
    its own. Probing for the database rather than for the .exe means a server-only copy still
    works, and neither layout has to be the "right" one.
    """
    for candidate in (install / "SPT" / "SPT_Data" / "database",
                      install / "SPT_Data" / "database"):
        if candidate.is_dir():
            return candidate
    return None


def find_spt() -> pathlib.Path:
    """Locate an SPT install, or raise NoDatabase explaining exactly what to do.

    Deliberately refuses to guess between several installs. This machine has three, on two
    different SPT versions, and one of them belongs to another team's measurement corpus -
    silently picking the wrong one would produce confident answers about the wrong game.
    """
    env = os.environ.get("DRIP_SPT_PATH")
    if env:
        p = pathlib.Path(env)
        if database_under(p):
            return p
        raise NoDatabase(
            f"DRIP_SPT_PATH is set to {env}, but there's no SPT install there.\n"
            "It should point at the folder holding EscapeFromTarkov.exe.")

    if PATH_FILE.exists():
        line = next((l.strip() for l in PATH_FILE.read_text(encoding="utf-8").splitlines()
                     if l.strip() and not l.startswith("#")), "")
        p = pathlib.Path(line)
        if line and database_under(p):
            return p
        raise NoDatabase(
            f"tools/spt-path.txt points at {line or '(nothing)'}, "
            "but there's no SPT install there.\n"
            "    Edit that file so it holds the folder that has EscapeFromTarkov.exe in it.")

    # Installed case: <SPT>/SPT/user/mods/DRIP/tools/ - just walk up. Needs no setup at all.
    for parent in MOD_ROOT.parents:
        if database_under(parent):
            return parent

    # Development case: the mod lives outside any install. Look for siblings, but only
    # accept an unambiguous answer.
    candidates = []
    for parent in list(MOD_ROOT.parents)[:3]:
        for child in sorted(parent.iterdir()) if parent.is_dir() else []:
            if child.is_dir() and database_under(child) and child not in candidates:
                candidates.append(child)
        if candidates:
            break

    if len(candidates) == 1:
        return candidates[0]
    if candidates:
        listed = "\n".join(f"      {c}" for c in candidates)
        raise NoDatabase(
            "There's more than one SPT install here, so I won't guess which one to read:\n"
            f"{listed}\n"
            "    Put the one you want in tools/spt-path.txt (one line, just the path).")
    raise NoDatabase(
        "I couldn't find an SPT install to read the game's item data from.\n"
        "    Put its path in tools/spt-path.txt - one line, the folder that has "
        "EscapeFromTarkov.exe in it.")


def version_of(spt: pathlib.Path) -> str:
    """Best-effort version string, so any number this module produces can name its scope.

    Worth the effort because this machine runs two SPT versions and the trader data differs
    between them - a seller count with no version on it invites being quoted against the
    wrong install.
    """
    for probe in (spt / "SPT" / "SPT.Server.deps.json", spt / "SPT.Server.deps.json"):
        try:
            found = re.search(r'"SPTarkov\.Server\.Core/([0-9.]+)',
                              probe.read_text(encoding="utf-8"))
            if found:
                return found.group(1)
        except Exception:
            continue
    return "unknown version"


# ------------------------------------------------------------------------------------------
# The database


class Database:
    def __init__(self, spt: pathlib.Path):
        self.root = spt
        self.db = database_under(spt)
        self.version = version_of(spt)
        self._items = None
        self._names = None
        self._traders = None
        self._roots = None
        self._quests = None

    # -- quests ---------------------------------------------------------------------------

    @property
    def quests(self) -> set:
        """Every quest id the game itself ships.

        Read for quest prerequisites: a DRIP quest may legitimately gate behind a vanilla
        quest, and a MongoId prerequisite is only checkable against the ids that exist.
        """
        if self._quests is None:
            qfile = self.db / "templates" / "quests.json"
            self._quests = set(json.loads(qfile.read_text(encoding="utf-8")))
        return self._quests

    # -- items ---------------------------------------------------------------------------

    @property
    def items(self) -> dict:
        if self._items is None:
            self._items = json.loads(
                (self.db / "templates" / "items.json").read_text(encoding="utf-8"))
        return self._items

    @property
    def names(self) -> dict:
        """tpl -> (name, shortName), English."""
        if self._names is None:
            loc = json.loads(
                (self.db / "locales" / "global" / "en.json").read_text(encoding="utf-8"))
            out = {}
            for key, value in loc.items():
                tpl, _, kind = key.partition(" ")
                if kind == "Name":
                    out.setdefault(tpl, ["", ""])[0] = ascii_only(value)
                elif kind == "ShortName":
                    out.setdefault(tpl, ["", ""])[1] = ascii_only(value)
            self._names = {k: tuple(v) for k, v in out.items()}
        return self._names

    def name_of(self, tpl: str) -> str:
        return (self.names.get(tpl) or ("", ""))[0] or tpl

    @property
    def wearable_roots(self) -> set:
        if self._roots is None:
            self._roots = {
                tpl for tpl, entry in self.items.items()
                if entry.get("_type") == "Node" and entry.get("_name") in WEARABLE_ROOTS
            }
        return self._roots

    def is_wearable(self, tpl: str) -> bool:
        roots = self.wearable_roots
        cur, seen = tpl, 0
        while cur and seen < 20:
            if cur in roots:
                return True
            cur = (self.items.get(cur) or {}).get("_parent")
            seen += 1
        return False

    def slots_of(self, tpl: str) -> list:
        return ((self.items.get(tpl) or {}).get("_props") or {}).get("Slots") or []

    def slot_filter(self, tpl: str, slot: str):
        """What the game will accept in one slot of one item.

        Returns None if the item has no such slot, otherwise the list of item IDs allowed
        in it. That list is very often a single entry: across every vanilla armour carrier,
        all 275 required soft-armour slots accept exactly one item and nothing else. So a
        wrong ID there is never a judgement an author made - it is a typo, and the game
        drops the part rather than fitting it.
        """
        for entry in self.slots_of(tpl):
            if entry.get("_name") != slot:
                continue
            filters = (entry.get("_props") or {}).get("filters") or [{}]
            return list(filters[0].get("Filter") or [])
        return None

    def slot_names(self, tpl: str) -> list:
        return [s.get("_name") for s in self.slots_of(tpl) if s.get("_name")]

    def resolve_item(self, text: str) -> tuple[str | None, list[tuple[str, str]]]:
        """Turn what an author typed into an item ID.

        Returns (id, matches). An exact ID passes straight through. Otherwise the text is
        matched against English names and short names, and only equipment is considered -
        an author retexturing something is retexturing something wearable.

        A single match resolves; several come back for the caller to offer as a choice.
        Ranked so that an exact short-name hit ("Slick") beats an incidental substring.
        """
        text = text.strip()
        if MONGO_ID.match(text.lower()):
            return text.lower(), []

        needle = text.lower()
        scored = []
        for tpl, (name, short) in self.names.items():
            entry = self.items.get(tpl)
            if not entry or entry.get("_type") != "Item" or not self.is_wearable(tpl):
                continue
            n, s = name.lower(), short.lower()
            if needle == s or needle == n:
                rank = 0
            elif s.startswith(needle) or n.startswith(needle):
                rank = 1
            elif needle in s or needle in n:
                rank = 2
            else:
                continue
            scored.append((rank, name, tpl))

        scored.sort(key=lambda x: (x[0], x[1]))
        matches = [(tpl, name) for _, name, tpl in scored]
        if len(matches) == 1:
            return matches[0][0], []
        # One exact hit outranking everything else is an answer, not a choice.
        if matches and scored[0][0] == 0 and (len(scored) == 1 or scored[1][0] != 0):
            return matches[0][0], []
        return None, matches

    # -- traders -------------------------------------------------------------------------

    @property
    def traders(self) -> "TraderIndex":
        if self._traders is None:
            self._traders = TraderIndex(self.db / "traders")
        return self._traders


class TraderIndex:
    """Which traders sell what, and which of those offers are locked behind a quest.

    `roots` holds only top-level offers - the entries whose parentId is "hideout". A child
    row in an assort is a plate or a strap fitted into an offer, not something you can buy on
    its own, so counting them would make an unsellable item look sellable.
    """

    def __init__(self, traders_dir: pathlib.Path):
        self.roots: dict[str, list[tuple[str, str]]] = {}
        self.locked: set[tuple[str, str]] = set()
        self.trader_count = 0
        for tdir in sorted(p for p in traders_dir.iterdir() if p.is_dir()):
            assort = tdir / "assort.json"
            if not assort.exists():
                continue
            self.trader_count += 1
            try:
                data = json.loads(assort.read_text(encoding="utf-8")) or {}
            except Exception:
                continue
            for row in data.get("items") or []:
                if row.get("parentId") == "hideout" and row.get("_tpl"):
                    self.roots.setdefault(row["_tpl"], []).append((tdir.name, row["_id"]))
            quest_assort = tdir / "questassort.json"
            if quest_assort.exists():
                try:
                    qd = json.loads(quest_assort.read_text(encoding="utf-8")) or {}
                except Exception:
                    continue
                for phase in qd.values():
                    for assort_id in (phase or {}):
                        self.locked.add((tdir.name, assort_id))

    def classify(self, tpl: str) -> str:
        """'sold', 'quest-locked' or 'unsold' for a base item.

        The three are genuinely different situations with different right answers, which is
        why this returns a category rather than a boolean.
        """
        offers = self.roots.get(tpl)
        if not offers:
            return "unsold"
        if all(o in self.locked for o in offers):
            return "quest-locked"
        return "sold"


_CACHE: dict[str, Database] = {}


def open_database() -> Database:
    """The one entry point. Raises NoDatabase with an author-readable message."""
    if "db" not in _CACHE:
        _CACHE["db"] = Database(find_spt())
    return _CACHE["db"]
