-- Link governed AI systems to the registered models they govern.
--
-- Before this migration, governance_ai_systems and models were disconnected:
-- there was no way to reach a model's governance record (or its environmental
-- assessments) from the model evaluation flow. This adds the missing edge so
-- the model detail view can resolve its governed system, run an environmental
-- assessment against it, and surface the release gate in the same place a
-- reviewer evaluates the model.
--
-- Nullable by design: a governed system may describe a business process or a
-- third-party vendor system that has no model row in this platform.

ALTER TABLE governance_ai_systems
    ADD COLUMN IF NOT EXISTS model_id VARCHAR(255);

-- Deliberately ON DELETE SET NULL rather than CASCADE: deleting a model must
-- never destroy its governance history, evidence, or approval trail. The
-- governed system survives with the link cleared.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_governance_ai_systems_model_id'
          AND table_name = 'governance_ai_systems'
    ) THEN
        ALTER TABLE governance_ai_systems
            ADD CONSTRAINT fk_governance_ai_systems_model_id
            FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE SET NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_governance_ai_systems_model_id
    ON governance_ai_systems (model_id);

-- One governed system per model. A model with two governance records would
-- make "the environmental gate for this model" ambiguous, and the release gate
-- must have exactly one answer. Partial index so the many NULLs stay allowed.
CREATE UNIQUE INDEX IF NOT EXISTS uq_governance_ai_systems_model_id
    ON governance_ai_systems (model_id)
    WHERE model_id IS NOT NULL;

COMMENT ON COLUMN governance_ai_systems.model_id IS
    'Registered model this governed system governs; NULL for systems with no model row in this platform.';
