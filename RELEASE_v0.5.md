# Tekken 6 PPSSPP Ultrawide Fix v0.5 beta

v0.5 keeps the visually validated v0.3/v0.4 3D ultrawide foundation and the v0.4 camera integration, while adding two focused changes: lower-churn PPSSPP JIT maintenance and a deliberately experimental HUD/UI logical-canvas hook.

## What changed

- Preserves the existing four 3D aspect sites and camera address/value behavior.
- Stops invalidating and rewriting healthy JIT blocks on every 77 ms maintenance poll.
- Still uses invalidate-before-write when the patch is first installed or when original guest code actually returns.
- Treats the expected PPSSPP `0x68xxxxxx` emuhack state as a healthy compiled block after installation.
- Adds `EnableHUDExperimental`.
- Hooks only three statically traced external calls to the 2D initializer at `0x08A392F0`:
  - `0x089A92D8`
  - `0x089AB3A4`
  - `0x089AD87C`
- The hook calls the original initializer first, preserves its return value, then changes only descriptor field `+0x28` from the original logical width of 480 to an aspect-derived width.
- For the supplied 20:9 configuration, that width is `600.0`, while logical height remains `272.0`.

## Why this approach

Earlier experiments that changed generic 480x272 projection paths were too broad and affected unrelated 2D rendering. Static analysis also showed that descriptor field `+0x4C` is broadly used and is more consistent with color/alpha state than a safe HUD-scale control, so v0.5 does not touch it.

The new HUD experiment is therefore caller-specific and reversible instead of a global 2D patch.

## Experimental warning

HUD/UI correction is **not considered finished** in v0.5. The three callsites are strongly associated with the traced UI descriptor family, but only device testing can confirm which Tekken 6 screens they affect.

If a menu, overlay, health bar, or other 2D element looks worse, edit:

```ini
EnableHUDExperimental = 0
```

Then fully restart PPSSPP. The validated 3D and camera fixes remain active.

## Supplied configuration

```ini
[MAIN]
ForceAspectRatio = 20:9
Enable3D = 1

EnableCamera = 1
CameraPreset = 2

EnableHUDExperimental = 1

PatchIntervalMs = 77
DebugLogging = 0
```

## Texture-replacement compatibility

v0.5 does not modify texture data or texture replacement keys. The runtime change is instead about reducing unnecessary code/JIT cache invalidation after a patch is already healthy. This removes avoidable repeated code-cache churn while retaining the known-good PPSSPP JIT-safe installation path.

When testing a replacement texture pack, compare the same screen with `EnableHUDExperimental = 1` and `0`. If a replacement disappears only with the HUD experiment enabled, report that specific screen and texture so the remaining renderer path can be isolated.

## Compatibility

- Game: Tekken 6 USA `ULUS10466`
- Primary development target: PPSSPP on 20:9 Android devices
- Other regions remain unsupported.
- Disable older CWCheats that write the same aspect or camera addresses.
- Cold-boot testing is preferred while this beta HUD path is being validated.
