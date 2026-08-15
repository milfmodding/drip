#!/usr/bin/env python3
"""
Assemble DRIP release archives.

    python build-release.py                    the base install (mod + Part 1)
    python build-release.py --all              base plus every add-on pack present
    python build-release.py --pack Part2       one add-on pack on its own
    python build-release.py --check-only       could we ship? copies nothing
    python build-release.py --skip-build       reuse the existing Release build

Two kinds of archive:

  DRIP-<version>.zip          the mod, its config, and the Essentials pack.
                              A complete, working, minimal install.

  DRIP-<pack>-<version>.zip   one content pack and its bundles. Nothing else --
                              no assembly, no config, no other pack's files.
                              Extracts over an existing install and adds a folder.

The loader enumerates whatever directories exist under ContentPacks/, so an add-on pack is
just a folder appearing. That is also the mechanism a third party would use to ship DRIP
content inside a larger mod, so both routes stay one code path: a content pack is a
self-describing directory and nothing here should assume otherwise.

Configs live in git; bundles deliberately don't. Archives are therefore assembled from the
repo and the bundle store together, which is why `git archive` cannot produce them -- it would
make something that installs cleanly and loads nothing.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys
import zipfile

MOD_ROOT = pathlib.Path(__file__).resolve().parent.parent
BUNDLE_STORE = pathlib.Path(r"F:\SPT\Mods\DRIP-bundles")
BUILD_OUTPUT = MOD_ROOT / "bin" / "Release" / "DRIP" / "DRIP"
PACKS_ROOT = MOD_ROOT / "bundles" / "ContentPacks"
DIST = MOD_ROOT / "dist"

# The pack that ships inside the base install. Everything else is a separate download.
BASE_PACK = "Essentials"

REQUIRED_BUNDLES = {
    "top": ["TOP.bundle", "HANDS.bundle"],
    "bottom": ["BOTTOM.bundle"],
    "gear": ["GEAR.bundle"],
}


def say(message: str = "") -> None:
    print(message, flush=True)


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


def mod_version() -> str:
    csproj = (MOD_ROOT / "DRIP.csproj").read_text(encoding="utf-8")
    m = re.search(r"<Version>([^<]+)</Version>", csproj)
    return m.group(1) if m else "0.0.0"


def packs_present() -> list[str]:
    if not PACKS_ROOT.exists():
        return []
    return sorted(p.name for p in PACKS_ROOT.iterdir() if p.is_dir())


def items_in(pack_dir: pathlib.Path):
    """Every item config in a pack, as (path, parsed) — or (path, None) if unreadable."""
    for sub in ("CustomItems", "CustomClothing"):
        root = pack_dir / sub
        if not root.exists():
            continue
        for f in sorted(root.rglob("*.jsonc")):
            try:
                yield f, json.loads(strip_jsonc(f.read_text(encoding="utf-8-sig")))
            except json.JSONDecodeError:
                yield f, None


# ------------------------------------------------------------------------------------------
# Checks
# ------------------------------------------------------------------------------------------

def step_check_content() -> bool:
    say("  Checking the content...")
    result = subprocess.run(
        [sys.executable, str(MOD_ROOT / "tools" / "drip.py"), "check"],
        capture_output=True, text=True)
    if result.returncode != 0:
        say(result.stdout)
        say("  Content has errors. Fix them before building a release.")
        return False
    say("    content is clean")
    return True


def check_pack_ready(pack: str) -> tuple[bool, int, list[str]]:
    """Could this one pack ship? Answered against the store, copying nothing."""
    pack_dir = PACKS_ROOT / pack
    store = BUNDLE_STORE / pack
    problems: list[str] = []
    items = 0

    if not store.exists():
        return False, 0, [f"the bundle store has nothing for this pack ({store})"]

    for f, data in items_in(pack_dir):
        if data is None:
            problems.append(f"{f.name}: not valid JSON")
            continue
        items += 1
        in_store = store / f.parent.relative_to(pack_dir)
        have = {b.name for b in in_store.glob("*.bundle")} if in_store.exists() else set()
        for want in REQUIRED_BUNDLES.get(str(data.get("type", "")).lower(), []):
            if want not in have:
                problems.append(f"{f.relative_to(pack_dir)}: no {want} in the store")

    return not problems, items, problems


def step_check_ready(packs: list[str]) -> bool:
    """Report readiness per pack: one can be unshippable while the others are fine."""
    say("  Checking release readiness (no files copied)...")
    all_ok = True
    for pack in packs:
        ok, items, problems = check_pack_ready(pack)
        label = "base" if pack == BASE_PACK else "add-on"
        if ok:
            say(f"    {pack} ({label}): {items} items, ready")
        else:
            all_ok = False
            say(f"    {pack} ({label}): NOT READY - {len(problems)} problem(s)")
            for p in problems[:10]:
                say(f"        {p}")
            if len(problems) > 10:
                say(f"        ... and {len(problems) - 10} more")
    return all_ok


# ------------------------------------------------------------------------------------------
# Building
# ------------------------------------------------------------------------------------------

def step_build(skip: bool) -> bool:
    if skip:
        if not BUILD_OUTPUT.exists():
            say(f"  No build output at {BUILD_OUTPUT.relative_to(MOD_ROOT)} - "
                "drop --skip-build to build it.")
            return False
        say("  Using the existing Release build.")
        return True

    say("  Building (Release)...")
    result = subprocess.run(["dotnet", "build", "-c", "Release", str(MOD_ROOT / "DRIP.csproj")],
                            capture_output=True, text=True)
    if result.returncode != 0:
        say(result.stdout[-3000:])
        say("  Build failed.")
        return False
    say("    build succeeded")
    return True


def copy_bundles_for(pack: str, into_pack_dir: pathlib.Path) -> int:
    store = BUNDLE_STORE / pack
    copied = 0
    for bundle in store.rglob("*.bundle"):
        target = into_pack_dir / bundle.relative_to(store)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(bundle, target)
        copied += 1
    return copied


def stage_base(stage: pathlib.Path) -> bool:
    """The mod, its config, and the base pack only."""
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)

    say("  Staging the build output...")
    shutil.copytree(BUILD_OUTPUT, stage, dirs_exist_ok=True)

    # The build copies every pack it finds in the repo; a base archive ships only its own.
    packs_out = stage / "bundles" / "ContentPacks"
    if not packs_out.exists():
        say("    the build output has no content packs - did the build copy them?")
        return False
    for extra in [p for p in packs_out.iterdir() if p.is_dir() and p.name != BASE_PACK]:
        shutil.rmtree(extra)
        say(f"    left out add-on pack '{extra.name}' - it ships separately")

    say(f"  Adding bundles for {BASE_PACK}...")
    say(f"    {copy_bundles_for(BASE_PACK, packs_out / BASE_PACK)} bundles")
    return True


def stage_addon(pack: str, stage: pathlib.Path, version: str) -> bool:
    """One pack's configs and bundles. Nothing the base install already provides."""
    if stage.exists():
        shutil.rmtree(stage)
    pack_out = stage / "bundles" / "ContentPacks" / pack
    pack_out.mkdir(parents=True)

    say(f"  Staging {pack} configs...")
    shutil.copytree(PACKS_ROOT / pack, pack_out, dirs_exist_ok=True)

    say(f"  Adding bundles for {pack}...")
    say(f"    {copy_bundles_for(pack, pack_out)} bundles")

    # Stamped so a pack running against a different DRIP is diagnosable rather than mysterious.
    (pack_out / "pack-info.json").write_text(json.dumps({
        "pack": pack,
        "builtForDripVersion": version,
        "note": "If DRIP's version differs from this, the pack may be older or newer than the "
                "mod it is installed into. Usually fine - a pack is only configs and bundles - "
                "but it is the first thing to check if this pack misbehaves.",
    }, indent=2) + "\n", encoding="utf-8")

    (stage / f"README-{pack}.txt").write_text(
        ADDON_README.format(pack=pack, version=version), encoding="utf-8")
    return True


