-- 035_trace_cost.sql
-- A live run and each of its steps may say what it cost, in whatever units the organisation records (no currency is
-- assumed). Agent loop and runaway detection (EV-MON-05) checks each run's spend against the limit set for the run.
--
-- Idempotent.

ALTER TABLE governance_agent_traces ADD COLUMN IF NOT EXISTS cost DOUBLE PRECISION;
ALTER TABLE governance_agent_trace_steps ADD COLUMN IF NOT EXISTS cost DOUBLE PRECISION;
