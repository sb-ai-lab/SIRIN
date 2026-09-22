"""Prompt optimization for API judges via Evolution (``evo-skills``).

API judges (:class:`~sirin.detection.judging.judges.base.OpenAIJudgeBase` and its
subclasses) have no gradient-based fine-tuning -- ``train()`` used to be a no-op stub.
Instead of doing nothing, ``train()`` can now *evolve* the judge prompt.

This integration is **bridge-free**: it does not start an HTTP server. Evolution is
called as a Python library (:func:`evolution.evolve.optimizer.optimize_skill`) and both
the solver and the editor run on the judge's own model adapter through
:class:`_AdapterBackend` -- so GigaChat (mTLS) is used exactly as on inference, with no
extra endpoint.

How a task is scored: Evolution's solver is a *code generator* -- it writes a small
Python script that the harness executes in a guarded child process and then runs a
pytest evaluator. Because that script runs in a separate process, it cannot receive the
in-memory adapter object; instead each task ships a tiny ``judge_client.py`` helper (and,
optionally, copies of the TLS cert/key) into the task workspace. The generated script
imports that helper, which builds the same ``GigaChatModelAdapter`` from environment
variables forwarded via ``pass_env``.

Requirements:
* ``evo-skills`` importable in the same interpreter as ``sirin`` (``pip install evo-skills``);
* for GigaChat, the adapter must expose ``cert_file``/``key_file``/``base_url`` on its
  config (``GigaChatConfig`` does) so the helper can rebuild it in the child process.
"""

from __future__ import annotations

import json
import os
import random
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
from loguru import logger as lg

from sirin.definitions import INPUT_COL, TARGET_COL
from sirin.models.detection import DetectionResult, PromptEvolutionConfig


_SYSTEM_MARK_OPEN = '<<<JUDGE_SYSTEM_PROMPT'
_SYSTEM_MARK_CLOSE = 'JUDGE_SYSTEM_PROMPT>>>'

# Env vars forwarded to task subprocesses so the helper can rebuild the adapter.
_JUDGE_ENV_VARS = (
    'SIRIN_JUDGE_KIND',
    'SIRIN_JUDGE_MODEL',
    'SIRIN_JUDGE_BASE_URL',
    'SIRIN_JUDGE_CERT_FILE',
    'SIRIN_JUDGE_KEY_FILE',
    'SIRIN_JUDGE_VERIFY_SSL',
)

# Written verbatim into every task workspace. Rebuilds the judge adapter from env and
# exposes a single ``judge(system_prompt, user_prompt)`` call.
_JUDGE_CLIENT_SRC = '''"""Rebuild the judge model in the task sandbox and call it (no HTTP bridge)."""
import os


def _make_adapter():
    kind = os.environ.get("SIRIN_JUDGE_KIND", "gigachat")
    if kind == "gigachat":
        from sirin.inference.adapters import GigaChatConfig, GigaChatModelAdapter
        cfg = GigaChatConfig(
            model_path=os.environ["SIRIN_JUDGE_MODEL"],
            base_url=os.environ["SIRIN_JUDGE_BASE_URL"],
            cert_file=os.environ["SIRIN_JUDGE_CERT_FILE"],
            key_file=os.environ["SIRIN_JUDGE_KEY_FILE"],
            verify_ssl_certs=os.environ.get("SIRIN_JUDGE_VERIFY_SSL", "false").lower() == "true",
        )
        adapter = GigaChatModelAdapter(config=cfg)
    elif kind == "openai":
        from sirin.inference.adapters import OpenAIModelAdapter
        from sirin.models.inference import OpenAIConfig
        adapter = OpenAIModelAdapter(config=OpenAIConfig(
            model_path=os.environ["SIRIN_JUDGE_MODEL"],
            base_url=os.environ.get("SIRIN_JUDGE_BASE_URL"),
            api_key=os.environ.get("SIRIN_JUDGE_API_KEY"),
        ))
    else:
        raise ValueError(f"unknown SIRIN_JUDGE_KIND: {kind!r}")
    adapter.load()
    return adapter


_ADAPTER = None


def judge(system_prompt, user_prompt, max_tokens=32, temperature=0.0):
    """Return the judge model's raw answer for one (system, user) pair."""
    global _ADAPTER
    if _ADAPTER is None:
        _ADAPTER = _make_adapter()
    out = _ADAPTER.sample(
        [[{"role": "system", "content": system_prompt},
          {"role": "user", "content": user_prompt}]],
        max_tokens=max_tokens, temperature=temperature,
    )
    return out[0] if isinstance(out, (list, tuple)) else str(out)
'''