def verify_stage(stage: pathlib.Path, expect_base: bool) -> bool:
    """Everything the archive claims to contain is actually in it, and nothing else is."""
    say("  Verifying the staged tree...")
    packs_out = stage / "bundles" / "ContentPacks"
    problems, items = [], 0

    for pack_dir in sorted(p for p in packs_out.iterdir() if p.is_dir()):
        for f, data in items_in(pack_dir):
            if data is None:
                problems.append(f"{f.name}: not valid JSON")
                continue
            items += 1
            here = {b.name for b in f.parent.glob("*.bundle")}
            for want in REQUIRED_BUNDLES.get(str(data.get("type", "")).lower(), []):
                if want not in here:
                    problems.append(f"{f.relative_to(stage)}: no {want}")

    if expect_base:
        if not (stage / "DRIP.dll").exists():
            problems.append("the mod assembly is not in the package")
        if not (stage / "config").exists():
            problems.append("the config folder is not in the package")
        present = sorted(p.name for p in packs_out.iterdir() if p.is_dir())
        if present != [BASE_PACK]:
            problems.append(f"base archive should hold only {BASE_PACK}, holds {present}")
    else:
        # An add-on carrying base files would overwrite them on extraction.
        for forbidden in ("DRIP.dll", "config", "README.txt"):
            if (stage / forbidden).exists():
                problems.append(f"add-on archive must not contain '{forbidden}'")
        present = [p.name for p in packs_out.iterdir() if p.is_dir()]
        if BASE_PACK in present:
            problems.append(f"add-on archive must not contain the base pack '{BASE_PACK}'")

    if problems:
        say(f"    {len(problems)} problem(s) - not packaging:")
        for p in problems[:15]:
            say(f"      {p}")
        if len(problems) > 15:
            say(f"      ... and {len(problems) - 15} more")
        return False

    say(f"    {items} items, all with their bundles")
    return True


