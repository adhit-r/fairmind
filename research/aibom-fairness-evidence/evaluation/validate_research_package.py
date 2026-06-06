#!/usr/bin/env python3
"""Validate the AIBOM fairness evidence research package.

This check intentionally uses only the Python standard library. JSON Schema
validation remains documented in validation_notes.md for environments that can
run check-jsonschema.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any


PACKAGE_ROOT = Path("research/aibom-fairness-evidence")

PROFILE_PATHS = {
    "Loan Approval Model": PACKAGE_ROOT
    / "examples/loan_approval_fairness_profile.json",
    "Hiring Ranker": PACKAGE_ROOT / "examples/hiring_ranker_fairness_profile.json",
    "Healthcare Triage Model": PACKAGE_ROOT
    / "examples/healthcare_triage_fairness_profile.json",
}

BASELINE_PATHS = {
    "Loan Approval Model": PACKAGE_ROOT
    / "examples/cyclonedx_style_loan_approval_mlbom.json",
    "Hiring Ranker": PACKAGE_ROOT
    / "examples/cyclonedx_style_hiring_ranker_mlbom.json",
    "Healthcare Triage Model": PACKAGE_ROOT
    / "examples/cyclonedx_style_healthcare_triage_mlbom.json",
}

GENERIC_BASELINE_PATHS = {
    "Loan Approval Model": PACKAGE_ROOT / "examples/generic_loan_approval_mlbom.json",
    "Hiring Ranker": PACKAGE_ROOT / "examples/generic_hiring_ranker_mlbom.json",
    "Healthcare Triage Model": PACKAGE_ROOT
    / "examples/generic_healthcare_triage_mlbom.json",
}

REQUIRED_FILES = [
    PACKAGE_ROOT / "ARTIFACT_README.md",
    PACKAGE_ROOT / "README.md",
    PACKAGE_ROOT / "FAIRMIND_INTEGRATION.md",
    PACKAGE_ROOT / "AIBOM_FAIRNESS_EVIDENCE_PROFILE_PLAN.md",
    PACKAGE_ROOT / "schema/aibom_fairness_evidence.schema.json",
    PACKAGE_ROOT / "evaluation/fault_injection_cases.csv",
    PACKAGE_ROOT / "evaluation/analysis_plan.md",
    PACKAGE_ROOT / "evaluation/pilot_results.md",
    PACKAGE_ROOT / "evaluation/response_sheet_template.csv",
    PACKAGE_ROOT / "evaluation/reviewer_task_cards.md",
    PACKAGE_ROOT / "evaluation/study_protocol.md",
    PACKAGE_ROOT / "evaluation/validation_notes.md",
    PACKAGE_ROOT / "evaluation/validate_research_package.py",
    PACKAGE_ROOT / "paper/CLAIM_LEDGER.md",
    PACKAGE_ROOT / "paper/ROADMAP.md",
    PACKAGE_ROOT / "paper/draft.md",
    PACKAGE_ROOT / "paper/prior_art_matrix.md",
    PACKAGE_ROOT / "poster/poster_outline.md",
    PACKAGE_ROOT / "poster/soups_abstract.md",
    *GENERIC_BASELINE_PATHS.values(),
    *PROFILE_PATHS.values(),
    *BASELINE_PATHS.values(),
]

OLD_ARTIFACT_NAMES = {
    "Bias" + "BOM",
    "bias" + "bom",
    "Bias" + " " + "BOM",
    "BIAS" + "BOM",
    "cyclonedx_loan_approval_mlbom.json",
    "cyclonedx_hiring_ranker_mlbom.json",
    "cyclonedx_healthcare_triage_mlbom.json",
    "stronger_loan_approval_mlbom.json",
    "stronger_hiring_ranker_mlbom.json",
    "stronger_healthcare_triage_mlbom.json",
    "baseline_loan_approval_mlbom.json",
    "baseline_hiring_ranker_mlbom.json",
    "baseline_healthcare_triage_mlbom.json",
}

REQUIRED_FAULT_COLUMNS = {
    "case_id",
    "system",
    "component_id",
    "fault_type",
    "generic_bom_visible",
    "fairness_profile_visible",
    "expected_reviewer_action",
    "severity",
    "ground_truth_explanation",
}

PROFILE_ONLY_KEYS = {
    "claim_support",
    "component_fault_localization",
    "evidence_gap_type",
    "evidence_state_reason",
    "unknowns",
    "review_status",
    "validation_state",
    "evidence_freshness",
    "reviewer_action",
    "reviewer_required_action",
    "simulated_evidence_count",
    "stale_evidence_count",
}

REQUIRED_COMPONENT_FIELDS = {
    "claim_support",
    "evidence_gap_type",
    "evidence_state_reason",
    "component_fault_localization",
    "reviewer_required_action",
}

REQUIRED_RESPONSE_COLUMNS = {
    "pilot_id",
    "reviewer_id",
    "reviewer_background_category",
    "prior_fairness_review_experience",
    "prior_bom_or_supply_chain_review_experience",
    "system_id",
    "system_name",
    "task_id",
    "artifact_condition",
    "artifact_file",
    "artifact_order_index",
    "system_order_index",
    "task_start_time",
    "task_end_time",
    "elapsed_seconds",
    "artifact_block_start_time",
    "artifact_block_end_time",
    "artifact_block_elapsed_minutes",
    "decision",
    "risk_found",
    "localized_component_id",
    "localized_evidence_object_id",
    "evidence_gap_type",
    "unsupported_claim_accepted",
    "confidence_1_to_5",
    "rationale_text",
    "facilitator_notes",
    "ground_truth_fault_ids",
    "expected_decision",
    "expected_evidence_gap_type",
    "expected_component_id",
    "expected_evidence_object_id",
    "unsupported_claim_type",
    "correct_decision",
    "detection_correct",
    "localization_correct",
    "false_assurance",
    "claim_level_false_assurance",
    "rationale_support_level",
    "high_confidence_error",
    "qualitative_error_theme",
    "exclude_from_analysis",
    "exclusion_reason",
    "interrupted_task",
    "duplicate_repeated_exposure",
    "answer_key_exposed",
    "author_walkthrough",
}


def load_json(path: Path, errors: list[str]) -> Any | None:
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        errors.append(f"Missing JSON file: {path}")
    except json.JSONDecodeError as exc:
        errors.append(f"Invalid JSON in {path}: line {exc.lineno}, column {exc.colno}: {exc.msg}")
    return None


def iter_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        keys = set(value)
        for child in value.values():
            keys.update(iter_keys(child))
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for item in value:
            keys.update(iter_keys(item))
        return keys
    return set()


def is_missing(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def validate_required_files(errors: list[str]) -> None:
    for path in REQUIRED_FILES:
        if not path.is_file():
            errors.append(f"Required file missing: {path}")


def validate_example_json_parse(errors: list[str]) -> None:
    examples_dir = PACKAGE_ROOT / "examples"
    if not examples_dir.is_dir():
        errors.append(f"Examples directory missing: {examples_dir}")
        return

    json_paths = sorted(examples_dir.glob("*.json"))
    if not json_paths:
        errors.append(f"No example JSON files found in {examples_dir}")
        return

    for path in json_paths:
        load_json(path, errors)


def validate_old_artifact_names(errors: list[str]) -> None:
    if not PACKAGE_ROOT.exists():
        errors.append(f"Package root missing: {PACKAGE_ROOT}")
        return

    self_path = Path(__file__).resolve()
    for path in sorted(PACKAGE_ROOT.rglob("*")):
        path_text = path.as_posix()
        matched_in_path = sorted(name for name in OLD_ARTIFACT_NAMES if name in path_text)
        for name in matched_in_path:
            errors.append(f"Old artifact name appears in path: {name} in {path}")

        if not path.is_file() or path.resolve() == self_path:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for name in sorted(OLD_ARTIFACT_NAMES):
            if name in content:
                errors.append(f"Old artifact name appears in {path}: {name}")


def validate_profiles(errors: list[str]) -> dict[str, set[str]]:
    component_ids_by_system: dict[str, set[str]] = {}

    for expected_system, path in PROFILE_PATHS.items():
        profile = load_json(path, errors)
        if not isinstance(profile, dict):
            errors.append(f"{path} must contain a JSON object")
            continue

        system_name = profile.get("system_name")
        if system_name != expected_system:
            errors.append(
                f"{path} has system_name={system_name!r}; expected {expected_system!r}"
            )

        context = profile.get("fairmind_context")
        if not isinstance(context, dict) or context.get("platform_name") != "FairMind":
            errors.append(f"{path} missing fairmind_context.platform_name='FairMind'")

        components = profile.get("components")
        if not isinstance(components, list):
            errors.append(f"{path} components must be a list")
            continue
        if len(components) < 6:
            errors.append(f"{path} has {len(components)} components; expected at least 6")

        ids: set[str] = set()
        for index, component in enumerate(components, start=1):
            if not isinstance(component, dict):
                errors.append(f"{path} component #{index} must be a JSON object")
                continue

            component_id = component.get("component_id")
            if not isinstance(component_id, str) or not component_id:
                errors.append(f"{path} component #{index} missing non-empty component_id")
                component_label = f"component #{index}"
            else:
                component_label = component_id
                if component_id in ids:
                    errors.append(f"{path} duplicate component_id: {component_id}")
                ids.add(component_id)

            missing_fields = sorted(
                field
                for field in REQUIRED_COMPONENT_FIELDS
                if field not in component or is_missing(component.get(field))
            )
            if missing_fields:
                errors.append(
                    f"{path} {component_label} missing required component fields: "
                    f"{', '.join(missing_fields)}"
                )

        component_ids_by_system[expected_system] = ids

    return component_ids_by_system


def validate_fault_cases(
    component_ids_by_system: dict[str, set[str]], errors: list[str]
) -> None:
    path = PACKAGE_ROOT / "evaluation/fault_injection_cases.csv"
    if not path.is_file():
        errors.append(f"Fault case CSV missing: {path}")
        return

    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = set(reader.fieldnames or [])

    missing_columns = sorted(REQUIRED_FAULT_COLUMNS - fieldnames)
    extra_columns = sorted(fieldnames - REQUIRED_FAULT_COLUMNS)
    if missing_columns or extra_columns:
        errors.append(
            f"{path} column mismatch: missing={missing_columns}, extra={extra_columns}"
        )

    if len(rows) != 24:
        errors.append(f"{path} has {len(rows)} rows; expected exactly 24")

    for row_number, row in enumerate(rows, start=2):
        case_id = row.get("case_id") or f"row {row_number}"
        system = row.get("system")
        component_id = row.get("component_id")
        if system not in component_ids_by_system:
            errors.append(f"{path} {case_id} references unknown system: {system!r}")
            continue
        if component_id not in component_ids_by_system[system]:
            errors.append(
                f"{path} {case_id} references unknown component_id "
                f"{component_id!r} for {system}"
            )


def validate_generic_baselines(
    component_ids_by_system: dict[str, set[str]], errors: list[str]
) -> None:
    for system, path in GENERIC_BASELINE_PATHS.items():
        baseline = load_json(path, errors)
        if not isinstance(baseline, dict):
            errors.append(f"{path} must contain a JSON object")
            continue

        components = baseline.get("components")
        if not isinstance(components, list):
            errors.append(f"{path} components must be a list")
            continue
        if not components:
            errors.append(f"{path} has no components")

        baseline_ids = {
            component.get("component_id")
            for component in components
            if isinstance(component, dict)
        }
        non_string_ids = sorted(
            repr(value) for value in baseline_ids if not isinstance(value, str)
        )
        if non_string_ids:
            errors.append(f"{path} contains non-string component_id values: {non_string_ids}")
        baseline_ids = {value for value in baseline_ids if isinstance(value, str)}

        profile_ids = component_ids_by_system.get(system, set())
        missing = sorted(profile_ids - baseline_ids)
        extra = sorted(baseline_ids - profile_ids)
        if missing or extra:
            errors.append(
                f"{system} generic baseline component mismatch: "
                f"missing={missing}, extra={extra}"
            )

        leaked_keys = sorted(PROFILE_ONLY_KEYS & iter_keys(baseline))
        if leaked_keys:
            errors.append(f"{path} contains profile-only keys: {', '.join(leaked_keys)}")


def validate_baselines(
    component_ids_by_system: dict[str, set[str]], errors: list[str]
) -> None:
    for system, path in BASELINE_PATHS.items():
        baseline = load_json(path, errors)
        if not isinstance(baseline, dict):
            errors.append(f"{path} must contain a JSON object")
            continue

        if baseline.get("bomFormat") != "CycloneDX":
            errors.append(f"{path} bomFormat must be 'CycloneDX'")

        components = baseline.get("components")
        if not isinstance(components, list):
            errors.append(f"{path} components must be a list")
            continue
        if not components:
            errors.append(f"{path} has no components")

        baseline_ids = {
            component.get("bom-ref")
            for component in components
            if isinstance(component, dict)
        }
        non_string_ids = sorted(
            repr(value) for value in baseline_ids if not isinstance(value, str)
        )
        if non_string_ids:
            errors.append(f"{path} contains non-string bom-ref values: {non_string_ids}")
        baseline_ids = {value for value in baseline_ids if isinstance(value, str)}

        profile_ids = component_ids_by_system.get(system, set())
        missing = sorted(profile_ids - baseline_ids)
        extra = sorted(baseline_ids - profile_ids)
        if missing or extra:
            errors.append(
                f"{system} CycloneDX baseline component mismatch: "
                f"missing={missing}, extra={extra}"
            )

        leaked_keys = sorted(PROFILE_ONLY_KEYS & iter_keys(baseline))
        if leaked_keys:
            errors.append(f"{path} contains profile-only keys: {', '.join(leaked_keys)}")


def validate_response_template(errors: list[str]) -> None:
    path = PACKAGE_ROOT / "evaluation/response_sheet_template.csv"
    if not path.is_file():
        errors.append(f"Response sheet template missing: {path}")
        return

    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    duplicates = sorted({name for name in fieldnames if fieldnames.count(name) > 1})
    if duplicates:
        errors.append(f"{path} has duplicate columns: {', '.join(duplicates)}")

    fieldname_set = set(fieldnames)
    missing_columns = sorted(REQUIRED_RESPONSE_COLUMNS - fieldname_set)
    extra_columns = sorted(fieldname_set - REQUIRED_RESPONSE_COLUMNS)
    if missing_columns or extra_columns:
        errors.append(
            f"{path} column mismatch: missing={missing_columns}, extra={extra_columns}"
        )

    if rows:
        errors.append(f"{path} should contain a header only, found {len(rows)} data rows")


def main() -> int:
    errors: list[str] = []

    validate_required_files(errors)
    validate_example_json_parse(errors)
    validate_old_artifact_names(errors)
    component_ids_by_system = validate_profiles(errors)
    validate_fault_cases(component_ids_by_system, errors)
    validate_generic_baselines(component_ids_by_system, errors)
    validate_baselines(component_ids_by_system, errors)
    validate_response_template(errors)

    if errors:
        print(f"FAIL: {len(errors)} validation issue(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    example_count = len(list((PACKAGE_ROOT / "examples").glob("*.json")))
    component_count = sum(len(ids) for ids in component_ids_by_system.values())
    print(
        "PASS: AIBOM fairness evidence package validation passed "
        f"({example_count} example JSON files, 3 profiles, "
        f"{component_count} profile components, 24 fault cases, "
        "3 generic baselines, 3 CycloneDX-style baselines, "
        "1 response sheet template)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
