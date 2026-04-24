-- Compliance retention enforcement (GDPR Art. 5(1)(e))
-- Implements a callable retention procedure because pg_cron is unavailable.

CREATE OR REPLACE FUNCTION public.enforce_compliance_retention(
    p_decision_retention_days integer DEFAULT 730,
    p_human_review_retention_days integer DEFAULT 1095,
    p_consent_retention_days integer DEFAULT 2190
)
RETURNS TABLE (
    deleted_human_review_requests bigint,
    deleted_automated_decision_log bigint,
    deleted_consent_events bigint
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_human_deleted bigint := 0;
    v_decision_deleted bigint := 0;
    v_consent_deleted bigint := 0;
BEGIN
    -- 1) Resolved/escalated human review requests beyond retention
    DELETE FROM public.human_review_requests hr
    WHERE hr.requested_at < (now() - make_interval(days => p_human_review_retention_days))
      AND hr.status IN ('resolved_uphold', 'resolved_overturn', 'escalated_to_authority');
    GET DIAGNOSTICS v_human_deleted = ROW_COUNT;

    -- 2) Automated decision log rows beyond retention where no review ticket remains
    DELETE FROM public.automated_decision_log ad
    WHERE ad.created_at < (now() - make_interval(days => p_decision_retention_days))
      AND NOT EXISTS (
          SELECT 1
          FROM public.human_review_requests hr
          WHERE hr.automated_decision_id = ad.id
      );
    GET DIAGNOSTICS v_decision_deleted = ROW_COUNT;

    -- 3) Consent events beyond long retention horizon
    DELETE FROM public.consent_events ce
    WHERE ce.created_at < (now() - make_interval(days => p_consent_retention_days));
    GET DIAGNOSTICS v_consent_deleted = ROW_COUNT;

    RETURN QUERY
    SELECT v_human_deleted, v_decision_deleted, v_consent_deleted;
END;
$$;

REVOKE ALL ON FUNCTION public.enforce_compliance_retention(integer, integer, integer) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.enforce_compliance_retention(integer, integer, integer) TO service_role;

