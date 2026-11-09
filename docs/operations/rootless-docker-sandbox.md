# Rootless Docker sandbox on the Lightsail host

Runbook for P1 slice S4, owner decision 2026-11-08: evaluation sandboxes run under a second,
rootless Docker daemon on the same Lightsail box as the app (`deploy/lightsail`). Nothing here has
been run. Do it by hand, in order, and check each step before going on.

The trade-off was accepted knowingly: a kernel exploit from inside a sandbox lands on the box that
holds the Neon production credentials. What this setup does guarantee is that the sandbox runs as
an unprivileged host user, cannot reach the network, cannot see the app's Docker daemon, and can
never take memory from the backend.

## What runs where

| Piece | Runs as | Can reach |
|---|---|---|
| App stack (backend, frontend, cloudflared) | rootful Docker, user `ubuntu` | unchanged |
| Rootless Docker daemon | host user `fmsandbox`, its own user namespace | its socket `/run/user/<uid>/docker.sock`, mode 0600, owned by `fmsandbox` |
| Launcher / supervisor (S5) | host user `fmworker`, never `fmsandbox` | the rootless socket (through one ACL entry, step 7) and the API |
| Sandbox containers | UID 65532 inside, a subordinate UID of `fmsandbox` outside | nothing: `--network=none`, no mounts |

The app's compose file never mounts the rootless socket, and neither `fmsandbox` nor `fmworker` is
in the `docker` group, so the sandbox daemon and the app daemon cannot reach each other.

The supervisor holds the service token, the lease credential and the IAM access key that may call
`kms:Sign`, so it must not share a host UID with the rootless daemon. Under rootless Docker,
container root and the daemon both map to host UID `fmsandbox`: a sandbox that escapes to container
root through a runc or containerd bug is `fmsandbox` on the host. If the supervisor ran as
`fmsandbox` too, that attacker could read its `/proc/<pid>/environ` and memory and sign forged
Passports. As `fmworker` it is a different UID, so `fmsandbox` cannot ptrace it, read its
environment or read its environment file. What such an attacker still has is the daemon, so it
could forge a container's stdout; the supervisor already treats that output as hostile.

## Memory budget

The box has 2 GB of RAM and 4 GB of swap (`deploy/lightsail/README.md`). The backend (TensorFlow)
relies on swap. The sandbox side gets a hard cap and no swap at all, so under pressure the kernel
kills a sandbox, never the backend:

| Item | Cap | Where it is set |
|---|---|---|
| Everything `fmsandbox` runs (rootless dockerd, containerd, rootlesskit, sandboxes) | 900 MiB RAM, 0 swap, 512 tasks, 1 CPU | `user-<uid>.slice`, step 6 |
| One sandbox container | 512 MiB RAM, memory-swap equal to memory (no swap), 64 pids, 1 CPU, 300 s wall clock | `SANDBOX_MAX_*` settings; the launcher refuses budgets above them |
| Concurrency | one sandbox at a time | the supervisor (S5) runs attempts one by one |
| Backend and the rest of the app | about 1.1 GiB RAM plus all 4 GB of swap | unchanged |

Every sandbox also runs with `--oom-score-adj=1000`, so if the whole host ever runs out of memory
the kernel's first choice is the sandbox. Do not raise `SANDBOX_MAX_MEMORY_MIB` above about
`900 - 250` MiB without raising the slice cap, and do not raise the slice cap without moving to a
bigger bundle.

## Setup

Run as `ubuntu` with sudo unless a step says otherwise. Ubuntu 24.04, Docker installed by
get.docker.com (which includes `docker-ce-rootless-extras`).

1. Packages and the user:

   ```bash
   sudo apt-get install -y uidmap dbus-user-session systemd-container acl
   sudo useradd --create-home --shell /bin/bash fmsandbox
   sudo useradd --system --create-home --shell /usr/sbin/nologin fmworker   # the supervisor; no subuid range needed
   grep fmsandbox /etc/subuid /etc/subgid   # both must list a range of 65536 or more
   ```

