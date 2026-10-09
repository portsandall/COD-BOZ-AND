# COD-BOZ-AND — Android 15/16 compatibility branch

## Purpose
Modernize the existing Call of Duty: Black Ops Zombies (2012) Android application wrapper without rewriting the game or taking credit for the upstream Kotlin reconstruction.

Upstream: [eugene373/COD-BOZ-Partially-Decompiled](https://github.com/eugene373/COD-BOZ-Partially-Decompiled)

## Test hardware
- Motorola moto g35 5G, Android 15 (API 35).
- Device-reported ABIs: `arm64-v8a,armeabi-v7a,armeabi`.
- Device supports 32-bit ARMv7 code. **Native ARM64 game-code translation is unnecessary on this phone.**
- This result does not guarantee support on 64-bit-only devices.

## First milestone: a reproducible test APK
- `MODERN-ANDROID` is the working branch.
- `.github/workflows/android-modern.yml` assembles the debug APK with GitHub Actions, without shipping signing secrets to the repository.
- APK output (upon successful run): workflow artifact `cod-boz-android15-armv7-debug`.
- `app/build.gradle.kts` now pins the ABI to `armeabi-v7a` for both debug and release builds so Android does not select the incomplete ARM64 JNI library directory.
- The Gradle build no longer requires a developer's private release keystore to configure debug builds.

## Known runtime risks — NOT YET VERIFIED
1. The Marmalade game runtime is 32-bit. Existing arm64-v8a JNI library files are incomplete, so ABI filtering is required.
2. The source currently gates startup on `MANAGE_EXTERNAL_STORAGE` for Android 11+, even though this permission does not generally grant writes into most of `/sdcard/Android/`; the app's own `getObbDir()` should be used.
3. `IsDevice.GetExpansionPath()` constructs a raw `/sdcard/Android/obb/<package>/` path; verify the native runtime accepts `getObbDir()` before changing behavior.
4. The original large `blackops_*.dz` payloads are not in the repository. The first-launch download path may no longer work; test with legitimately obtained game assets and do not publish proprietary assets.
5. JNI method/field descriptors used by Marmalade must remain stable.
6. Debug APK signing differs from existing installed copies; back up app data before replacement if signatures differ.

## Acceptance tests
- CI produces a debug APK and retains build logs.
- Inspect APK library entries; only `lib/armeabi-v7a/*` should be present.
- Install on an Android 15 ARMv7-capable device without ABI errors.
- Start application, confirm native game code loads, check EGL surface and touch input.
- Confirm game-data downloads/import, saves, level load, audio, lifecycle and screen-off/on.
- Record `logcat` for first crash or data path error.
- Validate on Android 16 and document any architecture/page-size limitations.

## Build locally or in CI
```sh
./gradlew :app:assembleDebug
```
APK: `app/build/outputs/apk/debug/app-debug.apk`.

## Current status
Compatibility fork and CI initiated. Build and gameplay verification are separate gates; a successful APK compilation alone is not proof that zombies gameplay functions.
