# eval-runner

The container image that runs one FairMind evaluation inside the sandbox (P1 plan, slice S4). It holds
python 3.11 on distroless Debian 12, the hash-locked wheels in `requirements.txt` (numpy, pandas,
scipy, scikit-learn and their dependencies; no TensorFlow, boto3, database driver, pip, shell or
network tools) and a copy of the two backend engine modules EV-TST-01 needs
(`eval_engines/common.py` and `eval_engines/model.py`). It runs as UID/GID 65532.

```bash
docker build --build-context engines=apps/backend/src/application/services/eval_engines \
  -t fairmind-eval-runner apps/eval-runner
```

## Protocol

`runner.py` takes no arguments and no environment. stdin is an uncompressed tar holding exactly
`request.json` (`{"v": 1, "engine": "EV-TST-01", "params": {...}}`) and one regular file
`inputs/<slot>` per slot the engine declares. Links, directories, unknown or repeated names,
unknown params and oversize input are refused. stdout is exactly one JSON line, at most 16 KiB:

- `{"v":1,"engine":"EV-TST-01","status":"passed|failed|insufficient","metrics":{...}}`
- `{"v":1,"error":"input_invalid|input_too_large|unsupported_engine|engine_failed|output_too_large"}`

Only an allowlist of numeric metrics leaves the sandbox. Per-class detail rows, summaries and
engine error messages stay inside, because they can carry labels or column names from the data.
The launcher (`apps/backend/src/infrastructure/sandbox/launcher.py`) parses the line again and
rejects anything else.

## Seccomp profile

`seccomp/sandbox.json` is Docker's default profile from
[moby/profiles](https://github.com/moby/profiles) `seccomp/default.json` at commit
`6fe7deb1b9fb7c0397a4593480d7d22b9ee8caef` (file sha256 `6416b477...3053f6`), with these removed
from the allow rules:

| Removed | Why |
|---|---|
| The kernel >= 4.8 rule allowing `ptrace`, `process_vm_readv`, `process_vm_writev` | Reading or writing another process's memory; no engine needs it |
| Every rule gated on a capability (`CAP_SYS_ADMIN`, `CAP_SYS_PTRACE`, `CAP_BPF`, `CAP_PERFMON`, `CAP_SYS_MODULE`, `CAP_SYS_TIME`, `CAP_SYS_NICE`, ...) | The launcher always passes `--cap-drop=ALL`, so these are dead; removing them keeps the profile safe even if that flag were ever lost |
| `memfd_create`, `memfd_secret` | Anonymous executable memory files bypass the noexec `/tmp` |
| `execveat` | Executes from a file descriptor, the other half of fileless execution |
| `name_to_handle_at` | File-handle probing, the first step of the open_by_handle_at container escape |
| `splice`, `tee`, `vmsplice` | Pipe page-cache primitives behind past privilege escalations (Dirty Pipe); numpy and pandas do not use them |

Kept on purpose: the argument-filtered `clone` rule and the `clone3` rule that returns ENOSYS, so
glibc falls back to `clone` without namespace flags. The default action stays `SCMP_ACT_ERRNO`
(EPERM). io_uring and userfaultfd are already absent upstream. To refresh it from a newer upstream
file, apply the same removals and run `tests/test_sandbox_launcher.py`, which asserts them.

## Publishing (left for the owner)

The plan has release.yml push this image to ghcr by digest with an SBOM and provenance, and write
that digest into the suite version's `runner_image_digest`. This branch does not change
release.yml; the CI lane in `.github/workflows/tests.yml` only builds the image and pushes it to a
throwaway local registry to test it.
