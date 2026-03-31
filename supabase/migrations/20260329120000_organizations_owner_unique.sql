-- BUG-017 FIX: Add UNIQUE constraint on organizations.owner_id
-- Without this, two simultaneous POST /api/organizations requests from the same user
-- can both pass the application-layer duplicate check before either INSERT completes,
-- resulting in two organization rows for the same owner.
-- The application-layer pre-check stays for UX (returns a friendly error before DB hit),
-- but the DB constraint is the authoritative safety net.

ALTER TABLE public.organizations
    ADD CONSTRAINT organizations_owner_id_unique UNIQUE (owner_id);
