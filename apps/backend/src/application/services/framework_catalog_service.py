"""Import immutable framework catalogs from versioned AIUC workbooks."""

from __future__ import annotations

import argparse
import hashlib
import re
import uuid
from dataclasses import dataclass
from pathlib import Path

from openpyxl import load_workbook
from sqlalchemy import insert, select
from sqlalchemy.orm import Session

from database.governance_models import GovernanceControlDefinition, GovernanceFrameworkVersion


REQUIRED_SHEETS = ("Instructions", "AIUC-1 requirements", "AIUC-1 Controls & Evidence")
DEFAULT_COUNTS = (51, 135)
REQUIREMENT_ID = re.compile(r"^([A-Z]\d{3}):")
CONTROL_ID = re.compile(r"^([A-Z]\d{3}\.\d+)")
VERSION = re.compile(r"\bVersion:\s*([^|\n]+)", re.IGNORECASE)


class WorkbookValidationError(ValueError):
    """Raised when a workbook cannot be safely imported as a catalog."""


@dataclass(frozen=True)
class ParsedRequirement:
    external_id: str
    source_title: str
    statement: str
    principle: str
    application: str
    frequency: str
    capabilities: tuple[str, ...]
    active: bool


@dataclass(frozen=True)
class ParsedControl:
    external_id: str
    parent_requirement_id: str
    source_parent_title: str
    source_statement: str
    source_evidence_title: str
    evidence: str
    category: str
    locations: tuple[str, ...]
    capabilities: tuple[str, ...]
    additional_category: str
    additional_locations: tuple[str, ...]
    additional_capabilities: tuple[str, ...]
    application: str
    active: bool


@dataclass(frozen=True)
class ParsedFrameworkCatalog:
    framework_key: str
    name: str
    version_label: str
    source_hash: str
    requirements: tuple[ParsedRequirement, ...]
    controls: tuple[ParsedControl, ...]

    @property
    def requirement_count(self) -> int:
        return len(self.requirements)

    @property
    def control_count(self) -> int:
        return len(self.controls)


@dataclass(frozen=True)
class FrameworkImportResult:
    version_id: str
    framework_key: str
    version_label: str
    requirement_count: int
    control_count: int
    source_hash: str
    created: bool


def _text(value: object) -> str:
    return "" if value is None else str(value).strip()


def _array(value: object) -> tuple[str, ...]:
    return tuple(item.strip() for item in _text(value).split(",") if item.strip())


def _active(*values: str) -> bool:
    return not any("retired" in value.lower() for value in values)


def _version_label(sheet: object) -> str:
    for row in sheet.iter_rows(values_only=True):
        for value in row:
            match = VERSION.search(_text(value))
            if match:
                return match.group(1).strip()
    raise WorkbookValidationError("missing AIUC-1 version label")


def _requirement_records(sheet: object) -> tuple[ParsedRequirement, ...]:
    rows = sheet.iter_rows(min_row=2, values_only=True)
    records: list[ParsedRequirement] = []
    seen: set[str] = set()
    for row in rows:
        title = _text(row[1] if len(row) > 1 else None)
        if not title:
            continue
        match = REQUIREMENT_ID.match(title)
        if not match:
            raise WorkbookValidationError(f"invalid requirement title: {title}")
        external_id = match.group(1)
        if external_id in seen:
            raise WorkbookValidationError(f"duplicate requirement ID: {external_id}")
        seen.add(external_id)
        records.append(
            ParsedRequirement(
                external_id=external_id,
                source_title=title,
                statement=_text(row[2] if len(row) > 2 else None),
                principle=_text(row[0] if row else None),
                application=_text(row[3] if len(row) > 3 else None),
                frequency=_text(row[4] if len(row) > 4 else None),
                capabilities=_array(row[5] if len(row) > 5 else None),
                active=_active(title),
            )
        )
    return tuple(records)


