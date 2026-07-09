#!/usr/bin/env python3
"""Compatibility entrypoint for the FairMind-E deterministic smoke harness."""

from __future__ import annotations

import argparse
import importlib.util
import pathlib


def _load_runner():
    root = pathlib.Path(__file__).resolve().parent
    module_path = root / "scripts" / "run_smoke.py"
    spec = importlib.util.spec_from_file_location("fairmind_e_run_smoke", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load harness runner at {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(argv: list[str] | None = None) -> int:
    root = pathlib.Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=pathlib.Path, help="Run one workload config")
    parser.add_argument("--config-dir", type=pathlib.Path, default=root / "configs")
    parser.add_argument("--output-root", type=pathlib.Path, default=root)
    args = parser.parse_args(argv)

    runner = _load_runner()
    if args.config:
        with args.config.open(encoding="utf-8") as handle:
            import json

            config = json.load(handle)
        rows = runner.write_csv(args.output_root, config)
        runner.write_summary_svg(args.output_root, rows)
        runner.write_gate_svg(args.output_root, rows)
        return 0
    return runner.run(args.config_dir, args.output_root)


if __name__ == "__main__":
    raise SystemExit(main())
