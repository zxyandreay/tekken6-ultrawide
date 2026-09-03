# Runtime Test Results

Last updated: 2026-09-03

## Target

- Game: Tekken 6 USA (`ULUS10466`)
- Emulator: PPSSPP Android
- Device: POCO F5, 2400x1080 / 20:9
- Display Layout: Stretch

## Known-good control

The existing CWCheat 20:9 patch remains the known-good control for 3D aspect correction.

## Plugin v0.1

User result:

- `HUDMode = 0`: 3D remained visibly stretched.
- HUD experimental modes: no correct 3D/HUD result.

Conclusion:

- v0.1 did not reproduce the known-good CWCheat behavior and cannot be treated as a reliable baseline.

## Plugin v0.2

v0.2 removed HUD experiments and added module/signature discovery, readback logging and early-boot monitoring.

User result:

- 3D still looks stretched.

Current interpretation:

This visual result alone cannot distinguish between:

1. PPSSPP not loading the plugin for Tekken 6,
2. `module_start` running but failing to find/patch the target sites,
3. the writes succeeding in guest RAM but not taking effect in translated/JIT code,
4. the target instructions being restored later,
5. an installation/per-game `Enable plugins` issue.

The v0.2 log is therefore the required next diagnostic artifact before another runtime patch is attempted.

Expected log path:

`PSP/PLUGINS/Tekken6.PPSSPP.UltrawideFix/Tekken6.PPSSPP.UltrawideFix.log`

## Important implementation note discovered after v0.2

PPSSPP's CWCheat engine invalidates JIT/instruction cache for a target range **before** performing a code write. PPSSPP source comments explain that JIT may temporarily overwrite guest instruction words and cache invalidation restores the original instruction representation before the cheat write.

Our PRX implementation has not yet matched that host-side CWCheat ordering exactly. This is a concrete area to investigate after obtaining the v0.2 log. The Warriors Fusion Fix is not directly equivalent here because it patches before normal game execution and performs a final global D-cache writeback/I-cache clear.

Do not label this as the confirmed cause until the v0.2 runtime log is reviewed.
