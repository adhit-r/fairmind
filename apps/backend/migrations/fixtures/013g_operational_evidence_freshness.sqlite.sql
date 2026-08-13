-- SQLite parity fixture for operational evidence freshness 013g.
--
-- PostgreSQL 14 is the only operational freshness authority. SQLite cannot
-- provide a table-valued classifier, a transaction-wide database timestamp,
-- or the required authority-lifecycle locking. Review and governance-decision
-- writes therefore fail closed instead of simulating release behavior.

DROP TRIGGER IF EXISTS governance_evidence_reviews_freshness_unavailable_013g;
CREATE TRIGGER governance_evidence_reviews_freshness_unavailable_013g
BEFORE INSERT ON governance_evidence_reviews
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'operational freshness is unavailable in SQLite parity');
END;

DROP TRIGGER IF EXISTS governance_evaluation_decisions_freshness_unavailable_013g;
CREATE TRIGGER governance_evaluation_decisions_freshness_unavailable_013g
BEFORE INSERT ON governance_evaluation_decisions
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'operational freshness is unavailable in SQLite parity');
END;
