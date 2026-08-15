# DRIP legacy -> v2 conversion report

Parts converted: 1
Files converted: 276

Every alteration is listed against the file it happened to. `REPAIRED` marks a case
where the converter changed content to fix a defect in the source file — those are
worth reading. See docs/CONFIG-SCHEMA-v2.md for why each transformation happens.

## Repairs

The converter altered content to fix a problem in the original file.

- **DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\GEN2\URBANREED\COMBAT_PANTS_URBANREED_BOTTOM - Copy.json5**
  - filename looks accidental; shipping as 'COMBAT_PANTS_URBANREED_BOTTOM'. The filename derives the item id, so this corrects the id too - free now, permanent once players have the item.

- **DRIP Part 1 (Essentials)\items\GEAR\ARMOR\ZHUK6A\BLACK\ZHUK6A_BLACK_ARMOR.json5**
  - includedParts["Soft_armor_back"] was 65764275d8537eb26a0355e9, which the game will not fit there - the slot was left empty. Now 657642b0e6d5dd75f40688a5. See SLOT_FIXES in this script.

- **DRIP Part 1 (Essentials)\items\GEAR\RIGS\AVSTAGILLA\EMR\RIG_AVSMBAV_EMR.json5**
  - includedParts["Soft_armor_back"] was 6575f5cbf6a13a7b7100b0bf, which the game will not fit there - the slot was left empty. Now 6575f5e1da698a4e98067869. See SLOT_FIXES in this script.

- **DRIP Part 1 (Essentials)\items\GEAR\RIGS\AVSTAGILLA\ERDL\RIG_AVSMBAV_ERDL.json5**
  - includedParts["Soft_armor_back"] was 6575f5cbf6a13a7b7100b0bf, which the game will not fit there - the slot was left empty. Now 6575f5e1da698a4e98067869. See SLOT_FIXES in this script.

- **DRIP Part 1 (Essentials)\items\GEAR\RIGS\AVSTAGILLA\RUSPLINTER\RIG_AVSMBAV_RUSPLINTER.json5**
  - includedParts["Soft_armor_back"] was 6575f5cbf6a13a7b7100b0bf, which the game will not fit there - the slot was left empty. Now 6575f5e1da698a4e98067869. See SLOT_FIXES in this script.

