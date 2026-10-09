# NUKETOWN-AND — Nuketown Zombies Android map-port track

**Base:** `portsandall/COD-BOZ-AND`, branched from the Android 15 ARMv7 build track `MODERN-ANDROID` on 2026-10-09.

**Target:** Bring the **Black Ops II Nuketown Zombies** level into the existing **Black Ops Zombies Android** application. This is a new map/runtime adaptation, not simply an APK rebuild. **No playable Nuketown build exists on this branch yet.**

## Architecture

- The Android application shell is Kotlin. Most gameplay logic and rendering still execute as ARM code inside `boz.s3e`; altering the Kotlin launcher alone cannot add a level.
- BOZ Android uses Marmalade `.dz` archives containing `*.group.bin` resources, with a mobile-specific renderer, scene layout, physics and gameplay data.
- BO2's `zm_nuked.ff` and related assets do not natively load as Marmalade resource groups. Renaming an `.ff` to `.dz` cannot convert it.
- The base APK currently restricts native libraries to `armeabi-v7a`, so the initial Android target must support 32-bit apps. True 64-bit-only Android compatibility needs a separate native engine port.
- Don't publish extracted third-party maps, game binaries, textures, music or paid game data in this public repo. Commit converter tools and documentation instead.

## Implemented: DTRZ archive inventory

The read-only script `tools/nuketown/inventory.py` reads the Marmalade DTRZ file index, catalogs `*.group.bin` members, and optionally fingerprints a BO2 fastfile. It does **not** unpack groups, convert BO2 fastfiles, alter `boz.s3e` or patch the game.

```sh
# Run on the smaller loader archive tracked in this repo.
python3 tools/nuketown/inventory.py \
  --archive app/src/main/assets/blackops_loader.dz \
  --json-out build/nuketown/loader-inventory.json

# Run privately when you have the complete BOZ mobile archive + BO2 map.
python3 tools/nuketown/inventory.py \
  --archive /path/to/blackops_etc.dz \
  --bo2-fastfile /path/to/zm_nuked.ff \
  --json-out build/nuketown/full-inventory.json

python3 -m unittest discover -s tests -p 'test_nuketown_inventory.py' -v
```

The loader archive only contains bootstrap and downloader resources; the main game's map groups are in the separately acquired large `blackops_*.dz` files. A `map_candidates` match is a *name match*, not proof of engine compatibility. Generated reports include archive hashes and file paths; share thoughtfully.

GitHub Actions workflow `.github/workflows/nuketown-assets.yml` tests the Python parser and inventories the tracked loader archive. Its artifact is metadata only. The Android APK workflow on `MODERN-ANDROID` produces the *unmodified BOZ game*, not Nuketown.

## Test gates

| Gate | Exit criterion | Status |
| --- | --- | --- |
| 0. Baseline | Android 15 ARMv7 debug APK assembles | Reported passing on parent `MODERN-ANDROID`; no new device test here |
| 1. Asset inventory | Parse loader and full `blackops_*.dz` group inventory | In progress: utility/tests/CI added |
| 2. Native load path | Find `boz.s3e` native map selection, resource group lookup, collision/AI hooks | Not started |
| 3. Proof-of-load | Load an original one-room test map with floor collision and one spawn | Not started |
| 4. Nuketown geometry | Convert legitimately sourced BO2 meshes, textures, sectors, lightmaps and collision to mobile format | Not started |
| 5. Zombies gameplay | Waves, barriers, perks, random drops, mystery box, Nuketown-specific events | Not started |
| 6. Device build | Build APK and verify input, render, AI, audio, save/exit on Android 15 | Not started |

## Next engineering steps

1. Confirm the DTRZ header/index variant by running CI on the tracked `blackops_loader.dz`. The unit tests use constructed test archives, so a real-file check is essential.
2. Inventory a complete mobile `blackops_etc.dz` (or equivalent) locally, without downloading it into CI. Look for `kino`, `ascension`, `callofthedead`, and their `*_statics`, `*_dynamics`, `*_sectors` groups.
3. Trace the mobile native code's map dispatch, scene parser, mesh/collision and IwRes group lookup. Write down format versions and resource type IDs.
4. Prove custom level loading with an authored dummy room **before** transforming any Nuketown content.
5. Create a proprietary-asset-free converter pipeline for sourced BO2 `zm_nuked.ff`/associated asset files. Geometry alone does not implement rounds, gameplay scripts, navmesh, or level transitions.
6. Verify the actual APK on a 32-bit-capable Android 15 device before claiming success.

### Research references

- Local `buildtools/BOZ_S3E_ANALYSIS.md` and `boz_s3e_tool.py`: executable container/config, **not** the level group's format.
- `knot126/Marmalade-Modding`: experimental DTRZ and `.group.bin` format investigation.
- `clixmods/zm_nuked`: BO3 remake *script* source only, not the original BO2 map geometry or Android runtime.
