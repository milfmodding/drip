# Future work — the docket

Ideas that are **not** for now, recorded so they are not re-invented, re-argued, or lost. Nothing
here blocks Part 1. Each entry says who raised it and what we know about feasibility, because the
expensive failure with a wish-list is a good idea being dismissed twice by different people who
each did the thinking privately.

Ordered by how much time they would give back to Colette and Amber, which is the only ranking
that matters for this list.

---

## 1. Hot-reload textures in a running client

**Raised by Colette and Amber, 2026-07-30.** Today, seeing how a retexture actually looks means
rebuilding the bundle, restarting the server, restarting the game, and getting back to a place
where the garment is visible. Every iteration on a colour or a decal pays that cost. It is
plausibly the single largest time sink in their week and it is invisible in any file we own.

**Feasibility: yes for the version they actually want, and it is much cheaper than it sounds —
but it needs something DRIP does not currently have.**

The instinct is "reload the AssetBundle", which is the hard version: EFT caches loaded bundles and
everything instantiated from them, so a genuine reload means finding and rebinding every live
reference. Do not start there.

The cheap version solves the real problem. A retexture iteration changes **pixels, not structure**
— same mesh, same material, same shader, same slot. So nothing needs reloading; a texture needs
*replacing in place*:

- find the live `Material` by name (`Hands_bear_tshirt`, `item_equipment_rig_commando_black`)
- `Texture2D.LoadImage(File.ReadAllBytes(png))` onto the texture already bound to it, or
  `material.SetTexture("_MainTex", newTex)`
- watch a folder, fire on write

That is a small BepInEx plugin with a `FileSystemWatcher`, and the result is: save the PNG in
Photoshop, look at the character, see it. No restart.

**The real cost is that it would be DRIP's first client-side component.** DRIP today is a single
server assembly — verified, zero references to `Harmony`, `BepInEx`, `MonoBehaviour` or
`UnityEngine`. That property is worth something: it is *why* DRIP is structurally incapable of
costing frames, which is what let Framesaver rule us out of their measurements without measuring
us. Adding a client plugin gives that up, so it should be a **separate optional download** rather
than part of DRIP itself — an authoring tool, shipped to the two people who need it, not to
players.

**It shares its front half with the rebuild pipeline.** That pipeline is
`texture + vanillaOrigin → bundle`; hot-reload is `texture → live material`. Same input, same
name-matching problem. Whichever is built first should expose the lookup for the other.

## 2. Weapon presets

**Raised by Colette and Amber, 2026-07-30, and the framing is the finding: they are *more*
painful than quests were.**

Quests were the thing Sophia named as the reason Colette never added more than a handful — so
"worse than quests" is the strongest prioritisation signal we have received from anyone.

**We do not know the shape of this yet, and should not guess.** DRIP does not currently do weapon
presets at all; it retextures clothing and gear. So this is new capability rather than a fix, and
the first question is what *specifically* is painful — authoring the preset, getting it into a
trader's assort, the ids, testing it, or something we have not thought of.

**Ask them tomorrow while it is fresh.** That answer is worth more than any amount of design done
without it. The quest proposal was built by inferring the barrier from the file format, and Tau
has already flagged that the inference may be wrong; making the same move twice would be a choice
rather than an accident.

## 3. The author toolkit — a GUI over the whole workflow

**Open research topic, signed off 2026-07-30. Raised independently from both directions**, which
is the strongest signal on this list: Sophia proposed a one-stop tool on 2026-07-29 (pick a
vanilla item, hand it a texture, get a bundle and a config), and **Colette asked for a GUI on
2026-07-30 without having seen that.** Per this file's own rule the constituency outranks us — and
here the constituency and the owner arrived at the same place separately.

**Scope, as Sophia framed it:** new item, edit existing, quests, and weapon presets. That is the
four things authors actually do, and it is a superset of everything `drip.py` does today.

**Why this is a stronger candidate than it looks, and the argument is Colette's own words.** Her
barrier is *"a ton of stuff I barely understand is in front of me and I have to figure out how to
piece it together to not break."* A CLI plus a text editor can reduce what is on screen; **a GUI
can show one decision at a time, with only valid choices offered, and no assembly order to hold in
your head.** That is a more direct answer to her stated problem than any file format is. The quest
template work (item 2 of tomorrow's asks) is the same goal reached through a weaker medium.

**It should not be a reimplementation, and this is the load-bearing design note.** `drip.py`
already does `new`, `id` and `check` against the schema and the game database. A GUI that calls
those is a fraction of the cost of a GUI that reinvents them — and, more importantly, cannot drift
away from what the CLI validates. **One engine, two front ends.**

**Which makes the `drip check` registry refactor (below) a shared prerequisite rather than a
coincidence.** It was signed off for a Gate 2 reason — proving the tooling is maintainable by
turning "add a check" into "write one function beside thirty examples". But a GUI needs exactly
the same thing for a different reason: to enumerate checks, render their results next to the
fields they concern, and re-run one as the user types. **Both goals want one function per check
with structured output.** Doing it once serves both.

**Other pieces already built that a GUI would sit on top of:** the JSON schema (field names, valid
values, hover docs), `drip id` (name → id), `vanilla-origins.json` (lineage), and the rebuild
pipeline for `texture + vanillaOrigin → bundle`, which remains the hardest component and is
scheduled work regardless.

**Open questions, none of which need answering now:** whether it is XAML (Windows-only, matches
the SPT launcher) or something cross-platform; whether it edits configs in place or owns them;
and whether it subsumes `Review Prices.cmd` or leaves the spreadsheet alone, since the spreadsheet
is currently the one thing Colette and Amber can drive unaided.

## 3b. `drip check` as a registry — signed off 2026-07-30

**Not future work; approved and scheduled, recorded here because item 3 depends on it.**

Today `check_config` is one long function with the rules inline, so adding a check means finding
the right place in it and not breaking the ones around it. Tau's observation is the sharp one:
**that is Colette's *"figure out how to piece it together to not break"*, aimed at Sophia instead.**

One function per check, taking a config and returning diagnostics, turns "add a check" into
"write one function beside thirty examples". Signed off as the demonstrator for **Gate 2** — it
makes maintainability testable rather than argued, because the test is *did she add a check
without help*.

Refactor with no behaviour change, testable against current output. Not before the demo.

## 4. Copy the quest lock along with the offer

**Ours, 2026-07-30.** Seven Part 1 configs are based on items a trader only sells after a quest.
DRIP correctly refuses to sell a retexture of something the player has not unlocked, so those
seven have no shelf — see `REPRICE-WORKSHEET.md`.

The faithful behaviour is *"sold wherever the original is sold, **including the gate**"*: copy the
quest requirement along with the offer so the retexture appears exactly when the original does.
That is loader work, it is small, and it converts a permanent "correct but odd" note into items
that behave the way an author would expect. Worth doing before Part 2 adds more of them.

## 5. Realised-appearance readback

**Ours, 2026-07-29.** DRIP can log what it *asked* a bot to wear. Nothing reads back what the
client actually rendered. That gap is why smoke test §6.7 needed a human looking at bots, and why
Framesaver's dose figure is modelled from bot counts rather than measured from garments.

Client-side work, so it shares the objection in (1) — and if a client plugin is ever built for
hot-reload, this rides along on it almost free.

---

## Recording rules for this file

- **Say who raised it.** An idea from Colette or Amber outranks one of ours by default; they are
  the constituency.
- **Say what is actually known about feasibility**, including "we do not know" — the point is to
  stop the next person re-deriving it.
- **Do not design it here.** A paragraph of what and why. Designs go in their own document when
  the thing is actually next.
