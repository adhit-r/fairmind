-- Function to get user simulations with pagination
CREATE OR REPLACE FUNCTION public.get_user_simulations(
  user_id integer,
  page_number integer DEFAULT 1,
  page_size integer DEFAULT 10
)
RETURNS TABLE (
  id integer,
  name text,
  description text,
  status text,
  created_at timestamptz,
  updated_at timestamptz
) 
LANGUAGE sql
SECURITY DEFINER
AS $$
  SELECT 
    id, 
    name, 
    description, 
    status::text,
    "createdAt" as created_at,
    "updatedAt" as updated_at
  FROM "Simulation"
  WHERE "userId" = user_id::integer
  ORDER BY "createdAt" DESC
  LIMIT page_size
  OFFSET ((page_number - 1) * page_size);
$$;

-- Function to get simulation with all related data
CREATE OR REPLACE FUNCTION public.get_simulation_details(sim_id integer)
RETURNS jsonb
LANGUAGE sql
SECURITY DEFINER
AS $$
  SELECT jsonb_build_object(
    'simulation', to_jsonb(sim.*),
    'bias_results', (
      SELECT jsonb_agg(to_jsonb(bias.*))
      FROM "BiasDetectionResult" bias
      WHERE bias."simulationId" = sim_id
    ),
    'fairness_assessments', (
      SELECT jsonb_agg(to_jsonb(fair.*))
      FROM "FairnessAssessment" fair
      WHERE fair."simulationId" = sim_id
    ),
    'explainability_analyses', (
      SELECT jsonb_agg(to_jsonb(exp.*))
      FROM "ExplainabilityAnalysis" exp
      WHERE exp."simulationId" = sim_id
    )
  )
  FROM "Simulation" sim
  WHERE sim.id = sim_id;
$$;

-- Function to log audit events
CREATE OR REPLACE FUNCTION public.log_audit_event(
  user_id integer,
  action text,
  resource_type text,
  resource_id integer,
  details jsonb DEFAULT '{}'::jsonb
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  INSERT INTO "AuditLog"(
    "userId",
    action,
    "resourceType",
    "resourceId",
    details
  ) VALUES (
    user_id::integer,
    action,
    resource_type,
    resource_id,
    details
  );
END;
$$;
