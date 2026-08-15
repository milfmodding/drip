#!/usr/bin/env python3
"""
Sets a machine up for authoring DRIP content, and reports what it actually did.

Run it through Setup.cmd rather than directly - that checks for Python first, which this
script obviously cannot do.

Two rules shape everything here, both learned from failures on this project:

  Say what you SKIPPED, not just what passed. A setup that exits 0 having quietly not
  checked something is the same shape as a verification tool reporting 547/547 over a
  population it could not see. Every step below reports one of done / found / skipped, and
  skipped is printed as loudly as failed.

  Refuse to guess, on anything that picks a target. This machine has three SPT installs
  across two versions and one of them is another team's measurement corpus. A setup script
  that helpfully picks one would eventually pick that one, and would be confidently wrong
  in a way nobody would notice for days.

Nothing here writes to an SPT install. The only file it creates is tools/spt-path.txt.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sptdb  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
MOD_ROOT = HERE.parent
PACKS_ROOT = MOD_ROOT / "bundles" / "ContentPacks"
VSCODE = MOD_ROOT / ".vscode" / "settings.json"

# Sibling of the clone - the same place build-release.py looks for it.
BUNDLE_STORE = MOD_ROOT.parent / "DRIP-bundles"

# --- bundle download ----------------------------------------------------------------------
# These three names are the contract with build-release.py, which WRITES them (it can't be
# imported - hyphen in the filename). "latest/download" needs no version: whatever release
# is newest serves the assets, so Setup never has to know one.
STORE_RELEASE = "https://github.com/milfmodding/drip/releases/latest/download"
STORE_MANIFEST = "DRIP-bundle-store.json"
# DRIP_STORE_URL overrides the release base (for testing this flow without a release).
STORE_URL = os.environ.get("DRIP_STORE_URL", STORE_RELEASE)

OK, INFO, TODO, SKIP = "  ok  ", " info ", " todo ", "SKIPPED"

_results: list[tuple[str, str]] = []


def say(mark: str, text: str, *detail: str) -> None:
    _results.append((mark, text))
    print(f"  [{mark}]  {text}")
    for line in detail:
        print(f"            {line}")


def interactive() -> bool:
    return sys.stdin is not None and sys.stdin.isatty()


def prompt(label: str) -> str:
    """input() that treats "no answer possible" as "skip" rather than as a crash.

    isatty() is not a reliable guard on Windows shells, so the EOF has to be caught here too
    - otherwise running this from a script turns a skippable step into a stack trace.
    """
    try:
        return input(label).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return ""


# ------------------------------------------------------------------------------------------


def step_python() -> None:
    v = sys.version_info
    say(OK, f"Python {v.major}.{v.minor}.{v.micro}",
        "The tools use the standard library only - there is nothing else to install.")


def step_spt() -> None:
    """Find the SPT install, or write spt-path.txt after asking. Never picks one silently."""
    try:
        db = sptdb.open_database()
        rel = "tools/spt-path.txt" if sptdb.PATH_FILE.exists() else "found automatically"
        say(OK, f"SPT {db.version} at {db.root}", f"({rel})")
        return
    except sptdb.NoDatabase as why:
        first = str(why).splitlines()[0]

    # Offer the ones we can see, but make the human choose which.
    candidates: list[pathlib.Path] = []
    for parent in list(MOD_ROOT.parents)[:3]:
        if not parent.is_dir():
            continue
        for child in sorted(parent.iterdir()):
            if child.is_dir() and sptdb.database_under(child) and child not in candidates:
                candidates.append(child)
        if candidates:
            break

    if not candidates or not interactive():
        say(TODO, "No SPT install configured.", first,
            "Two checks need it: what a vanilla item is called, and whether",
            "any trader sells it. Everything else works without it.",
            f"Fix: put the path in {sptdb.PATH_FILE}")
        return

    print(f"\n  [{TODO}]  Which SPT install should the tools read?")
    print("            (Only ever read from, never written to.)\n")
    for i, c in enumerate(candidates, 1):
        version = sptdb.version_of(c)
        print(f"              {i}. {c}   (SPT {version})")
    print("              0. skip - decide later\n")

    pick = prompt("            Number: ")
    if not pick.isdigit() or not 1 <= int(pick) <= len(candidates):
        say(TODO, "SPT install not set - skipped.",
            "Two checks stay off: what a vanilla item is called, and whether any",
            "trader sells it. Everything else works without them.",
            f"Fix: put the path in {sptdb.PATH_FILE}")
        return

    chosen = candidates[int(pick) - 1]
    sptdb.PATH_FILE.write_text(
        "# Which SPT install DRIP's tools read the game's item data from.\n"
        "# One line, no quotes: the folder that has EscapeFromTarkov.exe in it.\n"
        "# Only ever read, never written to. Written by Setup.cmd; safe to edit by hand.\n"
        f"\n{chosen}\n", encoding="utf-8")
    sptdb._CACHE.clear()
    say(OK, f"SPT {sptdb.version_of(chosen)} at {chosen}", "Written to tools/spt-path.txt")


def step_editor() -> None:
    """Confirm the schema actually binds. It is inert if it doesn't, and looks fine either way."""
    if not VSCODE.exists():
        say(TODO, "No .vscode/settings.json, so VS Code won't check configs as you type.")
        return
    try:
        settings = json.loads(
            re.sub(r"^\s*//.*$", "", VSCODE.read_text(encoding="utf-8"), flags=re.M))
    except Exception as e:
        say(TODO, f".vscode/settings.json isn't valid JSON ({e}).",
            "VS Code will ignore it, so configs get no autocomplete and no error checking.")
        return

    schemas = settings.get("json.schemas") or []
    targets = [MOD_ROOT / str(s.get("url", "")).lstrip("./") for s in schemas if s.get("url")]
    missing = [t for t in targets if not t.exists()]
    if not targets:
        say(TODO, ".vscode/settings.json defines no schema, so configs get no autocomplete.")
    elif missing:
        say(TODO, f"The schema it points at isn't there: {missing[0]}",
            "Autocomplete and inline error checking will silently do nothing.")
    else:
        say(OK, "VS Code will autocomplete and error-check DRIP configs.",
            "Open a file under bundles/ContentPacks to see it - a typo in a field",
            "name should underline in red straight away. If it doesn't, say so:",
            "that is the one way this can look set up and not be.")


