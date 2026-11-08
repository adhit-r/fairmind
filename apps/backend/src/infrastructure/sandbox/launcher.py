"""Sandbox launcher: runs one apps/eval-runner container per evaluation under a fixed confinement.

Every `docker run` comes from build_argv, one fixed template. Callers choose only the image digest
(which must be on the host allowlist) and the envelope budgets (which must be numbers at or under
the host ceilings); they cannot add flags, mounts, environment or a command. The container gets no
network, a read-only root, a small noexec tmpfs, no capabilities, the repository seccomp profile,
UID 65532, cgroup limits with memory-swap equal to memory, and a wall-clock kill. The docker socket
stays with the launcher; nothing is mounted into the container.

This runs on the worker host only (docs/operations/rootless-docker-sandbox.md) and is off unless
SANDBOX_LAUNCHER_ENABLED is set; SandboxConfig.from_settings fails closed on any gap.
"""

from __future__ import annotations

import json
import math
import os
import re
import subprocess
import threading
import time
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

SANDBOX_UID = 65532
LABEL = "io.fairmind.sandbox=1"
LABEL_FILTER = "label=io.fairmind.sandbox=1"
NAME_PREFIX = "fm-sbx-"
HARD_OUTPUT_CAP = 64 * 1024
_DOCKER_TIMEOUT = 30  # seconds for inspect, rm and ps calls

_DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
_REPOSITORY = re.compile(r"[a-z0-9]+(?:[._-][a-z0-9]+)*(?::[0-9]{1,5})?(?:/[a-z0-9]+(?:[._-][a-z0-9]+)*)+")
_DOCKER_HOST = re.compile(r"unix:///[A-Za-z0-9._/-]+")
_PATH = re.compile(r"/[A-Za-z0-9._/-]+")

OUTCOMES = ("completed", "timeout", "oom", "crashed", "output_invalid")
RUNNER_STATUSES = frozenset({"passed", "failed", "insufficient"})
RUNNER_ERRORS = frozenset({"input_invalid", "input_too_large", "unsupported_engine", "engine_failed", "output_too_large"})


class SandboxRefused(ValueError):
    """The launch request breaks the fixed contract; `code` is one fixed string."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class SandboxUnavailable(RuntimeError):
    """The launcher is off or its host configuration is incomplete or unsafe."""


class RunnerOutputInvalid(ValueError):
    """The runner's stdout is not exactly one well-formed result line."""