# --------------------------------------------------------------------------- helpers
def _resolve_evo(explicit: Optional[str]) -> Optional[str]:
    """Locate the ``evo`` CLI (used only for ``evo skill commit``)."""
    if explicit and Path(explicit).exists():
        return explicit
    found = shutil.which('evo')
    if found:
        return found
    for cand in (
        Path(sys.executable).parent / 'evo',  # console script of the current venv
        Path.home() / 'sirin_dialogs_bench' / 'evo_env' / 'bin' / 'evo',
        Path.home() / 'evo_env' / 'bin' / 'evo',
        Path.home() / '.local' / 'bin' / 'evo',
    ):
        if Path(cand).exists():
            return str(cand)
    return None


def _extract_marked(text: str, open_mark: str, close_mark: str) -> Optional[str]:
    match = re.search(
        re.escape(open_mark) + r'\n(.*?)\n' + re.escape(close_mark), text, re.S
    )
    return match.group(1) if match else None


def _chunk(records: List[Dict[str, Any]], size: int, count: int, seed: int):
    records = list(records)
    random.Random(seed).shuffle(records)
    size = max(1, size)
    units = [records[i * size : (i + 1) * size] for i in range(max(1, count))]
    units = [u for u in units if len(u) >= max(2, size // 2)]
    return units or ([records] if records else [])


class _AdapterBackend:
    """Evolution ``LLMBackend`` backed by a SIRIN model adapter (no HTTP).

    Implements the async protocol expected by ``optimize_skill``; the sync
    ``adapter.sample`` call is pushed to a worker thread.
    """

    seed_mode = 'forwarded'  # adapter ignores the seed; we accept it so the gate is happy

    def __init__(self, adapter, max_tokens: int = 2048, temperature: float = 0.0):
        self.adapter = adapter
        self.max_tokens = max_tokens
        self.temperature = temperature

    def _sample(self, messages: List[Dict[str, str]], system: Optional[str], max_tokens: int):
        from evolution.llm.backend import LLMResponse

        full: List[Dict[str, str]] = []
        if system:
            full.append({'role': 'system', 'content': system})
        full.extend(messages)
        try:
            # use_async=False: force the plain synchronous HTTP path. The harness calls
            # this backend from inside its own event loop, and the adapter's async path
            # would nest asyncio.run()/share an AsyncClient across loops and break.
            out = self.adapter.sample(
                [full], max_tokens=max_tokens, temperature=self.temperature, use_async=False
            )
        except Exception:
            lg.exception('Evolution backend: adapter.sample failed (see traceback above)')
            raise
        content = out[0] if isinstance(out, (list, tuple)) else str(out)
        return LLMResponse(content=content)

    async def complete(self, messages, system=None, seed=None):
        import asyncio

        return await asyncio.to_thread(self._sample, messages, system, self.max_tokens)

    async def complete_with_skill(self, messages, skill, system=None, seed=None):
        return await self.complete_with_skills(messages, [skill], system=system, seed=seed)

    async def complete_with_skills(self, messages, skills, system=None, seed=None):
        blocks = '\n\n'.join(
            f'<skill_content name="{s.name}">\n{s.body}\n</skill_content>' for s in skills
        )
        combined = f'{system}\n\n{blocks}' if system else blocks
        return await self.complete(messages, system=combined, seed=seed)


class EvolutionPromptTrainer:
    """Evolve an API judge's prompt with Evolution, in-process (no bridge)."""

    def __init__(self, judge, config: PromptEvolutionConfig, training_args=None):
        self.judge = judge
        self.config = config
        self.training_args = training_args
        self._skill_name = config.skill_name
        self._result: Any = None

    # ------------------------------------------------------------------ public
    def run(self, train_data, val_data=None, metrics: Optional[List[Any]] = None) -> DetectionResult:
        cfg = self.config
        try:
            from evolution.evolve.optimizer import optimize_skill
        except ImportError as exc:
            raise RuntimeError(
                'Evolution must be importable in the same interpreter as sirin. '
                'Install it with `pip install evo-skills` (or `pip install -e <evolution>/src`).'
            ) from exc

        adapter_cfg = self._adapter_identity()

        work_dir = Path(
            cfg.work_dir
            or (self.training_args.output_dir if self.training_args else None)
            or './evolution_judge'
        )
        work_dir.mkdir(parents=True, exist_ok=True)
        project = work_dir / 'project'
        if project.exists():
            shutil.rmtree(project)
        tasks_root = project / 'tasks'
        tasks_root.mkdir(parents=True)

        train_records = self._to_records(train_data)
        val_records = self._to_records(val_data) if val_data is not None else train_records
        if not train_records:
            lg.warning('Evolution: no training records; skipping prompt optimization')
            return DetectionResult()
        train_units = _chunk(train_records, cfg.claims_per_task, cfg.n_train_tasks, cfg.seed)
        val_units = _chunk(val_records, cfg.claims_per_task, cfg.n_val_tasks, cfg.seed)

        seed_system, _ = self._seed_prompts()
        skill_dir = project / '.agents' / 'skills' / self._skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / 'SKILL.md').write_text(self._skill_md(seed_system), encoding='utf-8')

        evo = _resolve_evo(cfg.evo_bin)
        if evo is None:
            raise RuntimeError(
                'evo CLI not found (needed for `evo skill commit`). Set '
                'PromptEvolutionConfig.evo_bin or install evo-skills on PATH.'
            )
        commit = subprocess.run(
            [evo, 'skill', 'commit', self._skill_name, '-m', 'seed prompt'],
            cwd=str(project), capture_output=True, text=True,
        )
        if commit.returncode != 0:
            lg.warning('evo skill commit output: ' + ((commit.stdout or '') + (commit.stderr or ''))[-800:])

        self._write_tasks(tasks_root, 'train', train_units, adapter_cfg)
        self._write_tasks(tasks_root, 'val', val_units, adapter_cfg)
        train_names = [f'train-{i}' for i in range(len(train_units))]
        val_names = [f'val-{i}' for i in range(len(val_units))]
        # The paired gate needs >=4 validation pairs; bump trials if needed.
        trials = max(cfg.trials, (4 + max(1, len(val_names)) - 1) // max(1, len(val_names)))

        backend = _AdapterBackend(self.judge.model_adapter, max_tokens=cfg.max_tokens)
        self._prepare_env(adapter_cfg)

        lg.info('Evolution (in-process): optimize_skill solver/editor via model_adapter')
        try:
            self._result = optimize_skill(
                self._skill_name,
                train_tasks=train_names,
                validate_tasks=val_names,
                solver_model='openai/sirin-adapter',  # nominal id; real calls go via backend
                editor_model='openai/sirin-adapter',
                project_dir=project,
                tasks_dir=tasks_root,
                rounds=cfg.rounds,
                trials=trials,
                seed=cfg.seed,
                rewrite_mode='edit-ops',
                max_tokens=cfg.max_tokens,
                timeout=cfg.timeout,
                solver_backend=backend,
                editor_backend=backend,
                pass_env=list(cfg.pass_env or _JUDGE_ENV_VARS),
            )
        except Exception as exc:  # noqa: BLE001 - surface a readable train() failure
            lg.error(f'Evolution optimization failed: {type(exc).__name__}: {exc}')
            raise

        active_md = (skill_dir / 'SKILL.md').read_text(encoding='utf-8')
        self._apply_evolved_prompt(active_md, seed_system)

        result = DetectionResult(metrics=self._evaluate(val_data), threshold=self.judge.threshold)
        self._save_artifacts(work_dir)
        return result

    # ------------------------------------------------------------------ adapter
    def _adapter_identity(self) -> Dict[str, Any]:
        adapter = self.judge.model_adapter
        cfg = getattr(adapter, 'config', None)
        name = type(adapter).__name__
        cert = getattr(cfg, 'cert_file', None)
        key = getattr(cfg, 'key_file', None)
        base_url = getattr(cfg, 'base_url', None)
        model = getattr(cfg, 'model_path', None)
        if cert and key:
            return {
                'kind': 'gigachat', 'model': model, 'base_url': base_url,
                'cert_file': cert, 'key_file': key,
                'verify_ssl': bool(getattr(cfg, 'verify_ssl_certs', False)),
                'copy_files': True,
            }
        # Non-cert adapters (e.g. OpenAI-compatible): helper rebuilds without certs.
        return {
            'kind': 'openai', 'model': model, 'base_url': base_url,
            'api_key': getattr(cfg, 'api_key', None), 'copy_files': False,
        }

    @property
    def _model_adapter(self):
        return self.judge.model_adapter

    def _prepare_env(self, adapter_cfg: Dict[str, Any]):
        os.environ['SIRIN_JUDGE_KIND'] = adapter_cfg['kind']
        if adapter_cfg.get('model'):
            os.environ['SIRIN_JUDGE_MODEL'] = str(adapter_cfg['model'])
        if adapter_cfg.get('base_url'):
            os.environ['SIRIN_JUDGE_BASE_URL'] = str(adapter_cfg['base_url'])
        os.environ['SIRIN_JUDGE_VERIFY_SSL'] = 'true' if adapter_cfg.get('verify_ssl') else 'false'
        if adapter_cfg.get('api_key'):
            os.environ['SIRIN_JUDGE_API_KEY'] = str(adapter_cfg['api_key'])

    # ------------------------------------------------------------------ data
    def _to_records(self, data) -> List[Dict[str, Any]]:
        from sirin.detection.judging.judges.utils import format_dialogue_samples

        if data is None or len(data) == 0:
            return []
        inputs = list(data[INPUT_COL])
        labels = list(data[TARGET_COL])
        formatted = format_dialogue_samples(self.judge.config, inputs)
        records = []
        for uid, (dialogue, label) in enumerate(zip(formatted, labels)):
            dialogue = str(dialogue)
            records.append({
                'uid': int(uid),
                'dialogue': dialogue,
                'user_prompt': self._user_prompt(dialogue),
                'label': int(label),
            })
        return records

    def _user_prompt(self, dialogue: str) -> str:
        template = getattr(self.judge.config, 'user_prompt', None) or ''
        try:
            return template.format(sample=dialogue)
        except (KeyError, IndexError):
            return f'{template}\n{dialogue}'

    def _seed_prompts(self) -> Tuple[str, str]:
        cfg = self.judge.config
        return getattr(cfg, 'system_prompt', '') or '', getattr(cfg, 'user_prompt', '') or ''

    # ------------------------------------------------------------------ project
    def _skill_md(self, system_prompt: str) -> str:
        return (
            '---\n'
            f'name: {self._skill_name}\n'
            "description: 'Судья: подтверждается ли утверждение/ответ саммари транскриптом "
            "встречи.'\n"
            '---\n\n'
            '# Judge prompt\n\n'
            '## Процедура\n'
            '1. Прочитай `claims.json` в рабочем каталоге.\n'
            '2. Импортируй `judge_client` и для каждого объекта вызови '
            '`judge_client.judge(<system prompt>, item["user_prompt"])`.\n'
            '3. Системное сообщение — ровно текст между маркерами ниже, дословно.\n'
            '4. Запиши `verdicts.json` в корень рабочего каталога.\n\n'
            '## Judge system prompt\n'
            f'{_SYSTEM_MARK_OPEN}\n{system_prompt}\n{_SYSTEM_MARK_CLOSE}\n'
        )

    _INSTRUCTION = '''# {name}

В рабочем каталоге лежит `claims.json` — список объектов
{{"uid": int, "dialogue": str, "user_prompt": str}}.
Определи для каждого, подтверждается ли ответ (1 = недостоверно, 0 = достоверно).

Системный промпт судьи — блок между `{sys_open}` и `{sys_close}` в подключённом skill
(`{skill}`); используй его дословно.

Судья доступен как локальный helper `judge_client` (импортируется без установки):
  import json, judge_client
  answer = judge_client.judge(SYSTEM_PROMPT, item["user_prompt"])   # "0 87" / "1"
Разбери метку из ответа и собери `verdicts.json` в корне рабочего каталога:
{{"<uid>": {{"label": 0 или 1, "confidence": 0-100}}, ...}}

Напиши ОДИН python-скрипт, который всё это делает (stdlib + `judge_client`).
'''

    _EVAL = '''import json, os
from pathlib import Path
import pytest

GOLD = {gold}

def _verdicts():
    ws = Path(os.environ.get("TASK_WORKSPACE") or os.environ.get("WORKSPACE_DIR") or ".")
    p = ws / "verdicts.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {{}}

@pytest.mark.parametrize("uid,gold", sorted(GOLD.items()))
def test_claim(uid, gold):
    v = _verdicts().get(str(uid))
    assert v is not None, f"нет вердикта для uid={{uid}}"
    assert int(v["label"]) == int(gold), f"uid={{uid}}: {{v}} != gold={{gold}}"
'''

    def _write_tasks(self, tasks_root: Path, split: str, units, adapter_cfg: Dict[str, Any]):
        for index, unit in enumerate(units):
            name = f'{split}-{index}'
            task_dir = tasks_root / name
            inputs = task_dir / 'inputs'
            inputs.mkdir(parents=True, exist_ok=True)
            (task_dir / 'tests').mkdir(parents=True, exist_ok=True)
            claims = [
                {'uid': int(r['uid']), 'dialogue': r['dialogue'], 'user_prompt': r['user_prompt']}
                for r in unit
            ]
            (inputs / 'claims.json').write_text(
                json.dumps(claims, ensure_ascii=False, indent=1), encoding='utf-8'
            )
            (inputs / 'judge_client.py').write_text(_JUDGE_CLIENT_SRC, encoding='utf-8')
            if adapter_cfg.get('copy_files'):
                # Guard blocks /home; copy TLS material next to the task so the child can read it.
                cert_dst = inputs / 'judge_cert.pem'
                key_dst = inputs / 'judge_key.pem'
                shutil.copyfile(adapter_cfg['cert_file'], cert_dst)
                shutil.copyfile(adapter_cfg['key_file'], key_dst)
                os.environ['SIRIN_JUDGE_CERT_FILE'] = cert_dst.name
                os.environ['SIRIN_JUDGE_KEY_FILE'] = key_dst.name
            (task_dir / 'instruction.md').write_text(
                self._INSTRUCTION.format(
                    name=name, skill=self._skill_name,
                    sys_open=_SYSTEM_MARK_OPEN, sys_close=_SYSTEM_MARK_CLOSE,
                ),
                encoding='utf-8',
            )
            gold = {int(r['uid']): int(r['label']) for r in unit}
            (task_dir / 'tests' / 'test_outputs.py').write_text(
                self._EVAL.format(gold=json.dumps(gold)), encoding='utf-8'
            )
            (task_dir / 'task.toml').write_text(
                'version = "1.0"\n\n'
                '[metadata]\n'
                f'name = "{name}"\n'
                'difficulty = "medium"\n'
                'category = "claim-verification"\n'
                'origin = "custom"\n\n'
                '[skills]\n'
                f'required = ["{self._skill_name}"]\n\n'
                '[evaluation]\n'
                f'timeout_sec = "{int(self.config.timeout)}"\n'
                'test_file = "tests/test_outputs.py"\n',
                encoding='utf-8',
            )

    # ------------------------------------------------------------------ results
    def _apply_evolved_prompt(self, active_md: str, seed_system: str):
        evolved = _extract_marked(active_md, _SYSTEM_MARK_OPEN, _SYSTEM_MARK_CLOSE)
        if evolved and evolved.strip():
            self.judge.config.system_prompt = evolved
            lg.info(
                f'Evolution: system_prompt updated '
                f'(changed={evolved.strip() != seed_system.strip()})'
            )
        else:
            lg.info('Evolution: prompt unchanged after optimization')

    def _evaluate(self, data) -> Optional[Dict[str, float]]:
        if data is None or len(data) == 0:
            return None
        inputs = list(data[INPUT_COL])
        labels = np.asarray(list(data[TARGET_COL]), dtype=float)
        try:
            probs, preds, _ = self.judge.detect(inputs, labels)
        except Exception as exc:  # noqa: BLE001
            lg.warning(f'Evolution: post-train evaluate failed ({type(exc).__name__}: {exc})')
            return None
        probs = np.asarray(probs, dtype=float)
        preds = np.asarray(preds, dtype=float)
        out: Dict[str, float] = {'n': float(len(labels))}
        if len(labels):
            out['accuracy'] = float((preds == labels).mean())
        mask = np.isfinite(probs)
        if mask.sum() and len(np.unique(labels[mask])) > 1:
            from sklearn.metrics import roc_auc_score

            out['auroc'] = float(roc_auc_score(labels[mask], probs[mask]))
        lg.info(f'Evolution: validation metrics {out}')
        return out

    def _save_artifacts(self, work_dir: Path):
        payload = {
            'result': getattr(self._result, 'to_dict', lambda: str(self._result))(),
            'system_prompt': getattr(self.judge.config, 'system_prompt', None),
            'user_prompt': getattr(self.judge.config, 'user_prompt', None),
        }
        try:
            (work_dir / 'evolution_result.json').write_text(
                json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding='utf-8'
            )
            lg.info(f'Evolution artifacts saved to {work_dir / "evolution_result.json"}')
        except Exception as exc:  # noqa: BLE001
            lg.warning(f'Evolution: could not save artifacts: {exc}')
