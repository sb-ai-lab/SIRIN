"""Prompt optimization for API judges via Evolution (``evo-skills``).

API judges (:class:`~sirin.detection.judging.judges.base.OpenAIJudgeBase` and its
subclasses) have no gradient-based fine-tuning -- ``train()`` used to be a no-op stub.
Instead of doing nothing, ``train()`` can now *evolve* the judge prompt:

1. Evolution gets a small project: tasks built from the training/validation samples, a
   skill whose body is the current judge system prompt, and a pytest evaluator that
   checks the judge's verdicts against the gold labels.
2. A local OpenAI-compatible bridge (``http://127.0.0.1:<port>/v1``) exposes the judge's
   *own* ``model_adapter`` -- whatever it is (GigaChat mTLS, DeepSeek, ...) -- so the
   Evolution solver and editor can call it with plain HTTP.
3. ``evo evolve optimize`` reflects on the judge's mistakes, rewrites the prompt, and
   promotes a candidate only if it passes the paired gate on validation.
4. The promoted prompt is written back onto the judge config, so the object returned by
   ``train()`` is already improved and ready for ``detect()``.

The module shells out to the ``evo`` CLI (installed as ``evo-skills``) rather than
importing it, so it has no import-time dependency on Evolution and works with any model
adapter that implements ``sample(inputs, max_tokens=..., temperature=...)``.
"""

from __future__ import annotations

import json
import random
import re
import shutil
import socket
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from loguru import logger as lg

from sirin.definitions import INPUT_COL, TARGET_COL
from sirin.models.detection import DetectionResult, PromptEvolutionConfig


_SYSTEM_MARK_OPEN = '<<<JUDGE_SYSTEM_PROMPT'
_SYSTEM_MARK_CLOSE = 'JUDGE_SYSTEM_PROMPT>>>'
_USER_MARK_OPEN = '<<<JUDGE_USER_PROMPT'
_USER_MARK_CLOSE = 'JUDGE_USER_PROMPT>>>'


# --------------------------------------------------------------------------- helpers
def _resolve_evo(explicit: Optional[str]) -> Optional[str]:
    """Locate the ``evo`` CLI: explicit path, ``PATH``, then known venv locations."""
    if explicit and Path(explicit).exists():
        return explicit
    found = shutil.which('evo')
    if found:
        return found
    candidates = [
        Path(sys.executable).parent / 'evo',
        Path.home() / 'sirin_dialogs_bench' / 'evo_env' / 'bin' / 'evo',
        Path.home() / 'evo_env' / 'bin' / 'evo',
        Path.home() / '.local' / 'bin' / 'evo',
    ]
    for cand in candidates:
        if Path(cand).exists():
            return str(cand)
    return None


