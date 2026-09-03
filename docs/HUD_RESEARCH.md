# HUD Research

Last updated: 2026-09-03

## Goal

Find the highest practical level where Tekken 6 converts logical HUD, UI, or screen-space coordinates into output coordinates, so HUD/UI proportions can be preserved independently from 20:9 3D rendering.

## Current Findings

No HUD or 2D transform function has been identified yet.

## Important Prior Negative Result

User-provided historical result:

- Previous sprite-level or individual 2D element experiments caused regressions including dark pause overlay issues, incorrect or empty health-bar fills, blocky graphical corruption, and inconsistent UI behavior.

Status: STRONG EVIDENCE that broad per-sprite manipulation is the wrong first strategy.

## Candidate Categories To Separate

- Gameplay HUD: health bars, names, timer, round indicators, rage indicators.
- Menus: title, character select, stage select, options, pause menu, results.
- Full-screen overlays: pause darkening, fades, screen effects.
- Pre-rendered/video elements.

## Research Rules

- Do not globally shrink all 2D rendering.
- Do not patch every occurrence of a coordinate or aspect constant.
- Trace usage before patching.
- Keep full-screen overlays distinct from ordinary HUD where evidence supports separate paths.