def zip_stage(stage: pathlib.Path, name: str) -> pathlib.Path:
    DIST.mkdir(exist_ok=True)
    archive = DIST / name
    say(f"  Compressing to {archive.name} (mostly bundles, so this takes a while)...")
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for f in sorted(stage.rglob("*")):
            if f.is_file():
                z.write(f, pathlib.PurePath("DRIP") / f.relative_to(stage))
    return archive


# ------------------------------------------------------------------------------------------

README = """\
DRIP {version}
==============

Clothing and gear for SPT. Requires SPT 4.0.

This is the full install and includes the Essentials content pack. Parts 2 and 3 are
separate downloads -- see ADD-ON PACKS below.


INSTALLING
----------

1. Close the SPT server and launcher.
2. Copy the "DRIP" folder from this archive into your SPT installation, at:

       <your SPT folder>\\user\\mods\\

   You should end up with:  <your SPT folder>\\user\\mods\\DRIP\\DRIP.dll

3. Start the server. It will say how many items it loaded.
4. Start the game. The new clothing is sold by Tupitsa and Georgia.

If you had DRIP for SPT 3.x, delete its folder from user\\mods before copying this one in --
replace it rather than merging. The two versions are built differently and leftovers from the
old one can confuse the server.


ADD-ON PACKS
------------

Parts 2 and 3 come as their own downloads. To install one, extract it the same way, over the
top of your existing install -- it adds a folder under DRIP\\bundles\\ContentPacks\\ and changes
nothing else.

To remove a pack, delete its folder from DRIP\\bundles\\ContentPacks\\ and restart the server.

Update the base install by re-extracting it over the top. Your add-on packs are left alone.


OPTIONS
-------

config\\config.jsonc changes how DRIP behaves -- whether bots wear DRIP clothing, whether
everything is free, and so on. Each setting says what it does. Edit it with any text editor,
then restart the server.


IF RAIDS FEEL HEAVY
-------------------

By default, the bots around you wear DRIP clothing too. That means a busy raid can be loading
and drawing a lot more high-resolution clothing than it otherwise would.

Whether that costs you frames depends on your machine -- on some it will make no difference at
all, on others it may. We have not measured it across different hardware, so we would rather
point you at the switch than quote you a number we don't have:

    config\\config.jsonc   ->   "addClothingToBots": false

That stops bots wearing DRIP clothing, and changes nothing else. You still buy and wear all of
it yourself, and DRIP gear is unaffected.

If your framerate dropped after installing DRIP, try that first.


IF SOMETHING GOES WRONG
-----------------------

The server window says what DRIP loaded, and names anything it couldn't. If items are missing,
that is where the reason will be.

Check first that the folder went to the right place:  user\\mods\\DRIP\\DRIP.dll
A common mistake is ending up with user\\mods\\DRIP\\DRIP\\DRIP.dll instead.

If raids feel heavier than they did before installing DRIP, see IF RAIDS FEEL HEAVY above.
"""