def _control_records(sheet: object, requirement_ids: set[str]) -> tuple[ParsedControl, ...]:
    records: list[ParsedControl] = []
    seen: set[str] = set()
    for row in sheet.iter_rows(min_row=3, values_only=True):
        parent_title = _text(row[0] if row else None)
        evidence_title = _text(row[5] if len(row) > 5 else None)
        if not parent_title and not evidence_title:
            continue
        parent_match = REQUIREMENT_ID.match(parent_title)
        control_match = CONTROL_ID.match(evidence_title)
        if not parent_match or not control_match:
            raise WorkbookValidationError("control row is missing a requirement or leaf control ID")
        parent_id, external_id = parent_match.group(1), control_match.group(1)
        if parent_id not in requirement_ids:
            raise WorkbookValidationError(f"missing parent requirement: {parent_id}")
        if external_id in seen:
            raise WorkbookValidationError(f"duplicate leaf control ID: {external_id}")
        seen.add(external_id)
        records.append(
            ParsedControl(
                external_id=external_id,
                parent_requirement_id=parent_id,
                source_parent_title=parent_title,
                source_statement=_text(row[4] if len(row) > 4 else None),
                source_evidence_title=evidence_title,
                evidence=_text(row[6] if len(row) > 6 else None),
                category=_text(row[7] if len(row) > 7 else None),
                locations=_array(row[8] if len(row) > 8 else None),
                capabilities=_array(row[9] if len(row) > 9 else None),
                additional_category=_text(row[10] if len(row) > 10 else None),
                additional_locations=_array(row[11] if len(row) > 11 else None),
                additional_capabilities=_array(row[12] if len(row) > 12 else None),
                application=_text(row[3] if len(row) > 3 else None),
                active=_active(parent_title, evidence_title),
            )
        )
    return tuple(records)


def parse_aiuc_workbook(
    path: Path, *, strict: bool = True, expected_counts: tuple[int, int] | None = None
) -> ParsedFrameworkCatalog:
    """Parse and validate an AIUC-1 workbook without changing database state."""
    path = Path(path)
    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        missing = set(REQUIRED_SHEETS) - set(workbook.sheetnames)
        if missing:
            raise WorkbookValidationError(f"missing required sheets: {', '.join(sorted(missing))}")
        requirements = _requirement_records(workbook[REQUIRED_SHEETS[1]])
        controls = _control_records(workbook[REQUIRED_SHEETS[2]], {item.external_id for item in requirements})
        target = DEFAULT_COUNTS if strict else expected_counts
        if target and (len(requirements), len(controls)) != target:
            raise WorkbookValidationError(
                f"expected {target[0]} requirements and {target[1]} controls; "
                f"found {len(requirements)} requirements and {len(controls)} controls"
            )
        return ParsedFrameworkCatalog(
            framework_key="aiuc-1",
            name="AIUC-1",
            version_label=_version_label(workbook[REQUIRED_SHEETS[0]]),
            source_hash=hashlib.sha256(path.read_bytes()).hexdigest(),
            requirements=requirements,
            controls=controls,
        )
    finally:
        workbook.close()


class FrameworkCatalogService:
    """Persist validated, immutable framework catalog versions."""

    def __init__(
        self, db: Session, *, strict: bool = True, expected_counts: tuple[int, int] | None = None
    ) -> None:
        self.db = db
        self.strict = strict
        self.expected_counts = expected_counts

    def import_workbook(self, path: Path, actor_id: str) -> FrameworkImportResult:
        catalog = parse_aiuc_workbook(path, strict=self.strict, expected_counts=self.expected_counts)
        with self.db.begin():
            versions = GovernanceFrameworkVersion.__table__
            controls = GovernanceControlDefinition.__table__
            existing = self.db.execute(
                select(versions.c.id).where(
                    versions.c.framework_key == catalog.framework_key,
                    versions.c.version_label == catalog.version_label,
                    versions.c.source_hash == catalog.source_hash,
                )
            ).scalar_one_or_none()
            if existing:
                return self._result(existing, catalog, created=False)
            version_id = str(uuid.uuid4())
            self.db.execute(
                insert(versions).values(
                    id=version_id,
                    framework_key=catalog.framework_key,
                    name=catalog.name,
                    version_label=catalog.version_label,
                    source_hash=catalog.source_hash,
                    status="active",
                )
            )
            self.db.execute(
                insert(controls),
                [
                    {
                        "id": str(uuid.uuid4()),
                        "framework_version_id": version_id,
                        "external_id": control.external_id,
                        "title": control.source_evidence_title,
                        "statement": control.source_statement,
                        "active": control.active,
                    }
                    for control in catalog.controls
                ],
            )
        return self._result(version_id, catalog, created=True)

    @staticmethod
    def _result(version_id: str, catalog: ParsedFrameworkCatalog, *, created: bool) -> FrameworkImportResult:
        return FrameworkImportResult(
            version_id=version_id,
            framework_key=catalog.framework_key,
            version_label=catalog.version_label,
            requirement_count=catalog.requirement_count,
            control_count=catalog.control_count,
            source_hash=catalog.source_hash,
            created=created,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate an AIUC-1 framework workbook")
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--check", action="store_true", help="validate without persisting")
    args = parser.parse_args()
    if not args.check:
        parser.error("only --check is supported from the command line")
    catalog = parse_aiuc_workbook(args.workbook)
    print(
        f"version={catalog.version_label} requirements={catalog.requirement_count} "
        f"controls={catalog.control_count} sha256={catalog.source_hash}"
    )


if __name__ == "__main__":
    main()
