-- 034_evaluation_reviews.sql
-- A person's review of each flagged item on a catalogue run that awaits review: EV-DAT-02 and EV-DAT-07 flagged rows and
-- documents, EV-DEV-03 high-severity findings. Append-only; the latest review of an item counts. Once every item is
-- cleared (or any confirmed) the run's verdict is stored as a new evaluation run that names the reviewed one.
--
-- Idempotent: IF NOT EXISTS, CREATE OR REPLACE and DROP TRIGGER IF EXISTS. Triggers make append-only enforced, as
-- 013b does for governance_evidence_reviews.

CREATE TABLE IF NOT EXISTS governance_evaluation_reviews (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    evidence_id TEXT NOT NULL REFERENCES governance_evidence(id),
    item VARCHAR(500) NOT NULL,
    decision VARCHAR(20) NOT NULL,
    note TEXT NOT NULL,
    reviewed_by TEXT NOT NULL,
    created_at TEXT NOT NULL
);

-- The ORM created these columns as unrestricted varchar in earlier installs.
ALTER TABLE governance_evaluation_reviews
    ALTER COLUMN id TYPE TEXT,
    ALTER COLUMN org_id TYPE TEXT,
    ALTER COLUMN evidence_id TYPE TEXT,
    ALTER COLUMN reviewed_by TYPE TEXT,
    ALTER COLUMN created_at TYPE TEXT;

CREATE INDEX IF NOT EXISTS ix_governance_evaluation_reviews_org_id ON governance_evaluation_reviews(org_id);
CREATE INDEX IF NOT EXISTS ix_governance_evaluation_reviews_evidence_id ON governance_evaluation_reviews(evidence_id);

CREATE OR REPLACE FUNCTION reject_governance_evaluation_review_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $function$
BEGIN
    RAISE EXCEPTION '% is append-only', TG_TABLE_NAME
        USING ERRCODE = '55000';
END;
$function$;

DO $review_function_path$
BEGIN
    EXECUTE pg_catalog.format(
        'ALTER FUNCTION %I.reject_governance_evaluation_review_mutation() SET search_path TO pg_catalog, %I, pg_temp',
        pg_catalog.current_schema(), pg_catalog.current_schema()
    );
END;
$review_function_path$;
REVOKE EXECUTE ON FUNCTION reject_governance_evaluation_review_mutation() FROM PUBLIC;

DROP TRIGGER IF EXISTS governance_evaluation_reviews_no_update ON governance_evaluation_reviews;
CREATE TRIGGER governance_evaluation_reviews_no_update
    BEFORE UPDATE ON governance_evaluation_reviews
    FOR EACH ROW EXECUTE FUNCTION reject_governance_evaluation_review_mutation();
DROP TRIGGER IF EXISTS governance_evaluation_reviews_no_delete ON governance_evaluation_reviews;
CREATE TRIGGER governance_evaluation_reviews_no_delete
    BEFORE DELETE ON governance_evaluation_reviews
    FOR EACH ROW EXECUTE FUNCTION reject_governance_evaluation_review_mutation();
