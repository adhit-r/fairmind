"""The sandbox confinement, checked against a real Docker daemon and the built apps/eval-runner image.

Skipped unless FAIRMIND_SANDBOX_IT_IMAGE names the image as <repository>@sha256:<digest> (the
sandbox job in .github/workflows/tests.yml pushes it to a local registry to get one). Probes run
through SandboxLauncher.run with the same fixed argv; only the entrypoint is swapped for a Python
probe whose findings come back as metrics on the runner's own result line.
"""

import io
import json
import os
import shutil
import subprocess
import tarfile
import time
from pathlib import Path

import pytest

from src.infrastructure.sandbox import launcher as launcher_module
from src.infrastructure.sandbox.launcher import LABEL_FILTER, SandboxConfig, SandboxLauncher

IMAGE = os.environ.get("FAIRMIND_SANDBOX_IT_IMAGE", "")
pytestmark = pytest.mark.skipif("@sha256:" not in IMAGE, reason="FAIRMIND_SANDBOX_IT_IMAGE is not set")

SECCOMP = Path(__file__).resolve().parents[2] / "eval-runner" / "seccomp" / "sandbox.json"
PYTHON = "/usr/bin/python3.11"


@pytest.fixture(scope="module")
def config():
    repository, digest = IMAGE.split("@")
    return SandboxConfig(
        docker_cli=shutil.which("docker"),
        docker_host=os.environ.get("DOCKER_HOST", "unix:///var/run/docker.sock"),
        require_rootless=os.environ.get("FAIRMIND_SANDBOX_IT_ROOTLESS") == "1",
        repository=repository,
        allowed_digests=frozenset({digest}),
        seccomp_profile=str(SECCOMP),
        cpus=1.0,
        max_memory_mib=256,
        max_processes=32,
        max_duration_seconds=60,
        max_disk_mib=16,
        max_input_bytes=1024 * 1024,
        max_output_bytes=16 * 1024,
    )


@pytest.fixture
def sandbox(config):
    launcher = SandboxLauncher(config)
    launcher.start()
    yield launcher
    assert orphans(config) == [], "a sandbox container outlived its run"


def orphans(config):
    listed = subprocess.run(
        [config.docker_cli, "ps", "--all", "--quiet", "--filter", LABEL_FILTER],
        capture_output=True, text=True, check=True, env={**os.environ, "DOCKER_HOST": config.docker_host},
    )
    return listed.stdout.split()


def digest():
    return IMAGE.split("@")[1]


def probe(monkeypatch, code):
    """Runs `code` in place of the runner, under the unchanged argv; it prints one result line."""
    original = launcher_module.build_argv

    def with_probe(*args, **kwargs):
        argv = original(*args, **kwargs)
        return argv[:-1] + [f"--entrypoint={PYTHON}", argv[-1], "-c", code]

    monkeypatch.setattr(launcher_module, "build_argv", with_probe)


REPORT = """
import json, sys
def report(**facts):
    sys.stdout.write(json.dumps({"v": 1, "engine": "EV-TST-01", "status": "passed", "metrics": facts}) + "\\n")
"""


def test_real_runner_evaluates_a_tar(sandbox):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        for name, data in (
            ("request.json", json.dumps({"v": 1, "engine": "EV-TST-01", "params": {"baseline": 0.5}}).encode()),
            ("inputs/predictions", b"y_true,y_pred\n1,1\n0,0\n1,0\n1,1\n"),
        ):
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
    result = sandbox.run(digest(), {}, buffer.getvalue())
    assert result.outcome == "completed", result
    assert result.output["status"] == "passed" and result.output["metrics"]["accuracy"] == 0.75


def test_real_runner_refuses_a_link(sandbox):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        info = tarfile.TarInfo("inputs/predictions")
        info.type, info.linkname = tarfile.SYMTYPE, "/etc/passwd"
        archive.addfile(info)
    result = sandbox.run(digest(), {}, buffer.getvalue())
    assert result.outcome == "completed" and result.output == {"v": 1, "error": "input_invalid"}


def test_root_filesystem_is_read_only_and_tmp_is_noexec(sandbox, monkeypatch):
    probe(monkeypatch, REPORT + """
import errno, os
def write(path):
    try:
        open(path, "w").write("x")
        return 0
    except OSError as e:
        return e.errno
open("/tmp/probe", "w").write("#!/usr/bin/python3.11\\n")
os.chmod("/tmp/probe", 0o755)
try:
    os.execv("/tmp/probe", ["/tmp/probe"])
except OSError as e:
    exec_errno = e.errno
report(etc=write("/etc/probe"), opt=write("/opt/runner/probe"), root=write("/probe"), tmp_exec=exec_errno, erofs=errno.EROFS)
""")
    result = sandbox.run(digest(), {}, b"")
    assert result.outcome == "completed", result
    m = result.output["metrics"]
    assert m["etc"] == m["opt"] == m["root"] == m["erofs"] == 30
    assert m["tmp_exec"] == 13  # EACCES: the tmpfs is noexec