def _free_port(preferred: int) -> int:
    """Return ``preferred`` if bindable, else an OS-assigned free port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind(('127.0.0.1', preferred))
            return preferred
        except OSError:
            pass
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def _extract_marked(text: str, open_mark: str, close_mark: str) -> Optional[str]:
    match = re.search(
        re.escape(open_mark) + r'\n(.*?)\n' + re.escape(close_mark), text, re.S
    )
    return match.group(1) if match else None


# --------------------------------------------------------------------------- bridge
class _BridgeHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *args):  # silence per-request logging
        pass

    def _send(self, code: int, obj: Dict[str, Any]):
        body = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802 - HTTP verb
        self._send(
            200,
            {
                'object': 'list',
                'data': [{'id': self.server.model_name, 'object': 'model'}],
            },
        )

    def do_POST(self):  # noqa: N802 - HTTP verb
        length = int(self.headers.get('Content-Length') or 0)
        try:
            request = json.loads(self.rfile.read(length) or b'{}')
            messages = request.get('messages') or []
            max_tokens = int(request.get('max_tokens') or 64)
            temperature = float(request.get('temperature') or 0.0)
            with self.server.lock:
                out = self.server.adapter.sample(
                    [messages], max_tokens=max_tokens, temperature=temperature
                )
            text = out[0] if isinstance(out, (list, tuple)) else str(out)
        except Exception as exc:  # surface the real error to the Evolution solver
            self._send(500, {'error': {'message': f'{type(exc).__name__}: {exc}'}})
            return
        self._send(
            200,
            {
                'id': 'sirin-bridge',
                'object': 'chat.completion',
                'model': self.server.model_name,
                'choices': [
                    {
                        'index': 0,
                        'finish_reason': 'stop',
                        'message': {'role': 'assistant', 'content': text},
                    }
                ],
                'usage': {
                    'prompt_tokens': 0,
                    'completion_tokens': 0,
                    'total_tokens': 0,
                },
            },
        )


class _BridgeServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, adapter, port: int, model_name: str):
        super().__init__(('127.0.0.1', port), _BridgeHandler)
        self.adapter = adapter
        self.model_name = model_name
        self.lock = threading.Lock()


# --------------------------------------------------------------------------- trainer
class EvolutionPromptTrainer:
    """Evolve an API judge's prompt with the ``evo`` CLI; drop-in for ``train()``.

    See the module docstring for the full flow. The judge's ``model_adapter`` is reused
    as the Evolution solver/editor backend, so no extra model configuration is needed.
    """

    def __init__(self, judge, config: PromptEvolutionConfig, training_args=None):
        self.judge = judge
        self.config = config
        self.training_args = training_args
        self._skill_name = config.skill_name
        self._report: Optional[Dict[str, Any]] = None

    # ------------------------------------------------------------------ public
    def run(
        self,
        train_data,
        val_data=None,
        metrics: Optional[List[Any]] = None,
    ) -> DetectionResult:
        cfg = self.config
        evo = _resolve_evo(cfg.evo_bin)
        if evo is None:
            raise RuntimeError(
                'Evolution CLI "evo" not found. Install evo-skills[llm] and/or set '
                'PromptEvolutionConfig.evo_bin to the evo executable.'
            )

        work_dir = Path(
            cfg.work_dir
            or (self.training_args.output_dir if self.training_args else None)
            or './evolution_judge'
        )
        work_dir.mkdir(parents=True, exist_ok=True)
        project = work_dir / 'project'
        if project.exists():
            shutil.rmtree(project)
        (project / 'tasks').mkdir(parents=True)

        train_records = self._to_records(train_data)
        val_records = (
            self._to_records(val_data) if val_data is not None else train_records
        )
        if not train_records:
            lg.warning('Evolution: no training records; skipping prompt optimization')
            return DetectionResult()

        train_units = _chunk(train_records, cfg.claims_per_task, cfg.n_train_tasks, cfg.seed)
        val_units = _chunk(val_records, cfg.claims_per_task, cfg.n_val_tasks, cfg.seed)

        seed_system, seed_user = self._seed_prompts()
        skill_md = self._skill_md(seed_system, seed_user)
        skill_dir = project / '.agents' / 'skills' / self._skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / 'SKILL.md').write_text(skill_md, encoding='utf-8')

        model = cfg.model or getattr(self._model_adapter.config, 'model_path', 'judge')
        editor = cfg.editor_model or cfg.model or model
        port = _free_port(cfg.bridge_port)
        bridge = _BridgeServer(self._model_adapter, port, str(model))
        threading.Thread(target=bridge.serve_forever, daemon=True).start()
        api_base = f'http://127.0.0.1:{port}/v1'
        lg.info(f'Evolution bridge on {api_base} -> {type(self._model_adapter).__name__}')

        try:
            self._run_evo(evo, ['skill', 'commit', self._skill_name, '-m', 'seed prompt'], project)
            train_names = self._write_tasks(project, 'train', train_units, api_base, str(model))
            val_names = self._write_tasks(project, 'val', val_units, api_base, str(model))

            smoke_ws = work_dir / 'ws_smoke'
            if smoke_ws.exists():
                shutil.rmtree(smoke_ws)
            self._run_evo(
                evo,
                [
                    'run', 'solve', train_names[0],
                    '-m', f'openai/{model}',
                    '--api-base', api_base,
                    '-s', self._skill_name,
                    '-w', str(smoke_ws),
                    '-d', 'tasks',
                    '--timeout', str(int(cfg.timeout)),
                ],
                project,
                check=False,
            )
            lg.info(f'Evolution smoke verdicts.json: {(smoke_ws / "verdicts.json").exists()}')

            self._report = self._optimize(
                evo, project, api_base, train_names, val_names, str(model), str(editor)
            )
        finally:
            bridge.shutdown()
            bridge.server_close()

        active_md = (skill_dir / 'SKILL.md').read_text(encoding='utf-8')
        self._apply_evolved_prompt(active_md, seed_system, seed_user)

        result = DetectionResult(
            metrics=self._evaluate(val_data),
            probs=None,
            threshold=self.judge.threshold,
        )
        self._save_artifacts(work_dir)
        return result

    # ------------------------------------------------------------------ data
    @property
    def _model_adapter(self):
        return self.judge.model_adapter

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
            records.append(
                {
                    'uid': int(uid),
                    'dialogue': dialogue,
                    'user_prompt': self._user_prompt(dialogue),
                    'label': int(label),
                }
            )
        return records

    def _user_prompt(self, dialogue: str) -> str:
        template = getattr(self.judge.config, 'user_prompt', None) or ''
        try:
            return template.format(sample=dialogue)
        except (KeyError, IndexError):
            return f'{template}\n{dialogue}'

    def _seed_prompts(self) -> Tuple[str, str]:
        cfg = self.judge.config
        return (
            getattr(cfg, 'system_prompt', '') or '',
            getattr(cfg, 'user_prompt', '') or '',
        )

    # ------------------------------------------------------------------ project
    def _skill_md(self, system_prompt: str, user_prompt: str) -> str:
        target = self.config.target
        blocks = [
            f'# Judge prompt\n',
            f'## Процедура\n',
            f'1. Прочитай `claims.json` в рабочем каталоге.',
            f'2. Для каждого объекта вызови модель судьи так, как описано в instruction.md.',
            f'3. Системное сообщение — ровно текст между маркерами ниже, дословно, без правок.',
            f'4. Запиши `verdicts.json` в корень рабочего каталога.\n',
        ]
        if target in ('system_prompt', 'both'):
            blocks += [
                '## Judge system prompt',
                _SYSTEM_MARK_OPEN,
                system_prompt,
                _SYSTEM_MARK_CLOSE,
                '',
            ]
        if target in ('user_prompt', 'both'):
            blocks += [
                '## Judge user prompt template',
                _USER_MARK_OPEN,
                user_prompt,
                _USER_MARK_CLOSE,
                '',
            ]
        body = '\n'.join(blocks)
        return (
            '---\n'
            f'name: {self._skill_name}\n'
            "description: 'Судья: подтверждается ли утверждение/ответ саммари транскриптом "
            "встречи.'\n"
            '---\n\n'
            f'{body}'
        )

    def _instruction(self, name: str, api_base: str, model: str) -> str:
        system_note = (
            'Системный промпт судьи — блок между строками '
            f'`{_SYSTEM_MARK_OPEN}` и `{_SYSTEM_MARK_CLOSE}`; используй его дословно.'
        )
        user_note = (
            'Если в skill есть блок '
            f'`{_USER_MARK_OPEN}` … `{_USER_MARK_CLOSE}`, подставляй в него '
            '`dialogue` из объекта.'
        )
        return f'''# {name}

В рабочем каталоге лежит `claims.json` — список объектов
{{"uid": int, "dialogue": str, "user_prompt": str}}.
Для каждого определи, подтверждается ли ответ/утверждение (1 = недостоверно, 0 = достоверно).

Правила процедуры — в подключённом skill (`{self._skill_name}`). {system_note}
{user_note}

Вызов модели (только stdlib):
  POST {api_base}/chat/completions
  body = {{"model": "{model}", "max_tokens": 32, "temperature": 0,
          "messages": [{{"role": "system", "content": <judge system prompt>}},
                       {{"role": "user", "content": item["user_prompt"]}}]}}
  ответ = response["choices"][0]["message"]["content"]  # например "0 87" или "1"

Запиши `verdicts.json` в корень рабочего каталога:
{{"<uid>": {{"label": 0 или 1, "confidence": 0-100}}, ...}}
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

    def _write_tasks(self, project: Path, split: str, units, api_base: str, model: str):
        names = []
        for index, unit in enumerate(units):
            name = f'{split}-{index}'
            task_dir = project / 'tasks' / name
            (task_dir / 'inputs').mkdir(parents=True, exist_ok=True)
            (task_dir / 'tests').mkdir(parents=True, exist_ok=True)
            claims = [
                {
                    'uid': int(r['uid']),
                    'dialogue': r['dialogue'],
                    'user_prompt': r['user_prompt'],
                }
                for r in unit
            ]
            (task_dir / 'inputs' / 'claims.json').write_text(
                json.dumps(claims, ensure_ascii=False, indent=1), encoding='utf-8'
            )
            (task_dir / 'instruction.md').write_text(
                self._instruction(name, api_base, model), encoding='utf-8'
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
            names.append(name)
        return names

    # ------------------------------------------------------------------ evo cli
    def _run_evo(self, evo: str, args: List[str], cwd: Path, check: bool = True):
        cmd = [evo] + args
        lg.info('$ ' + ' '.join(cmd))
        proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
        tail = (proc.stdout or '')[-4000:] + '\n' + (proc.stderr or '')[-2000:]
        lg.info(tail)
        if check and proc.returncode != 0:
            raise RuntimeError(f'evo {" ".join(args)} failed (rc={proc.returncode}):\n{tail}')
        return proc

    def _optimize(
        self,
        evo: str,
        project: Path,
        api_base: str,
        train_names: List[str],
        val_names: List[str],
        model: str,
        editor: str,
    ) -> Optional[Dict[str, Any]]:
        cfg = self.config
        args = (
            ['evolve', 'optimize', self._skill_name]
            + sum([['--train', name] for name in train_names], [])
            + sum([['--validate', name] for name in val_names], [])
            + [
                '--solver-model', f'openai/{model}',
                '--solver-api-base', api_base,
                '--editor-model', f'openai/{editor}',
                '--editor-api-base', api_base,
                '--solver-temperature', '0',
                '--editor-temperature', '0.4',
                '--rounds', str(cfg.rounds),
                '--trials', str(cfg.trials),
                '--rewrite-mode', 'edit-ops',
                '--max-tokens', str(cfg.max_tokens),
                '--timeout', str(cfg.timeout),
                '-d', 'tasks',
            ]
            + list(cfg.extra_evo_args or [])  # type: ignore[arg-type]
            + ['--json']
        )
        proc = self._run_evo(evo, args, project, check=False)
        report = self._parse_report(proc.stdout or '')
        if report is None:
            lg.warning('Evolution: optimizer JSON not parsed; tail:\n' + (proc.stdout or '')[-1500:])
        return report

    @staticmethod
    def _parse_report(text: str) -> Optional[Dict[str, Any]]:
        start = text.find('{"schema_version"')
        if start < 0:
            return None
        depth = 0
        for index in range(start, len(text)):
            char = text[index]
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start : index + 1])
                    except json.JSONDecodeError:
                        return None
        return None

    # ------------------------------------------------------------------ results
    def _apply_evolved_prompt(self, active_md: str, seed_system: str, seed_user: str):
        target = self.config.target
        applied = False
        if target in ('system_prompt', 'both'):
            evolved = _extract_marked(active_md, _SYSTEM_MARK_OPEN, _SYSTEM_MARK_CLOSE)
            if evolved and evolved.strip():
                self.judge.config.system_prompt = evolved
                applied = evolved.strip() != seed_system.strip()
                lg.info(f'Evolution: system_prompt updated (changed={applied})')
        if target in ('user_prompt', 'both'):
            evolved = _extract_marked(active_md, _USER_MARK_OPEN, _USER_MARK_CLOSE)
            if evolved and evolved.strip():
                self.judge.config.user_prompt = evolved
                applied = applied or evolved.strip() != seed_user.strip()
                lg.info('Evolution: user_prompt updated')
        if not applied:
            lg.info('Evolution: prompt unchanged after optimization')

    def _evaluate(self, data) -> Optional[Dict[str, float]]:
        if data is None or len(data) == 0:
            return None
        inputs = list(data[INPUT_COL])
        labels = np.asarray(list(data[TARGET_COL]), dtype=float)
        try:
            probs, preds, _ = self.judge.detect(inputs, labels)
        except Exception as exc:  # noqa: BLE001 - evaluation must never sink train()
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
            'report': self._report,
            'system_prompt': getattr(self.judge.config, 'system_prompt', None),
            'user_prompt': getattr(self.judge.config, 'user_prompt', None),
        }
        try:
            (work_dir / 'evolution_result.json').write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8'
            )
            lg.info(f'Evolution artifacts saved to {work_dir / "evolution_result.json"}')
        except Exception as exc:  # noqa: BLE001
            lg.warning(f'Evolution: could not save artifacts: {exc}')


def _chunk(records: List[Dict[str, Any]], size: int, count: int, seed: int):
    """Split records into ``count`` shuffled units of ``size`` (drop tiny leftovers)."""
    records = list(records)
    random.Random(seed).shuffle(records)
    size = max(1, size)
    units = [records[i * size : (i + 1) * size] for i in range(max(1, count))]
    units = [u for u in units if len(u) >= max(2, size // 2)]
    return units or ([records] if records else [])