def _fetch(url: str, dest: pathlib.Path) -> None:
    """Stream a file to disk with progress, so a multi-GB part isn't a silent minute."""
    with urllib.request.urlopen(url, timeout=60) as r, open(dest, "wb") as out:
        total = int(r.headers.get("Content-Length") or 0)
        done, next_report = 0, 0
        while chunk := r.read(1 << 20):
            out.write(chunk)
            done += len(chunk)
            if total and done >= next_report:
                print(f"            {done / (1024 ** 2):6.0f} / {total / (1024 ** 2):.0f} MB",
                      end="\r", flush=True)
                next_report = done + 200 * (1 << 20)      # every ~200 MB
    print()


def download_bundles() -> tuple[bool, list[str]]:
    """Fetch the bundle store from the latest GitHub release. Returns (ok, notes)."""
    notes: list[str] = []
    downloads = MOD_ROOT / "dist" / "downloads"
    downloads.mkdir(parents=True, exist_ok=True)

    try:
        manifest_path = downloads / STORE_MANIFEST
        _fetch(f"{STORE_URL}/{STORE_MANIFEST}", manifest_path)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except urllib.error.HTTPError as e:
        notes.append(f"no store manifest at the release ({e.code})")
        return False, notes
    except (urllib.error.URLError, OSError, ValueError) as e:
        notes.append(f"couldn't reach the download ({type(e).__name__}: {e})")
        return False, notes

    parts = manifest.get("parts") or []
    if not parts:
        notes.append("the manifest lists no parts")
        return False, notes

    for name in parts:
        target = downloads / name
        try:
            _fetch(f"{STORE_URL}/{name}", target)
        except (urllib.error.HTTPError, urllib.error.URLError, OSError) as e:
            notes.append(f"{name} didn't download ({type(e).__name__}: {e})")
            return False, notes

        # Each part is an independent zip: extract it, verify it, and only then continue -
        # a corrupt part stops the install with the part named rather than a broken store.
        try:
            with zipfile.ZipFile(target) as z:
                bad = z.testzip()
                if bad:
                    notes.append(f"{name} is corrupt at {bad}")
                    return False, notes
                z.extractall(BUNDLE_STORE)
        except zipfile.BadZipFile:
            notes.append(f"{name} isn't a valid zip (delete it from the release and re-upload)")
            return False, notes
        notes.append(f"{name}: extracted")

    return True, notes


