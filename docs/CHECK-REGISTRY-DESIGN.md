# The check registry — design notes before anyone writes it

**Status:** signed off, not started, and deliberately not before the demo. Recorded now because
it acquired a second consumer after it was proposed, and that changes its shape rather than its
priority.

---

## Why it exists — two unrelated reasons that want the same structure

**Gate 2.** Sophia's test is whether she can maintain the tooling unaided, and the tooling is the
layer she is most likely to want to change first. Today `check_config` is one long function with
every rule inline, so adding a check means finding the right place in it and not disturbing the
thirty around it. That is Colette's *"figure out how to piece it together to not break"* pointed
at Sophia. The demonstrable version of Gate 2 is **she adds a check without help**.

**The GUI** (`FUTURE-WORK.md`, research topic, not now). It needs to enumerate checks, show each
result beside the field it concerns, and re-run one as the user types. That is the same
structure, arrived at from a completely different direction.

**This is not a request to build for the GUI.** The refactor was justified before the GUI
existed as a plan. But knowing there will be a second consumer changes one decision, below, and
that decision is expensive to reverse later.

---

## The one thing that changes because of the second consumer

Echo's point: **a diagnostic should carry which field it concerns as data, not only as prose
inside its message.** A CLI can get away with `'price' is missing` because a human reads the
quotes. A GUI cannot put that message next to the price box without parsing English.

So `Diag` grows a field:

```python
class Diag:
    def __init__(self, code, severity, file, message, fix=None, field=None):
```

**Measured before signing up to it**, because "add a field to every call site" is the kind of
job that looks small and isn't:

| | call sites |
|---|---|
| already name a schema field literally in the message | 21 |
| interpolate the field name from a variable (`{key}`, `{field}`) | 4 |
| concern a field but don't name it — `DRIP-408` → `copyOriginalOffers`, `DRIP-101` → `type`, `DRIP-401` → `traderId` | 3 |
| **concern a specific field, total** | **28** |
| genuinely not about a field — `DRIP-001`, `102`, `112`, `113`, `200`, `201`, `400` | 7 |
| **total** | **35** |

The seven without a field are exactly the ones that *shouldn't* have one: invalid JSON, a
duplicate filename, an old-format file, an accidental filename, and the two pack-level
preconditions. **`field=None` is information, not a gap** — it means "this is about the file or
the pack, not about one line", which is precisely what a GUI needs to know in order to render it
somewhere other than beside an input box.

So the work is mechanical, the split is clean, and no diagnostic is left in an awkward middle.

---

## The constraint that matters most

**One engine, two front ends.** Echo's, and it is the load-bearing rule here.

`drip.py` already does `new`, `id` and `check` against the schema and the game database. A GUI
calls those. It does not reimplement them.

Two implementations of *"is this config valid"* is the population-disagreement problem — the one
that produced `verify_repack`'s 547/547 over bundles it could not see, and this project's three
recorded instances of two entry points diverging — except with a user in the middle of it,
watching one tool say yes and the other say no.

Corollary: the registry's output has to be **structured before it is formatted.** `report()`
turns diagnostics into terminal text today; that formatting has to stay a consumer of the list
rather than the thing that produces it.

---

## Shape

```python
@check("DRIP-301", about="price")
def price_is_present(cfg, ctx) -> Iterable[Diag]:
    ...
```

One function per check, each taking the config and a context (schema, pack, game database), each
returning zero or more diagnostics. Adding the thirty-third means writing one function beside
thirty examples — which is the whole point.

**Behaviour-preserving.** The test is that `drip check` produces byte-identical output over the
live pack before and after. That is a cheap and total check, and it should be run rather than
reasoned about.

---

## What not to do

- **Don't restructure the messages while restructuring the code.** Gate 1 has Sophia rewriting
  all 32 diagnostics' wording. Doing both at once means neither diff is reviewable, and a
  behaviour-preserving refactor stops being verifiable the moment the strings change.
- **Don't add checks during the refactor.** Same reason.
- **Don't let `field` become a second copy of the message.** It is the field's name as it appears
  in the config — `"price"`, `"basedOn"` — not a sentence about it.
