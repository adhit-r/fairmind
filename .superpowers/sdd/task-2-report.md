# Task 2 Report: Framework Catalog Importer

## Delivered

- Added `openpyxl>=3.1.5` and regenerated the backend lockfile.
- Added a pure AIUC-1 workbook parser with SHA-256 byte hashing, required-sheet validation, duplicate leaf-ID validation, parent-requirement validation, retirement preservation, and strict `51/135` production counts.
- Parsed records retain workbook source strings alongside normalized tuple arrays. The two parallel evidence metadata column groups remain separate (`category`/`locations`/`capabilities` and `additional_*`); they are never merged.
- Added transactional persistence into the Task 1 framework-version and control-definition tables. Re-import of the same framework key, version label, and source hash returns the existing version with `created=False`.
- Added the requested `--check` CLI mode. The supplied workbook was read but not copied or committed.

## TDD evidence

1. The initial focused test run failed at collection because `framework_catalog_service` did not exist.
2. The parser and persistence implementation made the synthetic importer suite green.
3. A follow-up RED test demonstrated that the second workbook metadata group was not retained; `additional_*` fields were then added and the suite returned green.

## Verification

- `cd apps/backend && uv run pytest tests/test_framework_catalog_service.py -q` — 6 passed.
- `cd apps/backend && uv run python -m src.application.services.framework_catalog_service "/Users/adhi/Downloads/AIUC-1 _ April, 2026 version.xlsx" --check` — `version=April, 2026 requirements=51 controls=135`.
- Workbook SHA-256: `d2b4a2aa2be4eab1047fc23b5dcc60cee8cbbcf58bc0f81b87dda1ee8b391629`.
- `tooling/check_backend_layer_boundaries.sh` — passed.
- `tooling/check_no_archive_imports.sh` — passed.
- `git diff --check` — passed.

## Concern

## Review remediation

- Extended the generic framework version and control-definition schema with provenance, `requirements_json`, and catalog fields needed by later framework/control views. The SQLite migration selector omits PostgreSQL's idempotent catalog-column upgrades after creating the complete SQLite schema.
- Added semantic header validation against the workbook's documented row-one requirement headers and row-two 21-column control headers. Merged group cells are intentionally not used as parsing contracts.
- Added SQLite round-trip assertions for provenance, requirements, control parent/principle, normalized capabilities, and metadata. An injected control insert failure proves the version insert is rolled back with the controls.
- `actor_id` is now persisted as `imported_by`. Serial idempotence remains covered. An `IntegrityError` re-queries the unique version key after rollback and returns the existing version when a concurrent importer won the race; no true concurrent SQLite race was exercised because SQLite's write locking does not provide a reliable equivalent to the deployment database behavior.
