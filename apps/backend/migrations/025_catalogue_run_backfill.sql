-- 025_catalogue_run_backfill.sql
-- Catalogue evaluation runs stored before they got a governance_evidence_runs row (evaluation_runs._store_run)
-- get one now, so they list under Evidence > Evaluation runs and a reviewer can map a passed one to a control.
-- Idempotent: only evidence rows with no source_run_id are touched.

WITH old AS (
    SELECT e.id, e.org_id, e.system_id, s.workspace_id, e.title, e.content_json,
           e.content_json::jsonb ->> 'evaluationId' AS evaluation_id,
           e.content_json::jsonb ->> 'status' AS status,
           COALESCE(e.captured_at, e.created_at) AS captured_at
    FROM governance_evidence AS e
    JOIN governance_ai_systems AS s ON s.id = e.system_id AND s.org_id = e.org_id
    WHERE e.evidence_type = 'evaluation_run' AND e.source = 'fairmind.eval_engines' AND e.source_run_id IS NULL
), runs AS (
    INSERT INTO governance_evidence_runs (
        id, org_id, system_id, workspace_id, passport_id, schema_version, capability_state, assurance_source,
        source_type, source_identifier, run_id, content_hash, result, provenance_json, artifact_refs_json,
        limitations_json, captured_at, evidence_id, created_at
    )
    SELECT gen_random_uuid()::text, org_id, system_id, workspace_id, id, 'fairmind-catalogue-1',
           CASE WHEN status = 'insufficient' THEN 'insufficient_data' ELSE 'validated' END, 'fairmind_internal',
           'fairmind_evaluation', evaluation_id, id, encode(sha256(convert_to(content_json, 'UTF8')), 'hex'),
           CASE status WHEN 'passed' THEN 'passed' WHEN 'failed' THEN 'failed' WHEN 'insufficient' THEN 'insufficient_data' ELSE 'unknown' END,
           jsonb_build_object('evaluation', jsonb_build_object('suite', jsonb_build_object('name', regexp_replace(title, ': [^:]*$', ''))))::text,
           '[]', '[]', captured_at, id, captured_at
    FROM old
    WHERE evaluation_id IS NOT NULL
    RETURNING id, evidence_id
)
UPDATE governance_evidence AS e SET source_run_id = runs.id FROM runs WHERE e.id = runs.evidence_id;
