"""Coding-agent CLI backend for Evolution LLM calls.

One :class:`LLMBackend` (:class:`AgentBackend`) drives any of several local
coding-agent CLIs — Codex (``codex exec``), Claude Code (``claude -p``), and
Hermes (``hermes -z``) — behind the same backend factory as LiteLLM and
GigaChat. The model id selects the agent:

  - ``codex`` / ``codex/<model>``        -> Codex CLI   (default ``gpt-5.5``)
  - ``claude-code`` / ``claude-code/<m>``-> Claude Code (default ``claude-sonnet-4-6``)
  - ``hermes`` / ``hermes/<model>``      -> Hermes CLI  (config default model)
  - any bare model name                  -> Codex CLI (back-compat)

The shared subprocess orchestration (temp dir, bounded output, isolated
environment, process-group timeout escalation, wall-clock timing) lives in
:class:`AgentBackend`; only the CLI-specific differences (argv,
working-directory mechanism, reply extraction, usage parsing) live in a small
:class:`CliAgent` strategy. Adding a fourth agent is one ``CliAgent`` subclass
plus one registry entry.

Concurrency: each call gets its own :class:`tempfile.TemporaryDirectory` and
its own process group, so concurrent ``complete``/``complete_file_edit`` calls
never share filesystem or process state. The convenience attributes
``last_usage``/``last_codex_diagnostics`` reflect the *most-recently-finished*
call; per-call truth is the returned :class:`LLMResponse` and the diagnostics
dict. Telemetry keys keep their historical ``codex_*`` names (a stable wire
format consumed by ``reflect.py`` and the tests).
"""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from evolution import config
from evolution.core._util import ms_since
from evolution.core.models import Skill
from evolution.eval.child_env import minimal_child_env
from evolution.eval.proc import _BoundedCapture
from evolution.llm.backend import LLMResponse, SeedMode, require_seed_support
from evolution.paths import account_home


class AgentBackendError(RuntimeError):
    """Raised when a coding-agent CLI cannot produce a completion."""


_ALLOWED_FILE_EDIT_SANDBOXES = frozenset({"workspace-write", "danger-full-access"})
_FILE_EDIT_BYPASS = "bypass"
_FILE_EDIT_BYPASS_FLAG = "--dangerously-bypass-approvals-and-sandbox"
_ALLOWED_FILE_EDIT_MODES = _ALLOWED_FILE_EDIT_SANDBOXES | {
    _FILE_EDIT_BYPASS,
    "dangerously-bypass-approvals-and-sandbox",
}
_BASHRC_PATH = Path(os.environ.get("EVO_BASHRC_PATH", str(account_home() / "research" / ".bashrc")))

# Claude Code built-in tools. Text completions disable edits (empty set); the
# file-edit path enables file-authoring tools so Claude rewrites SKILL.md in cwd.
_CLAUDE_NO_TOOLS = ""
_CLAUDE_FILE_EDIT_TOOLS = "Read,Edit,Write,Glob"
# Agentic-session tool set: file-authoring + Bash so the agent can explore
# traces, write a candidate solution, and run solve.sh/measure.sh in cwd.
_CLAUDE_SESSION_TOOLS = "Read,Edit,Write,Glob,Bash"

# Cloud agents (claude/codex) reach their API via the host egress proxy. A
# concurrently-open local-model proxy-strip context can pop these from
# os.environ; snapshot at import (before any local .complete()) and re-assert on
# every agent spawn so the cloud reflector never inherits a stripped env and 403s.
_PROXY_ENV_KEYS = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
    "NO_PROXY",
    "no_proxy",
)
_PROXY_ENV_AT_IMPORT = {k: os.environ[k] for k in _PROXY_ENV_KEYS if k in os.environ}

_COMMON_AGENT_ENV_KEYS = frozenset(
    {
        "HOME",
        "XDG_CONFIG_HOME",
        "NODE_EXTRA_CA_CERTS",
        *_PROXY_ENV_KEYS,
    }
)
_CLI_ENV_KEYS = {
    "codex": frozenset(
        {
            "CODEX_HOME",
            "OPENAI_API_KEY",
            "OPENAI_BASE_URL",
            "OPENAI_ORGANIZATION",
            "OPENAI_PROJECT",
        }
    ),
    "claude": frozenset(
        {
            "ANTHROPIC_API_KEY",
            "ANTHROPIC_AUTH_TOKEN",
            "ANTHROPIC_BASE_URL",
            "CLAUDE_CONFIG_DIR",
        }
    ),
}
_MAX_CAPTURE_BYTES = 1024 * 1024
_PROCESS_TERM_GRACE_SECONDS = 1.0

# Hermes delivers the prompt as the argv value of ``-z`` (not stdin); guard
# against Linux's per-argument size limit (MAX_ARG_STRLEN, 128 KiB) with a
# clear error rather than an opaque OSError on spawn.
_HERMES_ARGV_PROMPT_LIMIT = 120_000
AgentPermission = Literal["safe", "unsafe"]


def _agent_env(tool: str, permission: AgentPermission) -> dict[str, str]:
    source = {**os.environ, **_PROXY_ENV_AT_IMPORT}
    if permission == "unsafe":
        return source
    return minimal_child_env(
        source,
        allow=_COMMON_AGENT_ENV_KEYS | _CLI_ENV_KEYS.get(tool, frozenset()),
    )


async def _read_bounded(stream: asyncio.StreamReader | None) -> bytes:
    if stream is None:
        return b""
    capture = _BoundedCapture(_MAX_CAPTURE_BYTES)
    while chunk := await stream.read(64 * 1024):
        capture.feed(chunk)
    return capture.value()


