# Pre-v2 test fixtures

Two configs from before schema v2, kept as fixtures for `drip check`. They are **not content** —
nothing here loads, and nothing here should be copied into a content pack.

```
python tools/drip.py check --path tools/test-fixtures/pre-v2
```

Between them they exercise most of the legacy-format diagnostics:

| file | was | exercises |
|---|---|---|
| `COMMANDO_BARVIKHAPROTO_BOTTOM.json5` | DRIP 3.x format | `DRIP-112` old-format file, `DRIP-111` for the dropped `bottomBundlePath` and the renamed `bottomDependencies` |
| `hellomilfy.jsonc` | the 4.x scaffold, mid-migration | `DRIP-101`/`DRIP-104` missing `type` and `name`, `DRIP-111` for `itemTplToClone`, `overrideProperties`, `locales`, `copyAssort` |

They live under `tools/` on purpose. Anything inside `bundles/ContentPacks/` is enumerated by
the loader as a content pack, so keeping them there would produce load failures forever — see
`docs/STATUS.md`, settled decisions.

If a diagnostic's wording changes, the output here changes with it. That's the point: these are
what you look at to see whether an error message still reads well to someone who has never
opened Visual Studio.