def test_no_network_beyond_loopback(sandbox, monkeypatch):
    probe(monkeypatch, REPORT + """
import os, socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    s.connect(("1.1.1.1", 53)); s.send(b"x"); reached = 1
except OSError:
    reached = 0
report(interfaces=",".join(sorted(os.listdir("/sys/class/net"))), reached=reached)
""")
    result = sandbox.run(digest(), {}, b"")
    assert result.outcome == "completed", result
    assert result.output["metrics"] == {"interfaces": "lo", "reached": 0}


def test_runs_as_65532_with_no_capabilities(sandbox, monkeypatch):
    probe(monkeypatch, REPORT + """
import os
status = dict(line.split(":", 1) for line in open("/proc/self/status").read().splitlines() if ":" in line)
report(uid=os.getuid(), gid=os.getgid(), groups=len(os.getgroups()),
       **{k: int(status[k].strip(), 16) for k in ("CapInh", "CapPrm", "CapEff", "CapBnd", "CapAmb")},
       nnp=int(status["NoNewPrivs"]), seccomp=int(status["Seccomp"]))
""")
    result = sandbox.run(digest(), {}, b"")
    assert result.outcome == "completed", result
    m = result.output["metrics"]
    assert (m["uid"], m["gid"]) == (65532, 65532)
    assert m["CapInh"] == m["CapPrm"] == m["CapEff"] == m["CapBnd"] == m["CapAmb"] == 0
    assert m["nnp"] == 1 and m["seccomp"] == 2


def test_denied_syscalls_fail(sandbox, monkeypatch):
    probe(monkeypatch, REPORT + """
import os
try:
    os.memfd_create("x"); memfd = 0
except OSError as e:
    memfd = e.errno
report(memfd=memfd)
""")
    result = sandbox.run(digest(), {}, b"")
    assert result.outcome == "completed", result
    assert result.output["metrics"]["memfd"] == 1  # EPERM from the profile


def test_pids_limit_stops_a_fork_bomb(sandbox, monkeypatch):
    probe(monkeypatch, REPORT + """
import os, time
children = 0
try:
    while children < 1000:
        if os.fork() == 0:
            time.sleep(60); os._exit(0)
        children += 1
    blocked = 0
except OSError:
    blocked = 1
report(children=children, blocked=blocked)
""")
    result = sandbox.run(digest(), {"maxProcesses": 16, "maxDurationSeconds": 20}, b"")
    assert result.outcome == "completed", result
    assert result.output["metrics"]["blocked"] == 1 and result.output["metrics"]["children"] < 16


def test_memory_limit_kills_the_sandbox(sandbox, monkeypatch):
    probe(monkeypatch, "blocks = []\nwhile True:\n    blocks.append(b\"x\" * (16 * 1024 * 1024))\n")
    result = sandbox.run(digest(), {"maxMemoryMiB": 96, "maxDurationSeconds": 30}, b"")
    assert result.outcome == "oom", result


def test_wall_clock_kills_the_sandbox(sandbox, monkeypatch):
    probe(monkeypatch, "import time\ntime.sleep(600)\n")
    started = time.monotonic()
    result = sandbox.run(digest(), {"maxDurationSeconds": 3}, b"")
    assert result.outcome == "timeout", result
    assert time.monotonic() - started < 3 + 35


def test_cpu_limit_kills_a_spinning_process(sandbox, monkeypatch):
    probe(monkeypatch, "while True:\n    pass\n")
    result = sandbox.run(digest(), {"maxCpuSeconds": 2, "maxDurationSeconds": 30}, b"")
    assert result.outcome == "crashed", result  # SIGKILL from RLIMIT_CPU, well before the wall clock


def test_oversize_output_is_rejected(sandbox, monkeypatch):
    probe(monkeypatch, "import sys\nsys.stdout.write('x' * 100000)\n")
    result = sandbox.run(digest(), {"maxOutputBytes": 1024}, b"")
    assert result.outcome == "output_invalid", result


def test_reaper_removes_labelled_orphans(config):
    started = subprocess.run(
        [config.docker_cli, "run", "--detach", "--label=io.fairmind.sandbox=1", "--network=none",
         f"--entrypoint={PYTHON}", IMAGE, "-c", "import time; time.sleep(600)"],
        capture_output=True, text=True, env={**os.environ, "DOCKER_HOST": config.docker_host},
    )
    assert started.returncode == 0, started.stderr
    assert SandboxLauncher(config).start() >= 1
    assert orphans(config) == []
