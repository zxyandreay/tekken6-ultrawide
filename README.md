# Tekken 6 PPSSPP Aspect Ratio + Camera CWCheat

A lightweight CWCheat configuration for **Tekken 6 USA (`ULUS10466`)** on PPSSPP. It provides selectable aspect-ratio patches for common phone and tablet displays, adjustable gameplay camera widths, and a native 60 FPS state entry without requiring a PPSSPP plugin.

> **Format:** CWCheat (`ULUS10466.ini`)  
> **Game:** Tekken 6 USA (`ULUS10466`)  
> **Emulator:** PPSSPP with cheats enabled

The cheat is device-agnostic: it patches the emulated game rather than targeting a specific phone, tablet, handheld, or computer.

The project is not affiliated with Bandai Namco Entertainment, Sony, or PPSSPP. Use your own legally obtained copy of Tekken 6.

## Features

- Eight selectable screen aspect ratios covering common phone and tablet formats.
- Four camera choices: Original, Slightly Wider, Wider, and Widest.
- Native 60 FPS state entry.
- Clean PPSSPP cheat-menu sections for Aspect Ratio, Camera, Framerate, and Restore.
- Independent screen and camera entries, so you can combine any supported ratio with your preferred camera.
- Restore entry for returning aspect ratio, camera, and framerate state to their defaults.
- Plain CWCheat configuration: no PRX/plugin installation or device-specific package.

## Cheat menu

Recent PPSSPP versions recognize the section-title convention used by this file, so the cheat list is organized like this:

```text
ASPECT RATIO
  20:9
  19.5:9
  19:9
  18.5:9
  18:9 (2:1)
  16:9
  16:10
  4:3

CAMERA
  Original
  Slightly Wider
  Wider
  Widest

FRAMERATE
  60 FPS (Native)

RESTORE
  Restore All Defaults
```

Use only **one aspect-ratio entry** and **one camera entry** at a time.

## Installation

1. In PPSSPP, enable **Cheats**.
2. Copy [`ULUS10466.ini`](ULUS10466.ini) into your active PPSSPP cheat folder:

   ```text
   PSP/Cheats/ULUS10466.ini
   ```

3. Start Tekken 6 USA (`ULUS10466`).
4. Set PPSSPP's display layout/scaling so the game fills the target display.
5. Open PPSSPP's **Cheats** menu.
6. Under **ASPECT RATIO**, enable the single entry that matches your display or PPSSPP output area.
7. Under **CAMERA**, optionally enable one camera preset.
8. **60 FPS (Native)** normally does not need to be enabled because Tekken 6 already targets 60 FPS. It is provided as an explicit native-state/restore option if another cheat has changed the framerate state.

If another Tekken 6 cheat modifies the same aspect, camera, or framerate addresses, disable it to avoid conflicts.

## Supported aspect ratios

| Cheat entry | Typical use |
| --- | --- |
| `20:9` | Common modern phones |
| `19.5:9` | Common modern phones |
| `19:9` | Phones |
| `18.5:9` | Phones |
| `18:9 (2:1)` | Phones |
| `16:9` | Original game aspect / older widescreen devices |
| `16:10` | Common Android tablets |
| `4:3` | Common tablet format |

The ratio patches all use the same four proven game-code sites as the original 20:9 patch. Each entry only changes the embedded aspect-ratio float, so the patching method remains identical across the supported ratios.

## Camera options

| Cheat entry | Effect |
| --- | --- |
| `Original` | Stock gameplay camera |
| `Slightly Wider` | Small increase in visible play area |
| `Wider` | Wider gameplay framing |
| `Widest` | Maximum included camera preset |

The camera presets use a separate gameplay-camera address, so changing the aspect ratio does not force a particular camera width.

## 60 FPS clarification

**Tekken 6 already runs with a native 60 FPS target.** This file therefore does not include a fake or unnecessary "60 FPS unlock."

The included `60 FPS (Native)` entry writes the native framerate state:

```text
0x20452890 = 0x00000001
```

This is useful for restoring the game's normal 60 FPS state if another cheat has modified that value. A commonly reposted code using the same address with value `0x00000002` is a **30 FPS modification**, not a 60 FPS unlock.

PPSSPP also carries game-specific compatibility handling for Tekken 6 under its `ForceMax60FPS` compatibility setting. If the emulator reports fewer than 60 rendered frames during gameplay, that can be a performance/full-speed issue rather than a missing 60 FPS patch.

## How the screen patch works

Tekken 6's original aspect constant is **16:9**. Each screen entry writes a different IEEE-754 aspect-ratio value into the same four runtime sites used by the established 20:9 patch.

| Ratio | Float value |
| --- | ---: |
| 20:9 | 2.2222222 |
| 19.5:9 | 2.1666667 |
| 19:9 | 2.1111112 |
| 18.5:9 | 2.0555556 |
| 18:9 | 2.0000000 |
| 16:9 | 1.7777778 |
| 16:10 | 1.6000000 |
| 4:3 | 1.3333334 |

## Compatibility

This repository targets the **USA release of Tekken 6 (`ULUS10466`)**. The addresses are specific to that game build and should not be assumed to work with other regional releases.

Because this is a CWCheat patch, it is not tied to a particular physical device. It can be used anywhere PPSSPP supports the same game build and CWCheat functionality.

For best geometry, choose the aspect-ratio entry matching the physical display or PPSSPP output area. A mismatched ratio will intentionally produce the wrong horizontal geometry.

## Limitations

- The aspect patch corrects the game's 3D projection for the selected output ratio.
- Tekken's original 2D HUD/menu layout is not independently repositioned or corrected.
- The `60 FPS (Native)` entry does not make hardware run the emulator faster; PPSSPP still needs to sustain full emulation speed.
- PPSSPP display scaling, texture packs, emulator settings, and other cheats can affect the final presentation.
- For a clean test after changing conflicting cheats, fully restart the game.

## Repository contents

```text
ULUS10466.ini
```

The repository intentionally remains focused on the CWCheat configuration and its usage documentation.
