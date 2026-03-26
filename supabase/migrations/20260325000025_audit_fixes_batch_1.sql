-- Audit Fixes Batch 1: Schema alignment
-- Date: 2026-03-25
-- Fixes: [H3] Schema-DB Desync (Organization Contact)

-- Add contact_email to organizations table as expected by Pydantic schemas
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='organizations' AND column_name='contact_email') THEN
        ALTER TABLE public.organizations ADD COLUMN contact_email TEXT;
    END IF;
END $$;

COMMENT ON COLUMN public.organizations.contact_email IS 'Primary contact email for the organization, for verification and outreach.';
