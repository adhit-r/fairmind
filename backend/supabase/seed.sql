-- Create Simulation table if it doesn't exist
CREATE TABLE IF NOT EXISTS "Simulation" (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create Prediction table if it doesn't exist
CREATE TABLE IF NOT EXISTS "Prediction" (
  id SERIAL PRIMARY KEY,
  simulation_id INTEGER REFERENCES "Simulation"(id) ON DELETE CASCADE,
  model_name TEXT NOT NULL,
  prediction_data JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create FairnessAssessment table if it doesn't exist
CREATE TABLE IF NOT EXISTS "FairnessAssessment" (
  id SERIAL PRIMARY KEY,
  simulation_id INTEGER REFERENCES "Simulation"(id) ON DELETE CASCADE,
  assessment JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert test simulation if it doesn't exist
INSERT INTO "Simulation" (id, name, description)
SELECT 1, 'Test Simulation', 'Test simulation for fairness analysis'
WHERE NOT EXISTS (SELECT 1 FROM "Simulation" WHERE id = 1);

-- Insert test predictions if they don't exist
INSERT INTO "Prediction" (simulation_id, model_name, prediction_data)
SELECT 1, 'test_model', '{"feature1": 0.5, "feature2": 0.3, "outcome": 1, "sensitive_attr": "group1"}'
WHERE NOT EXISTS (SELECT 1 FROM "Prediction" WHERE simulation_id = 1 LIMIT 1)
UNION ALL
SELECT 1, 'test_model', '{"feature1": 0.7, "feature2": 0.2, "outcome": 0, "sensitive_attr": "group2"}'
WHERE NOT EXISTS (SELECT 1 FROM "Prediction" WHERE simulation_id = 1 LIMIT 1)
UNION ALL
SELECT 1, 'test_model', '{"feature1": 0.3, "feature2": 0.8, "outcome": 1, "sensitive_attr": "group1"}';

-- Create or update a function to calculate fairness metrics
CREATE OR REPLACE FUNCTION calculate_fairness_metrics(sim_id INTEGER)
RETURNS JSONB AS $$
DECLARE
  metrics JSONB;
  total_rows INTEGER;
  group1_count INTEGER;
  group2_count INTEGER;
  group1_positive INTEGER;
  group2_positive INTEGER;
BEGIN
  -- Get total predictions
  SELECT COUNT(*) INTO total_rows
  FROM "Prediction"
  WHERE simulation_id = sim_id;
  
  -- Get group counts
  SELECT COUNT(*) INTO group1_count
  FROM "Prediction"
  WHERE simulation_id = sim_id
  AND prediction_data->>'sensitive_attr' = 'group1';
  
  SELECT COUNT(*) INTO group2_count
  FROM "Prediction"
  WHERE simulation_id = sim_id
  AND prediction_data->>'sensitive_attr' = 'group2';
  
  -- Get positive outcomes by group
  SELECT COUNT(*) INTO group1_positive
  FROM "Prediction"
  WHERE simulation_id = sim_id
  AND prediction_data->>'sensitive_attr' = 'group1'
  AND (prediction_data->>'outcome')::INTEGER = 1;
  
  SELECT COUNT(*) INTO group2_positive
  FROM "Prediction"
  WHERE simulation_id = sim_id
  AND prediction_data->>'sensitive_attr' = 'group2'
  AND (prediction_data->>'outcome')::INTEGER = 1;
  
  -- Calculate metrics (simplified example)
  metrics := jsonb_build_object(
    'total_predictions', total_rows,
    'demographic_parity', 
      CASE 
        WHEN group2_count > 0 AND group1_count > 0 THEN 
          (group1_positive::FLOAT / NULLIF(group1_count, 0)) - 
          (group2_positive::FLOAT / NULLIF(group2_count, 0))
        ELSE 0
      END,
    'equal_opportunity', 
      CASE 
        WHEN group2_count > 0 AND group1_count > 0 THEN
          (group1_positive::FLOAT / NULLIF(group1_count, 0)) / 
          NULLIF((group2_positive::FLOAT / NULLIF(group2_count, 0)), 0)
        ELSE 0
      END,
    'statistical_parity', 
      CASE 
        WHEN total_rows > 0 THEN
          (group1_positive + group2_positive)::FLOAT / total_rows
        ELSE 0
      END,
    'group1_positive_rate', 
      CASE 
        WHEN group1_count > 0 THEN group1_positive::FLOAT / group1_count 
        ELSE 0 
      END,
    'group2_positive_rate', 
      CASE 
        WHEN group2_count > 0 THEN group2_positive::FLOAT / group2_count 
        ELSE 0 
      END,
    'group1_count', group1_count,
    'group2_count', group2_count,
    'group1_positive', group1_positive,
    'group2_positive', group2_positive,
    'calculated_at', NOW()
  );
  
  -- Upsert the fairness assessment
  INSERT INTO "FairnessAssessment" (simulation_id, assessment, updated_at)
  VALUES (sim_id, metrics, NOW())
  ON CONFLICT (simulation_id) 
  DO UPDATE SET 
    assessment = EXCLUDED.assessment,
    updated_at = EXCLUDED.updated_at;
  
  RETURN metrics;
END;
$$ LANGUAGE plpgsql;
