# Practice and Gold Rush HUD

## Status

Open mode-specific HUD research target after the persistent normal battle HUD, center timer, and character-name anchoring were validated.

The normal Arcade/Story/Ghost battle-HUD fixes should remain frozen unless a regression is demonstrated. Practice and Gold Rush introduce additional HUD families that require separate ownership/geometry work.

## Practice observations

Device screenshots with the current integrated HUD build show two distinct issues.

### Infinite-time indicator

The Practice infinite-time (`∞`) indicator is no longer centered after the normal round-timer correction. It is displaced left into/behind the P1 health-bar region.

The normal round countdown is rendered through two dedicated calls at:

```text
0x08929AF8
0x08929B44
```

The plugin currently wraps both calls unconditionally and temporarily enables the centered rectangle scope. Normal two-digit timers are device-validated with that rule, but Practice demonstrates that an alternate timer/status presentation shares part of this path and cannot be assumed to have identical geometry semantics.

Do not remove or weaken the validated normal timer correction globally. Identify the Practice-specific draw/geometry and gate the alternate behavior narrowly.

### Practice statistics panel

The left-side Practice HITS / DAMAGE / combo/readout family appears to have correct LEFT ownership/placement but remains horizontally stretched.

Desired behavior:

```text
anchor: LEFT
horizontal scale: 0.8 at fixed 20:9
vertical placement/scale: preserve
```

This should be treated separately from the normal P1 name/rank/HP families.

Static string resources in ULUS10466 include Practice formatting/text near the 0x08B9B2xx/0x08B9B3xx range, including `DAMAGE` and `HIT COMBO` format strings. String identity alone is not sufficient to patch the renderer; stable draw ownership must be established first.

## Gold Rush observations

The Gold Rush right-side score/gold HUD appears correctly RIGHT-owned but horizontally stretched.

Desired behavior:

```text
anchor: RIGHT
horizontal scale: 0.8 at fixed 20:9
vertical placement/scale: preserve
```

Do not apply a global right-side text transform because ordinary battle labels and menu/result screens have separate composition rules.

## Capture plan

Use:

```text
node research/tools/ppsspp_mode_hud_capture.mjs <host:port>
```

The tool records two stable frames for each phase:

```text
practice-idle
practice-hit
goldrush
```

and runs `ppdmp_mode_hud_analysis.py` to inventory stable THROUGH draws over the full HUD area.

The Practice idle/hit split is intended to separate the infinite-time indicator from the dynamic hit/damage/combo family. Gold Rush is captured independently to isolate its right-side HUD.

## Safety rules

- Do not reopen the validated normal countdown geometry to solve Practice.
- Do not globally transform font/sprite renderers.
- Prefer a mode/owner/shape predicate that affects only the target family.
- Preserve PPSSPP texture replacement behavior and emulator controls; test PRXs must retain the clean validated module layout.
