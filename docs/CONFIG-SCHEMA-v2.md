# DRIP Content Config — Schema v2

**Status:** draft for review · **Owner:** Tau (DX) · **Implementer:** Kappa · **Routing:** Echo

This is the contract between content authors and the loader. Authors write these files;
Kappa's loader consumes them. If the loader and this document disagree, that's a bug in one
of them — say so rather than working around it.

Every claim about the legacy format below is measured against all 543 parseable configs in
`DRIP-3.x-main/ContentPacks` (Part 1: 275, Part 2: 136, Part 3: 132), not inferred from
reading `collection.ts`. Counts are cited so they can be re-checked.

---

## 1. Design principles

1. **The file already knows.** If the loader can work something out from the filename or
   from what's sitting in the folder, the author shouldn't type it. Every field that can be
   inferred is a field that can be typo'd.
2. **Silence is the enemy.** A misspelled field must produce a message, never a no-op. The
   legacy loader and the current C# port both fail silently in ways that cost hours.
3. **One name per concept.** No aliases in the binder. Legacy spellings are recognised by the
   *validator* and turned into "did you mean" errors, not quietly accepted.
4. **Errors are written for someone who has never opened Visual Studio.** File, field, plain
   English, and a copy-pasteable fix.
5. **Additive by default.** Unknown fields are preserved, not rejected — `tags` has to survive
   untouched for ICUP later, and future field groups shouldn't require a converter run.

---

## 2. What the corpus actually says

Four findings drove the design. Each removes fields rather than adding them.

### 2.1 Every `*BundlePath` field is decorative

`bundlePath`, `topBundlePath`, `handsBundlePath`, `bottomBundlePath` appear 599 times across
the corpus. **They are never read.** `collection.ts` hardcodes `TOP.bundle`, `HANDS.bundle`,
`BOTTOM.bundle`, `GEAR.bundle` from the config's own directory (`collection.ts:416-527`), and
every single value on disk is exactly the constant the loader assumes:

| field | distinct values across 543 files |
|---|---|
| `bundlePath` | `GEAR.bundle` ×265 |
| `topBundlePath` | `TOP.bundle` ×165 |
| `handsBundlePath` | `HANDS.bundle` ×165 |
| `bottomBundlePath` | `BOTTOM.bundle` ×104 |

Two files prove the field is actively misleading — they declare a path that does not match
what is on disk, and are broken today:

- `Part 2/…/INFILTRATOR/NIGHTGREY/INFILTRATOR_NIGHTGREY_PANTS.json5` declares
  `"bottomBundlePath": "BOTTOM.bundle"`; the folder contains `INFILTRATOR_NIGHTGREY_PANTS.bundle`.
- `Part 3/…/BLACKLYNX/ORANGE/TACTICALHOODIE_ORANGE_TOP.json5` has no `HANDS.bundle` at all
  (folder contains `ORANGE.bundle`, `TOP.bundle`).

**v2 drops all four fields.** Bundles are discovered by co-location. If the expected bundle is
missing, that is now a validation error naming the file — instead of a runtime mystery.

### 2.2 `textureGearDependencies` is not a dependency list

19 files use `textureGearDependencies`, 2 use the numbered `textureGearDependencies1/2`. The
value is `[]` in **all 23 instances** — the field carries no data. Its only function is to make
`collection.ts:515-526` register an extra co-located `TEXTURE.bundle` and append it to the GEAR
bundle's dependencies. It is a presence marker wearing a dependency list's clothes.

Since v2 discovers co-located bundles anyway, **the field and its numbered-suffix wart are
deleted outright.** No v2 equivalent is needed. Drop `TEXTURE.bundle` next to `GEAR.bundle` and
it is picked up.

### 2.3 Bundle dependencies are nearly always the defaults

Only 11 distinct non-default dependency values exist across all 543 files, and **63% of Part 1
needs no dependency declaration at all** once `shaders`, `cubemaps` and
`assets/commonassets/physics/physicsmaterials.bundle` are applied automatically.

So the `bundles` block is **optional** and most files will not have one. It is also the one
field group the bundle workstream may still change, so it is deliberately isolated under a
single top-level key (§4.6) — a later change touches one nested object and nothing else.

### 2.4 `copyAssort` cleanly partitions all gear

| `copyAssort` | has `price` | has `loyaltyLevel` | has `childAssorts` | count |
|---|---|---|---|---|
| `true` | no | no | no | 198 |
| `false` | yes | yes | no | 57 |
| `false` | yes | yes | yes | 19 |

There are no mixed cases. This is a genuine either/or — "sell it wherever the original is
sold" versus "sell it at my price" — so v2 keeps it explicit rather than inferring it from
whether `price` happens to be present. The name changes to `copyOriginalOffers`; "assort" is
trader-database jargon that means nothing to a retexture author.

---

## 3. File layout

```
bundles/ContentPacks/<PackName>/
  CustomItems/     <path>/<ITEM_NAME>.jsonc   + co-located *.bundle
  CustomClothing/  <path>/<ITEM_NAME>.jsonc   + co-located *.bundle
  CustomTraders/   <traderId>.json  + <traderId>.jpeg
  CustomQuests/    *.jsonc + *.png
  CustomLocales/   en.json, ru.json, …
```

Folder depth under `CustomItems`/`CustomClothing` is free — organise however you like. The
loader walks recursively and only the filename matters.