## Every file

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\COMMANDO\BARVIKHAPROTO\COMMANDO_BARVIKHAPROTO_BOTTOM.json5
- vanillaOrigin: assets/content/characters/character/prefabs/pants_usec_commando.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\GEN2\BARVIKHAPROTO\COMBAT_PANTS_BARVIKHAPROTO_BOTTOM.json5
- vanillaOrigin: assets/content/characters/character/prefabs/pants_usec_gen2.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\GEN2\BLACK\COMBAT_PANTS_BLACK_BOTTOM.json5
- questRequirements: 'DRIP_1' -> '669cdb5039f39e1bd6019b56' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669cdb5039f39e1bd6019b56' -> '55b0f24605877596e6ea8474' (THE_MORNING_AFTER.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/pants_usec_gen2.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\GEN2\ERDL\COMBAT_PANTS_ERDL_BOTTOM.json5
- vanillaOrigin: assets/content/characters/character/prefabs/pants_usec_gen2.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\GEN2\FLECKTARN\COMBAT_PANTS_FLECKTARN_BOTTOM.json5
- questRequirements: 'DRIP_18' -> '669f7b28d1dbbbdb0475e7be' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f7b28d1dbbbdb0475e7be' -> '87f2ff0b5d7e277e642330bc' (FRIENDLY_FEUD.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/pants_usec_gen2.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\GEN2\GHOSTPARTIZAN\COMBAT_PANTS_GHOSTPARTIZAN_PANTS.json5
- questRequirements: 'DRIP_1' -> '669cdb5039f39e1bd6019b56' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669cdb5039f39e1bd6019b56' -> '55b0f24605877596e6ea8474' (THE_MORNING_AFTER.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/pants_usec_gen2.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\GEN2\REDURBAN\COMBAT_PANTS_REDURBAN_BOTTOM.json5
- vanillaOrigin: assets/content/characters/character/prefabs/pants_usec_gen2.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\GEN2\URBANREED\COMBAT_PANTS_URBANREED_BOTTOM - Copy.json5
- questRequirements: 'DRIP_1' -> '669cdb5039f39e1bd6019b56' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669cdb5039f39e1bd6019b56' -> '55b0f24605877596e6ea8474' (THE_MORNING_AFTER.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/pants_usec_gen2.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)
- REPAIRED — filename looks accidental; shipping as 'COMBAT_PANTS_URBANREED_BOTTOM'. The filename derives the item id, so this corrects the id too - free now, permanent once players have the item.

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\GORKA4\BLACK\GORKA4_BLACK_PANTS.json5
- vanillaOrigin: assets/content/characters/character/prefabs/pants_security_gorka4.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\GORKA4\CLASSIC\GORKA4_CLASSIC_PANTS.json5
- vanillaOrigin: assets/content/characters/character/prefabs/pants_security_gorka4.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\GORKA4\FLORA\GORKA4_FLORA_PANTS.json5
- vanillaOrigin: assets/content/characters/character/prefabs/pants_security_gorka4.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\GORKA4\KLMK\GORKA4_KLMK_PANTS.json5
- vanillaOrigin: assets/content/characters/character/prefabs/pants_security_gorka4.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\GORKA4\SKOL\GORKA4_SKOL_PANTS.json5
- questRequirements: 'DRIP_12' -> '669f79c7f8b1f185365997e3' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f79c7f8b1f185365997e3' -> 'd5fb79830a150e4c596468bd' (SYSTEM_DESTROYER_PART_2.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/pants_security_gorka4.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)
- override: price 0 -> 57500 (see OVERRIDES in this script)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\INFILTRATOR\6COLOURDESERT\INFILTRATOR_CHOCCHIP_PANTS.json5
- vanillaOrigin: assets/content/characters/character/prefabs/pants_usec_cryeprecision.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\INFILTRATOR\MGOTIGER\INFILTRATOR_GRASSY_TIGER_PANTS.json5
- questRequirements: 'DRIP_14' -> '669f7a46a33b9e7cbda18b33' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f7a46a33b9e7cbda18b33' -> '02cf1311c15283c098411606' (MOSIN_MAN.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/pants_usec_cryeprecision.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\INFILTRATOR\NIGHTDIGITAL\INFILTRATOR_NIGHTDIGITAL_BOTTOM.json5
- questRequirements: 'DRIP_13' -> '669f7a04a6bd56d17bae1089' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f7a04a6bd56d17bae1089' -> '74f0e746d3720d3fae01ccab' (HEAD_EYES.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/pants_usec_cryeprecision.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\INFILTRATOR\USEC\INFILTRATOR_USEC_BOTTOM.json5
- vanillaOrigin: assets/content/characters/character/prefabs/pants_usec_cryeprecision.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\KNIGHT\M81\KNIGHT_M81_BOTTOM.json5
- questRequirements: 'DRIP_2' -> '669f74d7e7211bf21d8af254' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f74d7e7211bf21d8af254' -> 'b05a483cc90cb02bc9b090d3' (MATERIAL_HANDLER.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/pants_boss_blackknight.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\OLDSCHOOL\BARVIKHAPROTO\OLDSCHOOL_BARVIKHAPROTO_BOTTOM.json5
- vanillaOrigin: assets/content/characters/character/prefabs/pants_bear_oldschool.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\OLDSCHOOL\KLMK\OLDSCHOOL_KLMK_PANTS.json5
- vanillaOrigin: assets/content/characters/character/prefabs/pants_bear_oldschool.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\OLDSCHOOL\RYZHUKHA\OLDSCHOOL_RYZHUKHA_BOTTOM.json5
- vanillaOrigin: assets/content/characters/character/prefabs/pants_bear_oldschool.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\OLDSCHOOL\SKOL\OLDSCHOOL_SKOL_PANTS.json5
- questRequirements: 'DRIP_12' -> '669f79c7f8b1f185365997e3' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f79c7f8b1f185365997e3' -> 'd5fb79830a150e4c596468bd' (SYSTEM_DESTROYER_PART_2.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/pants_bear_oldschool.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)
- override: price 0 -> 84000 (see OVERRIDES in this script)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\OLDSCHOOL\TARNANZUG\OLDSCHOOL_TARNANZUG_BOTTOM.json5
- questRequirements: 'DRIP_12' -> '669f79c7f8b1f185365997e3' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f79c7f8b1f185365997e3' -> 'd5fb79830a150e4c596468bd' (SYSTEM_DESTROYER_PART_2.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/pants_bear_oldschool.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)
- override: price 0 -> 84000 (see OVERRIDES in this script)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\OLDSCHOOL\TTSKO5\OLDSCHOOL_TTSKO5_PANTS.json5
- vanillaOrigin: assets/content/characters/character/prefabs/pants_bear_oldschool.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\SAGEWARRIOR\MM14\ALLWEATHER_MM14_PANTS.json5
- vanillaOrigin: assets/content/characters/character/prefabs/pants_usec_beltstaff.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\SCAVJEANS\BLACK\JEANS_BLACK_PANTS.json5
- vanillaOrigin: assets/content/characters/character/prefabs/pants_wild_victory.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\SCAVJEANS\THREECOLOURSOVIET\JEANS_THREECOLOURSOVIET_PANTS.json5
- questRequirements: 'DRIP_14' -> '669f7a46a33b9e7cbda18b33' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f7a46a33b9e7cbda18b33' -> '02cf1311c15283c098411606' (MOSIN_MAN.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/pants_wild_victory.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\SCAVJEANS\VZ95\JEANS_VZ95_PANTS.json5
- questRequirements: 'DRIP_14' -> '669f7a46a33b9e7cbda18b33' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f7a46a33b9e7cbda18b33' -> '02cf1311c15283c098411606' (MOSIN_MAN.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/pants_wild_victory.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\SPN\BARVIKHAPROTO\CARGOPANTS_BARVIKHAPROTO_BOTTOM.json5
- vanillaOrigin: assets/content/characters/character/prefabs/pants_bear_spna.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\SPN\EMERCOMVSR\CARGOPANTS_EMERCOMVSR_PANTS.json5
- vanillaOrigin: assets/content/characters/character/prefabs/pants_bear_spna.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\SPN\VZ95\CARGOPANTS_VZ95_PANTS.json5
- vanillaOrigin: assets/content/characters/character/prefabs/pants_bear_spna.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\SRVV\BLACKSHARK\TACTICAL_PANTS_BLACK_SHARK_PANTS.json5
- questRequirements: 'DRIP_10' -> '669f78e3ea69f9bde9904a1b' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f78e3ea69f9bde9904a1b' -> '3c2d875540934244abcbc58e' (PARTY_CITY.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/pants_bear_triarius.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\SRVV\CAUSTIC\TACTICAL_PANTS_CAUSTIC_PANTS.json5
- questRequirements: 'DRIP_10' -> '669f78e3ea69f9bde9904a1b' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f78e3ea69f9bde9904a1b' -> '3c2d875540934244abcbc58e' (PARTY_CITY.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/pants_bear_triarius.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\SRVV\CZECHMLOK\TACTICAL_PANTS_CZECHMLOK_PANTS.json5
- traderId: replaced raw ID 579dc571d53a0658a154fbec with 'fence'
- questRequirements: 'DRIP_14' -> '669f7a46a33b9e7cbda18b33' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f7a46a33b9e7cbda18b33' -> '02cf1311c15283c098411606' (MOSIN_MAN.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/pants_bear_triarius.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\SRVV\OLIVEDRAB\TACTICAL_PANTS_OLIVEDRAB_PANTS.json5
- questRequirements: 'DRIP_9' -> '669f78890cf4da93267775f6' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f78890cf4da93267775f6' -> '8cddf80eec8b1a35289ac0de' (JUNKER.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/pants_bear_triarius.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\SRVV\PLANAVAL\TACTICAL_PANTS_PLANAVAL_PANTS.json5
- questRequirements: 'DRIP_14' -> '669f7a46a33b9e7cbda18b33' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f7a46a33b9e7cbda18b33' -> '02cf1311c15283c098411606' (MOSIN_MAN.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/pants_bear_triarius.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\SRVV\TARNANZUG\TACTICAL_PANTS_TARNANZUG_PANTS.json5
- vanillaOrigin: assets/content/characters/character/prefabs/pants_bear_triarius.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\URBANRESPONDER\3COLOURDESERT\URBANFIGHTER_3COLOURDESERT_PANTS.json5
- questRequirements: 'DRIP_11' -> '669f795b4657ccef2265f1be' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f795b4657ccef2265f1be' -> '578a93566b8b54357bf354bb' (SYSTEM_DESTROYER_PART_1.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/pants_usec_urbanresponder.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\URBANRESPONDER\BLACK\URBANFIGHTER_BLACK_PANTS.json5
- questRequirements: 'DRIP_7' -> '669f78036d104f2127da9a3b' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f78036d104f2127da9a3b' -> '6ba9c681caa1ac2561cf8802' (SHOCK_AND_AWE.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/pants_usec_urbanresponder.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\URBANRESPONDER\CADPAT\URBANFIGHTER_CADPAT_PANTS.json5
- questRequirements: 'DRIP_12' -> '669f79c7f8b1f185365997e3' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f79c7f8b1f185365997e3' -> 'd5fb79830a150e4c596468bd' (SYSTEM_DESTROYER_PART_2.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/pants_usec_urbanresponder.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)
- override: price 0 -> 32000 (see OVERRIDES in this script)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\URBANRESPONDER\LEAFS\URBANFIGHTER_LEAFS_PANTS.json5
- questRequirements: 'DRIP_9' -> '669f78890cf4da93267775f6' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f78890cf4da93267775f6' -> '8cddf80eec8b1a35289ac0de' (JUNKER.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/pants_usec_urbanresponder.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\URBANRESPONDER\SIXCOLOURURBAN\URBANFIGHTER_SIXCOLOURURBAN_PANTS.json5
- questRequirements: 'DRIP_12' -> '669f79c7f8b1f185365997e3' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f79c7f8b1f185365997e3' -> 'd5fb79830a150e4c596468bd' (SYSTEM_DESTROYER_PART_2.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/pants_usec_urbanresponder.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)
- override: price 0 -> 32000 (see OVERRIDES in this script)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\URBANRESPONDER\UCPBRUSH\URBANFIGHTER_UCPBRUSH_PANTS.json5
- questRequirements: 'DRIP_12' -> '669f79c7f8b1f185365997e3' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f79c7f8b1f185365997e3' -> 'd5fb79830a150e4c596468bd' (SYSTEM_DESTROYER_PART_2.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/pants_usec_urbanresponder.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)
- override: price 0 -> 32000 (see OVERRIDES in this script)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\URBANRESPONDER\VZ95\URBANFIGHTER_VZ95_PANTS.json5
- vanillaOrigin: assets/content/characters/character/prefabs/pants_usec_urbanresponder.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\USECBASE\AOR2\FATIGUES_AOR2_PANTS.json5
- questRequirements: 'DRIP_1' -> '669cdb5039f39e1bd6019b56' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669cdb5039f39e1bd6019b56' -> '55b0f24605877596e6ea8474' (THE_MORNING_AFTER.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/pants_usec_cryeac.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\USECBASE\CADPAT\FATIGUES_CADPAT_PANTS.json5
- questRequirements: 'DRIP_1' -> '669cdb5039f39e1bd6019b56' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669cdb5039f39e1bd6019b56' -> '55b0f24605877596e6ea8474' (THE_MORNING_AFTER.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/pants_usec_cryeac.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\USECBASE\KHAKI\FATIGUES_KHAKI_PANTS.json5
- questRequirements: 'DRIP_1' -> '669cdb5039f39e1bd6019b56' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669cdb5039f39e1bd6019b56' -> '55b0f24605877596e6ea8474' (THE_MORNING_AFTER.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/pants_usec_cryeac.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\USECBASE\RANGERGREEN\FATIGUES_RANGERGREEN_PANTS.json5
- questRequirements: 'DRIP_1' -> '669cdb5039f39e1bd6019b56' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669cdb5039f39e1bd6019b56' -> '55b0f24605877596e6ea8474' (THE_MORNING_AFTER.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/pants_usec_cryeac.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\ZASLON\AOR2\ZASLON_SOC_PANTS.json5
- vanillaOrigin: assets/content/characters/character/prefabs/pants_bear_zaslon.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\ZASLON\BARVIKHAPROTO\ZASLON_BARVIKHAPROTO_BOTTOM.json5
- vanillaOrigin: assets/content/characters/character/prefabs/pants_bear_zaslon.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\ZASLON\BLACK\ZASLON_BLACK_PANTS.json5
- questRequirements: 'DRIP_13' -> '669f7a04a6bd56d17bae1089' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f7a04a6bd56d17bae1089' -> '74f0e746d3720d3fae01ccab' (HEAD_EYES.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/pants_bear_zaslon.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\ZASLON\CADPAT\ZASLON_CADPAT_PANTS.json5
- vanillaOrigin: assets/content/characters/character/prefabs/pants_bear_zaslon.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\ZASLON\GOERGIAKKO\ZASLON_GEORGIAKKO_PANTS.json5
- traderId: replaced raw ID 579dc571d53a0658a154fbec with 'fence'
- vanillaOrigin: assets/content/characters/character/prefabs/pants_bear_zaslon.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\ZASLON\GREY\ZASLON_GREY_PANTS.json5
- questRequirements: 'DRIP_9' -> '669f78890cf4da93267775f6' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f78890cf4da93267775f6' -> '8cddf80eec8b1a35289ac0de' (JUNKER.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/pants_bear_zaslon.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\ZASLON\LUXEMBOURG\ZASLON_LUXEMBOURG_PANTS.json5
- vanillaOrigin: assets/content/characters/character/prefabs/pants_bear_zaslon.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\ZASLON\MM14\ZASLON_MM14_PANTS.json5
- vanillaOrigin: assets/content/characters/character/prefabs/pants_bear_zaslon.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\BOTTOM\ZASLON\PENCOTT\ZASLON_PENCOTT_PANTS.json5
- questRequirements: 'DRIP_14' -> '669f7a46a33b9e7cbda18b33' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f7a46a33b9e7cbda18b33' -> '02cf1311c15283c098411606' (MOSIN_MAN.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/pants_bear_zaslon.bundle
- bundles: 'bottomDependencies' -> bundles['BOTTOM.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bottomBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\ADAPTIVECOMBAT\ERDL\COMBAT_UNIFORM_ERDL_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/top_usec_acu.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\ADAPTIVECOMBAT\MM14\COMBAT_UNIFORM_MM14_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/top_usec_acu.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\ADAPTIVECOMBAT\REDURBAN\COMBAT_UNIFORM_REDURBAN_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/top_usec_acu.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\AGGRESSOR\3COLOURDESERT\COMBATPARKA_3COLOURDESERT_TOP.json5
- questRequirements: 'DRIP_11' -> '669f795b4657ccef2265f1be' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f795b4657ccef2265f1be' -> '578a93566b8b54357bf354bb' (SYSTEM_DESTROYER_PART_1.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/top_usec_aggressor_parka.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\AGGRESSOR\6COLOURDESERT\COMBATPARKA_SIXCOLOURDESERT_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/top_usec_aggressor_parka.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\AGGRESSOR\BLACK\COMBATPARKA_BLACK_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/top_usec_aggressor_parka.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\AGGRESSOR\FLECKTARN\COMBATPARKA_FLECKTARN_TOP.json5
- questRequirements: 'DRIP_18' -> '669f7b28d1dbbbdb0475e7be' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f7b28d1dbbbdb0475e7be' -> '87f2ff0b5d7e277e642330bc' (FRIENDLY_FEUD.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/top_usec_aggressor_parka.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\AGGRESSOR\NAVY\COMBATPARKA_NAVY_TOP.json5
- questRequirements: 'DRIP_12' -> '669f79c7f8b1f185365997e3' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f79c7f8b1f185365997e3' -> 'd5fb79830a150e4c596468bd' (SYSTEM_DESTROYER_PART_2.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/top_usec_aggressor_parka.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)
- override: price 0 -> 46000 (see OVERRIDES in this script)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\BAJAJACKET\BLACK\BAJAJACKET_BLACK_TOP.json5
- questRequirements: 'DRIP_13' -> '669f7a04a6bd56d17bae1089' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f7a04a6bd56d17bae1089' -> '74f0e746d3720d3fae01ccab' (HEAD_EYES.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/top_boss_birdeye.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\BAJAJACKET\GREY\BAJAJACKET_GREY_TOP.json5
- questRequirements: 'DRIP_13' -> '669f7a04a6bd56d17bae1089' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f7a04a6bd56d17bae1089' -> '74f0e746d3720d3fae01ccab' (HEAD_EYES.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/top_boss_birdeye.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\BEARBASE\USEC\ROLLED_USEC_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/tshirt_bear_turtleneck.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\BLACKLYNX\GREY\TACTICALHOODIE_GRAY_TOP.json5
- questRequirements: 'DRIP_14' -> '669f7a46a33b9e7cbda18b33' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f7a46a33b9e7cbda18b33' -> '02cf1311c15283c098411606' (MOSIN_MAN.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/top_bear_blacklynx.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\BLACKLYNX\OLIVEDRAB\TACTICALHOODIE_OLIVEDRAB_TOP.json5
- questRequirements: 'DRIP_14' -> '669f7a46a33b9e7cbda18b33' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f7a46a33b9e7cbda18b33' -> '02cf1311c15283c098411606' (MOSIN_MAN.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/top_bear_blacklynx.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\BOREAS\BLACKSHARK\TACTICAL_JACKET_BLACK_SHARK_TOP.json5
- questRequirements: 'DRIP_10' -> '669f78e3ea69f9bde9904a1b' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f78e3ea69f9bde9904a1b' -> '3c2d875540934244abcbc58e' (PARTY_CITY.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/top_bear_borey.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\BOREAS\CAUSTIC\TACTICAL_JACKET_CAUSTIC_TOP.json5
- questRequirements: 'DRIP_10' -> '669f78e3ea69f9bde9904a1b' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f78e3ea69f9bde9904a1b' -> '3c2d875540934244abcbc58e' (PARTY_CITY.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/top_bear_borey.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\CEREUM\URBAN_HUNTER\PUFFER_URBAN_HUNTER_TOP.json5
- questRequirements: 'DRIP_14' -> '669f7a46a33b9e7cbda18b33' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f7a46a33b9e7cbda18b33' -> '02cf1311c15283c098411606' (MOSIN_MAN.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/top_usec_cereum.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\FSBFASTRESPONSE\PLAIDRED\PLAIDSHIRT_RED_TOP.json5
- questRequirements: 'DRIP_2' -> '669f74d7e7211bf21d8af254' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f74d7e7211bf21d8af254' -> 'b05a483cc90cb02bc9b090d3' (MATERIAL_HANDLER.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/top_bear_fsbfastresponse.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\FSBFASTRESPONSE\PLAIDYELLOW\PLAIDSHIRT_YELLOW_TOP.json5
- questRequirements: 'DRIP_2' -> '669f74d7e7211bf21d8af254' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f74d7e7211bf21d8af254' -> 'b05a483cc90cb02bc9b090d3' (MATERIAL_HANDLER.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/top_bear_fsbfastresponse.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\GHILLIE\WOODLAND\GHILLIE_WOODLAND_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/top_boss_zryachi.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\GHOSTMARKSMAN\BARVIKHAPROTO\MARKSGORKA_BARVIKHAPROTO_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/top_bear_ghostmarksman.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\GHOSTMARKSMAN\BLACK\MARKSGORKA_BLACK_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/top_bear_ghostmarksman.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\GHOSTMARKSMAN\CLASSIC\MARKSGORKA_CLASSIC_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/top_bear_ghostmarksman.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\GHOSTMARKSMAN\FLORA\MARKSGORKA_FLORA_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/top_bear_ghostmarksman.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\GHOSTMARKSMAN\IZLOM\MARKSGORKA_IZLOM_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/top_bear_ghostmarksman.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\GHOSTMARKSMAN\KLMK\MARKSGORKA_KLMK_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/top_bear_ghostmarksman.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\GORKA4\BARVIKHAPROTO\GORKA4_BARVIKHAPROTO_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/top_security_gorka4.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\GORKA4\BLACK\GORKA4_BLACK_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/top_security_gorka4.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\GORKA4\CLASSIC\GORKA4_CLASSIC_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/top_security_gorka4.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\GORKA4\CLEARSKY\GORKA4_CLEARSKY_STALKER_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/top_security_gorka4.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\GORKA4\FLORA\GORKA4_FLORA_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/top_security_gorka4.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\GORKA4\KLMK\GORKA4_KLMK_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/top_security_gorka4.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\GORKA4\RYZHUKHA\GORKA4_RYZHUKHA_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/top_security_gorka4.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\GORKA4\SKOL\GORKA4_SKOL_TOP.json5
- questRequirements: 'DRIP_12' -> '669f79c7f8b1f185365997e3' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f79c7f8b1f185365997e3' -> 'd5fb79830a150e4c596468bd' (SYSTEM_DESTROYER_PART_2.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/top_security_gorka4.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)
- override: price 0 -> 57500 (see OVERRIDES in this script)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\GORKA4\TTSKO5\GORKA4_TTSKO5_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/top_security_gorka4.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\HOODIE\BD\HOODIE_BD.json5
- questRequirements: 'DRIP_8' -> '669f78477ebc9a09e44cbd6d' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f78477ebc9a09e44cbd6d' -> '8acd28ed1cb7a0574113612c' (LACK_OF_LUBRICATION.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/top_usec_hoody.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\HOODIE\BLACKMESA\HOODIE_BLACKMESA_TOP.json5
- questRequirements: 'DRIP_6' -> '669f77bd952e94e100e88847' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f77bd952e94e100e88847' -> '45f06642a9c58e1b8cb224a9' (FULL_LIFE_CONSEQUENCES.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/top_usec_hoody.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\HOODIE\GLOCKBLACK\HOODIE_GLOCKBLACK_TOP.json5
- questRequirements: 'DRIP_4' -> '669f76cb1fec55b3413b554c' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f76cb1fec55b3413b554c' -> '2a31b752cd9bd6f4a801df8c' (GLOCK_WICK_PART_2.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/top_usec_hoody.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\HOODIE\GLOCKBLUE\HOODIE_GLOCKBLUE_TOP.json5
- questRequirements: 'DRIP_3' -> '669f759a1c5ee26e33c5afb2' (the quest was renumbered; see QUEST_ID_MAP)
- vanillaOrigin: assets/content/characters/character/prefabs/top_usec_hoody.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\HOODIE\GLOCKPURPLE\HOODIE_GLOCKPURPLE_TOP.json5
- questRequirements: 'DRIP_5' -> '669f775edfe50ca330aaa91d' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f775edfe50ca330aaa91d' -> '5f7fbf47c4c42b168789d458' (GLOCK_WICK_PART_3.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/top_usec_hoody.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\HOODIE\HELLISH_RED\HOODIE_HELLISH_RED_TOP.json5
- questRequirements: 'DRIP_8' -> '669f78477ebc9a09e44cbd6d' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f78477ebc9a09e44cbd6d' -> '8acd28ed1cb7a0574113612c' (LACK_OF_LUBRICATION.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/top_usec_hoody.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\HOODIE\HELLISH_W\HOODIE_HELLISH_W_TOP.json5
- questRequirements: 'DRIP_8' -> '669f78477ebc9a09e44cbd6d' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f78477ebc9a09e44cbd6d' -> '8acd28ed1cb7a0574113612c' (LACK_OF_LUBRICATION.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/top_usec_hoody.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\HOODIE\HUNTER\HOODIE_HUNTER_TOP.json5
- questRequirements: 'DRIP_2' -> '669f74d7e7211bf21d8af254' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f74d7e7211bf21d8af254' -> 'b05a483cc90cb02bc9b090d3' (MATERIAL_HANDLER.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/top_usec_hoody.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\HOODIE\REMINGTON\HOODIE_REMINGTON_BLACK_TOP.json5
- questRequirements: 'DRIP_7' -> '669f78036d104f2127da9a3b' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f78036d104f2127da9a3b' -> '6ba9c681caa1ac2561cf8802' (SHOCK_AND_AWE.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/top_usec_hoody.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\INFILTRATOR\MGOTIGER\INFILTRATOR_GRASSY_TIGER_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/tshirt_usec_combatshirt.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\INFILTRATOR\NIGHTDIGITAL\INFILTRATOR_NIGHTDIGITAL_TOP.json5
- questRequirements: 'DRIP_18' -> '669f7b28d1dbbbdb0475e7be' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f7b28d1dbbbdb0475e7be' -> '87f2ff0b5d7e277e642330bc' (FRIENDLY_FEUD.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/tshirt_usec_combatshirt.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\INFILTRATOR\SIXCOLOURDESERT\INFILTRATOR_SIXCOLOURDESERT_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/tshirt_usec_combatshirt.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\INFILTRATOR\USEC\INFILTRATOR_USEC_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/tshirt_usec_combatshirt.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\NIGHTPATROL\BARVIKHAPROTO\PATROLJACKET_BARVIKHAPROTO_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/top_usec_nightpatrol.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\RASHGUARD\BLACK\RASH_BLACK_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/top_bear_voin.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\SECURITYJACKET\GEORGIAKKO\SECURITYJACKET_GEORGIAKKO.json5
- traderId: replaced raw ID 579dc571d53a0658a154fbec with 'fence'
- vanillaOrigin: assets/content/characters/character/prefabs/wild_security_body_1.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\SECURITYJACKET\M05\SECUIRTY_JACKET_M05_TOP.json5
- questRequirements: 'DRIP_14' -> '669f7a46a33b9e7cbda18b33' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f7a46a33b9e7cbda18b33' -> '02cf1311c15283c098411606' (MOSIN_MAN.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/wild_security_body_1.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\SECURITYJACKET\OLIVEDRAB\SECURITY_JACKET_OLIVEDRAB_TOP.json5
- questRequirements: 'DRIP_1' -> '669cdb5039f39e1bd6019b56' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669cdb5039f39e1bd6019b56' -> '55b0f24605877596e6ea8474' (THE_MORNING_AFTER.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/wild_security_body_1.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\SPN\BARVIKHAPROTO\SURPLUSJACKET_BARVIKHAPROTO_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/top_bear_spna.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\SPN\EMERCOMVSR\SURPLUSJACKET_EMERCOMVSR_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/top_bear_spna.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\SPN\VZ95\SURPLUSJACKET_VZ95_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/top_bear_spna.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\SUMMERFIELD\FLORA\FIGHTINGJACKET_FLORA_TOP.json5
- questRequirements: 'DRIP_12' -> '669f79c7f8b1f185365997e3' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f79c7f8b1f185365997e3' -> 'd5fb79830a150e4c596468bd' (SYSTEM_DESTROYER_PART_2.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/top_bear_polevoi.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)
- override: price 0 -> 42000 (see OVERRIDES in this script)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\SUMMERFIELD\SKOL\FIGHTINGJACKET_SKOL_TOP.json5
- questRequirements: 'DRIP_12' -> '669f79c7f8b1f185365997e3' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f79c7f8b1f185365997e3' -> 'd5fb79830a150e4c596468bd' (SYSTEM_DESTROYER_PART_2.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/top_bear_polevoi.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)
- override: price 0 -> 42000 (see OVERRIDES in this script)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\TELNIK\EMERCOM\TELNIK_EMERCOM_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/tshirt_bear_telnik.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\TELNIK\FSB\TELNIK_FSB_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/tshirt_bear_telnik.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\TIGR\COYOTE\TIGER_COYOTE_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/tshirt_bear_tiger.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\TIGR\GREENZONE\TIGER_GREENZONE_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/tshirt_bear_tiger.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\TIGR\WALDTARNDRUCK\TIGER_LUXEMBOURG_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/tshirt_bear_tiger.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\TSHIRT\AGENDA\TSHIRT_AGENDA_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/tshirt_bear_black.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\TSHIRT\BAIKAL_BLACK\TSHIRT_BAIKAL_BLACK_TOP.json5
- questRequirements: 'DRIP_9' -> '669f78890cf4da93267775f6' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f78890cf4da93267775f6' -> '8cddf80eec8b1a35289ac0de' (JUNKER.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/tshirt_bear_black.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\TSHIRT\BAIKAL_WHITE\TSHIRT_BAIKAL_WHITE_TOP.json5
- questRequirements: 'DRIP_9' -> '669f78890cf4da93267775f6' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f78890cf4da93267775f6' -> '8cddf80eec8b1a35289ac0de' (JUNKER.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/tshirt_bear_black.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\TSHIRT\BOYKISSER\TSHIRT_BOYKISSER_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/tshirt_bear_black.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\TSHIRT\COLETTE\TSHIRT_COLETTE_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/tshirt_bear_black.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\TSHIRT\HEADEYES\TSHIRT_HEADEYES_TOP.json5
- questRequirements: 'DRIP_13' -> '669f7a04a6bd56d17bae1089' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f7a04a6bd56d17bae1089' -> '74f0e746d3720d3fae01ccab' (HEAD_EYES.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/tshirt_bear_black.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\TSHIRT\HEADPAT\TSHIRT_HEADPAT_WINTER_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/tshirt_bear_black.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\TSHIRT\IMMORAL\TSHIRT_IMMORAL_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/tshirt_bear_black.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\TSHIRT\TULA_BLACK\TSHIRT_TULA_BLACK_TOP.json5
- questRequirements: 'DRIP_14' -> '669f7a46a33b9e7cbda18b33' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f7a46a33b9e7cbda18b33' -> '02cf1311c15283c098411606' (MOSIN_MAN.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/tshirt_bear_black.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\TSHIRT\TULA_WHITE\TSHIRT_TULA_WHITE_TOP.json5
- questRequirements: 'DRIP_14' -> '669f7a46a33b9e7cbda18b33' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f7a46a33b9e7cbda18b33' -> '02cf1311c15283c098411606' (MOSIN_MAN.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/tshirt_bear_black.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\USECBASE\AOR2\FATIGUES_AOR2_TOP.json5
- questRequirements: 'DRIP_1' -> '669cdb5039f39e1bd6019b56' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669cdb5039f39e1bd6019b56' -> '55b0f24605877596e6ea8474' (THE_MORNING_AFTER.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/tshirt_usec_cryeac.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\USECBASE\CADPAT\FATIGUES_CADPAT_TOP.json5
- questRequirements: 'DRIP_1' -> '669cdb5039f39e1bd6019b56' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669cdb5039f39e1bd6019b56' -> '55b0f24605877596e6ea8474' (THE_MORNING_AFTER.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/tshirt_usec_cryeac.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\USECBASE\KHAKI\FATIGUES_KHAKI_TOP.json5
- questRequirements: 'DRIP_1' -> '669cdb5039f39e1bd6019b56' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669cdb5039f39e1bd6019b56' -> '55b0f24605877596e6ea8474' (THE_MORNING_AFTER.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/tshirt_usec_cryeac.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\USECBASE\RANGERGREEN\FATIGUES_RANGERGREEN_TOP.json5
- questRequirements: 'DRIP_1' -> '669cdb5039f39e1bd6019b56' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669cdb5039f39e1bd6019b56' -> '55b0f24605877596e6ea8474' (THE_MORNING_AFTER.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/tshirt_usec_cryeac.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\WINTERJACKET\DRIP\WINTERJACKET_DRIP_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/top_boss_shturman_skin.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\WINTERJACKET\HORNETSTRIPE\WINTERJACKET_HORNETSTRIPE_TOP.json5
- vanillaOrigin: assets/content/characters/character/prefabs/top_boss_shturman_skin.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\CLOTHING\TOP\WINTERJACKET\SOC\WINTERJACKET_SOC_TOP.json5
- questRequirements: 'DRIP_14' -> '669f7a46a33b9e7cbda18b33' (the quest was renumbered; see QUEST_ID_MAP)
- questRequirements: '669f7a46a33b9e7cbda18b33' -> '02cf1311c15283c098411606' (MOSIN_MAN.jsonc now ships the quest; see QUEST_FILENAME)
- vanillaOrigin: assets/content/characters/character/prefabs/top_boss_shturman_skin.bundle
- bundles: 'topDependencies' -> bundles['TOP.bundle'], dropped 2 dependency(ies) now applied automatically
- bundles: 'handsDependencies' -> bundles['HANDS.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'topBundlePath' — bundles are found by co-location now
- dropped 'handsBundlePath' — bundles are found by co-location now
- kept 'tags' unchanged (reserved for ICUP)

### DRIP Part 1 (Essentials)\items\GEAR\ARMOR\6B23\CLEARSKY_STALKER\ARMOR_6B23_CLEARSKY_STALKER.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\ARMOR\6B23\KLMK\ARMOR_6B23_KLMK.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\ARMOR\6B23\SKOL\ARMOR_6B23_SKOL.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\ARMOR\6B23\TTSKO5\ARMOR_6B23_TTSKO5.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\ARMOR\6B2\OLIVEDRAB\ARMOR_6B2_OLIVE.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\ARMOR\6B43\BLACK\ARMOR_6B43_BLACK.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\ARMOR\6B43\FLORA\ARMOR_6B43_FLORA.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\ARMOR\HEXATAC\VZ95\HEXATAC_VZ95_ARMOR.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\ARMOR\IOTVASSAULT\DIGITALTIGERSTRIPE\GEN4_ASSAULT_DIGITALTIGERSTRIPE.json5
- price: flattened {currency, amount} to price 368043 + currency RUB
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- dropped 'textureGearDependencies' — it was always empty; the co-located TEXTURE bundle is discovered automatically
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'
- renamed 'childAssorts' to 'includedParts'

### DRIP Part 1 (Essentials)\items\GEAR\ARMOR\IOTVFULL\DIGITALTIGERSTRIPE\GEN4_FULL_DIGITALTIGERSTRIPE.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- dropped 'textureGearDependencies' — it was always empty; the co-located TEXTURE bundle is discovered automatically
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\ARMOR\IOTVMOBILITY\DIGITALTIGERSTRIPE\GEN4_MOBILITY_DIGITALTIGERSTRIPE.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- dropped 'textureGearDependencies' — it was always empty; the co-located TEXTURE bundle is discovered automatically
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\ARMOR\KORUND\EMR\KORUND_EMR_ARMOR.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\ARMOR\KORUND\KKO\KORUND_KKO_ARMOR.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\ARMOR\KORUND\TTSKO5\KORUND_TTSKO5_ARMOR.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\ARMOR\SLICK\CADPAT\SLICK_CADPAT_ARMOR.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\ARMOR\SLICK\ERDL\SLICK_ERDL_ARMOR.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\ARMOR\SLICK\GREENZONE\SLICK_GREENZONE_ARMOR.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\ARMOR\SLICK\LEAFS\SLICK_LEAFS_ARMOR.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\ARMOR\SLICK\LUXEMBOURG\SLICK_LUXEMBOURG_ARMOR.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\ARMOR\THORINTEGRATED\BLACK\ARMOR_THORINT_BLACK.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\ARMOR\TROOPER\BLACK\TROOPER_BLACK_ARMOR.json5
- price: flattened {currency, amount} to price 1360 + currency USD
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'
- renamed 'childAssorts' to 'includedParts'

### DRIP Part 1 (Essentials)\items\GEAR\ARMOR\TROOPER\FLECKTARN\TROOPER_FLECKTARN_ARMOR.json5
- price: flattened {currency, amount} to price 1360 + currency USD
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'
- renamed 'childAssorts' to 'includedParts'

### DRIP Part 1 (Essentials)\items\GEAR\ARMOR\TROOPER\FUCKTARN\TROOPER_FUCKTARN_ARMOR.json5
- price: flattened {currency, amount} to price 1360 + currency USD
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'
- renamed 'childAssorts' to 'includedParts'

### DRIP Part 1 (Essentials)\items\GEAR\ARMOR\UNTAR\3COLOURDESERT\FLAKJACKET_3COLOURDESERT_VEST.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\ARMOR\UNTAR\6COLOURDESERT\FLAKJACKET_CHOCOLATE_ARMOR.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\ARMOR\UNTAR\BLACK\FLAKJACKET_BLACK_ARMOR.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\ARMOR\UNTAR\CONTRACTOR\FLAKJACKET_CONTRACTOR_ARMOR.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\ARMOR\UNTAR\LUXEMBOURG\FLAKJACKET_LUXEMBOURG_ARMOR.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\ARMOR\UNTAR\M81\FLAKJACKET_M81_ARMOR.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\ARMOR\UNTAR\OLIVEDRAB\FLAKJACKET_OLIVEDRAB_ARMOR.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\ARMOR\ZHUK6A\BLACK\ZHUK6A_BLACK_ARMOR.json5
- price: flattened {currency, amount} to price 2450 + currency USD
- REPAIRED — includedParts["Soft_armor_back"] was 65764275d8537eb26a0355e9, which the game will not fit there - the slot was left empty. Now 657642b0e6d5dd75f40688a5. See SLOT_FIXES in this script.
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'
- renamed 'childAssorts' to 'includedParts'

### DRIP Part 1 (Essentials)\items\GEAR\BAGS\6SH118\BLACK\RAID_BLACK_BAG.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\BAGS\BERKUT\USEC\BERKUT_USEC_BAG.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\BAGS\BETA2\CADPAT\BETA2_CADPAT_BAG.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\BAGS\BETA2\COMBATBLACK\BETA2_COMBATBLACK_BAG.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\BAGS\BETA2\MONOLITA\BETA2_MONOLITA_BAG.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\BAGS\BETA2\NIGHTPATROL\BETA2_NIGHTPATROL_BAG.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\BAGS\BETA2\OLIVEDRAB\BETA2_OLIVEDRAB_BAG.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\BAGS\BLACKJACK\BLACK\BLACKJACK_BLACK_BAG.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\BAGS\DAYPACK\HELLOMILFY\DAYPACK_HELLOMILFY_BAG.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\BAGS\DAYPACK\LUXEMBOURG\DAYPACK_LUXEMBOURG_BAG.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\BAGS\DAYPACK\PENCOTT\DAYPACK_PENCOTT_BAG.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\BAGS\DAYPACK\TTSKO5\DAYPACK_TTSKO5_BAG.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\BAGS\MBSS\CADPAT\MBSS_CADPAT_BAG.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\BAGS\MBSS\ERDL\MBSS_ERDL_BAG.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\BAGS\MBSS\LUXEMOURG\MBSS_LUXEMBOURG_BAG.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\BAGS\MBSS\OLIVEDRAB\MBSS_OLIVEDRAB_BAG.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\BAGS\MBSS\PINKDEATH\MBSS_PINKDEATH_BAG.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\BAGS\NICECOMM\3COLOURDESERT\NICECOMM_3COLOURDESERT_BAG.json5
- price: flattened {currency, amount} to price 217999 + currency RUB
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\BAGS\NICECOMM\BLACK\NICECOMM_BLACK_BAG.json5
- price: flattened {currency, amount} to price 217999 + currency RUB
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\BAGS\NICECOMM\M81DIGITAL\NICECOMM_M81DIGITAL_BAG.json5
- price: flattened {currency, amount} to price 217999 + currency RUB
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\BAGS\SLING\PENCOTTGREENZONE\SLING_PENCOTTGREENZONE_BAG.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\BAGS\SLING\TARNANZUGNEU\SLING_TARNANZUGNEU_BAG.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\BAGS\SLING\VZ95\SLING_VZ95_BAG.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\BAGS\TRIZIP\6COLOURWOODLAND\TRIZIP_6COLOURWOODLAND_BAG.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\BAGS\TRIZIP\OLIVEDRAB\TRIZIP_OD_BAG.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\BAGS\TROOPER35\BLACK\TROOPER35_BLACK_BAG.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\FACE\HALFMASK\SMILE1\HALFMASK_SMILE1.json5
- price: flattened {currency, amount} to price 1620 + currency RUB
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- bundles: GEAR.bundle depends on ContentPacks/Essentials/CustomItems/FACE/HALFMASK/SMILE1/TEXTURE.bundle (see BUNDLE_DEPENDENCIES in this script)
- dropped 'bundlePath' — bundles are found by co-location now
- dropped 'textureGearDependencies' — it was always empty; the co-located TEXTURE bundle is discovered automatically
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\FACE\HALFMASK\SMILE2\HALFMASK_SMILE2.json5
- price: flattened {currency, amount} to price 1620 + currency RUB
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- bundles: GEAR.bundle depends on ContentPacks/Essentials/CustomItems/FACE/HALFMASK/SMILE2/TEXTURE.bundle (see BUNDLE_DEPENDENCIES in this script)
- dropped 'bundlePath' — bundles are found by co-location now
- dropped 'textureGearDependencies' — it was always empty; the co-located TEXTURE bundle is discovered automatically
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\FACE\HALFMASK\SMILE3\HALFMASK_SMILE3.json5
- price: flattened {currency, amount} to price 1620 + currency RUB
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- bundles: GEAR.bundle depends on ContentPacks/Essentials/CustomItems/FACE/HALFMASK/SMILE3/TEXTURE.bundle (see BUNDLE_DEPENDENCIES in this script)
- dropped 'bundlePath' — bundles are found by co-location now
- dropped 'textureGearDependencies' — it was always empty; the co-located TEXTURE bundle is discovered automatically
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\FACE\HALFMASK\SMILE4\HALFMASK_SMILE4.json5
- price: flattened {currency, amount} to price 1620 + currency RUB
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- bundles: GEAR.bundle depends on ContentPacks/Essentials/CustomItems/FACE/HALFMASK/SMILE4/TEXTURE.bundle (see BUNDLE_DEPENDENCIES in this script)
- dropped 'bundlePath' — bundles are found by co-location now
- dropped 'textureGearDependencies' — it was always empty; the co-located TEXTURE bundle is discovered automatically
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\FACE\MOMEX\COYOTE\MOMEX_COYOTE_FACE.json5
- price: flattened {currency, amount} to price 150 + currency EUR
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\FACE\MOMEX\OD\MOMEX_OD_FACE.json5
- price: flattened {currency, amount} to price 150 + currency EUR
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\FACE\MUSTACHE\BLONDE\MUSTACHE_BLONDE_FACE.json5
- price: flattened {currency, amount} to price 100 + currency USD
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\FACE\MUSTACHE\DARKGREY\MUSTACHE_DARKGREY_FACE.json5
- price: flattened {currency, amount} to price 100 + currency USD
- questRequirements: 'DRIP_3' -> '669f759a1c5ee26e33c5afb2' (the quest was renumbered; see QUEST_ID_MAP)
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\FACE\MUSTACHE\GINGER\MUSTACHE_GINGER_FACE.json5
- price: flattened {currency, amount} to price 100 + currency USD
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\FACE\MUSTACHE\GREY\MUSTACHE_GREY_FACE.json5
- price: flattened {currency, amount} to price 100 + currency USD
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 2 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\FACE\WELDINGSHIELD\COCKENJOYER\WELDINGSHIELD_COCKENJOYER_FACE.json5
- price: flattened {currency, amount} to price 69420 + currency RUB
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\FACE\WELDINGSHIELD\PISSBABY\WELDINGSHIELD_PISSBABY_FACE.json5
- price: flattened {currency, amount} to price 69420 + currency RUB
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\HATS\ARMYCAP\CZECHMLOK\ARMYCAP_CZECHMLOK_HAT.json5
- price: flattened {currency, amount} to price 100 + currency EUR
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\HATS\ARMYCAP\ERDL\ARMYCAP_ERDL_HAT.json5
- price: flattened {currency, amount} to price 100 + currency EUR
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\HATS\ARMYCAP\NWU\ARMYCAP_NWU_HAT.json5
- price: flattened {currency, amount} to price 100 + currency EUR
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\HATS\ARMYCAP\REDURBAN\ARMYCAP_REDURBAN_HAT.json5
- price: flattened {currency, amount} to price 100 + currency EUR
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\HATS\DOORKICKER\CADPAT\DOORKICKER_CADPAT_HAT.json5
- price: flattened {currency, amount} to price 130 + currency USD
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\HATS\DOORKICKER\ERDL\DOORKICKER_ERDL_HAT.json5
- price: flattened {currency, amount} to price 130 + currency USD
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\HATS\DOORKICKER\REDURBAN\DOORKICKER_REDURBAN_HAT.json5
- price: flattened {currency, amount} to price 130 + currency USD
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\HATS\DOORKICKER\TTSKO5\DOORKICKER_TTSKO5_HAT.json5
- price: flattened {currency, amount} to price 130 + currency USD
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\HATS\EMERCOMCAP\EMERCOMVSR\EMERCOMCAP_EMERCOMVSR_HAT.json5
- price: flattened {currency, amount} to price 75 + currency USD
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\HATS\MILTECBOONIE\ERDL\PANAMA_ERDL_HAT.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\HATS\MILTECBOONIE\REDURBAN\PANAMA_REDURBAN_HAT.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\HATS\MILTECBOONIE\TTSKO5\PANAMA_TTSKO5_HAT.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\HEADSET\COMTAC4\BLACK\COMTAC4_BLACK_HEADSET.json5
- price: flattened {currency, amount} to price 845 + currency USD
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\HELM\6B47COVERED\CHZECHMLOK\HELMET_6B47_CZECHMLOK.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\HELM\6B47COVERED\KLMK\HELM_6B47_COVERED_KLMK.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\HELM\6B47COVERED\SKOL\HELM_6B47_COVERED_SKOL.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\HELM\6B47COVERED\VZ95\HELM_6B47_COVERED_VZ95.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\HELM\AIRFRAME\RANGERGREEN\AIRFRAME_RANGERGREEN_HELM.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- bundles: GEAR.bundle depends on ContentPacks/Essentials/CustomItems/HELM/AIRFRAME/RANGERGREEN/TEXTURE.bundle (see BUNDLE_DEPENDENCIES in this script)
- dropped 'bundlePath' — bundles are found by co-location now
- dropped 'textureGearDependencies' — it was always empty; the co-located TEXTURE bundle is discovered automatically
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\HELM\FASTMT\USEC\FASTMT_USEC_MESH.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- bundles: GEAR.bundle depends on ContentPacks/Essentials/CustomItems/HELM/FASTMT/USEC/TEXTURE1.bundle (see BUNDLE_DEPENDENCIES in this script)
- bundles: GEAR.bundle depends on ContentPacks/Essentials/CustomItems/HELM/FASTMT/USEC/TEXTURE2.bundle (see BUNDLE_DEPENDENCIES in this script)
- dropped 'bundlePath' — bundles are found by co-location now
- dropped 'textureGearDependencies1' — it was always empty; the co-located TEXTURE bundle is discovered automatically
- dropped 'textureGearDependencies2' — it was always empty; the co-located TEXTURE bundle is discovered automatically
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\HELM\TACKEKHEAVY\BLACK\HELMET_TKHEAVYTROOPER_BLACK.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\6SH112\CLEARSKY\RIG_6SH112_CLEARSKY_STALKER.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\6SH112\FLORA\RIG_6SH112_FLORA.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\6SH112\KLMK\RIG_6SH112_KLMK.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\6SH112\SKOL\RIG_6SH112_SKOL.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\A18\CADPAT\RIG_A18_CADPAT.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\A18\MM14\RIG_A18_MM14.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\ANAALPHA\EMR\RIG_ALPHA_EMR.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\ANAM1\ERDL\RIG_M1_ERDL.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\ANAM1\MM14\RIG_M1_MM14.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\AVSTAGILLA\EMR\RIG_AVSMBAV_EMR.json5
- price: flattened {currency, amount} to price 243844 + currency RUB
- REPAIRED — includedParts["Soft_armor_back"] was 6575f5cbf6a13a7b7100b0bf, which the game will not fit there - the slot was left empty. Now 6575f5e1da698a4e98067869. See SLOT_FIXES in this script.
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'
- renamed 'childAssorts' to 'includedParts'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\AVSTAGILLA\ERDL\RIG_AVSMBAV_ERDL.json5
- price: flattened {currency, amount} to price 243844 + currency RUB
- REPAIRED — includedParts["Soft_armor_back"] was 6575f5cbf6a13a7b7100b0bf, which the game will not fit there - the slot was left empty. Now 6575f5e1da698a4e98067869. See SLOT_FIXES in this script.
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'
- renamed 'childAssorts' to 'includedParts'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\AVSTAGILLA\RUSPLINTER\RIG_AVSMBAV_RUSPLINTER.json5
- price: flattened {currency, amount} to price 243844 + currency RUB
- REPAIRED — includedParts["Soft_armor_back"] was 6575f5cbf6a13a7b7100b0bf, which the game will not fit there - the slot was left empty. Now 6575f5e1da698a4e98067869. See SLOT_FIXES in this script.
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'
- renamed 'childAssorts' to 'includedParts'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\AVS\CADPAT\AVS_CADPAT_ARMOR.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\AVS\FLECKTARN\AVS_FLECKTARN_ARMOR.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\AVS\MM14\AVS_MM14_ARMOR.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\AVS\USEC\AVS_USEC_ARMOR.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\AZIMUTZHUK\SIXCOLOURURBAN\RIG_ZHUK_SIXCOLOURURBAN.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\BANKROBBER\FLECKTARN\RIG_BANKROBBER_FLECKTARN.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\BANSHEE\AOR2\RIG_BANSHEE_AOR2.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\BANSHEE\CADPAT\RIG_BANSHEE_CADPAT.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\BANSHEE\COYOTE\RIG_BANSHEE_COYOTE.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\BLACKROCK\BLACK\RIG_BLACKROCK_BLACK.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\BSSMK1\EMR\BSSMK1_EMR_RIG.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\BSSMK1\VZ95\BSSMK1_VZ95_RIG.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\COMMANDO\AHEGAO\RIG_COMMANDO_AHEGAO.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\COMMANDO\LUXEMBOURG\RIG_COMMANDO_LUXEMBOURG.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\COMMANDO\M81\RIG_COMMANDO_M81.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\COMMANDO\OLIVEDRAB\RIG_COMMANDO_OLIVEDRAB.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\COMMANDO\PENCOTT\RIG_COMMANDO_PENCOTT.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\CPC\USEC\CPC_USEC_ARMOR.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\D3CRX\BLACK\D3CRX_BLACK_RIG.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\D3CRX\M81\D3CRX_M81_RIG.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\LBT1961A\CADPAT\RIG_LBCR_CADPAT.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\LBT1961A\ERDL\RIG_LBCR_ERDL.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\LBT1961A\OLIVEDRAB\RIG_LBCR_OLIVEDRAB.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\LBT1961A\SAFETY\RIG_LBCR_SAFETY.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\LBT1961A\TARNANZUG\RIG_LCBR_TARNANZUG.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\MMAC\AOR2\RIG_MMAC_AOR2.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\OSPREYMK4A\BLACK\RIG_OSPREYPROTECTION_BLACK.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\PLATEFRAME\FLECKTARN\RIG_PLATEFRAME_FLECK.json5
- price: flattened {currency, amount} to price 260953 + currency RUB
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'
- renamed 'childAssorts' to 'includedParts'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\PLATEFRAME\USEC\RIG_PLATEFRAME_USEC.json5
- price: flattened {currency, amount} to price 260953 + currency RUB
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'
- renamed 'childAssorts' to 'includedParts'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\SCAVVEST\M81\SCAVVEST_M81.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\TACTEC\CADPAT\RIG_TACTEC_CADPAT.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\TACTEC\GREENZONE\RIG_TACTEC_GREENZONE.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\TACTEC\MM14\RIG_TACTEC_MM14.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\TACTEC\USEC\RIG_TACTEC_USEC.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\TARZAN\EMR\TARZAN_EMR_RIG.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\TRITON\LES\TRITON_LES_RIG.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\TV110\CADPAT\RIG_TV110_CADPAT.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 1 (Essentials)\items\GEAR\RIGS\TV110\MM14\RIG_TV110_MM14.json5
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'

### DRIP Part 3\items\GEAR\BAGS\SLING\OLIVEDRAB\SLING_OLIVEDRAB_BAG.json5
- pulled into Part 1 from Part 3 (see PROMOTIONS in this script)
- bundles: 'gearDependencies' -> bundles['GEAR.bundle'], dropped 3 dependency(ies) now applied automatically
- dropped 'bundlePath' — bundles are found by co-location now
- renamed 'baseItemID' to 'basedOn'
- renamed 'copyAssort' to 'copyOriginalOffers'
- renamed 'weightingMult' to 'botWeightMultiplier'
