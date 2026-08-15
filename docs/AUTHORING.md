# Adding items to DRIP

For people making content. You don't need to write any code, and you don't need to understand
the mod's internals — this covers everything.

If you're after the technical contract instead, that's [CONFIG-SCHEMA-v2.md](CONFIG-SCHEMA-v2.md).

---

## First time: run Setup

**Double-click `Setup.cmd` in the DRIP folder.** That's the whole first step.

It installs what the tools need, works out which SPT install to read the game's item names
from, and then **tells you what it did and what it couldn't do**. Nothing it reports is fatal —
each outstanding item just turns one check back on. Run it again whenever you like; it changes
nothing that's already right.

Two things it deliberately won't do on its own:

- **It won't pick an SPT install for you** if you have more than one. It lists them with their
  versions and asks. Reading the wrong install would give confident answers about the wrong game.
- **It won't pretend.** If it skips a check, it says which one and why. A setup that reports
  success having quietly skipped something is worse than one that admits it.

### What Setup can't do for you

**The bundles.** The repository holds the configs but not the `.bundle` files — they're about
3 GB and would make the repository unusable. So a fresh copy has 276 items and no models, and
Setup will tell you so. Fetch them once:

```
python tools/convert-legacy.py --part 1 --out bundles/ContentPacks/Essentials --bundles link
```

`--bundles link` uses hard links, so this is instant and costs no extra disk space, as long as
the DRIP source and the 3.x content are on the same drive. Use `--bundles copy` if they aren't.

If `drip check` says **"273 of 275 items have no bundle on disk"**, that's this step not done —
it means an un-bootstrapped copy, not broken content.

---

## What you need

