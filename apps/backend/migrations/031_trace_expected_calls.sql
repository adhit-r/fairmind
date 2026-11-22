-- 031_trace_expected_calls.sql
-- A test run can say which tool calls it should make, in order ({tool, args} each, as JSON), so Tool-call
-- correctness (EV-TST-06) reads live runs. A step a guardrail stopped is stored with status 'blocked'; the
-- status column is free text, so that needs no change here.
--
-- Idempotent.

ALTER TABLE governance_agent_traces ADD COLUMN IF NOT EXISTS expected_calls TEXT;
