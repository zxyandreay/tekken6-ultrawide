# Research Tools

Executable utilities used to produce or verify the evidence under `research/`.

## Layout

```text
tools/research/
├── probes/      read-only/runtime PPSSPP probes
├── audits/      static/binary audits
└── builders/
    ├── build_opt_exp4a_slot_scope_compact.py
    └── archive/ historical deterministic experiment builders
```

## Policy

- Probes should answer one narrow ownership/ABI question.
- Builders should require exact parent hashes and expected patch-site words.
- Historical builders are preserved for reproducibility; they are not the current implementation source of truth.
- The official v1.2.1 PRX remains the authoritative runtime artifact.

See [`docs/development/`](../../docs/development/) for current methodology and patching rules.
