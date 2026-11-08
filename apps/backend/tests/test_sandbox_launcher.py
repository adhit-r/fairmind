"""The sandbox launcher's fixed docker run template, its budget handling and the runner output parser."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.infrastructure.sandbox import (
    RunnerOutputInvalid,
    SandboxConfig,
    SandboxRefused,
    SandboxUnavailable,
    build_argv,
    limits_for,
    parse_runner_output,
)

SECCOMP = Path(__file__).resolve().parents[2] / "eval-runner" / "seccomp" / "sandbox.json"
DIGEST = "sha256:" + "a" * 64
OTHER = "sha256:" + "b" * 64
NAME = "fm-sbx-" + "0" * 32


def config(**overrides):
    values = dict(
        docker_cli="/usr/bin/docker",
        docker_host="unix:///run/user/1001/docker.sock",
        require_rootless=True,
        repository="ghcr.io/adhit-r/fairmind-eval-runner",
        allowed_digests=frozenset({DIGEST}),
        seccomp_profile=str(SECCOMP),
        cpus=1.0,
        max_memory_mib=768,
        max_processes=64,
        max_duration_seconds=300,
        max_disk_mib=64,
        max_input_bytes=32 * 1024 * 1024,
        max_output_bytes=16 * 1024,
    )
    values.update(overrides)
    return SandboxConfig(**values)


def argv(budgets=None, **overrides):
    cfg = config(**overrides)
    return build_argv(cfg, DIGEST, limits_for(cfg, budgets or {}), NAME)


def test_argv_is_the_fixed_template():
    args = argv({"maxMemoryMiB": 256, "maxProcesses": 32, "maxDiskMiB": 16, "maxCpuSeconds": 10})
    assert args[:2] == ["/usr/bin/docker", "run"]
    for flag in (
        "--interactive",
        "--pull=never",
        "--log-driver=none",
        "--network=none",
        "--ipc=private",
        "--read-only",
        "--tmpfs=/tmp:rw,noexec,nosuid,nodev,size=16m",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges=true",
        f"--security-opt=seccomp={SECCOMP}",
        "--user=65532:65532",
        "--pids-limit=32",
        "--memory=256m",
        "--memory-swap=256m",
        "--oom-score-adj=1000",
        "--cpus=1",
        "--ulimit=core=0:0",
        "--ulimit=nofile=256:256",
        "--ulimit=cpu=10:10",
        f"--ulimit=fsize={16 * 1024 * 1024}:{16 * 1024 * 1024}",
        f"--name={NAME}",
        "--label=io.fairmind.sandbox=1",
    ):
        assert flag in args, flag
    # The image is the last element: no command, no caller arguments after it.
    assert args[-1] == f"ghcr.io/adhit-r/fairmind-eval-runner@{DIGEST}"
    flags = args[2:-1]
    assert all(a.startswith("--") for a in flags)
    assert not any(a.split("=")[0] in {"--volume", "-v", "--mount", "--env", "-e", "--env-file", "--privileged", "--device", "--cap-add", "--entrypoint"} for a in flags)
    assert not any("docker.sock" in a for a in args)


def test_missing_budgets_take_the_host_ceilings():
    args = argv({})
    assert "--memory=768m" in args and "--memory-swap=768m" in args and "--pids-limit=64" in args


@pytest.mark.parametrize(
    "budgets, code",
    [
        ({"maxMemoryMiB": "256m --privileged"}, "invalid_budget"),
        ({"maxMemoryMiB": True}, "invalid_budget"),
        ({"maxProcesses": float("nan")}, "invalid_budget"),
        ({"maxDurationSeconds": float("inf")}, "invalid_budget"),
        ({"maxDiskMiB": -1}, "invalid_budget"),
        ({"maxDiskMiB": 0}, "invalid_budget"),
        ({"maxProcesses": [1]}, "invalid_budget"),
        ({"maxMemoryMiB": 769}, "budget_exceeds_host"),
        ({"maxDurationSeconds": 301}, "budget_exceeds_host"),
        ({"maxCpuSeconds": 301}, "budget_exceeds_host"),
        ({"maxOutputBytes": 16 * 1024 + 1}, "budget_exceeds_host"),
        ("maxMemoryMiB=1", "invalid_budget"),
    ],
)
def test_budgets_cannot_inject_or_exceed(budgets, code):
    with pytest.raises(SandboxRefused) as caught:
        limits_for(config(), budgets)
    assert caught.value.code == code


def test_fractional_budgets_round_up_and_unrelated_keys_are_ignored():
    limits = limits_for(config(), {"maxMemoryMiB": 100.2, "maxCases": 10, "maxCostUsd": 0})
    assert limits.memory_mib == 101


@pytest.mark.parametrize(
    "digest",
    [OTHER, "sha256:" + "A" * 64, DIGEST + " --privileged", "--privileged", DIGEST[7:], "latest", None, 7, f"x@{DIGEST}"],
)
def test_image_must_be_an_allowlisted_digest(digest):
    cfg = config()
    with pytest.raises(SandboxRefused) as caught:
        build_argv(cfg, digest, limits_for(cfg, {}), NAME)
    assert caught.value.code == "image_not_allowed"


@pytest.mark.parametrize("name", ["fm-sbx-x", "--privileged", "fm-sbx-" + "0" * 32 + " --rm"])
def test_container_name_is_launcher_generated(name):
    cfg = config()
    with pytest.raises(SandboxRefused):
        build_argv(cfg, DIGEST, limits_for(cfg, {}), name)


@pytest.mark.parametrize(
    "overrides",
    [
        {"repository": "ghcr.io/adhit-r/runner:latest"},
        {"repository": "--privileged"},
        {"repository": "ghcr.io/x y"},
        {"repository": f"ghcr.io/adhit-r/runner@{DIGEST}"},
        {"allowed_digests": frozenset()},
        {"allowed_digests": frozenset({"latest"})},
        {"docker_host": "tcp://10.0.0.1:2375"},
        {"docker_cli": "docker"},
        {"seccomp_profile": "unconfined"},
        {"seccomp_profile": "/etc/x,y"},
        {"cpus": 0},
        {"max_memory_mib": 32},
        {"max_processes": True},
        {"max_output_bytes": 1 << 20},
    ],
)
def test_host_config_fails_closed(overrides):
    with pytest.raises(SandboxUnavailable):
        config(**overrides)


def settings(**overrides):
    values = dict(
        sandbox_launcher_enabled=True,
        sandbox_docker_cli="/usr/bin/docker",
        sandbox_docker_host="unix:///run/user/1001/docker.sock",
        sandbox_require_rootless=True,
        sandbox_runner_repository="ghcr.io/adhit-r/fairmind-eval-runner",
        sandbox_runner_digests=f"{DIGEST}, {OTHER}",
        sandbox_seccomp_profile=str(SECCOMP),
        sandbox_cpus=1.0,
        sandbox_max_memory_mib=768,
        sandbox_max_processes=64,
        sandbox_max_duration_seconds=300,
        sandbox_max_disk_mib=64,
        sandbox_max_input_bytes=32 * 1024 * 1024,
        sandbox_max_output_bytes=16 * 1024,
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def test_from_settings_is_off_by_default_and_checks_the_profile_exists():
    assert SandboxConfig.from_settings(settings()).allowed_digests == {DIGEST, OTHER}
    with pytest.raises(SandboxUnavailable):
        SandboxConfig.from_settings(settings(sandbox_launcher_enabled=False))
    with pytest.raises(SandboxUnavailable):
        SandboxConfig.from_settings(settings(sandbox_seccomp_profile="/nonexistent/profile.json"))
    with pytest.raises(SandboxUnavailable):
        SandboxConfig.from_settings(settings(sandbox_runner_digests=""))


def test_settings_defaults_keep_the_launcher_off():
    from config.settings import Settings

    assert Settings.model_fields["sandbox_launcher_enabled"].default is False
    assert Settings.model_fields["sandbox_require_rootless"].default is True


RESULT = {"v": 1, "engine": "EV-TST-01", "status": "passed", "metrics": {"accuracy": 0.9, "metric": "accuracy", "r2": None}}


def line(value):
    return (json.dumps(value) + "\n").encode()


def test_parser_accepts_the_two_closed_shapes():
    assert parse_runner_output(line(RESULT)) == RESULT
    assert parse_runner_output(line({"v": 1, "error": "input_invalid"})) == {"v": 1, "error": "input_invalid"}


@pytest.mark.parametrize(
    "raw",
    [
        line(RESULT) * 2,  # two lines
        line(RESULT)[:-1],  # no newline
        line(RESULT) + b"x",  # data after the line
        b"\n" + line(RESULT),
        line(RESULT).replace(b"\n", b"\r\n"),
        b'{"v":1,"v":1,"error":"input_invalid"}\n',  # duplicate top-level key
        b'{"v":1,"engine":"EV-TST-01","status":"passed","metrics":{"a":1,"a":2}}\n',  # duplicate nested key
        b'{"v":1,"engine":"EV-TST-01","status":"passed","metrics":{"a":NaN}}\n',
        b'{"v":1,"engine":"EV-TST-01","status":"passed","metrics":{"a":Infinity}}\n',
        b'{"v":1,"engine":"EV-TST-01","status":"passed","metrics":{"a":-Infinity}}\n',
        b'{"v":1,"engine":"EV-TST-01","status":"passed","metrics":{"a":1e999}}\n',
        line({**RESULT, "detail": []}),
        line({**RESULT, "status": "succeeded"}),
        line({**RESULT, "v": True}),
        line({**RESULT, "v": 2}),
        line({**RESULT, "engine": "../x"}),
        line({**RESULT, "metrics": {"a": {"nested": 1}}}),
        line({**RESULT, "metrics": {"a": True}}),
        line({**RESULT, "metrics": {"a": "x" * 65}}),
        line({**RESULT, "metrics": {str(i): i for i in range(33)}}),
        line({"v": 1, "error": "anything else"}),
        line([RESULT]),
        b"\xff\xfe\n",
        b"not json\n",
        b"[" * 5000 + b"]" * 5000 + b"\n",
    ],
)
def test_parser_rejects_everything_else(raw):
    with pytest.raises(RunnerOutputInvalid):
        parse_runner_output(raw)


def test_parser_rejects_oversize_output():
    big = line({**RESULT, "metrics": {f"k{i}": "x" * 60 for i in range(32)}})
    assert len(big) > 1024
    with pytest.raises(RunnerOutputInvalid):
        parse_runner_output(big, cap=1024)
    with pytest.raises(RunnerOutputInvalid):
        parse_runner_output(b" " * (64 * 1024) + line(RESULT), cap=1 << 30)


def test_seccomp_profile_starts_from_docker_default_and_denies_more():
    profile = json.loads(SECCOMP.read_text())
    assert profile["defaultAction"] == "SCMP_ACT_ERRNO"
    allowed = {n for rule in profile["syscalls"] if rule["action"] == "SCMP_ACT_ALLOW" for n in rule["names"]}
    for denied in ("ptrace", "process_vm_readv", "process_vm_writev", "memfd_create", "memfd_secret", "execveat",
                   "name_to_handle_at", "open_by_handle_at", "splice", "tee", "vmsplice", "bpf", "perf_event_open",
                   "unshare", "setns", "mount", "kexec_load", "init_module", "keyctl", "io_uring_setup", "userfaultfd"):
        assert denied not in allowed, denied
    assert not any("caps" in (rule.get("includes") or {}) for rule in profile["syscalls"])
    # glibc falls back from clone3 to clone only when clone3 returns ENOSYS.
    assert any(r["names"] == ["clone3"] and r["action"] == "SCMP_ACT_ERRNO" and r.get("errnoRet") == 38 for r in profile["syscalls"])
    assert {"read", "write", "mmap", "futex", "execve", "clone", "exit_group"} <= allowed
