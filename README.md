# Tekken 6 PPSSPP Ultrawide CWCheat

A lightweight CWCheat configuration for **Tekken 6 USA (`ULUS10466`)** on PPSSPP. It provides a 20:9 ultrawide screen patch plus selectable gameplay camera widths, without requiring a PPSSPP plugin.

> **Format:** CWCheat (`ULUS10466.ini`)  
> **Game:** Tekken 6 USA (`ULUS10466`)  
> **Emulator:** PPSSPP with cheats enabled

The cheat is device-agnostic: it patches the emulated game, not a specific phone, tablet, handheld, or computer. Actual presentation still depends on your display aspect ratio and PPSSPP display settings.

The project is not affiliated with Bandai Namco Entertainment, Sony, or PPSSPP. Use your own legally obtained copy of Tekken 6.

## Features

- 20:9 ultrawide screen patch.
- Four camera choices: Original, Slightly Wider, Wider, and Widest.
- Independent screen and camera entries, so you can choose the camera setting you prefer.
- Restore entry for returning the patched screen and camera values to their originals.
- Plain CWCheat configuration: no PRX/plugin installation, build toolchain, or device-specific package.

## Installation

1. In PPSSPP, enable **Cheats**.
2. Copy [`ULUS10466.ini`](ULUS10466.ini) into your active PPSSPP cheat folder:

   ```text
   PSP/Cheats/ULUS10466.ini
   ```

3. Start Tekken 6 USA (`ULUS10466`).
4. Open PPSSPP's **Cheats** menu.
5. Enable **Screen - 20:9 Ultrawide**.
6. Enable one camera option if you want a wider gameplay view.

If another Tekken 6 cheat modifies the same screen/aspect or camera addresses, disable it to avoid conflicts.

## Camera options

| Cheat entry | Effect |
| --- | --- |
| `Camera - Original` | Stock gameplay camera |
| `Camera - Slightly Wider` | Small increase in visible play area |
| `Camera - Wider` | Wider gameplay framing |
| `Camera - Widest` | Maximum included camera preset |

Use only one camera entry at a time.

## Compatibility

This repository targets the **USA release of Tekken 6 (`ULUS10466`)**. The addresses are specific to that game build and should not be assumed to work with other regional releases.

Because this is a CWCheat patch, it is not tied to a particular physical device. It can be used anywhere PPSSPP supports the same game build and CWCheat functionality. The included screen patch is specifically tuned for **20:9** output; displays with other aspect ratios may require different aspect values for geometrically correct results.

## Cheat contents

The repository intentionally keeps the usable patch in one file:

```text
ULUS10466.ini
```

The screen patch modifies four runtime sites, while the camera presets modify the gameplay camera value. The restore entry writes the original screen and camera values back.

## Notes

- CWCheat changes are applied to the emulated game and do not modify your game image on disk.
- PPSSPP settings, display scaling, texture packs, and other cheats can affect the final result.
- If the image looks incorrectly stretched, verify your PPSSPP display/layout configuration and remember that the included aspect patch is tuned for 20:9.
- For a clean test, fully restart the game after changing conflicting cheats.
