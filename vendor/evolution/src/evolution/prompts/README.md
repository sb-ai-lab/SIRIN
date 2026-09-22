# Unified Prompt Corpus

Evolution prompt assets are authored here as Markdown. Core rewrite modes use reflection and structured-edit assets. Agentic editors use their wrapper assets. Compatibility rewrite modes use active legacy assets.

## Layout

- `_blocks/` holds reusable fragments. Structural blocks use include syntax. The caller passes value blocks as placeholder values. `blind_evidence` and the legacy-named `oracle_evidence` file fill the active train-evidence policy; the latter filename remains for prompt-template compatibility. The runtime-contract blocks fill `runtime_contract`.
- Top-level `*.md` files are active prompts. They include `system_*`, `reflect_*`, `propose_edits`, `merge_edits`, and `agentic_wrapper_*`. Active compatibility prompts and frozen compact prompts are under `legacy/`.

## Authoring rules

- Use `snake_case` placeholders in braces from the fixed vocabulary. Pass every placeholder for a file. Use an empty string for an absent optional section. Optional values contain their own `##` heading.
- Include one level only with `{{include:_blocks/<name>}}`. Blocks must not include other blocks. Put each integrity rule in one block.
- Use `##` section headers and one logical line per paragraph or bullet. Do not hard-wrap a sentence. New response-producing templates end with a `## Output` contract. Blocks and compatibility templates retain their established contracts.
- Every JSON example quotes its keys (for example `"op":`), so no braced token is ever mistaken for a placeholder.
- Use one EditOp JSON shape for structured edits. Each edit has `op`, `target`, `content`, `rationale`, and `evidence_refs`. `target` must be an exact substring of the shown skill body.