**One extension: `.jsonc`.** The tree currently mixes `.json5`, `.jsonc` and `.json`; the
converter normalises everything to `.jsonc`. Comments and trailing commas are supported (§7),
which covers everything the legacy files actually used — no true JSON5 syntax (unquoted keys,
single-quoted strings) appears anywhere in the corpus, verified by scan.

---

## 4. The schema

### 4.1 Identity

| field | type | required | notes |
|---|---|---|---|
| `type` | `"top"` \| `"bottom"` \| `"gear"` | yes | matched case-insensitively |
| `id` | string (24-char MongoId) | no | override; omit and it's derived from the filename |

**`type` collapses four legacy values into three.** `RETEXTURE` (271) and `CUSTOM` (3) run
down the identical code path in `collection.ts:489-531`; `CUSTOM` differs only by carrying a
`customProperties` block, which in v2 is just two optional fields any gear item may use
(§4.5). One less decision to get wrong.

**Bind `type` as a string, not directly as an enum.** `[JsonConverter(typeof(JsonStringEnumConverter<T>))]`
matches case-insensitively — `"top"`, `"TOP"` and `"Top"` all bind, which is what we want — but
an unrecognised value **throws `JsonException`** rather than producing a diagnostic. Verified
against .NET 9:

| value | result |
|---|---|
| `"top"` / `"TOP"` / `"Top"` | binds to `Top` |
| `"TOPP"` (typo) | **throws** |
| `"retexture"` (legacy value) | **throws** |
| absent | `null` |

Three things break as a result: `DRIP-101` can never say *did you mean "top"?*; the failure
surfaces as "this file isn't valid JSON", which is untrue and sends the author hunting for a
missing comma; and deserialisation aborts before `[JsonExtensionData]` is populated, so no
other problem in the file gets reported either. One typo, one misleading message, nothing else
diagnosed.

Keep the raw string and parse it leniently, so the validator does the talking:

```csharp
[JsonPropertyName("type")] public string? TypeRaw { get; set; }

public ContentItemType? Type =>
    Enum.TryParse<ContentItemType>(TypeRaw, ignoreCase: true, out var t) ? t : null;
```

`Type` is `null` for both "absent" and "unrecognised"; `TypeRaw` distinguishes them and gives
`DRIP-101` the actual text the author wrote.

**ID derivation.** The author never writes an ID. The loader derives it as
`SHA1(filename-without-extension)[..24]`, lowercased — deterministic, stable across restarts,
and unchanged if you reorganise folders. Keep this; it is the single best ergonomic decision
in the existing port.

It needs one guard. Three filename stems collide in the corpus:

| stem | files | identical content? |
|---|---|---|
| `ZASLON_SOC_PANTS` | Part 1 + Part 3 | **yes** — byte-identical |
| `INFILTRATOR_NIGHTGREY_PANTS` | Part 2 TOP + Part 2 BOTTOM | no — different items |
| `TSHIRT_KHAKI` | Part 3 ×2 | no — different prices |

Because parts must be drop-in installable, the Part 1 / Part 3 pair would have Part 3 silently
overwrite a Part 1 item. So:

- Colliding IDs with **identical content** → skip the duplicate, log at info. (Re-shipping the
  same item in two packs is legitimate.)
- Colliding IDs with **differing content** → hard error naming both files (§8, `DRIP-102`).

Rename-to-fix is the right answer for the two genuine collisions; both are content bugs
(a top and a bottom named `..._PANTS`, and two different t-shirts with one name).

### 4.2 Naming and text

| field | type | required | notes |
|---|---|---|---|
| `name` | text | yes | in-game name |
| `shortName` | text | gear only | inventory abbreviation |
| `description` | text | gear only | |

**"text" means either a plain string or a map of language to string.** Both are valid
everywhere text is accepted:

```jsonc
"name": "Winter Jacket - DRIP"
"name": { "en": "Winter Jacket - DRIP", "ru": "Зимняя куртка - DRIP" }
```

