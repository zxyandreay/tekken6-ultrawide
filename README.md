# Tekken 6 PPSSPP Aspect Ratio + Camera CWCheat

A lightweight CWCheat configuration for **Tekken 6 USA (`ULUS10466`)** on PPSSPP. It provides selectable aspect-ratio patches for common phone and tablet displays plus adjustable gameplay camera widths, without requiring a PPSSPP plugin.

> **Format:** CWCheat (`ULUS10466.ini`)  
> **Game:** Tekken 6 USA (`ULUS10466`)  
> **Emulator:** PPSSPP with cheats enabled

The cheat is device-agnostic: it patches the emulated game rather than targeting a specific phone, tablet, handheld, or computer.

The project is not affiliated with Bandai Namco Entertainment, Sony, or PPSSPP. Use your own legally obtained copy of Tekken 6.

## Features

- Eight selectable screen aspect ratios covering the most common phone and tablet formats.
- Four camera choices: Original, Slightly Wider, Wider, and Widest.
- Independent screen and camera entries, so you can combine any supported ratio with your preferred camera.
- Restore entry for returning the screen and camera values to their originals.
- Plain CWCheat configuration: no PRX/plugin installation or device-specific package.

## Supported aspect ratios

| Cheat entry | Typical use |
| --- | --- |
| `Screen - 20:9` | Common modern phones |
| `Screen - 19.5:9` | Common modern phones |
| `Screen - 19:9` | Phones |
| `Screen - 18.5:9` | Phones |
| `Screen - 18:9 (2:1)` | Phones |
| `Screen - 16:9` | Original game aspect / older widescreen devices |
| `Screen - 16:10` | Common Android tablets |
| `Screen - 4:3` | Common tablet format |

Use only **one screen entry at a time**.

The ratio patches all use the same four proven game-code sites as the original 20:9 patch. Each entry only changes the embedded aspect-ratio float, so the patching method remains identical across the supported ratios.

## Installation

1. In PPSSPP, enable **Cheats**.
2. Copy [`ULUS10466.ini`](ULUS10466.ini) into your active PPSSPP cheat folder:

   ```text
   PSP/Cheats/ULUS10466.ini
   ```

3. Start Tekken 6 USA (`ULUS10466`).
4. Set PPSSPP's display layout/scaling so the game fills the target display.
5. Open PPSSPP's **Cheats** menu.
6. Enable the **single Screen entry that matches your display aspect ratio**.
7. Optionally enable one camera entry.

If another Tekken 6 cheat modifies the same screen/aspect or camera addresses, disable it to avoid conflicts.

## Camera options

| Cheat entry | Effect |
| --- | --- |
| `Camera - Original` | Stock gameplay camera |
| `Camera - Slightly Wider` | Small increase in visible play area |
| `Camera - Wider` | Wider gameplay framing |
| `Camera - Widest` | Maximum included camera preset |

Use only **one camera entry at a time**.

## Compatibility

This repository targets the **USA release of Tekken 6 (`ULUS10466`)**. The addresses are specific to that game build and should not be assumed to work with other regional releases.

Because this is a CWCheat patch, it is not tied to a particular physical device. It can be used anywhere PPSSPP supports the same game build and CWCheat functionality.

For best geometry, choose the screen entry matching the physical display or PPSSPP output area. A mismatched ratio will intentionally produce the wrong horizontal geometry.

## How the screen patch works

Tekken 6's original aspect constant is **16:9**. Each screen entry writes a different IEEE-754 aspect-ratio value into the same four runtime sites used by the established 20:9 patch.

The supported values are:

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

The camera presets use a separate gameplay-camera address, so changing the aspect ratio does not force a particular camera width.

## Limitations

- The aspect patch corrects the game's 3D projection for the selected output ratio.
- Tekken's original 2D HUD/menu layout is not independently repositioned or corrected.
- PPSSPP display scaling, texture packs, and other cheats can affect the final presentation.
- Runtime behavior can vary with emulator configuration; if a ratio looks wrong, confirm that the selected cheat matches the actual PPSSPP output area.
- For a clean test after changing conflicting cheats, fully restart the game.

## Repository contents

```text
ULUS10466.ini
```

The repository intentionally remains focused on the CWCheat configuration and its usage documentation.