async def _communicate_bounded(
    proc: asyncio.subprocess.Process, stdin: bytes | None
) -> tuple[bytes, bytes]:
    stdout_task = asyncio.create_task(_read_bounded(proc.stdout))
    stderr_task = asyncio.create_task(_read_bounded(proc.stderr))
    if proc.stdin is not None:
        try:
            if stdin is not None:
                proc.stdin.write(stdin)
                await proc.stdin.drain()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            proc.stdin.close()
    await proc.wait()
    return await asyncio.gather(stdout_task, stderr_task)


def _resolve_file_edit_sandbox() -> str:
    val = os.environ.get("EVO_CODEX_FILE_EDIT_SANDBOX", _FILE_EDIT_BYPASS)
    if val == "dangerously-bypass-approvals-and-sandbox":
        val = _FILE_EDIT_BYPASS
    if val not in _ALLOWED_FILE_EDIT_MODES:
        raise AgentBackendError(
            f"EVO_CODEX_FILE_EDIT_SANDBOX={val!r} invalid; "
            f"allowed: {sorted(_ALLOWED_FILE_EDIT_MODES)}"
        )
    return val


def _resolve_agent_bin(tool: str, override: str | None = None) -> str:
    """Resolve a coding-agent executable from override/<TOOL>_BIN/PATH/bashrc.

    ``tool`` is ``"codex"`` / ``"claude"`` / ``"hermes"`` (env key
    ``CODEX_BIN`` / ``CLAUDE_BIN`` / ``HERMES_BIN``). The bashrc fallback
    mirrors how the user launches the agents
    (``bash --rcfile $EVO_BASHRC_PATH``), so PATH/auth set up
    there are honoured — codex and claude auth depend on it.
    """
    candidate = override or os.environ.get(f"{tool.upper()}_BIN") or tool
    if os.path.basename(candidate) != candidate:
        if os.access(candidate, os.X_OK):
            return candidate
        raise AgentBackendError(f"{tool} executable not found or not executable: {candidate!r}")

    resolved = shutil.which(candidate)
    if resolved:
        return resolved

    if _BASHRC_PATH.is_file():
        try:
            proc = subprocess.run(
                [
                    "bash",
                    "--rcfile",
                    str(_BASHRC_PATH),
                    "-ic",
                    f"command -v {shlex.quote(candidate)}",
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=15,
            )
        except (OSError, subprocess.TimeoutExpired):
            proc = None
        if proc is not None:
            candidates = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
            if candidates and os.access(candidates[-1], os.X_OK):
                return candidates[-1]

    raise AgentBackendError(
        f"{tool} executable not found: {candidate!r}. Set {tool.upper()}_BIN or put {tool} on PATH."
    )


def _parse_codex_jsonl_events(combined: str) -> dict[str, Any]:
    """Parse codex `--json` JSONL stdout into a structured diagnostics dict.

    Handles codex 0.132 event shapes (turn.completed, item.started/completed
    for command_execution and file_change, error). Non-JSON lines (codex's
    plain stderr) are counted; any non-JSON line containing ``bwrap:`` is
    captured into ``sandbox_errors`` as a fallback for sandbox failures that
    codex routes outside the JSONL stream. Defensive — never raises.
    """
    diag: dict[str, Any] = {
        "sandbox_errors": [],
        "command_failures": [],
        "file_changes": [],
        "tool_calls": [],
        "errors": [],
        "completion_tokens": None,
        "prompt_tokens": None,
        "non_json_lines": 0,
    }
    for raw in combined.splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            evt = json.loads(line)
        except json.JSONDecodeError:
            diag["non_json_lines"] += 1
            if "bwrap:" in line:
                diag["sandbox_errors"].append(line)
            continue
        if not isinstance(evt, dict):
            continue
        etype = evt.get("type")
        if etype == "turn.completed":
            usage = evt.get("usage") or {}
            it = usage.get("input_tokens")
            ot = usage.get("output_tokens")
            if isinstance(it, int):
                diag["prompt_tokens"] = it
            if isinstance(ot, int):
                diag["completion_tokens"] = ot
        elif etype == "item.started":
            item = evt.get("item") or {}
            itype = item.get("type")
            if itype in ("command_execution", "file_change"):
                diag["tool_calls"].append(itype)
        elif etype == "item.completed":
            item = evt.get("item") or {}
            itype = item.get("type")
            if itype == "command_execution":
                ec = item.get("exit_code")
                if isinstance(ec, int) and ec != 0:
                    diag["command_failures"].append(
                        {
                            "cmd": item.get("command"),
                            "exit_code": ec,
                            "stderr": item.get("aggregated_output") or "",
                        }
                    )
            elif itype == "file_change":
                for ch in item.get("changes") or []:
                    if isinstance(ch, dict) and ch.get("path"):
                        diag["file_changes"].append(ch)
        elif etype == "error":
            msg = str(evt.get("message") or "")
            if msg:
                diag["errors"].append(msg)
                low = msg.lower()
                if "bwrap:" in low or "permission denied" in low:
                    diag["sandbox_errors"].append(msg)
    return diag


def _normalise_model(model: str) -> str:
    if model == "codex":
        return "gpt-5.5"
    if model.startswith("codex/"):
        return model.split("/", 1)[1] or "gpt-5.5"
    return model


def _format_agent_prompt(messages: list[dict[str, str]], system: str | None = None) -> str:
    parts: list[str] = []
    if system:
        parts.append(system)
    for message in messages:
        content = str(message.get("content") or "")
        if content.strip():
            parts.append(content)
    return "\n\n".join(parts).strip()


def _parse_tokens_used(text: str) -> int:
    """Best-effort parse of Codex CLI token totals from stdout/stderr."""

    patterns = (
        r"tokens\s+used\s*[:=]\s*([0-9][0-9,]*)",
        r"total\s+tokens\s*[:=]\s*([0-9][0-9,]*)",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return int(match.group(1).replace(",", ""))
    return 0


def _parse_codex_usage(text: str) -> dict[str, int | None]:
    """Best-effort parse of Codex CLI usage telemetry.

    Returns ``{prompt_tokens, completion_tokens, tool_turns}``; each is
    the parsed int or ``None`` if not present.  Codex's stdout format
    varies, so the patterns are deliberately broad.
    """

    def _first_int(patterns: tuple[str, ...]) -> int | None:
        for pat in patterns:
            m = re.search(pat, text, flags=re.IGNORECASE)
            if m:
                return int(m.group(1).replace(",", ""))
        return None

    prompt_tokens = _first_int(
        (
            r"prompt\s+tokens?\s*[:=]\s*([0-9][0-9,]*)",
            r"input\s+tokens?\s*[:=]\s*([0-9][0-9,]*)",
            r"tokens?\s+in\s*[:=]\s*([0-9][0-9,]*)",
        )
    )
    completion_tokens = _first_int(
        (
            r"completion\s+tokens?\s*[:=]\s*([0-9][0-9,]*)",
            r"output\s+tokens?\s*[:=]\s*([0-9][0-9,]*)",
            r"tokens?\s+out\s*[:=]\s*([0-9][0-9,]*)",
        )
    )
    tool_turns = _first_int(
        (
            r"tool[_\s]+turns?\s*[:=]\s*([0-9]+)",
            r"\bturns?\s*[:=]\s*([0-9]+)",
            r"iterations?\s*[:=]\s*([0-9]+)",
        )
    )
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "tool_turns": tool_turns,
    }


def _parse_claude_result(stdout: str) -> str:
    """Extract Claude's final reply from a ``--output-format json`` payload.

    Claude ``-p --output-format json`` prints a single JSON object whose
    ``result`` field holds the final assistant text. A non-JSON payload or an
    ``is_error`` result yields ``""`` so callers treat it as a failed run.
    Defensive — never raises.
    """
    text = (stdout or "").strip()
    if not text:
        return ""
    try:
        payload = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return ""
    if isinstance(payload, dict) and not payload.get("is_error"):
        result = payload.get("result")
        if isinstance(result, str):
            return result
    return ""


def _parse_claude_usage(stdout: str) -> tuple[int | None, int | None]:
    """Best-effort ``(input_tokens, output_tokens)`` from Claude JSON output.

    Reads ``.usage.{input_tokens,output_tokens}``; returns ``(None, None)`` for
    non-JSON or missing fields. Defensive — never raises.
    """
    text = (stdout or "").strip()
    if not text:
        return None, None
    try:
        payload = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None, None
    if not isinstance(payload, dict):
        return None, None
    usage = payload.get("usage")
    if not isinstance(usage, dict):
        return None, None
    it = usage.get("input_tokens")
    ot = usage.get("output_tokens")
    return (it if isinstance(it, int) else None, ot if isinstance(ot, int) else None)


def _parse_claude_num_turns(stdout: str) -> int | None:
    """Best-effort ``num_turns`` from Claude ``--output-format json`` output.

    The single JSON result object carries a top-level ``num_turns``; returns
    ``None`` for non-JSON or missing fields. Defensive — never raises.
    """
    text = (stdout or "").strip()
    if not text:
        return None
    try:
        payload = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    n = payload.get("num_turns")
    return n if isinstance(n, int) else None


def _tail(text: str, limit: int = 900) -> str:
    return text[-limit:] if len(text) > limit else text


def _file_digest(path: Path | None) -> str | None:
    if path is None or path.is_symlink() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _record_required_write(
    diagnostics: dict[str, Any],
    required_write: Path | None,
    before_digest: str | None,
) -> None:
    if required_write is None:
        return
    after_digest = _file_digest(required_write)
    if before_digest == after_digest:
        diagnostics.setdefault("file_changes", [])
        return
    kind = "add" if before_digest is None else "delete" if after_digest is None else "update"
    changes = diagnostics.setdefault("file_changes", [])
    if not any(
        isinstance(change, dict)
        and (
            Path(str(change.get("path") or "")).resolve()
            if Path(str(change.get("path") or "")).is_absolute()
            else (required_write.parent / str(change.get("path") or "")).resolve()
        )
        == required_write.resolve()
        for change in changes
    ):
        changes.append(
            {
                "path": str(required_write),
                "kind": kind,
                "source": "backend_before_after",
                "before_sha256": before_digest,
                "after_sha256": after_digest,
            }
        )


@dataclass(frozen=True)
class AgentInvocation:
    """One spawn recipe produced by a :class:`CliAgent` for one call.

    ``stdin`` is the prompt for codex/claude (delivered on stdin) or ``None``
    for hermes (prompt rides in ``argv``). ``cwd`` scopes file edits for
    claude/hermes; codex uses ``-C`` and leaves ``cwd=None``. ``out_file`` is
    codex's ``-o`` reply file (others read the reply from stdout).
    ``diagnostics_seed`` carries CLI-specific keys folded into the file-edit
    diagnostics dict (e.g. codex's resolved sandbox mode).
    """

    argv: list[str]
    stdin: str | None
    cwd: Path | None
    out_file: Path | None
    diagnostics_seed: dict[str, Any] = field(default_factory=dict)


class CliAgent:
    """Strategy for one coding-agent CLI: argv, cwd, reply, and usage.

    A subclass localizes the four things that differ between coding agents:
    how to build the argv (text vs file-edit), how the reply is recovered, and
    how usage telemetry is parsed. Everything else (the spawn/timeout/kill
    loop, env-ladder config, ``last_usage`` bookkeeping) stays agent-agnostic
    in :class:`AgentBackend`.
    """

    tool: str = ""  # binary name + ``<TOOL>_BIN`` env key
    label_prefix: str = ""  # ``model_label`` prefix
    default_model: str = ""
    supports_file_edit: bool = True

    def normalize_model(self, model_id: str) -> str:
        return model_id

    def text_invocation(
        self,
        *,
        agent_bin: str,
        model: str,
        reasoning_effort: str,
        agent_permission: AgentPermission = "safe",
        sandbox: str,
        prompt: str,
        work: Path,
        out_file: Path,
    ) -> AgentInvocation:
        raise NotImplementedError

    def file_edit_invocation(
        self,
        *,
        agent_bin: str,
        model: str,
        reasoning_effort: str,
        agent_permission: AgentPermission = "safe",
        prompt: str,
        work_dir: Path,
        out_file: Path,
    ) -> AgentInvocation:
        raise NotImplementedError

    def session_invocation(
        self,
        *,
        agent_bin: str,
        model: str,
        reasoning_effort: str,
        agent_permission: AgentPermission = "safe",
        prompt: str,
        work_dir: Path,
        out_file: Path,
        budget_usd: float | None,
    ) -> AgentInvocation:
        """Multi-turn agentic session in a rich workspace.

        Defaults to the file-edit recipe (codex/hermes already run shell tools
        there); :class:`ClaudeCli` overrides to add Bash + ``--max-budget-usd``.
        """
        return self.file_edit_invocation(
            agent_bin=agent_bin,
            model=model,
            reasoning_effort=reasoning_effort,
            agent_permission=agent_permission,
            prompt=prompt,
            work_dir=work_dir,
            out_file=out_file,
        )

    def extract_reply(self, *, stdout: str, stderr: str, out_file: Path | None) -> str:
        raise NotImplementedError

    def parse_usage(
        self, *, stdout: str, stderr: str
    ) -> tuple[int | None, int | None, dict[str, Any]]:
        return None, None, {}

    def tool_turns(self, diag: dict[str, Any]) -> int | None:
        return None


class CodexCli(CliAgent):
    """Codex CLI: ``codex exec`` with a ``-C`` workspace and ``-o`` reply file."""

    tool = "codex"
    label_prefix = "codex"
    default_model = "gpt-5.5"

    def normalize_model(self, model_id: str) -> str:
        return _normalise_model(model_id)

    def text_invocation(
        self,
        *,
        agent_bin: str,
        model: str,
        reasoning_effort: str,
        agent_permission: AgentPermission = "safe",
        sandbox: str,
        prompt: str,
        work: Path,
        out_file: Path,
    ) -> AgentInvocation:
        if agent_permission == "safe":
            sandbox = "read-only"
        argv = [
            agent_bin,
            "exec",
            "-m",
            model,
            "-c",
            f"model_reasoning_effort={reasoning_effort}",
            "-s",
            sandbox,
            "--skip-git-repo-check",
            "--ephemeral",
            "--json",
            "-C",
            str(work),
            "-o",
            str(out_file),
            "-",
        ]
        return AgentInvocation(argv=argv, stdin=prompt, cwd=None, out_file=out_file)

    def file_edit_invocation(
        self,
        *,
        agent_bin: str,
        model: str,
        reasoning_effort: str,
        agent_permission: AgentPermission = "safe",
        prompt: str,
        work_dir: Path,
        out_file: Path,
    ) -> AgentInvocation:
        sandbox = "workspace-write" if agent_permission == "safe" else _resolve_file_edit_sandbox()
        argv = [
            agent_bin,
            "exec",
            "-m",
            model,
            "-c",
            f"model_reasoning_effort={reasoning_effort}",
        ]
        if sandbox == _FILE_EDIT_BYPASS:
            argv.append(_FILE_EDIT_BYPASS_FLAG)
        else:
            argv.extend(["-s", sandbox])
        argv.extend(
            [
                "--skip-git-repo-check",
                "--ephemeral",
                "--json",
                "-C",
                str(work_dir),
                "-o",
                str(out_file),
                "-",
            ]
        )
        seed = {
            "sandbox": sandbox,
            "bypass_approvals_and_sandbox": sandbox == _FILE_EDIT_BYPASS,
        }
        return AgentInvocation(
            argv=argv, stdin=prompt, cwd=None, out_file=out_file, diagnostics_seed=seed
        )

    def extract_reply(self, *, stdout: str, stderr: str, out_file: Path | None) -> str:
        if out_file is not None and Path(out_file).is_file():
            return Path(out_file).read_text(encoding="utf-8", errors="replace")
        return ""

    def parse_usage(
        self, *, stdout: str, stderr: str
    ) -> tuple[int | None, int | None, dict[str, Any]]:
        combined = f"{stdout}\n{stderr}"
        diag = _parse_codex_jsonl_events(combined)
        text_usage = _parse_codex_usage(combined)
        prompt_tokens = diag.get("prompt_tokens") or text_usage.get("prompt_tokens")
        completion_tokens = diag.get("completion_tokens") or text_usage.get("completion_tokens")
        if completion_tokens is None:
            completion_tokens = _parse_tokens_used(combined) or None
        return prompt_tokens, completion_tokens, diag

    def tool_turns(self, diag: dict[str, Any]) -> int | None:
        return len(diag.get("tool_calls") or []) or None


class ClaudeCli(CliAgent):
    """Claude Code CLI: ``claude -p`` scoped by subprocess cwd, JSON reply.

    The sandbox argument is ignored; safe mode retains Claude's permission
    checks, while explicit unsafe mode passes ``--dangerously-skip-permissions``.
    The reply and usage come from the stdout JSON payload, not a ``-o`` file.
    """

    tool = "claude"
    label_prefix = "claude-code"
    default_model = "claude-sonnet-4-6"

    def _base_argv(
        self,
        agent_bin: str,
        model: str,
        reasoning_effort: str,
        tools: str,
        agent_permission: AgentPermission = "safe",
    ) -> list[str]:
        argv = [
            agent_bin,
            "-p",
            "--model",
            model,
            "--effort",
            reasoning_effort,
            "--no-session-persistence",
        ]
        if agent_permission == "unsafe":
            argv.append("--dangerously-skip-permissions")
        argv.extend(
            [
                "--output-format",
                "json",
                "--tools",
                tools,
            ]
        )
        return argv

    def text_invocation(
        self,
        *,
        agent_bin: str,
        model: str,
        reasoning_effort: str,
        agent_permission: AgentPermission = "safe",
        sandbox: str,
        prompt: str,
        work: Path,
        out_file: Path,
    ) -> AgentInvocation:
        argv = self._base_argv(
            agent_bin, model, reasoning_effort, _CLAUDE_NO_TOOLS, agent_permission
        )
        return AgentInvocation(argv=argv, stdin=prompt, cwd=work, out_file=None)

    def file_edit_invocation(
        self,
        *,
        agent_bin: str,
        model: str,
        reasoning_effort: str,
        agent_permission: AgentPermission = "safe",
        prompt: str,
        work_dir: Path,
        out_file: Path,
    ) -> AgentInvocation:
        argv = self._base_argv(
            agent_bin, model, reasoning_effort, _CLAUDE_FILE_EDIT_TOOLS, agent_permission
        )
        seed = {
            "sandbox": (
                "claude-skip-permissions" if agent_permission == "unsafe" else "claude-permissions"
            )
        }
        return AgentInvocation(
            argv=argv, stdin=prompt, cwd=work_dir, out_file=None, diagnostics_seed=seed
        )

    def session_invocation(
        self,
        *,
        agent_bin: str,
        model: str,
        reasoning_effort: str,
        agent_permission: AgentPermission = "safe",
        prompt: str,
        work_dir: Path,
        out_file: Path,
        budget_usd: float | None,
    ) -> AgentInvocation:
        argv = self._base_argv(
            agent_bin, model, reasoning_effort, _CLAUDE_SESSION_TOOLS, agent_permission
        )
        if budget_usd is not None:
            argv.extend(["--max-budget-usd", str(budget_usd)])
        seed = {
            "sandbox": (
                "claude-skip-permissions" if agent_permission == "unsafe" else "claude-permissions"
            ),
            "session": True,
        }
        return AgentInvocation(
            argv=argv, stdin=prompt, cwd=work_dir, out_file=None, diagnostics_seed=seed
        )

    def extract_reply(self, *, stdout: str, stderr: str, out_file: Path | None) -> str:
        return _parse_claude_result(stdout)

    def parse_usage(
        self, *, stdout: str, stderr: str
    ) -> tuple[int | None, int | None, dict[str, Any]]:
        ti, to = _parse_claude_usage(stdout)
        diag: dict[str, Any] = {}
        n = _parse_claude_num_turns(stdout)
        if n is not None:
            diag["num_turns"] = n
        return ti, to, diag

    def tool_turns(self, diag: dict[str, Any]) -> int | None:
        n = diag.get("num_turns")
        return n if isinstance(n, int) else None


class HermesCli(CliAgent):
    """Hermes CLI: ``hermes -z "<prompt>"`` one-shot, scoped by subprocess cwd.

    The prompt rides in ``argv`` (not stdin); the final assistant text is the
    process stdout. Approvals are auto-bypassed inside hermes; there is no
    token telemetry, so usage is empty and ``time_ms`` is wall clock. An empty
    model falls back to hermes's configured default (``-m`` omitted).
    """

    tool = "hermes"
    label_prefix = "hermes"
    default_model = ""

    def _argv(
        self,
        agent_bin: str,
        model: str,
        prompt: str,
        agent_permission: AgentPermission,
    ) -> list[str]:
        if agent_permission == "safe":
            raise ValueError(
                "Hermes does not support agent_permission='safe': "
                "its noninteractive one-shot mode auto-bypasses approvals"
            )
        if len(prompt.encode("utf-8")) > _HERMES_ARGV_PROMPT_LIMIT:
            raise AgentBackendError(
                f"hermes prompt is too large for argv delivery "
                f"({len(prompt.encode('utf-8'))} bytes > {_HERMES_ARGV_PROMPT_LIMIT})"
            )
        argv = [agent_bin, "-z", prompt]
        if model:
            argv.extend(["-m", model])
            provider = os.environ.get("HERMES_PROVIDER", "").strip()
            if provider:
                argv.extend(["--provider", provider])
        return argv

    def text_invocation(
        self,
        *,
        agent_bin: str,
        model: str,
        reasoning_effort: str,
        agent_permission: AgentPermission = "safe",
        sandbox: str,
        prompt: str,
        work: Path,
        out_file: Path,
    ) -> AgentInvocation:
        return AgentInvocation(
            argv=self._argv(agent_bin, model, prompt, agent_permission),
            stdin=None,
            cwd=work,
            out_file=None,
        )

    def file_edit_invocation(
        self,
        *,
        agent_bin: str,
        model: str,
        reasoning_effort: str,
        agent_permission: AgentPermission = "safe",
        prompt: str,
        work_dir: Path,
        out_file: Path,
    ) -> AgentInvocation:
        return AgentInvocation(
            argv=self._argv(agent_bin, model, prompt, agent_permission),
            stdin=None,
            cwd=work_dir,
            out_file=None,
        )

    def extract_reply(self, *, stdout: str, stderr: str, out_file: Path | None) -> str:
        return stdout or ""


_AGENT_CLIS: dict[str, CliAgent] = {
    cli.label_prefix: cli for cli in (CodexCli(), ClaudeCli(), HermesCli())
}
_DEFAULT_CLI = _AGENT_CLIS["codex"]


def _select_cli(model_id: str) -> tuple[CliAgent, str]:
    """Resolve ``(cli, normalized_model)`` from a model id.

    Splits on the first ``/``: a known prefix (``codex``/``claude-code``/
    ``hermes``) selects that CLI with the suffix as the model (or the CLI's
    default); any other string routes to Codex with the whole id as the model.
    """
    prefix, _, rest = model_id.partition("/")
    cli = _AGENT_CLIS.get(prefix)
    if cli is not None:
        return cli, (rest or cli.default_model)
    return _DEFAULT_CLI, _DEFAULT_CLI.normalize_model(model_id)


class AgentBackend:
    """LLMBackend that routes completions through a coding-agent CLI.

    The text path (:meth:`complete`) runs in a fresh temporary directory; the
    file-edit path (:meth:`complete_file_edit`) edits a caller-seeded
    ``SKILL.md`` candidate in place. The agent is chosen from the model id (see
    :func:`_select_cli`). See the module docstring for the concurrency and
    telemetry contract.
    """

    seed_mode: SeedMode = "unsupported"

    def __init__(
        self,
        model: str = "codex/gpt-5.5",
        *,
        agent_permission: Literal["safe", "unsafe"] = "safe",
        reasoning_effort: str | None = None,
        timeout_s: float | None = None,
        sandbox: str | None = None,
        agent_bin: str | None = None,
        **_ignored_kwargs: Any,
    ) -> None:
        if agent_permission not in ("safe", "unsafe"):
            raise ValueError("agent_permission must be 'safe' or 'unsafe'")
        self._cli, self._model = _select_cli(model)
        if isinstance(self._cli, HermesCli) and agent_permission == "safe":
            raise ValueError(
                "Hermes does not support agent_permission='safe': "
                "its noninteractive one-shot mode auto-bypasses approvals; "
                "use agent_permission='unsafe' explicitly"
            )
        self.model_label = f"{self._cli.label_prefix}/{self._model or 'default'}"
        self.agent_permission = agent_permission
        self._reasoning_effort = (
            reasoning_effort
            or os.environ.get("EVO_CODEX_REASONING_EFFORT")
            or config.llm_reasoning_effort()
            or "xhigh"
        )
        self._timeout_s = float(
            timeout_s
            or os.environ.get("EVO_CODEX_TIMEOUT_S")
            or os.environ.get("EVO_LLM_TIMEOUT_S")
            or 1800
        )
        self._sandbox = (
            "read-only"
            if agent_permission == "safe"
            else sandbox or os.environ.get("EVO_CODEX_SANDBOX") or "read-only"
        )
        self._agent_bin = agent_bin
        # Populated after every ``complete``/``complete_file_edit`` call so
        # callers can fold usage into the rewrite-audit JSON (C1 §1.4).
        self.last_usage: dict[str, int | None] = {
            "prompt_tokens": None,
            "completion_tokens": None,
            "tool_turns": None,
            "wall_time_ms": None,
        }
        self.last_codex_diagnostics: dict[str, Any] = {}

    async def complete(
        self,
        messages: list[dict[str, str]],
        system: str | None = None,
        seed: int | None = None,
    ) -> LLMResponse:
        require_seed_support(self, seed)
        prompt = _format_agent_prompt(messages, system=system)
        if not prompt:
            raise AgentBackendError(
                f"empty prompt for AgentBackend.complete (model={self.model_label})"
            )

        agent_bin = _resolve_agent_bin(self._cli.tool, self._agent_bin)

        with tempfile.TemporaryDirectory(prefix="evo_agent_") as work:
            out_file = Path(work) / "last_message.txt"
            inv = self._cli.text_invocation(
                agent_bin=agent_bin,
                model=self._model,
                reasoning_effort=self._reasoning_effort,
                agent_permission=self.agent_permission,
                sandbox=self._sandbox,
                prompt=prompt,
                work=Path(work),
                out_file=out_file,
            )
            timed_out, rc, stdout, stderr, elapsed_ms = await self._run(inv, self._timeout_s)
            combined = f"{stdout}\n{stderr}"

            if timed_out:
                raise AgentBackendError(
                    f"{self._cli.tool} timed out after {self._timeout_s:.0f}s "
                    f"(model={self.model_label}, effort={self._reasoning_effort})"
                )
            if rc != 0:
                raise AgentBackendError(
                    f"{self._cli.tool} exited rc={rc} "
                    f"(model={self.model_label}, effort={self._reasoning_effort}). "
                    f"tail:\n{_tail(combined)}"
                )

            content = self._cli.extract_reply(
                stdout=stdout, stderr=stderr, out_file=inv.out_file
            ).strip()
            if not content:
                raise AgentBackendError(
                    f"{self._cli.tool} produced an empty completion "
                    f"(model={self.model_label}, effort={self._reasoning_effort}). "
                    f"tail:\n{_tail(combined)}"
                )

            tokens_in, tokens_out, diag = self._cli.parse_usage(stdout=stdout, stderr=stderr)
            self.last_usage = {
                "prompt_tokens": tokens_in,
                "completion_tokens": tokens_out,
                "tool_turns": self._cli.tool_turns(diag),
                "wall_time_ms": elapsed_ms,
            }
            self.last_codex_diagnostics = diag
            return LLMResponse(
                content=content,
                tokens_in=tokens_in or 0,
                tokens_out=tokens_out or 0,
                time_ms=elapsed_ms,
            )

    async def complete_file_edit(
        self,
        work_dir: Path,
        prompt: str,
        system: str | None = None,
        *,
        timeout_s: float | None = None,
    ) -> LLMResponse:
        """Run the agent CLI against a caller-seeded ``SKILL.md`` candidate.

        Used by the C1 file-edit rewrite mode. The caller seeds
        ``work_dir/SKILL.md``; this method invokes the agent in that directory
        and **does not** delete ``work_dir`` afterwards — the caller reads the
        post-exit file. Codex edits via ``-C``; Claude/Hermes edit in
        ``cwd=work_dir``. Safe Codex runs use ``workspace-write``; historical
        bypass behavior requires ``agent_permission="unsafe"``.

        Returns ``LLMResponse(content="", ...)``. ``content`` is empty by
        contract; the caller reads the candidate SKILL.md from disk.
        """
        if not prompt:
            raise AgentBackendError(
                f"empty prompt for AgentBackend.complete_file_edit (model={self.model_label})"
            )
        if not self._cli.supports_file_edit:
            raise AgentBackendError(f"{self._cli.tool} does not support file-edit rewrites")

        agent_bin = _resolve_agent_bin(self._cli.tool, self._agent_bin)

        work_dir = Path(work_dir)
        if not work_dir.is_dir():
            raise AgentBackendError(f"work_dir does not exist: {work_dir}")

        self.last_codex_diagnostics = {}
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        deadline = float(timeout_s if timeout_s is not None else self._timeout_s)
        with tempfile.TemporaryDirectory(prefix="evo_agent_file_edit_meta_") as meta_dir:
            out_file = Path(meta_dir) / "last_message.txt"
            inv = self._cli.file_edit_invocation(
                agent_bin=agent_bin,
                model=self._model,
                reasoning_effort=self._reasoning_effort,
                agent_permission=self.agent_permission,
                prompt=full_prompt,
                work_dir=work_dir,
                out_file=out_file,
            )
            timed_out, rc, stdout, stderr, elapsed_ms = await self._run(inv, deadline)
            combined = f"{stdout}\n{stderr}"

            if timed_out:
                raise AgentBackendError(
                    f"{self._cli.tool} file-edit timed out after {deadline:.0f}s "
                    f"(model={self.model_label}, effort={self._reasoning_effort})"
                )

            last_message = self._cli.extract_reply(
                stdout=stdout, stderr=stderr, out_file=inv.out_file
            )
            tokens_in, tokens_out, diag = self._cli.parse_usage(stdout=stdout, stderr=stderr)
            diag = dict(diag)
            diag.update(inv.diagnostics_seed)
            diag.update(
                {
                    "returncode": rc,
                    "command": inv.argv,
                    "stdout_tail": _tail(stdout),
                    "stderr_tail": _tail(stderr),
                    "last_message": last_message,
                }
            )
            self.last_codex_diagnostics = diag
            self.last_usage = {
                "prompt_tokens": tokens_in,
                "completion_tokens": tokens_out,
                "tool_turns": self._cli.tool_turns(diag),
                "wall_time_ms": elapsed_ms,
            }

            if rc != 0:
                raise AgentBackendError(
                    f"{self._cli.tool} file-edit exited rc={rc} "
                    f"(model={self.model_label}, effort={self._reasoning_effort}). "
                    f"tail:\n{_tail(combined)}"
                )

            return LLMResponse(
                content="",
                tokens_in=tokens_in or 0,
                tokens_out=tokens_out or _parse_tokens_used(combined),
                time_ms=elapsed_ms,
            )

    async def complete_agent_session(
        self,
        work_dir: Path,
        prompt: str,
        system: str | None = None,
        *,
        budget_usd: float | None = None,
        timeout_s: float | None = None,
        required_write: Path | None = None,
    ) -> LLMResponse:
        """Run a multi-turn agentic session in an existing rich workspace.

        Unlike :meth:`complete_file_edit` (which seeds a ``SKILL.md``-only dir),
        the caller seeds ``work_dir`` with a full scratch workspace (traces,
        task inputs, ``solve.sh``, ``measure.sh``, ``SKILL.md``). The agent
        explores, edits ``SKILL.md`` in place, and may run shell tools. This
        method **does not** delete ``work_dir`` — the caller lifts ``SKILL.md``
        and ``DIAGNOSIS.json`` after exit. Bounds: ``budget_usd`` (claude
        ``--max-budget-usd``) and the wall-clock ``timeout_s``.

        Raises only on timeout / empty prompt / missing work_dir. A non-zero rc
        is recorded in :attr:`last_codex_diagnostics` rather than raised — a
        session can make partial, useful progress before exiting non-zero — so
        the caller decides based on whether ``SKILL.md`` actually changed.
        """
        if not prompt:
            raise AgentBackendError(
                f"empty prompt for AgentBackend.complete_agent_session (model={self.model_label})"
            )
        if not self._cli.supports_file_edit:
            raise AgentBackendError(f"{self._cli.tool} does not support agentic sessions")

        agent_bin = _resolve_agent_bin(self._cli.tool, self._agent_bin)

        work_dir = Path(work_dir)
        if not work_dir.is_dir():
            raise AgentBackendError(f"work_dir does not exist: {work_dir}")
        if required_write is not None:
            required_write = Path(required_write)
            if not required_write.resolve().is_relative_to(work_dir.resolve()):
                raise AgentBackendError("required_write must be inside work_dir")
        before_digest = _file_digest(required_write)

        self.last_codex_diagnostics = {}
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        deadline = float(timeout_s if timeout_s is not None else self._timeout_s)
        with tempfile.TemporaryDirectory(prefix="evo_agent_session_meta_") as meta_dir:
            out_file = Path(meta_dir) / "last_message.txt"
            inv = self._cli.session_invocation(
                agent_bin=agent_bin,
                model=self._model,
                reasoning_effort=self._reasoning_effort,
                agent_permission=self.agent_permission,
                prompt=full_prompt,
                work_dir=work_dir,
                out_file=out_file,
                budget_usd=budget_usd,
            )
            timed_out, rc, stdout, stderr, elapsed_ms = await self._run(inv, deadline)
            combined = f"{stdout}\n{stderr}"

            if timed_out:
                raise AgentBackendError(
                    f"{self._cli.tool} session timed out after {deadline:.0f}s "
                    f"(model={self.model_label}, effort={self._reasoning_effort})"
                )

            last_message = self._cli.extract_reply(
                stdout=stdout, stderr=stderr, out_file=inv.out_file
            )
            tokens_in, tokens_out, diag = self._cli.parse_usage(stdout=stdout, stderr=stderr)
            diag = dict(diag)
            _record_required_write(diag, required_write, before_digest)
            diag.update(inv.diagnostics_seed)
            diag.update(
                {
                    "returncode": rc,
                    "command": inv.argv,
                    "stdout_tail": _tail(stdout),
                    "stderr_tail": _tail(stderr),
                    "last_message": last_message,
                }
            )
            self.last_codex_diagnostics = diag
            self.last_usage = {
                "prompt_tokens": tokens_in,
                "completion_tokens": tokens_out,
                "tool_turns": self._cli.tool_turns(diag),
                "wall_time_ms": elapsed_ms,
            }
            return LLMResponse(
                content=last_message or "",
                tokens_in=tokens_in or 0,
                tokens_out=tokens_out or _parse_tokens_used(combined),
                time_ms=elapsed_ms,
            )

    async def _run(self, inv: AgentInvocation, timeout: float) -> tuple[bool, int, str, str, int]:
        """Spawn one invocation in its own process group; return outcome.

        Returns ``(timed_out, returncode, stdout, stderr, elapsed_ms)``. On
        timeout the process group is terminated and bounded captured output is returned.
        """
        start = time.monotonic()
        proc = await asyncio.create_subprocess_exec(
            *inv.argv,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(inv.cwd) if inv.cwd is not None else None,
            start_new_session=True,
            env=_agent_env(self._cli.tool, self.agent_permission),
        )
        stdin_bytes = inv.stdin.encode("utf-8") if inv.stdin is not None else None
        communicate = asyncio.create_task(_communicate_bounded(proc, stdin_bytes))
        try:
            stdout_b, stderr_b = await asyncio.wait_for(
                asyncio.shield(communicate), timeout=timeout
            )
        except TimeoutError:
            await self._terminate(proc)
            try:
                stdout_b, stderr_b = await asyncio.wait_for(
                    asyncio.shield(communicate), timeout=_PROCESS_TERM_GRACE_SECONDS
                )
            except TimeoutError:
                communicate.cancel()
                with contextlib.suppress(asyncio.CancelledError, Exception):
                    await communicate
                stdout_b, stderr_b = b"", b""
            elapsed_ms = ms_since(start)
            rc = proc.returncode if proc.returncode is not None else -1
            return (
                True,
                rc,
                stdout_b.decode("utf-8", errors="replace"),
                stderr_b.decode("utf-8", errors="replace"),
                elapsed_ms,
            )
        except asyncio.CancelledError:
            await self._terminate(proc)
            communicate.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await communicate
            raise

        elapsed_ms = ms_since(start)
        return (
            False,
            int(proc.returncode or 0),
            stdout_b.decode("utf-8", errors="replace"),
            stderr_b.decode("utf-8", errors="replace"),
            elapsed_ms,
        )

    async def _terminate(self, proc: asyncio.subprocess.Process) -> None:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            try:
                proc.terminate()
            except ProcessLookupError:
                pass
        await asyncio.sleep(_PROCESS_TERM_GRACE_SECONDS)
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            if proc.returncode is None:
                with contextlib.suppress(ProcessLookupError):
                    proc.kill()
        if proc.returncode is None:
            await proc.wait()

    async def complete_with_skill(
        self,
        messages: list[dict[str, str]],
        skill: Skill,
        system: str | None = None,
        seed: int | None = None,
    ) -> LLMResponse:
        return await self.complete_with_skills(messages, [skill], system, seed=seed)

    async def complete_with_skills(
        self,
        messages: list[dict[str, str]],
        skills: list[Skill],
        system: str | None = None,
        seed: int | None = None,
    ) -> LLMResponse:
        skill_blocks = "\n\n".join(
            f'<skill_content name="{s.name}">\n{s.body}\n</skill_content>' for s in skills
        )
        combined_system = f"{system}\n\n{skill_blocks}" if system else skill_blocks
        return await self.complete(messages, system=combined_system, seed=seed)


__all__ = [
    "AgentBackend",
    "AgentBackendError",
    "AgentInvocation",
    "CliAgent",
    "ClaudeCli",
    "CodexCli",
    "HermesCli",
    "_format_agent_prompt",
    "_normalise_model",
    "_parse_claude_result",
    "_parse_claude_num_turns",
    "_parse_claude_usage",
    "_parse_codex_jsonl_events",
    "_parse_codex_usage",
    "_parse_tokens_used",
    "_resolve_agent_bin",
    "_resolve_file_edit_sandbox",
    "_select_cli",
]