def step_bundles() -> None:
    if not PACKS_ROOT.exists():
        say(TODO, f"No content packs at {PACKS_ROOT}.")
        return
    # Item configs only. Counting every .jsonc would sweep in quests and traders and report a
    # number one or two higher than `drip check` says, which reads as one of them being wrong.
    configs = sum(1 for d in ("CustomItems", "CustomClothing")
                  for _ in PACKS_ROOT.rglob(f"*/{d}/**/*.jsonc"))
    bundles = sum(1 for _ in PACKS_ROOT.rglob("*.bundle"))
    if bundles:
        say(OK, f"{configs} item configs and {bundles} bundles on disk.")
        return

    say(TODO, f"{configs} item configs, no .bundle files - fetching them now...")
    ok, notes = download_bundles()
    for n in notes:
        print(f"            {n}")
    if not ok:
        print("            Either the bundle store hasn't been uploaded as a release asset yet,")
        print("            or this machine has no connection to github.com.")
        print("            With the legacy corpus on disk instead, populate by hand:")
        print("              python tools/convert-legacy.py --part 1 "
              "--out bundles/ContentPacks/Essentials --bundles link")
        return

    # The store is populated; mirror its bundles into the packs so the loader sees them.
    copied = 0
    for pack_dir in (p for p in BUNDLE_STORE.iterdir() if p.is_dir()):
        target_pack = PACKS_ROOT / pack_dir.name
        if not target_pack.exists():
            continue                     # a pack this checkout's configs don't have
        for bundle in pack_dir.rglob("*.bundle"):
            target = target_pack / bundle.relative_to(pack_dir)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(bundle, target)
            copied += 1

    bundles = sum(1 for _ in PACKS_ROOT.rglob("*.bundle"))
    if bundles:
        say(OK, f"Downloaded the bundle store and copied {copied} bundles into the packs.",
            f"Store: {BUNDLE_STORE}")
    else:
        say(TODO, "Download ran but no bundles landed in the packs.",
            "Tell whoever set up the release - the assets extracted but matched nothing.")


CONTENT: list[str] = []


def step_check() -> None:
    """Run the real tool rather than reimplementing its summary - one source of truth.

    Reported separately from the setup steps. Setup being finished and the content being
    correct are different claims, and rolling them together is how "all set" ends up printed
    over thirteen real errors.
    """
    proc = subprocess.run([sys.executable, str(HERE / "drip.py"), "check"],
                          capture_output=True, text=True, cwd=str(MOD_ROOT))
    tail = [l for l in proc.stdout.splitlines() if "checked" in l]
    headline = tail[-1].strip() if tail else "drip check produced no summary."
    if proc.returncode != 0:
        CONTENT.append(headline)
    say(OK if proc.returncode == 0 else INFO, headline,
        "Run  drip check  yourself any time - it is the same command.")


# ------------------------------------------------------------------------------------------


def main() -> int:
    print()
    for step in (step_python, step_spt, step_editor, step_bundles, step_check):
        try:
            step()
        except Exception as e:                     # a broken step must not hide the others
            say(TODO, f"{step.__name__} could not finish: {e}")
        print()

    todo = [t for m, t in _results if m == TODO]
    print("  " + "-" * 68)
    if todo:
        print(f"\n  Setup done, with {len(todo)} thing(s) left:\n")
        for t in todo:
            print(f"    - {t}")
        print("\n  None of them stop you writing content. Each one turns a check back on.")
    else:
        print("\n  Setup done. Every check this machine can run is switched on.")

    # Deliberately after, and phrased as content rather than setup: the tools being ready and
    # the content being correct are separate claims.
    if CONTENT:
        print(f"\n  The content itself has something to fix:  {CONTENT[0]}")
        print("  Run  drip check  to see which files and what to do about them.")

    print("\n  Next:  read docs/AUTHORING.md, or run  drip new  to make something.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
