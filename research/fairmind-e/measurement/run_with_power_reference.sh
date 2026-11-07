#!/usr/bin/env bash
# Run the measurement suite with an independent power reference sampling
# alongside it, then integrate and calibrate.
#
# One privileged step: powermetrics needs root, so this asks for sudo once and
# elevates ONLY the sampler. The workload harness runs as the normal user, so
# nothing being measured gains privileges.
#
#   bash research/fairmind-e/measurement/run_with_power_reference.sh [BASELINE_WATTS]
#
# Stop it at any time with Ctrl-C; the sampler is cleaned up on exit.

set -euo pipefail

BASELINE_W="${1:-}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
RESULTS="${REPO_ROOT}/research/fairmind-e/results/measurement"
POWER_LOG="${POWER_LOG:-${HOME}/fairmind-power.txt}"
RUNS_CSV="${RESULTS}/m1_runs_ref.csv"
REF_CSV="${RESULTS}/m1_power_reference.csv"
CALIB_JSON="${RESULTS}/m1_calibration.json"

mkdir -p "${RESULTS}"

echo "Repo:        ${REPO_ROOT}"
echo "Power log:   ${POWER_LOG}"
echo "Runs CSV:    ${RUNS_CSV}"
echo
echo "powermetrics needs root. Only the sampler is elevated; the workloads are not."
sudo -v

# One sudo call starts powermetrics under a small root-side watcher. The watcher
# stops the sampler when the user-owned stop file disappears or this script
# exits, so stopping needs no second sudo (and no credential keep-alive loop).
STOP_FILE="$(mktemp -t fairmind-power-stop)"
SAMPLER_PID=""
cleanup() {
  if [[ -n "${SAMPLER_PID}" ]]; then
    echo
    echo "Stopping power sampler..."
    rm -f "${STOP_FILE}"
    wait "${SAMPLER_PID}" 2>/dev/null || true
    SAMPLER_PID=""
  fi
  rm -f "${STOP_FILE}"
}
trap cleanup EXIT INT TERM

echo "Starting power sampler at 200 ms..."
sudo /bin/sh -c '
  powermetrics --samplers cpu_power,gpu_power -i 200 -o "$1" &
  sampler=$!
  while [ -e "$2" ] && kill -0 "$3" 2>/dev/null && kill -0 "$sampler" 2>/dev/null; do
    sleep 1
  done
  kill "$sampler" 2>/dev/null
  wait "$sampler" 2>/dev/null
' fairmind-power "${POWER_LOG}" "${STOP_FILE}" "$$" &
SAMPLER_PID=$!

# Let the sampler settle so the first run is fully covered.
sleep 3
if ! ps -p "${SAMPLER_PID}" >/dev/null 2>&1; then
  echo "Power sampler failed to start; aborting rather than producing a study with no reference." >&2
  exit 1
fi

echo "Running the measurement suite (this takes roughly 30 minutes)..."
cd "${REPO_ROOT}/apps/backend"
uv run python ../../research/fairmind-e/measurement/harness.py \
    --workload all \
    --iterations 5 \
    --region IND \
    --seed 1337 \
    --config-overrides ../../research/fairmind-e/measurement/overrides_m1.json \
    --gap-seconds "${GAP_SECONDS:-20}" \
    --output "${RUNS_CSV}"

# Keep sampling briefly past the last run so its window is fully covered.
sleep 3
cleanup

echo
echo "Integrating the power log over each run window..."
BASELINE_ARGS=()
if [[ -n "${BASELINE_W}" ]]; then
  BASELINE_ARGS=(--baseline-w "${BASELINE_W}")
fi
uv run python ../../research/fairmind-e/measurement/power_reference.py \
    --log "${POWER_LOG}" \
    --runs "${RUNS_CSV}" \
    ${BASELINE_ARGS[@]+"${BASELINE_ARGS[@]}"} \
    --out "${REF_CSV}"

echo
echo "Calibrating assigned confidence against the reference..."
uv run python ../../research/fairmind-e/analysis/calibrate_confidence.py \
    --runs "${RUNS_CSV}" \
    --reference "${REF_CSV}" \
    --out "${CALIB_JSON}"

echo
echo "Done. Artifacts:"
echo "  runs        ${RUNS_CSV}"
echo "  reference   ${REF_CSV}"
echo "  calibration ${CALIB_JSON}"
echo "  power log   ${POWER_LOG}  (archive this with the results)"
