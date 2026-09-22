# Release-readiness assessment after OPT-EXP4A — 2026-09-22

## Recommendation

Proceed to the next official release from OPT-EXP4A rather than starting another optimization experiment first.

Recommended version:

```text
v1.2.1
```

## Why v1.2.1

The published v1.2.0 already introduced AutoHUD as the feature release.

The accepted EXP4A line is primarily maintenance:

- fixes the compact winner-glow UV identity;
- fixes first-slot-only winner-glow ownership so later wins follow the correct orb;
- preserves the full dynamic AutoHUD model;
- consolidates HP ownership;
- compacts the slot installer/table;
- reduces Practice/Gold hook topology;
- compacts the slot-scope wrapper;
- retains the fixed one-LOAD 0x0EB0 resident layout.

There is no new user-facing feature category that requires a minor-version bump.

## Release-quality device evidence

The accepted EXP4A build passed:

- startup/loading;
- Arcade;
- Story;
- Ghost Battle;
- Practice;
- Gold Rush;
- HP shell/fill including normal states tested;
- ranks and side strips;
- character names;
- timer;
- persistent round markers;
- P1 first and later winner-glow slots;
- P2 first and later winner-glow slots;
- visible spinner animation;
- custom replacement textures/fonts;
- fast-forward.

This specifically closes the historical first-win-only winner-glow validation gap.

## Why not continue optimizing first

The optimization line has reached diminishing returns.

Current accepted hard-free capacity:

```text
136 bytes general-purpose detached capacity
```

The known high-risk renderer paths have already produced several rejected experiments.

Another optimization round would:

- add regression surface;
- require another full device-validation cycle;
- delay shipping a confirmed winner-glow bug fix;
- provide no current user-visible benefit.

The fixed PT_LOAD remains 0x0EB0, so shrinking the internal live-code footprint further would not reduce resident allocation unless a separate memory-layout project safely shrinks the load segment. That is a different, higher-risk objective and should not block v1.2.1.

## Proposed v1.2.1 release focus

User-facing release notes should emphasize:

- corrected animated winner/earned-round glow;
- correct first and later win-slot tracking for both players;
- preserved automatic HUD aspect correction;
- stability/maintenance improvements;
- preserved replacement textures/fonts and fast-forward.

Internal free-byte counts and failed experimental history belong in research documentation, not the public release highlights.

## Main-branch promotion policy

Promote the exact validated EXP4A PRX.

Do not rebuild the runtime code from readable research source unless byte/behavior equivalence has been independently proven.

For the release commit:

- update README from v1.2.0 to v1.2.1;
- add a `release/v1.2.1/` package payload/checksum;
- update release-facing documentation;
- preserve research history separately;
- create/tag v1.2.1 only after the exact package checksum is recorded.

## Release automation policy

Do not use GitHub Actions for this release.

Create the package deterministically from the accepted binary and publish/tag it through direct repository/release operations.

## Deferred future optimization

After v1.2.1 is published, further optimization may continue on a new research branch from the exact EXP4A baseline.

Potential future work should have a concrete target such as:

- supporting another HUD family;
- freeing space needed by a new correction;
- safely shrinking the resident PT_LOAD through a dedicated memory-layout experiment.

Pure byte-count optimization should not block this release.

No GitHub Actions are used.
