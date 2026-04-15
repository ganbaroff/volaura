/**
 * Canonical Atlas identity — loaded from identity.json at package root.
 *
 * JSON import uses TS --resolveJsonModule. Shape validated through Zod
 * so a malformed identity.json fails loudly at import time.
 */
import { z } from "zod";
import identityJson from "../../identity.json" assert { type: "json" };

export const AtlasIdentitySchema = z
  .object({
    name: z.string(),
    named_by: z.string(),
    named_at: z.string(),
    role: z.string(),
    primary_language: z.string(),
    voice_style: z.string(),
    banned_patterns: z.array(z.string()),
    ecosystem_products: z.array(z.string()),
    constitution_laws: z.record(z.string(), z.string()),
    portable_brief_url: z.string().url(),
    version: z.string().default("0.1.0"),
  })
  .strict();

export type AtlasIdentity = z.infer<typeof AtlasIdentitySchema>;

export function loadIdentity(raw: unknown = identityJson): AtlasIdentity {
  return AtlasIdentitySchema.parse(raw);
}

// Module-level singleton — parsed once at import.
export const IDENTITY: AtlasIdentity = loadIdentity();
