-- FORCE ROW LEVEL SECURITY — tables missed by or created after 20260415210000.
--
-- Why a second migration instead of editing the original DO block:
--   20260415210000 uses existence-checks (IF EXISTS in pg_class) so tables that
--   didn't exist at that point were silently skipped. Three tables existed before
--   April 15 but were never added to the DO block array; fourteen more were
--   created in later migrations. Together these 17 tables had RLS enabled but
--   not FORCE, leaving the table-owner bypass hole open.
--
-- Coverage:
--   Pre-April-15, not in original DO block (3):
--     org_saved_searches, agent_memory, agent_run_log
--   Post-April-15 (14):
--     grievances, lifesim_events,
--     modules, module_activations,
--     eventshift_events, eventshift_departments, eventshift_areas,
--     eventshift_units, eventshift_unit_assignments, eventshift_unit_metrics,
--     atlas_obligations, atlas_proofs, atlas_nag_log,
--     assessment_completion_jobs
--
-- Pattern: same existence-checked DO block as 20260415210000 — migration-order safe.

DO $$
DECLARE
    tbl TEXT;
    tables_to_force TEXT[] := ARRAY[
        -- pre-April-15, missed from original array
        'org_saved_searches',
        'agent_memory',
        'agent_run_log',
        -- post-April-15 tables
        'grievances',
        'lifesim_events',
        'modules',
        'module_activations',
        'eventshift_events',
        'eventshift_departments',
        'eventshift_areas',
        'eventshift_units',
        'eventshift_unit_assignments',
        'eventshift_unit_metrics',
        'atlas_obligations',
        'atlas_proofs',
        'atlas_nag_log',
        'assessment_completion_jobs'
    ];
BEGIN
    FOREACH tbl IN ARRAY tables_to_force LOOP
        IF EXISTS (
            SELECT 1 FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relname = tbl AND c.relkind = 'r'
        ) THEN
            EXECUTE format('ALTER TABLE public.%I FORCE ROW LEVEL SECURITY', tbl);
        END IF;
    END LOOP;
END $$;