2. Ubuntu 24.04 blocks unprivileged user namespaces through AppArmor. Allow them for rootlesskit
   only, not system-wide:

   ```bash
   sudo tee /etc/apparmor.d/usr.bin.rootlesskit >/dev/null <<'EOF'
   abi <abi/4.0>,
   include <tunables/global>

   /usr/bin/rootlesskit flags=(unconfined) {
     userns,
     include if exists <local/usr.bin.rootlesskit>
   }
   EOF
   sudo systemctl restart apparmor
   ```

3. Delegate the cgroup v2 controllers to user sessions, without which Docker silently ignores
   `--memory`, `--pids-limit` and `--cpus` (the launcher's `check_host` refuses to start then):

   ```bash
   sudo mkdir -p /etc/systemd/system/user@.service.d
   printf '[Service]\nDelegate=cpu cpuset io memory pids\n' | sudo tee /etc/systemd/system/user@.service.d/delegate.conf
   sudo systemctl daemon-reload
   ```

4. Keep the user's services running without a login:

   ```bash
   sudo loginctl enable-linger fmsandbox
   ```

5. Install the rootless daemon as `fmsandbox`:

   ```bash
   sudo machinectl shell fmsandbox@ /bin/bash -lc 'dockerd-rootless-setuptool.sh install && systemctl --user enable --now docker'
   ```

6. Cap the user's whole slice (step "Memory budget"):

   ```bash
   UID_SBX=$(id -u fmsandbox)
   sudo systemctl set-property user-$UID_SBX.slice MemoryMax=900M MemorySwapMax=0 TasksMax=512 CPUQuota=100%
   ```

7. Let `fmworker` reach the rootless socket and nothing else of `fmsandbox`'s. One ACL entry on the
   runtime directory (search only) and one on the socket, set again every time the daemon starts,
   because `/run/user/<uid>` is a tmpfs and the socket is recreated:

   ```bash
   sudo -u fmsandbox mkdir -p ~fmsandbox/.config/systemd/user/docker.service.d
   sudo -u fmsandbox tee ~fmsandbox/.config/systemd/user/docker.service.d/fmworker-socket.conf >/dev/null <<'EOF'
   [Service]
   ExecStartPost=/usr/bin/timeout 30 /bin/sh -c "until [ -S %t/docker.sock ]; do sleep 0.2; done"
   ExecStartPost=/usr/bin/setfacl -m u:fmworker:x %t
   ExecStartPost=/usr/bin/setfacl -m u:fmworker:rw %t/docker.sock
   EOF
   sudo machinectl shell fmsandbox@ /bin/bash -lc 'systemctl --user daemon-reload && systemctl --user restart docker'
   ```

   `fmsandbox` owns this drop-in and could remove the ACL, but that only stops sandboxes; it gives
   it nothing of `fmworker`'s.

8. Check the daemon. All of these must hold:

   ```bash
   sudo machinectl shell fmsandbox@ /bin/bash -lc \
     'DOCKER_HOST=unix:///run/user/$(id -u)/docker.sock docker info --format "{{.SecurityOptions}} {{.CgroupVersion}} {{.MemoryLimit}} {{.SwapLimit}} {{.PidsLimit}} {{.CpuCfsQuota}}"'
   # expect: [... name=seccomp,profile=builtin name=rootless name=cgroupns] 2 true true true true
   cat /sys/fs/cgroup/user.slice/user-$UID_SBX.slice/user@$UID_SBX.service/cgroup.controllers
   # expect at least: cpu io memory pids
   ls -l /run/user/$UID_SBX/docker.sock   # owner fmsandbox, no access for other
   getfacl -p /run/user/$UID_SBX/docker.sock   # user:fmworker:rw- is the only named entry, other::---
   sudo -u fmworker env DOCKER_HOST=unix:///run/user/$UID_SBX/docker.sock docker info --format '{{.SecurityOptions}}'
   # expect the same options as above, from fmworker
   ```

9. Install the seccomp profile root-owned so the sandbox user cannot change it:

   ```bash
   sudo install -D -o root -g root -m 0644 apps/eval-runner/seccomp/sandbox.json /etc/fairmind/sandbox-seccomp.json
   ```

10. Pull the runner image by digest (the launcher runs with `--pull=never` and only accepts
    allowlisted digests):

   ```bash
   sudo machinectl shell fmsandbox@ /bin/bash -lc \
     'DOCKER_HOST=unix:///run/user/$(id -u)/docker.sock docker pull ghcr.io/adhit-r/fairmind-eval-runner@sha256:<digest>'
   ```

11. Launcher settings go in `/etc/fairmind/worker.env`, owned by root with mode 0600. systemd reads
    it for the supervisor's unit (`User=fmworker`, `EnvironmentFile=/etc/fairmind/worker.env`; the
    unit ships with S5), so the service token and the KMS IAM key that S5 adds there stay out of
    `fmsandbox`'s reach. Never put any of it in the app's `.env`.

    ```bash
    SANDBOX_LAUNCHER_ENABLED=true
    SANDBOX_DOCKER_CLI=/usr/bin/docker
    SANDBOX_DOCKER_HOST=unix:///run/user/<fmsandbox uid>/docker.sock
    SANDBOX_REQUIRE_ROOTLESS=true
    SANDBOX_RUNNER_REPOSITORY=ghcr.io/adhit-r/fairmind-eval-runner
    SANDBOX_RUNNER_DIGESTS=sha256:<digest>
    SANDBOX_SECCOMP_PROFILE=/etc/fairmind/sandbox-seccomp.json
    SANDBOX_MAX_MEMORY_MIB=512
    SANDBOX_MAX_PROCESSES=64
    SANDBOX_MAX_DURATION_SECONDS=300
    SANDBOX_MAX_DISK_MIB=64
    ```

    Check: `sudo -u fmsandbox cat /etc/fairmind/worker.env` must fail with permission denied.

    On start the launcher checks the daemon (rootless, cgroup v2, seccomp, limits enforced) and
    removes every container labelled `io.fairmind.sandbox=1`; `run()` refuses until that start has
    succeeded. Before every run it removes labelled containers again (sandboxes run one at a time),
    and it refuses to launch while one survives, so a failed cleanup cannot leak memory into the
    next run.