ADDON_README = """\
DRIP -- {pack}
==============

Extra content for DRIP. This is NOT a standalone mod: install DRIP first.

Built for DRIP {version}.


INSTALLING
----------

1. Close the SPT server.
2. Copy the "DRIP" folder from this archive into your SPT installation, at:

       <your SPT folder>\\user\\mods\\

   It merges into the DRIP you already have and adds one folder:

       DRIP\\bundles\\ContentPacks\\{pack}\\

   Nothing else is touched. Your settings, your other packs and the mod itself are left
   exactly as they were.

3. Start the server. It will list {pack} alongside the packs you already had.


REMOVING IT
-----------

Delete DRIP\\bundles\\ContentPacks\\{pack}\\ and restart the server. Anything from this pack
stops being sold.


IF IT DOESN'T LOAD
------------------

Check DRIP itself is installed and working first -- this pack does nothing on its own.

If your DRIP version isn't {version}, this pack was built for a different one. That is usually
fine, since a pack is only configs and models, but it is the first thing worth checking.
"""


# ------------------------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pack", default=None,
                    help="build one add-on pack instead of the base install")
    ap.add_argument("--all", action="store_true",
                    help="build the base install and every add-on pack present")
    ap.add_argument("--skip-build", action="store_true",
                    help="use the existing Release output instead of building")
    ap.add_argument("--no-zip", action="store_true",
                    help="leave the staged folders in place, don't compress")
    ap.add_argument("--check-only", action="store_true",
                    help="report whether each pack could ship; copy nothing")
    args = ap.parse_args()

    version = mod_version()
    present = packs_present()

    say(f"\n{'=' * 74}\nDRIP {version} release\n{'=' * 74}")

    if not present:
        say("  No content packs found. Has the content been converted yet?\n")
        return 1

    if args.pack and args.pack not in present:
        say(f"  No content pack called '{args.pack}'. Present: {', '.join(present)}\n")
        return 1
    if args.pack == BASE_PACK:
        say(f"  '{BASE_PACK}' ships inside the base install - build it without --pack.\n")
        return 1

    if not step_check_content():
        return 1

    if args.check_only:
        ok = step_check_ready(present)
        say()
        return 0 if ok else 1

    # What are we building?
    build_base = not args.pack
    addons = [args.pack] if args.pack else (
        [p for p in present if p != BASE_PACK] if args.all else [])

    needed = ([BASE_PACK] if build_base else []) + addons
    if not step_check_ready(needed):
        say()
        return 1

    if build_base and not step_build(args.skip_build):
        return 1

    built: list[pathlib.Path] = []

    if build_base:
        say(f"\n  --- base install ---")
        stage = DIST / "stage" / "base" / "DRIP"
        if not stage_base(stage):
            return 1
        (stage / "README.txt").write_text(README.format(version=version), encoding="utf-8")
        if not verify_stage(stage, expect_base=True):
            return 1
        if not args.no_zip:
            built.append(zip_stage(stage, f"DRIP-{version}.zip"))

    for pack in addons:
        say(f"\n  --- add-on: {pack} ---")
        stage = DIST / "stage" / pack / "DRIP"
        if not stage_addon(pack, stage, version):
            return 1
        if not verify_stage(stage, expect_base=False):
            return 1
        if not args.no_zip:
            built.append(zip_stage(stage, f"DRIP-{pack}-{version}.zip"))

    say()
    if args.no_zip:
        say(f"  Staged under {DIST / 'stage'}\n")
        return 0
    for archive in built:
        say(f"  {archive.name}   {archive.stat().st_size / (1024 ** 3):.2f} GB")
    say("\n  Players extract these into user\\mods. The base install first.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