- **Your bundle**, made the usual way (Asset Studio / UABEA / Tarkov Bundle Helper).
- **A text editor.** [VS Code](https://code.visualstudio.com/) is the one to use — DRIP is set
  up so it autocompletes field names and underlines mistakes in red as you type. Notepad works
  too, you just don't get any of that help.
- **Python** — `Setup.cmd` handles this, including offering to install it.

---

## Adding an item, start to finish

### 1. Make the file

From the DRIP folder, run:

```
drip new
```

It asks what you're making and where it goes, then writes the file for you with the right
fields already in place. If you'd rather type it in one line:

```
drip new gear ARMOR/6B23/TIGERSTRIPE/ARMOR_6B23_TIGERSTRIPE
```

**When it asks which item you're retexturing, type the name** — `slick`, `tactec`, `fast mt`.
It looks up the item and shows you what it found. If several things match, it lists them and
you pick a number:

```
  Which item are you retexturing? (its name, e.g. Slick): slick

     3 items match 'slick':
       1. LBT-6094A Slick Plate Carrier (Black)
       2. LBT-6094A Slick Plate Carrier (Coyote Tan)
       3. LBT-6094A Slick Plate Carrier (Olive Drab)

     Which one? 2
     -> LBT-6094A Slick Plate Carrier (Coyote Tan)  (6038b4b292ec1c3103795a0b)
```

You never have to find the 24-character ID yourself. If you're editing a config that already
exists and want a different item, look the ID up on its own:

```
drip id fast mt
```

**The filename becomes the item's ID**, so make it descriptive and make it unique. Two files
with the same name anywhere in DRIP become the same item, and one silently replaces the other —
`drip check` catches this, but it's easier to just pick a distinct name.

### 2. Put your bundle next to it

Drop your `.bundle` into the same folder as the config, named for what it is:

| making | bundle files |
|---|---|
| gear (armour, helmets, rigs, bags, masks) | `GEAR.bundle` |
| a top | `TOP.bundle` and `HANDS.bundle` |
| trousers | `BOTTOM.bundle` |

That's the whole of it. You don't write the path anywhere — DRIP looks in the folder. If you
also have a separate texture bundle, call it `TEXTURE.bundle` and leave it there; it gets picked
up too.

### 3. Fill in the config and check it

Edit the file, then:

```
drip check
```

It tells you what's wrong, in which file, and what to do about it — in about a second. When it
says *All good*, start the server.

---

## What goes in a config

### Gear — a retexture of an existing item

```jsonc
{
  "type": "gear",

  "name": "6B23-1 body armor (Tiger Stripe)",
  "shortName": "6B23-1",
  "description": "What a player reads when they inspect it.",

  // The item you're retexturing.
  "basedOn": "5c0e5bab86f77461f55ed1f3",

  "traderId": "moron",
  "copyOriginalOffers": true
}
```

`copyOriginalOffers` is the one that matters most:

- **`true`** — your item shows up wherever the original is sold, at the original's price. Nothing
  else to fill in. This is what most gear does.
- **`false`** — the trader you named sells it at your price. Then you must also add `price` and
  `loyaltyLevel`.

### Clothing — a top or trousers

```jsonc
{
  "type": "bottom",

  "name": "Gen.2 Khyber - Combat Black",
  "traderId": "georgia",

  "price": 66000,
  "loyaltyLevel": 1,
  "profileLevel": 3,
  "standing": 0,

  "questRequirements": ["DRIP_1"]
}
```

Clothing is always sold at its own price, so `price` and `loyaltyLevel` are always needed.
`price` can be `0` if you want it free as a quest reward.

Clothing has no `shortName` or `description` — the game never shows them for clothing.

---

## Every field

Only `type`, `name` and `traderId` are needed on everything. The rest depend on what you're
making.

| field | what it does |
|---|---|
| `type` | `gear`, `top` or `bottom` |
| `name` | what players see in game |
| `shortName` | short label on the item in your inventory *(gear)* |
| `description` | flavour text when inspecting *(gear)* |
| `traderId` | who sells it — see below |
| `price` | what the trader charges. `0` is allowed |
| `currency` | `RUB`, `USD` or `EUR`. Leave it out for roubles |
| `loyaltyLevel` | trader level needed to buy it, 1 to 4 |
| `profileLevel` | player level needed *(clothing)* |
| `standing` | trader standing needed *(clothing)* |
| `questRequirements` | quest IDs that must be done first, e.g. `["DRIP_1"]` |
| `basedOn` | the item you're retexturing *(gear)* |
| `copyOriginalOffers` | sell it wherever the original is sold *(gear, default true)* |
| `addToBots` | can bots spawn wearing it *(gear, default true)* |
| `botWeightMultiplier` | how often bots wear it vs the original. `0.5` = half as often |
| `includedParts` | armour plates that come fitted, e.g. `{"Front_plate": "656fa..."}` |
| `handbookPrice` / `fleaPrice` | catalogue and flea values. Default to the original's |
| `properties` | override things like `Width`, `Height`, `Weight` |
| `copyPropertiesFrom` | take armour stats from a different item |
| `bundles` | extra bundle dependencies — **you almost never need this** |
| `tags` | outfit-matching tags. Leave any you find alone |

**Traders.** Use `moron` or `georgia` for DRIP's own, or a vanilla trader by name: `ragman`,
`fence`, `prapor`, `therapist`, `skier`, `peacekeeper`, `mechanic`, `jaeger`,
`lighthousekeeper`, `btr`, `ref`.

**About `bundles`.** Nearly two thirds of DRIP's items don't have this field at all, and yours
probably shouldn't either. Shaders, cubemaps and physics materials are added automatically. Only
add it if your bundle needs something unusual, and copy the shape from an item that already
does.

---

## When something goes wrong

Run `drip check`. It looks like this:

```
  Essentials/CustomItems/ARMOR/BANSHEE/USEC/BANSHEE_USEC.jsonc
    error    DRIP-301  'price' is missing. This item has "copyOriginalOffers": false,
                       so it needs its own price.
                       Add:  "price": 58000,
                       Or set "copyOriginalOffers": true to sell it wherever the
                       original is sold.
```

**Errors** stop that one item loading. **Warnings** don't, but are usually worth fixing.
Everything else in the pack still loads either way — one broken file never takes the rest down.

A few common ones:

| message | what happened |
|---|---|
| `isn't valid JSON` | a missing comma, quote or bracket. The line number is in the message |
| `Expected GEAR.bundle in this item's folder` | the bundle isn't there, or is named something else |
| `isn't a field DRIP knows` | a typo in a field name. It usually guesses what you meant |
| `was renamed to ... in the new format` | the file is in the old format — see below |
| `have the same name` | two files share a filename, so they'd be the same item |
| `'price' is 0, so this item is free` | probably left over from testing. Set a real price unless you meant it |
| `No trader sells ...` | see below — the item needs a price of its own |
| `items have no bundle on disk` | see below — normal on a fresh copy of the repo |

### "No trader sells ..."

`copyOriginalOffers: true` means *sell this wherever the original is sold*. That works for most
gear — but a few vanilla items aren't sold by anyone at all, only found as loot. Copying the
offers of an item nobody sells copies nothing, and the result is an item that exists in the
game and can never be bought.

The fix is to give it a price of its own:

```jsonc
"copyOriginalOffers": false,
"price": 58000,
"loyaltyLevel": 3
```

If you're not sure what to charge, double-click **`Review Prices.cmd`** — it opens a
spreadsheet with every DRIP item grouped next to its siblings, so you can see what the rest of
the set costs.

**A related case that is *not* an error and gets no message:** some vanilla items are sold, but
only after you finish a quest. DRIP doesn't copy those offers, on purpose — doing so would put
an item on the shelf that the game means you to earn. Those items have no shelf either, and
that's correct. `drip check` mentions the count at the end as a note, so the number matches the
server log, but there's nothing to do about them.

This check needs to read the game's own data. If `drip check` says it *couldn't find an SPT
install*, put the path to yours in `tools/spt-path.txt` — one line, the folder with
`EscapeFromTarkov.exe` in it. Everything else is still checked without it.

### "No bundles on disk"

If `drip check` opens with something like *273 of 275 items have no bundle on disk*, nothing is
broken. Bundles are big binaries and aren't stored in the repo, so a fresh copy doesn't have
them. The message includes the one command that fetches them. You only need to do this once.

This is deliberately reported once for the whole pack rather than once per item — if it told you
275 separate times, a genuinely missing bundle would be impossible to spot in the noise.

Trailing commas and `//` comments are fine — write them freely.

---

## Old files

Anything written for DRIP 3.x uses the old format and won't load as-is. Don't edit them by
hand:

```
python tools/convert-legacy.py --part 1 --out bundles/ContentPacks/Essentials
```

It writes a `CONVERSION-REPORT.md` listing every change it made to every file, so you can see
exactly what happened rather than taking its word for it.

---

## Getting help

`drip check` first — it answers most questions faster than a person can. If it doesn't, bring
the output with you; it names the file and the field, which is most of the answer already.