## Kill switches and removal

- Stop all sandboxes now: `sudo systemctl stop user@$(id -u fmsandbox).service`.
- Stop new ones: set `SANDBOX_LAUNCHER_ENABLED=false` and restart the supervisor.
- Remove: as `fmsandbox`, `systemctl --user disable --now docker && dockerd-rootless-setuptool.sh uninstall`,
  then `sudo loginctl disable-linger fmsandbox`, `sudo systemctl revert user-$(id -u fmsandbox).slice`,
  and delete `/etc/apparmor.d/usr.bin.rootlesskit` and `/etc/systemd/system/user@.service.d/delegate.conf`.
  Once the supervisor unit is gone, `sudo userdel --remove fmworker` and delete `/etc/fairmind/worker.env`.

## What CI proves and what it does not

The `sandbox` job in `.github/workflows/tests.yml` runs `apps/backend/tests/test_sandbox_docker.py`
against the runner image on the GitHub runner's default (rootful) Docker daemon with the same
launcher argv: EROFS on the root filesystem, noexec `/tmp`, only `lo`, UID 65532 with every
capability set empty, no-new-privileges and seccomp on, memfd_create denied, the pids, memory, CPU
and wall-clock kills, and zero orphans. Rootless mode is not exercised there: ubuntu-24.04 runners
need step 2's AppArmor change and a lingering user session to start a rootless daemon. The
launcher's refusals (not rootless, cgroup v1, no seccomp, a limit not enforced), the reaper, and
the outcome and cleanup mapping of `run()` are covered without Docker in the main backend job, by
`tests/test_sandbox_launcher.py` against a fake docker CLI. Run the
same test on the host after step 10 to cover it:

```bash
FAIRMIND_SANDBOX_IT_IMAGE=ghcr.io/adhit-r/fairmind-eval-runner@sha256:<digest> \
FAIRMIND_SANDBOX_IT_ROOTLESS=1 DOCKER_HOST=unix:///run/user/<uid>/docker.sock \
FAIRMIND_TEST_POSTGRES_URL=<a disposable test server, never production> \
uv run pytest -q tests/test_sandbox_docker.py
```
