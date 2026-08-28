-- SQLite fail-closed parity fixture for idempotency-retention integrity 013h.
--
-- PostgreSQL 14 is the release authority. SQLite cannot provide a trusted
-- database clock, transaction-safe rollover claims, or runtime trigger-owner
-- separation. Every write therefore fails closed instead of simulating the
-- release contract.

DROP TRIGGER IF EXISTS governance_idempotency_records_insert_unavailable_013h;
CREATE TRIGGER governance_idempotency_records_insert_unavailable_013h
BEFORE INSERT ON governance_idempotency_records
FOR EACH ROW
BEGIN
    SELECT RAISE(
        ABORT,
        'idempotency retention authority requires PostgreSQL'
    );
END;

DROP TRIGGER IF EXISTS governance_idempotency_records_update_unavailable_013h;
CREATE TRIGGER governance_idempotency_records_update_unavailable_013h
BEFORE UPDATE ON governance_idempotency_records
FOR EACH ROW
BEGIN
    SELECT RAISE(
        ABORT,
        'idempotency retention authority requires PostgreSQL'
    );
END;

DROP TRIGGER IF EXISTS governance_idempotency_records_delete_unavailable_013h;
CREATE TRIGGER governance_idempotency_records_delete_unavailable_013h
BEFORE DELETE ON governance_idempotency_records
FOR EACH ROW
BEGIN
    SELECT RAISE(
        ABORT,
        'idempotency retention authority requires PostgreSQL'
    );
END;
