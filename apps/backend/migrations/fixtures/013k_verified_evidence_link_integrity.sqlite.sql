-- SQLite cannot prove the PostgreSQL link-time authority chain. Fail closed.

DROP TRIGGER IF EXISTS governance_evaluation_suite_evidence_links_verified_unavailable_013k;
CREATE TRIGGER governance_evaluation_suite_evidence_links_verified_unavailable_013k
BEFORE INSERT ON governance_evaluation_suite_evidence_links
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'verified evidence linking requires PostgreSQL');
END;