A map must include `en`, because English is what every unlisted language falls back to
(`DRIP-107` if it doesn't). Language codes are `xx` or `xx-yy`.

> Earlier drafts had a separate `translations` block holding non-English text. Sophia's call —
> the same field taking either shape keeps everything about an item in one place, and removes
> the question of which of two fields a given string belongs in. It also means there is no
> separate mechanism to keep synchronised, and nothing to export or re-import unless a
> translator specifically asks for a flat file, at which point it is an *output* of this data
> rather than the source of truth.
>
> Nothing was migrated: `translations` was in the schema but used by zero of the 276 configs.
> The same shape applies to quest text — see `QUEST-FORMAT-PROPOSAL.md` §4 — so there is one
> answer to "how do I write this in another language" across every config type.

Clothing (`top`/`bottom`) has no `shortName`/`description` because the game never shows them
for customization items — the legacy loader only ever writes a `… Name` locale key for suits
(`collection.ts:136-138`). Supplying them is a validation warning, not an error.

### 4.3 Where it's sold

| field | type | required | notes |
|---|---|---|---|
| `traderId` | string | yes | friendly name or raw MongoId |
| `price` | number | see §4.4 | what the trader charges |
| `currency` | `"RUB"` \| `"USD"` \| `"EUR"` | no | **defaults to `RUB`** |
| `loyaltyLevel` | 1–4 | see §4.4 | |
| `profileLevel` | number ≥ 0 | no | clothing only |
| `standing` | number | no | clothing only |
| `questRequirements` | string[] | no | quest IDs that must be completed |

**`traderId` resolution order:** DRIP trader names (`moron`, `georgia`) → vanilla trader names
(`fence`, `ragman`, `prapor`, `therapist`, `skier`, `peacekeeper`, `mechanic`, `jaeger`,
`lighthousekeeper`, `btr`, `ref`) → raw 24-char MongoId. Matched case-insensitively. Vanilla
names and IDs must come from `SPTarkov.Server.Core.Models.Enums.Traders`, never hand-written.

Keeping the friendly names is not negotiable — 515 of 543 configs use them. Adding vanilla
names is new: 28 configs (3 in Part 1) hardcode `579dc571d53a0658a154fbec`, which nobody
should have to recognise on sight.

> That ID is **Fence**, not Ragman. It was mis-identified as Ragman during this design pass,
> which would have silently relocated 28 items to a different trader had the converter shipped
> with it. Verified against `Traders.cs` in both the 3.x type definitions and SPT 4.0.5. Worth
> stating plainly because it is exactly the failure mode friendly names exist to prevent —
> nobody reads a raw MongoId and notices it is wrong.

### 4.4 Resolving the price duality

Legacy has two incompatible shapes, split exactly along the clothing/gear line:

- clothing (269 files): `"price": 43000` + `"currency": "RUB"`
- gear (76 files): `"price": { "currency": "USD", "amount": 368043 }`

**v2 uses the flat form for both**, with `currency` defaulting to `RUB`:

```jsonc
"price": 43000,              // RUB, currency omitted
"price": 368043, "currency": "USD",
```

Rationale: it is the majority shape (269 vs 76), it is less to type, and defaulting the
currency removes a required field from every file — 269 configs lose a line. The nested form's
one advantage, keeping currency next to the amount, is worth less than that. The converter
flattens the 76 nested cases.

**`price: 0` is valid, must not be treated as absent, and is worth warning about.**

Two separate points, easily conflated:

*It parses.* A "price is missing" check must test the field's **presence**, not whether it is
non-zero. In C# that means `Price is null`, never `Price == 0` or a falsiness check.

*It's usually a mistake.* Ten Part 1 configs carry `price: 0` and Sophia confirms these are
leftovers — "just for testing back in the day" — not deliberate giveaways. So a config-level
zero raises `DRIP-307` (warning, names the file): it loads fine, but someone should set a real
price before release. Parts 2 and 3 are being reviewed separately; log theirs and move on.

> I originally recorded these ten as intentional free quest rewards. That was my inference from
> the data, not something the data said — every one of them is quest-locked, which made the
> reading plausible and wrong. Corrected here rather than quietly edited, because the earlier
> version of this document argued *for* accepting them silently.

*And keep the two zeroes apart.* `NoClothingRequirements` also zeroes clothing prices, but it
does so as a **runtime transform after loading**. That zero is correct and must keep working. A
zero written into a config file is a different thing and is what `DRIP-307` reports.

**`price` and `loyaltyLevel` are required exactly when `copyOriginalOffers` is not in effect**
(§4.5). Supplying them alongside `copyOriginalOffers: true` is a warning — the legacy loader
silently ignored them, which is precisely the kind of surprise this schema exists to remove.

Two other prices exist and are now named separately instead of overloading `price`:

| field | type | meaning |
|---|---|---|
| `handbookPrice` | number | catalogue valuation (was `customProperties.price.handbook`) |
| `fleaPrice` | number | flea market valuation (was `customProperties.price.flea`) |

Both default to the cloned item's values.

### 4.5 Gear-only fields

| field | type | default | was |
|---|---|---|---|
| `basedOn` | MongoId | **required** | `baseItemID` |
| `copyOriginalOffers` | bool | `true` | `copyAssort` |
| `addToBots` | bool | `true` | `addToBots` |
| `botWeightMultiplier` | number | `1.0` | `weightingMult` |
| `includedParts` | `{ [slot]: MongoId }` | — | `childAssorts` |
| `properties` | object | — | `customProperties.props.changeProps` |
| `copyPropertiesFrom` | `{ [tpl]: string[] }` | — | `customProperties.props.copyPropsFrom` |

`basedOn` replaces `baseItemID` (legacy) / `itemTplToClone` (current C# port) — those two names
had to be reconciled anyway, so it may as well say what it means to a retexture author.

`properties` and `copyPropertiesFrom` are what made `CUSTOM` a separate type. As plain optional
fields they are available to any gear item, which is strictly more useful: all 3 legacy `CUSTOM`
files do the same thing (copy armour stats from `639343fce101f4caa40a4ef3`, then override size
and penalties), and that is a recipe other armour retextures will want.

`includedParts` maps a slot name to the item that fills it — armour plates, in practice
(19 files, all plate carriers). Only meaningful when `copyOriginalOffers` is `false`.

**`parentId` and `handbookParentId` are not author-facing.** The current `CustomItemConfig`
requires both (`CustomItemConfig.cs:161-166`), which asks a non-programmer to look up two
internal MongoIds for a retexture. Both default from the cloned item; a content pack should
never need to state them. If a case turns up that does, it goes in `properties`.

### 4.5b Which bots may wear a garment

| field | type | who writes it | notes |
|---|---|---|---|
| `vanillaOrigin` | string | **the converter** | clothing only; the vanilla bundle this garment was cloned from |

3.x put every DRIP garment into every clothed bot type's pool, so a scav could turn up in modern
military kit and a Gluhar follower in scav jeans. The fix derives suitability instead of
annotating it: **a garment suits a bot type if the vanilla garment it was cloned from is already
in that bot type's vanilla appearance pool.** BSG decided which garments each bot wears, and a
retexture inherits that — the same principle as `copyOriginalOffers` and `updateFilters`.

Every DRIP bundle carries an `AssetBundle` object naming its vanilla origin:

```
assets/content/characters/character/prefabs/top_usec_acu.bundle
```

The loader registers bundles by key and never opens them, so it cannot see this. The converter
already walks every bundle, so it reads the value out and emits it.

**It is a recorded fact, not a re-derived one.** `tools/vanilla-origins.json` holds the origin
of every garment in all three parts — 270 garments, 36 distinct origins — keyed by
`<filename>|<type>`. The converter reads that record first and only falls back to opening a
bundle for a garment it has never seen.

That matters because the value is about the garment's *lineage*, not about the bundle file. It
is readable from the bundle today only because DRIP's bundles were built as modified copies of
vanilla ones. The Unity rebuild constructs bundles that **reference** vanilla assets instead of
embedding them, so their internal `AssetBundle` name will no longer carry the vanilla path —
and re-deriving would then fail for every garment at once. The record was captured while it was
still readable, and includes one garment whose origin was only recoverable because its
misnamed bundle was still sitting beside it.

Same shape as `price-overrides.json`: a decision recorded upstream of the converter, honoured
rather than recomputed. Don't delete entries; if a garment is retired, remove its config and its
line together.

**Every DRIP garment is a retexture** — none has ever been built from scratch — so a garment
with no origin is an alarm, not an unset option. `DRIP-114` is checking an invariant.

Two notes on the record itself, both in its `_README`. Entries are not garments: a renamed
garment is stored under both the name on disk and the name it ships under, so lookups work from
either direction. And two garments sharing a filename *and* a type, differing only by folder,
collapse to one key — real in Part 3, harmless because that pair already hard-errors as an id
collision, and left unfixed because putting folder in the key would stop keys surviving a file
move.

**The field is the raw origin, deliberately.** The converter could resolve the bot-type list
itself and emit that — and it must not. That would freeze the answer against whatever game
version was installed when the converter ran, and the whole reason this beats a hand-written
annotation is that it *self-corrects when BSG changes a pool*. Resolution belongs at runtime
against the live database; the converter's job is only to surface what the loader can't see.

**A missing origin is a loud failure, not a default.** If the bundle is absent or unreadable the
converter omits the field and names the file. Neither silent fallback is acceptable: including
the garment anyway recreates the every-bot-wears-everything behaviour this replaces, and
excluding it makes a garment vanish from bots with no explanation. `DRIP-114` warns on any
clothing config without one, and `drip origins` fills them in for hand-authored garments.

### 4.6 Bundles — provisional

> ⚠️ **Interim contract.** This is correct for the bundles that exist today, and it is isolated
> under a single key so that replacing it stays cheap. Do not spread bundle concerns into other
> fields, and do not invest further in this section — the bundle workstream has established
> that dependency declaration is on its way to being generated rather than authored (see the
> note at the end of this section). Treat `bundles` as scaffolding with a known demolition date.

Bundles are discovered by co-location: every `*.bundle` file in the same folder as the config
is registered automatically, and these dependencies are always applied:
`shaders`, `cubemaps`, `assets/commonassets/physics/physicsmaterials.bundle`.

Expected bundle filenames per type — missing ones are a validation error (`DRIP-201`):

| type | expected today | also accepted |
|---|---|---|
| `top` | `TOP.bundle`, `HANDS.bundle` | — |
| `bottom` | `BOTTOM.bundle` | — |
| `gear` | `GEAR.bundle` | `TEXTURE.bundle`, `TEXTURE1.bundle`, `TEXTURE2.bundle`, … |

**This table is a snapshot, not a rule to harden against.** The bundle workstream has confirmed
that the split `GEAR.bundle` + `TEXTURE.bundle` shape used by 19 files today — mesh in one,
texture in the other — is what every item is expected to look like after the Unity rebuild. So
`TEXTURE.bundle` is likely to go from rare-optional to the normal case, and the mesh half may
stop shipping per-item at all. Implement `DRIP-201` as a lookup over a per-type list, not as
branching logic, so that shift is a data change.

Extra dependencies, only when a bundle needs something beyond the defaults:

```jsonc
"bundles": {
  "TOP.bundle": ["assets/content/characters/character/skeleton.bundle"],
  "HANDS.bundle": [
    "assets/content/hands/bear/bear_watch.bundle",
    "assets/content/hands/bear/bear_hands_watch_texture.bundles"
  ]
}
```

Omit `bundles` entirely and you get co-location plus defaults — which is correct for 63% of
Part 1. Keys are bundle *filenames*, not paths.

> **Considered and rejected: role-based dependency defaults.** The 11 distinct non-default
> dependencies are highly stereotyped — `skeleton.bundle` appears on all 165 tops — so
> inferring them from the bundle's role would have taken the remaining 37% of files down to
> nearly nothing. The bundle workstream ruled it out, correctly: every DRIP bundle self-declares
> the vanilla bundle it was cloned from, and all 364 in Part 1 resolve against the live game
> install, so the exact dependency graph is mechanically derivable *today* and will be emitted
> as a manifest after the rebuild. A heuristic that is right 95% of the time is worse than a
> generated list that is right always, and it would need maintaining in the meantime.
>
> The consequence for this schema: `bundles` is expected to become vestigial rather than to
> grow. Nothing further should be built on it.

### 4.7 Passthrough fields

`tags` **must round-trip untouched.** 268 configs carry it (93 distinct tag names, value always
literally `1`); it moves to ICUP later. It is deliberately **not** in this schema and **not**
validated — but the loader must not choke on it, and the converter must not drop it.

The same applies to any unrecognised field: preserved, never fatal. See §7 for how, and §8 for
how the validator still catches typos without rejecting anything.

---

## 5. Worked examples

### Gear, sold wherever the original is sold (the 198-file majority case)

```jsonc
{
  "$schema": "../../../../drip-item.schema.json",
  "type": "gear",

  "name": "6B2 body armor (Olive Drab)",
  "shortName": "6B2",
  "description": "An old army body armor from Afghanistan war times…",

  "basedOn": "5df8a2ca86f7740bfe6df777",
  "traderId": "moron",

  "tags": { "olivedrab": 1, "woodland": 1 }
}
```

Everything else is default: `copyOriginalOffers: true`, `addToBots: true`,
`botWeightMultiplier: 1.0`, bundles discovered from the folder.

### Gear with its own price and armour plates

```jsonc
{
  "type": "gear",
  "name": "Shellback Tactical Banshee (Russian Splinter)",
  "shortName": "Banshee",
  "description": "…",

  "basedOn": "5e4abc1f86f774069619fbaa",
  "traderId": "georgia",

  "copyOriginalOffers": false,
  "price": 58000,
  "loyaltyLevel": 2,

  "includedParts": {
    "Front_plate": "656fa8d700d62bcd2e024084",
    "Back_plate":  "656fa8d700d62bcd2e024084"
  },

  "copyPropertiesFrom": {
    "639343fce101f4caa40a4ef3": ["ArmorMaterial", "ArmorType", "Durability", "armorClass"]
  },
  "properties": { "Width": 3, "Height": 3, "Weight": 6 },

  "handbookPrice": 58000,
  "fleaPrice": 58000
}
```

### Top

```jsonc
{
  "type": "top",
  "name": "Adaptive Combat - ERDL Model E",
  "traderId": "moron",

  "price": 72500,
  "loyaltyLevel": 1,
  "profileLevel": 14,
  "standing": 0,

  "bundles": {
    "TOP.bundle": ["assets/content/characters/character/skeleton.bundle"],
    "HANDS.bundle": [
      "assets/content/hands/bear/bear_watch.bundle",
      "assets/content/hands/bear/bear_hands_watch_texture.bundles",
      "assets/content/hands/usec/materials/watch_usec_textures"
    ]
  },

  "tags": { "woodland": 1, "erdl": 1 }
}
```

### Bottom, quest-locked (the 63%-of-Part-1 shape — no bundles block)

```jsonc
{
  "type": "bottom",
  "name": "Gen.2 Khyber - Combat Black",
  "traderId": "georgia",

  "price": 66000,
  "loyaltyLevel": 1,
  "profileLevel": 3,
  "standing": 0,
  "questRequirements": ["DRIP_1"],

  "tags": { "black": 1, "civilian": 1, "operator": 1, "drip": 1 }
}
```

---

## 6. Global mod config

`config/config.json5` moves to `config/config.jsonc`. Options carry over unchanged except
where the corpus made them meaningless:

| option | v2 | notes |
|---|---|---|
| `NoClothingRequirements` | keep | |
| `AddClothingToBots` | keep | |
| `AddEquipmentToBots` | keep | |
| `VanillaClothingPricePercentage` | keep | |
| `CollectionInDescription` | keep | rename "collection" → "content pack" in the text |
| `DebugNames` | keep | |
| `UseDRIPTagSystem` | **drop** | tag system is tabled; belongs to ICUP now |
| `vanillaclothing` | **drop** | same |

Casing is inconsistent in the legacy file (`vanillaclothing` vs `DebugNames`). Normalise to
camelCase and read case-insensitively.

---

## 7. Deserialization requirements — read before implementing

**Do not use `ModHelper.GetJsonDataFromFile` for content pack configs.** It routes to
`JsonUtil.Deserialize`, whose shared options
(`SPTarkov.Server.Core/Utils/JsonUtil.cs:17-28`) are wrong for author-written files in three
ways. DRIP needs its own `JsonSerializerOptions`:

| setting | SPT's shared options | DRIP must use | why |
|---|---|---|---|
| `AllowTrailingCommas` | **not set → `false`** | `true` | Legacy configs use trailing commas throughout, and so do both current example files (`hellomilfy.jsonc`, `WINTERJACKET_DRIP_TOP.jsonc`). As written, **those two files throw on load today.** |
| `PropertyNameCaseInsensitive` | **not set → `false`** | `true` | See below. |
| `UnmappedMemberHandling` | `Disallow` under `#if DEBUG` | not set + `[JsonExtensionData]` | `Disallow` would make any file carrying `tags` throw in a debug build — and `tags` must survive (§4.7). |
| `ReadCommentHandling` | `Skip` | `Skip` | ✔ already correct |

**Answering Echo's question directly: SPT's deserializer is case-sensitive.** So the mismatch
already shipped in the port is real —

- `hellomilfy.jsonc` writes `copyAssort` and `addToBots`
- `CustomItemConfig.cs:141,52` binds `cloneAssort` and `addtoBots`

— and in a Release build both fields are **silently ignored**, while in a Debug build the file
**throws**. That difference in behaviour between build configurations is worse than either
outcome alone. v2 fixes it at the root: canonical names (`copyOriginalOffers`, `addToBots`),
case-insensitive binding, and unknown fields surfaced by the validator instead of vanishing.

Concretely:

```csharp
private static readonly JsonSerializerOptions ContentPackOptions = new()
{
    ReadCommentHandling      = JsonCommentHandling.Skip,
    AllowTrailingCommas      = true,
    PropertyNameCaseInsensitive = true,
    // no UnmappedMemberHandling — unknowns land in Extra, see below
};

public sealed class ItemConfig
{
    // 'tags', '$schema', author comments — preserved, never fatal.
    [JsonExtensionData] public Dictionary<string, JsonElement> Extra { get; set; } = new();
}
```

`Extra` is what makes §4.7 work and what feeds the "did you mean" check in §8.

### Case-insensitivity stops at the DRIP/BSG boundary

**`PropertyNameCaseInsensitive` is not a global setting.** It is right for DRIP's own config
classes and unsafe for anything binding an SPT model type. Two option sets are required, not
one with an exception:

| options | used for | `PropertyNameCaseInsensitive` |
|---|---|---|
| `DripJson.Options` | DRIP's own config classes | `true` |
| `DripJson.SptTypeOptions` | anything binding an SPT/BSG model | `false` |

The reason, in one line: **our field names are forgiving because authors type them; BSG's are
exact because BSG chose them.**

`TemplateItemProperties` declares two pairs of properties differing only by case:

```
ExplDelay / explDelay
ShotgunDispersion / shotgunDispersion
```

Under case-insensitive binding System.Text.Json does not quietly pick one — it refuses to build
metadata for the type at all and throws. A scan of every type in `SPTarkov.Server.Core.Models`
found these are the only two collisions in the tree, both in this one type. Bounded, and
unfortunately it is the exact type `properties` binds onto.

This shipped as a real failure: setting the flag globally broke 30 armour items at runtime, and
only items carrying a `properties` block died — which is why neither scaffold file ever revealed
it. Unlike the trailing-comma and `UnmappedMemberHandling` traps, this one does not vary by
build configuration, so it would have reached players.

So `properties` (§4.5) must not bind straight to `TemplateItemProperties`. Hold it as raw JSON
and bind it in a second step through the strict options:

```csharp
[JsonPropertyName("properties")] public JsonElement? Properties { get; set; }

public TemplateItemProperties? MaterializeProperties() =>
    Properties is null ? null : BindToSptType<TemplateItemProperties>(Properties.Value);
```

**The same hazard applies to `copyPropertiesFrom`**, which looks BSG property names up by
reflection rather than through the serializer. A case-insensitive match there would silently
copy whichever of `ShotgunDispersion` / `shotgunDispersion` reflection happened to return first
— no exception, just the wrong value. Match exactly first, and fall back to case-insensitive
only when the match is unambiguous.

---

## 8. Validation and error messages

This is the part that decides whether a retexture author can work unsupervised. The existing
`Validate()` methods throw strings like `"masterySections[3].level2 is required"` — accurate,
and useless to someone who has never written C#.

### Rules

1. **Never throw for content problems.** Collect diagnostics, report them together, load
   everything that is loadable. One bad file must not cost the author the other 274.
2. **Every diagnostic names the file** by its path relative to the content pack.
3. **Every error says what to do**, with a copy-pasteable fix.
4. **No C# vocabulary.** No type names, no exception names, no stack traces, no
   `InvalidDataException`.
5. **Report at the end, grouped by file**, with a one-line summary. Authors run this and read
   the last screen.
6. **Diagnose the precondition, not each of its consequences.**

   When one missing thing makes every item fail, the failure count is noise — it measures how
   big the pack is, not what is wrong. Say it once, name the precondition, give the fix.

   This is the same instinct behind binding `type` as a string rather than an enum (§4.1): one
   bad value there aborted the file and masked every other problem in it. Both are cases of a
   single root cause presenting as many symptoms, and in both the fix is to report the cause.

   The distinction to preserve is **absent precondition** versus **broken reference**:

   | situation | means | report |
   |---|---|---|
   | most of the pack has no bundle on disk | un-bootstrapped checkout — normal for a fresh clone | one `DRIP-200` for the pack |
   | pack is populated, one item's bundle is missing | genuine content bug | `DRIP-201` per item |
   | no trader definitions anywhere, items reference DRIP traders | pack shipped without its traders | one `DRIP-400` for the pack |
   | traders exist, one item names a trader that doesn't | genuine content bug | `DRIP-401` per item |

   Zero items loading is the *correct* outcome for the first and third rows, and should read
   that way rather than as hundreds of failures.

   Two implementation notes, both learned the hard way here:

   - **Judge by proportion, not by whether any instance exists.** `bundles.Count == 0` does not
     fire: four bundles were committed before `.gitignore` covered them, and four are enough to
     make a 275-item pack look populated. Use "more than half the items are missing theirs".
   - **Suppress the per-item diagnostics when the pack-level one fires**, or the summary drowns
     anyway and the whole exercise is wasted.

   **The cost of that suppression: a pack-level diagnostic hides the per-item ones underneath
   it.** A real example is in the tree right now — `hellomilfy.bundle` sits beside
   `DAYPACK_HELLOMILFY_BAG.jsonc`, which requires `GEAR.bundle`, so that item has a genuinely
   wrong bundle name. `DRIP-201` would say so, and doesn't, because `DRIP-200` is firing and
   suppressing it. The trade is still right — 279 errors would be worse than one — but it means
   **a clean run under an active pack-level warning is not proof of a clean pack.** Re-run once
   the precondition is satisfied. Anything checking for regressions should treat "pack-level
   diagnostic active" as *incomplete*, not as *passed*.

### Format

```
DRIP  ✗  Essentials/CustomItems/ARMOR/BANSHEE/USEC/BANSHEE_USEC.jsonc

  DRIP-301  'price' is missing.
            This item has "copyOriginalOffers": false, so it needs its own price.
            Add:  "price": 58000,
            Or set "copyOriginalOffers": true to sell it wherever the original is sold.
```

### Catalogue

| code | severity | trigger | message |
|---|---|---|---|
| `DRIP-101` | error | `type` missing or unrecognised | `'type' must be "top", "bottom" or "gear" — found "TOPP".` |
| `DRIP-102` | error | ID collision, differing content | `This item's name collides with <other file>. Both become the same item ID. Rename one of them.` |
| `DRIP-103` | info | ID collision, identical content | `Identical to <other file>; skipping the duplicate.` |
| `DRIP-104` | error | `name` missing | `'name' is missing — this is what players see in game.` |
| `DRIP-110` | warning | unknown field, close to a known one | `'addtoBots' isn't a field DRIP knows. Did you mean 'addToBots'?` |
| `DRIP-111` | warning | legacy field name | `'baseItemID' was renamed to 'basedOn' in v2. Run the converter, or rename it.` |
| `DRIP-200` | warning | most of a pack has no bundles | `273 of 275 items have no bundle on disk, so they can't load yet.` + the one command to fix it |
| `DRIP-201` | error | required bundle absent | `Expected HANDS.bundle next to this file — the folder has: TOP.bundle, ORANGE.bundle.` |
| `DRIP-202` | warning | `bundles` key names a file that isn't there | `'bundles' mentions TEXTURE.bundle, but there's no TEXTURE.bundle in this folder.` |
| `DRIP-203` | warning | stray bundle, no config | `<name>.bundle sits in a folder with no config file — it will never load.` |
| `DRIP-301` | error | `price`/`loyaltyLevel` missing when required | see format example above |
| `DRIP-302` | warning | `price` set with `copyOriginalOffers: true` | `'price' is ignored here — with "copyOriginalOffers": true the original's price is used.` |
| `DRIP-303` | error | `loyaltyLevel` out of 1–4 | `'loyaltyLevel' is 7 — traders only have levels 1 to 4.` |
| `DRIP-304` | error | `currency` unrecognised | `'currency' must be "RUB", "USD" or "EUR" — found "ROUBLES".` |
| `DRIP-307` | warning | `price` is `0` in the config | `'price' is 0, so this item is free. If that wasn't deliberate, set a real price.` |
| `DRIP-400` | warning | pack references DRIP traders but no trader definitions exist anywhere | `Nothing here defines DRIP's own traders, so 136 items have nowhere to be sold.` + where they come from |
| `DRIP-401` | error | `traderId` unresolvable | `No trader called "gerogia". DRIP traders: moron, georgia. Or use a trader's ID.` |
| `DRIP-402` | error | `basedOn` missing on gear | `'basedOn' is missing — gear needs the ID of the item it's a retexture of.` |
| `DRIP-403` | error | `basedOn` not a real item | `'basedOn' is "5df8a2ca86f7740bfe6df77" (23 characters) — item IDs are 24. Check for a missing character.` |
| `DRIP-408` | error | `copyOriginalOffers` is on, but no trader sells the base item | `No trader sells Ars Arma A18 Skanda plate carrier (MultiCam), so copying its offers gives this item nowhere to be sold and nobody can buy it.` + set `copyOriginalOffers: false` and give it a price |
| `DRIP-409` | error | `includedParts` names a slot the base item doesn't have | `BNTI Zhuk body armor (EMR) has no slot called "Soft_armor_bak", so this part has nowhere to go and is ignored.` + did you mean, or the real slot names |
| `DRIP-410` | error | `includedParts` names a part the slot won't accept | `'includedParts' puts the "Soft_armor_front" part into the "Soft_armor_back" slot, so "Soft_armor_back" is left empty and that part of the BNTI Zhuk body armor (EMR) is unprotected.` + the one ID that does fit |
| `DRIP-501` | warning | `shortName`/`description` on clothing | `'description' isn't shown for clothing — you can remove it.` |
| `DRIP-502` | warning | `questRequirements` names an unknown quest | `'questRequirements' mentions "DRIP_9", which no quest in this pack defines.` |

`DRIP-110` uses Levenshtein distance ≤ 2 against the known field set, case-insensitive. This is
the single highest-value check in the table — it is the class of failure that produced
`copyAssort`/`cloneAssort` and `addToBots`/`addtoBots`, and it costs about fifteen lines.

#### `DRIP-408` and the three ways an item can have no shelf

`DRIP-408` is the one check that reads the game's own database rather than the content pack,
and it exists because the same server-side symptom — *this item has no trader* — has three
causes with three different right answers:

| The base item is | What it means | What the author should do |
|---|---|---|
| sold normally | copying its offers works | nothing |
| sold, but only after a quest | DRIP deliberately does not copy quest-locked offers | **nothing** — this is correct |
| not sold anywhere | copying its offers copies nothing | give the item its own price |

**Only the third is reported.** Warning about the second would be a check that fires on healthy
data, which is how a diagnostic teaches people to ignore it — the same reason the fourth price
placeholder flag was deleted.

But the *server log counts the second and third together*, so an author reading both would find
13 and 20 and have no way to reconcile them. `drip check` therefore prints the quest-locked
count as a plain note: not a warning, and not silence either.

**Reading the database off disk agrees with the running server, and that was checked rather
than assumed.** DRIP loads at `PostDBModLoader + 2` (400,002); Fence's assort is generated at
`TraderCallbacks` (800,000). So DRIP never sees a Fence assort — and Fence's on-disk
`assort.json` is empty, which is exactly what DRIP sees. The two agree by construction.

When no SPT install is configured the check is skipped and **says so**. A clean run that
quietly omitted a check is worse than a run that admits its scope.

#### `DRIP-409` / `DRIP-410` — parts the game will not fit

Same database, a different question: not *where is this sold* but *will this part go in*.

Each slot on a vanilla item carries its own list of what fits. For armour those lists are
almost always a single entry — **across all 60 vanilla armour carriers, all 275 required
soft-armour slots accept exactly one item and nothing else** (measured). So a wrong ID in one
of those is never a judgement someone made; it is a typo with one correct answer, which is why
`DRIP-410` can print the fix rather than describe it.

It earns its place because of *how* it fails. The game does not reject the config — it declines
to fit the part. The slot ends up empty, the armour has a hole exactly where the author
believed they had coverage, and nothing anywhere says so. It is invisible in-game, invisible in
the log, and invisible on the page.

Four shipping Part 1 items are in that state today, all the same shape: `Soft_armor_back` holds
the ID that belongs in `Soft_armor_front`. Every other slot in those files matches vanilla
exactly, which is the signature of a duplicated line. The two inserts involved **share a name** —
both are called `Aramid insert`, and they differ only by which colliders they cover — so
`DRIP-410` says so outright rather than printing a message that reads as if it were arguing
with itself.

The plate slots are the opposite case: 3 to 20 legal choices each. There the check can only
list them, and it does. **That split — determined for soft armour, a real choice for plates —
is the whole shape of the `includedParts` question**, and it is why the two halves want
different treatment in the schema. See [PARTS-AND-PRESETS.md](PARTS-AND-PRESETS.md).

### Pre-flight in the editor

The JSON Schema at `docs/drip-item.schema.json` gives autocomplete and red squiggles in VS
Code before the server is ever started. Every converted file gets a `$schema` pointer, and
`.vscode/settings.json` in the mod root maps it by glob so new files pick it up automatically.
This catches most of the table above at typing time; the validator remains the backstop for
everything a schema can't see (does the bundle exist, does the trader resolve, does the quest
exist).

---

## 9. Open questions

1. ~~**Bundle field group (§4.6)**~~ — **answered.** Stays optional and isolated as the interim
   contract; dependency declaration is heading toward being generated, not authored. No further
   investment.
2. ~~**Role-based dependency defaults (§4.6)**~~ — **answered: dropped.** Rationale recorded in
   §4.6.
3. **`type` for future non-clothing, non-retexture content** — the enum is open; adding a
   value is additive.
4. **One legacy file is unparseable:**
   `Part 3/…/GHOSTMARKSMAN/BEREZKA/MARKSGORKA_BEREZKA_TOP.json5` has a literal tab inside the
   `name` string, which is invalid in both JSON and JSON5. Part 3, so not release-blocking; the
   converter repairs it (tab → space) and logs it.

---

## 10. Changes required in the current port

Flagged for Kappa; all verified in the tree as it stands.

| # | file | issue |
|---|---|---|
| 1 | `Services/DRIPCustomTraderService.cs:47` | `$"{pathToMod}/bundles/${contentPackPath}"` — literal `$` (a JS template-literal habit), and `contentPackPath` already begins with `bundles/`, so the path is doubly wrong. Traders cannot load. |
| 2 | `DRIP.cs:84-89` | The commented-out WTT loader calls carry the same `${…}` typo — they'll break the moment they're uncommented. |
| 3 | `DRIP.cs:100-109` | `DoIfPathExists` calls `toDo()` without awaiting and returns `Task.CompletedTask`. Exceptions are swallowed and the "traders before items" ordering the comment promises is not actually enforced. |
| 4 | `Services/DRIPCustomItemService.cs:117-123` | `ParentId`/`HandbookParentId` hardcoded to backpack IDs and both prices to `69420`, ignoring the config. |
| 5 | `Models/CustomItemConfig.cs:161-166` | `parentId`/`handbookParentId` required from the author; should default from the cloned item (§4.5). |
| 6 | `Models/CustomItemConfig.cs:141,52` | `cloneAssort`/`addtoBots` vs the example file's `copyAssort`/`addToBots` — silent no-op in Release, throw in Debug (§7). |
| 7 | `bundles/…/COMMANDO_BARVIKHAPROTO_BOTTOM.json5` | Still in legacy 3.x format inside the new mod's content pack. The converter handles it. |
| 8 | everywhere | Three extensions in one tree (`.json5`, `.jsonc`, `.json`); `DRIPCustomItemService.cs:54` globs `*.json*`, which will also pick up any stray JSON that isn't an item config. |
