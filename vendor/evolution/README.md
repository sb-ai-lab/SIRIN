# Evolution

Evolution applies a shared edit brake after finalization and integrity checks. The brake runs before optimizer evaluation and promotion. The default base budget is `0.40`. Retained promotions reduce the effective budget unless users disable promotion-count decay.

[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)

Evolution 0.2 is a trace-driven lifecycle for Agent Skills. It runs tasks with immutable skill versions, records attempts, diagnoses failures, and proposes edits. Users can save changes manually or promote them through paired held-back validation.

## Install

Install the published package by its distribution name:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install "evo-skills[llm]"
evo --version
evo --help
```

The base `evo-skills` wheel contains the offline core. Add `[llm]`, `[gigachat]`, or `[gui]` only when needed. Provider credentials come from environment variables such as `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`, or `GIGACHAT_CREDENTIALS`; the CLI has no credential flag.

The wheel deliberately contains no tasks, skills, benchmark corpus, or `experiments/` tree. Those are not needed by the core package. A source checkout contains optional research runners under `experiments/`; their dependencies are the repository's `research` dependency group, not a package extra.

## Start From An Empty Project

A new project has no tasks or skills. Run:

```bash
evo quickstart -m mock
```

This creates a small task under `tasks/`, a skill under `.agents/skills/`, and runs an offline attempt. For a real task:

```bash
evo task new my-task --skill my-skill
evo skill create my-skill -d "Reusable instructions for my task family"
# Edit tasks/my-task/instruction.md and tasks/my-task/tests/test_outputs.py.
export OPENROUTER_API_KEY=...
evo doctor -m openrouter/anthropic/claude-sonnet-4 \
  --task my-task --skill my-skill
```

Task roots always resolve in this order:

1. an explicit `--dir`/`tasks_dir` value;
2. `EVO_TASKS_ROOT`;
3. `tasks/` under the current working directory.

## Manual Lifecycle

The public CLI is grouped; there are no flat command aliases.

```bash
evo run solve my-task -m openrouter/anthropic/claude-sonnet-4 \
  --skill my-skill
evo trace list my-skill --task my-task
evo trace show my-skill --last --section result
evo evolve reflect my-skill -m openrouter/anthropic/claude-sonnet-4 \
  --task my-task
evo evolve rewrite my-skill -m openrouter/anthropic/claude-sonnet-4 \
  --task my-task
evo skill diff my-skill
evo skill commit my-skill -m "Improve the general procedure"
evo skill history my-skill
```

Solves inject the active version, never an uncommitted working copy. A version snapshots `SKILL.md` plus `scripts/`, `references/`, and `assets/`; its full managed tree is hashed and recorded in trace provenance. If a task requires multiple skills, `--skill` replaces only its primary requirement and all supporting requirements remain pinned and injected.

`--permission safe` is the default for agent CLI backends. Unsafe execution requires the explicit `--permission unsafe`. Hermes cannot provide safe mode, so it fails closed unless unsafe mode is requested explicitly.

Child solution and evaluator processes receive a restricted environment. Pass an additional variable by name with repeatable `--pass-env`, for example:

```bash
evo run solve my-task -m openai/local-model \
  --api-base http://127.0.0.1:8000/v1 \
  --pass-env HTTPS_PROXY --pass-env SSL_CERT_FILE
```

The output-token budget resolves as explicit `--max-tokens`, then `EVO_LLM_MAX_TOKENS`, then `16384`. Use `--seed N` only with a solver backend that supports seed forwarding. Accepted seeds appear in trace provenance. Agent-CLI and GigaChat solver calls reject the option.

## Next Steps

Use [Quickstart](QUICKSTART.md) for the first successful workflow. Use [the CLI reference](docs/cli.md) for command syntax. Use [Python API usage](docs/api-usage.md) for supported calls. Use [configuration](docs/configuration.md) for settings. Use [architecture](docs/architecture.md) for the optimizer and edit-brake design.

## Repository Layout

```text
src/evolution/          installed Python package
  core/                 skill parsing, validation, stores, exact bindings
  eval/                 task discovery, isolated workspaces, solver, evaluator
  evolve/               reflection, rewrite, and production optimizer
  lineage/              immutable versions, active selection, traces
  llm/                  LiteLLM, GigaChat, mock, and agent CLI backends
  cli/                  grouped `evo` command tree
.agents/skills/         project skill working area (created by the user)
tasks/                  project task root (created by the user)
experiments/            optional source-checkout research code; not installed
docs/                   framework documentation
```

The external AFTER benchmark corpus is available from [Hugging Face](https://huggingface.co/datasets/DavydenkoGr/AFTER); it is not a runtime dependency of Evolution.

## Documentation

- [Quickstart](QUICKSTART.md)
- [CLI reference](docs/cli.md)
- [Python API](docs/api-usage.md)
- [Architecture](docs/architecture.md)
- [Configuration](docs/configuration.md)
- [Custom tasks](docs/custom-tasks.md)

## License

Apache License 2.0. See [LICENSE](LICENSE).