@dataclass(frozen=True, slots=True)
class SandboxConfig:
    docker_cli: str
    docker_host: str
    require_rootless: bool
    repository: str
    allowed_digests: frozenset[str]
    seccomp_profile: str
    cpus: float
    max_memory_mib: int
    max_processes: int
    max_duration_seconds: int
    max_disk_mib: int
    max_input_bytes: int
    max_output_bytes: int

    def __post_init__(self) -> None:
        if not (_PATH.fullmatch(self.docker_cli) and _PATH.fullmatch(self.seccomp_profile)):
            raise SandboxUnavailable("docker_cli and seccomp_profile must be absolute paths")
        if not _DOCKER_HOST.fullmatch(self.docker_host):
            raise SandboxUnavailable("docker_host must be a unix:/// socket")
        if not _REPOSITORY.fullmatch(self.repository):
            raise SandboxUnavailable("repository must be a registry path without tag or digest")
        if not self.allowed_digests or not all(_DIGEST.fullmatch(d) for d in self.allowed_digests):
            raise SandboxUnavailable("allowed_digests must be sha256:<64 hex> values")
        if not (isinstance(self.cpus, (int, float)) and 0 < self.cpus <= 64):
            raise SandboxUnavailable("cpus must be in (0, 64]")
        for name, low, high in (
            ("max_memory_mib", 64, 65_536),
            ("max_processes", 8, 4_096),
            ("max_duration_seconds", 1, 3_600),
            ("max_disk_mib", 1, 4_096),
            ("max_input_bytes", 1, 1 << 30),
            ("max_output_bytes", 64, HARD_OUTPUT_CAP),
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
                raise SandboxUnavailable(f"{name} must be an integer in [{low}, {high}]")

    @classmethod
    def from_settings(cls, settings: Any) -> "SandboxConfig":
        if not getattr(settings, "sandbox_launcher_enabled", False):
            raise SandboxUnavailable("the sandbox launcher is disabled")
        digests = frozenset(d.strip() for d in settings.sandbox_runner_digests.split(",") if d.strip())
        config = cls(
            docker_cli=settings.sandbox_docker_cli,
            docker_host=settings.sandbox_docker_host,
            require_rootless=settings.sandbox_require_rootless,
            repository=settings.sandbox_runner_repository,
            allowed_digests=digests,
            seccomp_profile=settings.sandbox_seccomp_profile,
            cpus=settings.sandbox_cpus,
            max_memory_mib=settings.sandbox_max_memory_mib,
            max_processes=settings.sandbox_max_processes,
            max_duration_seconds=settings.sandbox_max_duration_seconds,
            max_disk_mib=settings.sandbox_max_disk_mib,
            max_input_bytes=settings.sandbox_max_input_bytes,
            max_output_bytes=settings.sandbox_max_output_bytes,
        )
        if not os.path.isfile(config.seccomp_profile):
            raise SandboxUnavailable("seccomp_profile does not exist")
        return config


@dataclass(frozen=True, slots=True)
class Limits:
    duration_seconds: float
    cpu_seconds: int
    memory_mib: int
    processes: int
    disk_mib: int
    input_bytes: int
    output_bytes: int


# envelope budget key -> the SandboxConfig ceiling attribute; None is CPU time, capped at wall clock times cpus
_BUDGETS = {
    "maxDurationSeconds": "max_duration_seconds",
    "maxCpuSeconds": None,
    "maxMemoryMiB": "max_memory_mib",
    "maxProcesses": "max_processes",
    "maxDiskMiB": "max_disk_mib",
    "maxInputBytes": "max_input_bytes",
    "maxOutputBytes": "max_output_bytes",
}


def limits_for(config: SandboxConfig, budgets: Mapping[str, Any]) -> Limits:
    """The envelope budgets as sandbox limits; a missing budget takes the host ceiling, one above it is refused."""
    if not isinstance(budgets, Mapping):
        raise SandboxRefused("invalid_budget")
    values: dict[str, float] = {}
    for key, attribute in _BUDGETS.items():
        ceiling = math.ceil(config.max_duration_seconds * config.cpus) if attribute is None else getattr(config, attribute)
        value = budgets.get(key, ceiling)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise SandboxRefused("invalid_budget")
        if value > ceiling:
            raise SandboxRefused("budget_exceeds_host")
        values[key] = value
    whole = {k: math.ceil(v) for k, v in values.items()}
    return Limits(
        duration_seconds=float(values["maxDurationSeconds"]),
        cpu_seconds=whole["maxCpuSeconds"],
        memory_mib=max(whole["maxMemoryMiB"], 64),
        processes=max(whole["maxProcesses"], 8),
        disk_mib=whole["maxDiskMiB"],
        input_bytes=whole["maxInputBytes"],
        output_bytes=min(whole["maxOutputBytes"], HARD_OUTPUT_CAP),
    )


def image_ref(config: SandboxConfig, digest: Any) -> str:
    if not isinstance(digest, str) or not _DIGEST.fullmatch(digest) or digest not in config.allowed_digests:
        raise SandboxRefused("image_not_allowed")
    return f"{config.repository}@{digest}"


def build_argv(config: SandboxConfig, digest: str, limits: Limits, name: str) -> list[str]:
    """The one docker run template. The image is always the last element, with no command after it."""
    if not re.fullmatch(NAME_PREFIX + "[0-9a-f]{32}", name):
        raise SandboxRefused("invalid_name")
    disk_bytes = limits.disk_mib * 1024 * 1024
    return [
        config.docker_cli,
        "run",
        "--interactive",
        "--pull=never",
        f"--name={name}",
        f"--label={LABEL}",
        "--log-driver=none",
        "--network=none",
        "--ipc=private",
        "--read-only",
        f"--tmpfs=/tmp:rw,noexec,nosuid,nodev,size={limits.disk_mib}m",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges=true",
        f"--security-opt=seccomp={config.seccomp_profile}",
        f"--user={SANDBOX_UID}:{SANDBOX_UID}",
        f"--pids-limit={limits.processes}",
        f"--memory={limits.memory_mib}m",
        f"--memory-swap={limits.memory_mib}m",
        "--oom-score-adj=1000",
        f"--cpus={config.cpus:g}",
        "--ulimit=core=0:0",
        "--ulimit=nofile=256:256",
        f"--ulimit=cpu={limits.cpu_seconds}:{limits.cpu_seconds}",
        f"--ulimit=fsize={disk_bytes}:{disk_bytes}",
        image_ref(config, digest),
    ]


def _reject_constant(token: str) -> None:
    raise RunnerOutputInvalid("non-finite number")


def _finite_float(token: str) -> float:
    value = float(token)
    if not math.isfinite(value):
        raise RunnerOutputInvalid("non-finite number")
    return value


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = dict(pairs)
    if len(result) != len(pairs):
        raise RunnerOutputInvalid("duplicate key")
    return result


def _scalar(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return len(value) <= 64
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def parse_runner_output(raw: bytes, cap: int = HARD_OUTPUT_CAP) -> dict[str, Any]:
    """Exactly one newline-terminated JSON object in the runner's closed result or error shape."""
    if len(raw) > min(cap, HARD_OUTPUT_CAP):
        raise RunnerOutputInvalid("output too large")
    if not raw.endswith(b"\n") or raw.count(b"\n") != 1 or b"\r" in raw:
        raise RunnerOutputInvalid("output must be exactly one line")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_no_duplicates,
            parse_constant=_reject_constant,
            parse_float=_finite_float,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise RunnerOutputInvalid("output is not JSON") from exc
    if not isinstance(value, dict) or value.get("v") != 1 or isinstance(value.get("v"), bool):
        raise RunnerOutputInvalid("unknown output version")
    if set(value) == {"v", "error"}:
        if value["error"] not in RUNNER_ERRORS:
            raise RunnerOutputInvalid("unknown error code")
        return value
    if set(value) != {"v", "engine", "status", "metrics"}:
        raise RunnerOutputInvalid("unexpected keys")
    metrics = value["metrics"]
    if (
        not isinstance(value["engine"], str)
        or not re.fullmatch(r"EV-[A-Z]{2,5}-[0-9]{2}", value["engine"])
        or value["status"] not in RUNNER_STATUSES
        or not isinstance(metrics, dict)
        or len(metrics) > 32
        or not all(isinstance(k, str) and len(k) <= 64 and _scalar(v) for k, v in metrics.items())
    ):
        raise RunnerOutputInvalid("result does not match the closed shape")
    return value


@dataclass(frozen=True, slots=True)
class SandboxResult:
    outcome: str  # one of OUTCOMES
    output: dict[str, Any] | None = None  # the parsed runner line when outcome is "completed"


class SandboxLauncher:
    def __init__(self, config: SandboxConfig) -> None:
        self._config = config
        # The docker CLI gets this environment and nothing from the launcher's own.
        self._env = {"DOCKER_HOST": config.docker_host, "PATH": "/usr/bin:/bin"}

    def _docker(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [self._config.docker_cli, *args],
            env=self._env,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=_DOCKER_TIMEOUT,
            check=False,
        )

    def check_host(self) -> None:
        """Refuses a daemon that would silently ignore the cgroup limits or seccomp."""
        info = self._docker("info", "--format", "{{json .}}")
        if info.returncode != 0:
            raise SandboxUnavailable("docker daemon is not reachable")
        data = json.loads(info.stdout)
        options = " ".join(data.get("SecurityOptions") or [])
        if not all(data.get(key) is True for key in ("MemoryLimit", "SwapLimit", "PidsLimit", "CpuCfsQuota")):
            raise SandboxUnavailable("docker daemon cannot enforce memory, swap, pids and cpu limits")
        if data.get("CgroupVersion") != "2" or "name=seccomp" not in options:
            raise SandboxUnavailable("docker daemon needs cgroup v2 and seccomp")
        if self._config.require_rootless and "name=rootless" not in options:
            raise SandboxUnavailable("docker daemon is not rootless")

    def reap(self) -> int:
        """Removes every labelled sandbox container; run on start, when no sandbox may legitimately exist."""
        listed = self._docker("ps", "--all", "--quiet", "--no-trunc", "--filter", LABEL_FILTER)
        if listed.returncode != 0:
            raise SandboxUnavailable("cannot list sandbox containers")
        ids = [i for i in listed.stdout.split() if re.fullmatch(r"[0-9a-f]{64}", i)]
        if ids:
            self._docker("rm", "--force", *ids)
        return len(ids)

    def start(self) -> int:
        self.check_host()
        return self.reap()

    def run(self, digest: str, budgets: Mapping[str, Any], payload: bytes) -> SandboxResult:
        limits = limits_for(self._config, budgets)
        if not isinstance(payload, (bytes, bytearray)) or len(payload) > limits.input_bytes:
            raise SandboxRefused("input_too_large")
        name = NAME_PREFIX + uuid.uuid4().hex
        argv = build_argv(self._config, digest, limits, name)
        deadline = time.monotonic() + limits.duration_seconds
        process = subprocess.Popen(
            argv, env=self._env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        )
        output = bytearray()
        try:
            feeder = threading.Thread(target=_feed, args=(process, bytes(payload)), daemon=True)
            reader = threading.Thread(target=_drain, args=(process, output, limits.output_bytes), daemon=True)
            feeder.start()
            reader.start()
            reader.join(limits.duration_seconds)
            if reader.is_alive():
                return SandboxResult("timeout")
            if len(output) > limits.output_bytes:
                return SandboxResult("output_invalid")
            try:
                code = process.wait(timeout=max(0.1, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                return SandboxResult("timeout")
            if self._oom_killed(name):
                return SandboxResult("oom")
            if code != 0:
                return SandboxResult("crashed")
            try:
                return SandboxResult("completed", parse_runner_output(bytes(output), limits.output_bytes))
            except RunnerOutputInvalid:
                return SandboxResult("output_invalid")
        finally:
            self._docker("rm", "--force", name)
            if process.poll() is None:
                process.kill()
                process.wait()

    def _oom_killed(self, name: str) -> bool:
        inspected = self._docker("inspect", "--format", "{{.State.OOMKilled}}", name)
        return inspected.returncode == 0 and inspected.stdout.strip() == "true"


def _feed(process: subprocess.Popen[bytes], payload: bytes) -> None:
    try:
        assert process.stdin is not None
        process.stdin.write(payload)
        process.stdin.close()
    except (BrokenPipeError, OSError):
        pass


def _drain(process: subprocess.Popen[bytes], output: bytearray, cap: int) -> None:
    assert process.stdout is not None
    while len(output) <= cap:
        chunk = process.stdout.read1(65_536)
        if not chunk:
            return
        output.extend(chunk)


__all__ = [
    "Limits",
    "OUTCOMES",
    "RunnerOutputInvalid",
    "SandboxConfig",
    "SandboxLauncher",
    "SandboxRefused",
    "SandboxResult",
    "SandboxUnavailable",
    "build_argv",
    "image_ref",
    "limits_for",
    "parse_runner_output",
]
