-- Fix WARN: function_search_path_mutable for 2 trigger functions
-- Supabase security advisor flagged these as having mutable search_path
-- Applied to prod via MCP apply_migration 2026-04-19 20:30 Baku

CREATE OR REPLACE FUNCTION public.human_review_requests_set_sla()
 RETURNS trigger
 LANGUAGE plpgsql
 SET search_path = ''
AS $function$
BEGIN
    IF NEW.requested_at IS NULL THEN
        NEW.requested_at := now();
    END IF;
    NEW.sla_deadline := NEW.requested_at + interval '30 days';
    RETURN NEW;
END;
$function$;

CREATE OR REPLACE FUNCTION public.policy_versions_hash_content()
 RETURNS trigger
 LANGUAGE plpgsql
 SET search_path = ''
AS $function$
BEGIN
    NEW.content_sha256 := encode(extensions.digest(NEW.content_markdown, 'sha256'), 'hex');
    RETURN NEW;
END;
$function$;
