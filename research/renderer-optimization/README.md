# Renderer Optimization Research

This branch is for finding a smaller Tekken 6 AutoHUD/ultrawide architecture by comparing a completely stock runtime against the v1.2.0 implementation.

The first tools are:

- `research/tools/ppsspp_debugger_smoke_test.mjs` — verifies TCP, WebSocket upgrade, required subprotocol, PPSSPP version, game identity, and CPU status without touching PSP memory.
- `research/tools/ppsspp_stock_renderer_census.mjs` — captures read-only CPU/register/memory context at renderer paths already identified during v1.2.0 research.

The first completed stock run and preliminary architectural interpretation are recorded in [`stock-census-2026-09-20.md`](stock-census-2026-09-20.md).

## Clean-control requirements

- Tekken 6 USA: `ULUS10466`.
- Fully disable `Tekken6Ultrawide.prx` before launching the game.
- Disable aspect/HUD/camera CWCheats for this stock census.
- Restart Tekken 6 after disabling the plugin/cheats. Do not rely on disabling them mid-session.
- Keep the same PPSSPP graphics/display/texture settings for the entire run.
- Enable PPSSPP remote debugging and note the phone IP and debugger port.
- PC and phone must be reachable on the same network.
- Node.js 20+ is recommended.

The probe verifies the game ID, checks for the Tekken6Ultrawide module, and validates known stock instructions before capture. If any of those checks fail, it stops rather than collecting a contaminated control.

The probe does not patch Tekken memory. It temporarily adds/removes debugger execution breakpoints, reads registers/memory/backtraces, then resumes the CPU.

## Run

From the repository root:

```powershell
node research/tools/ppsspp_debugger_smoke_test.mjs <PHONE_IP>:<PORT>
```

Only proceed to the census after the smoke test reports the expected game and a responsive CPU.

```powershell
node research/tools/ppsspp_stock_renderer_census.mjs <PHONE_IP>:<PORT>
```

Example:

```powershell
node research/tools/ppsspp_stock_renderer_census.mjs 192.168.0.101:43091
```

The script guides you through seven phases. Press Enter only when the requested state is visible. Type `s` and press Enter to skip a phase you cannot reach.

1. **battle-baseline** — Arcade/Ghost/Story active fight, both HP bars full, timer visible.
2. **battle-partial-hp** — damage both fighters so both colored fills are visibly partial.
3. **round-win** — prepare the opponent at very low HP before Enter; after capture starts, immediately finish the round and remain through the winner orb/glow into the next-round HUD.
4. **practice** — Practice HUD/stat rows visible; after Enter perform a short combo so hit/combo/damage rows update.
5. **gold-rush** — Gold Rush with REWARD / ATTACK VARIATION visible during the capture.
6. **pause-menu** — start from an active fight; after Enter open pause, move selection, and optionally open one submenu.
7. **character-select** — character-select UI visible; after Enter move the cursor between characters at least once.

The game can briefly pause when a sampled renderer breakpoint is hit. The probe resumes it automatically and caps samples per renderer to keep capture traffic manageable.

## Output

Successful runs create:

```text
research/captures/stock-renderer-census-<timestamp>.json
```

Keep the JSON unchanged and send it back for comparison against the v1.2.0 hook/packet architecture. Captures are intentionally ignored by Git.

## PPSSPP v1.20.4 debugger notes

- `memory.read_u32` may return a live JIT/emuhack replacement word instead of the original guest instruction. Stock code verification uses `memory.read` with `replacements: false` and decodes the returned bytes as little-endian words.
- Execution-breakpoint stops are delivered as `cpu.stepping`. v1.20.4 may omit newer structured hit details, so the census matches the stopped PC/related address only against breakpoints owned by the active phase.
- Pausing PPSSPP from its UI can leave the TCP port open while HTTP/WebSocket requests stop being serviced. Keep PPSSPP running when connecting; let debugger breakpoints perform the temporary capture pauses.
- The debugger emits unsolicited events such as analog-input state. Ticketed responses must be separated from those broadcasts.
