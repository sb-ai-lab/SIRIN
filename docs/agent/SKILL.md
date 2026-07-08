---
name: sirin-framework
description: Use when working in the SIRIN repository to implement, debug, review, or document hallucination and answerability detection code, including probing, judging, uncertainty estimation, feature processors, model adapters, Hydra configs, checkpoint compatibility, Streamlit UI presets, or SIRIN tests.
---

# SIRIN Framework

Use this as the entry point. Load only the reference file that matches the task.

## First Checks

- Work from the repo root and pin imports with `PYTHONPATH=$PWD`; the shared environment may otherwise import another checkout.
- Prefer existing detector, processor, adapter, logger, splitter, and config patterns before adding anything new.
- Treat vendored dependencies, config compatibility, and cache behavior as documented in [../reference/pitfalls.md](../reference/pitfalls.md).
- When changing configs or public imports, update the matching shared reference doc.
- Keep generated or captured artifacts out of commits unless they are intentional fixtures.

## Reference Router

- Need architecture, dataflow, or import paths: read [../reference/architecture.md](../reference/architecture.md).
- Need dataclass defaults, enum names, constants, or config field ownership: read [../reference/configs.md](../reference/configs.md).
- Need side selection, layer indexing, attention behavior, feature processor capability, or compression details: read [../reference/feature-processing.md](../reference/feature-processing.md).
- Need dataset shape, runnable examples, Hydra layout, save/load, context splitting, logging, or caching patterns: read [../reference/workflows.md](../reference/workflows.md).
- Need known failure modes, validation traps, batch-size meanings, vendored compatibility, or environment setup: read [../reference/pitfalls.md](../reference/pitfalls.md).
- Need Streamlit UI specifics: read [../ui.md](../ui.md).

## Common Workflows

### Change Detection Behavior

1. Identify the family: probing, judge, or uncertainty.
2. Read the relevant imports/configs in `../reference/architecture.md` and `../reference/configs.md`.
3. Trace the flow through adapter -> feature processor -> detector -> pipeline.
4. Add one focused check for the behavior you changed.
5. Run the narrowest relevant test command.

### Touch Feature Extraction

1. Read `../reference/feature-processing.md` before choosing `side`, `pooling_type`, `layers`, or `attn_implementation`.
2. Follow the cache and attention constraints documented there.

### Touch Generation or API Adapters

1. Keep standard sampling explicit: `max_length` maps to adapter `max_tokens`.
2. Put provider-specific request extensions where `../reference/configs.md` says they belong.
3. Use an integration test only when endpoint shape matters.

### Touch Checkpoint Loading

1. Follow the checkpoint compatibility notes in `../reference/pitfalls.md`.
2. Keep legacy loading behavior covered by a focused test.

## Minimum Verification

```bash
PYTHONPATH=$PWD python -c "import sirin; print(sirin.__file__)"
PYTHONPATH=$PWD python -m pytest -q tests/ -m 'not integration'
PYTHONPATH=$PWD python -m ruff check <changed-python-files>
```

Set `CUDA_VISIBLE_DEVICES` as needed, then run `PYTHONPATH=$PWD python -m pytest -q tests/ -m integration` only for tests explicitly marked integration.
