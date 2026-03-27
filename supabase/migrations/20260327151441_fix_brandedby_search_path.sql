-- Sprint B1: Fix brandedby.set_updated_at search_path syntax
-- Applied by other AI session immediately after create_brandedby_schema.
-- Ensures SET search_path uses TO syntax (Postgres canonical form).

CREATE OR REPLACE FUNCTION brandedby.set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path TO ''
AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;
