-- Seed initial policy versions so consent_events can reference them.
-- Without these rows, assessment.py consent logging silently skips (no active policy found).
-- Idempotent via ON CONFLICT DO NOTHING on (document_type, version, locale).

INSERT INTO public.policy_versions (document_type, version, locale, content_markdown, content_sha256, effective_from)
VALUES
    ('terms_of_service', '1.0', 'en',
     'Terms of Service v1.0 — effective 2026-04-19. Full text at https://volaura.app/en/terms',
     '',  -- trigger auto-computes
     '2026-04-19T00:00:00Z'),
    ('terms_of_service', '1.0', 'az',
     'İstifadə Şərtləri v1.0 — 2026-04-19 tarixindən qüvvədədir. Tam mətn: https://volaura.app/az/terms',
     '',
     '2026-04-19T00:00:00Z'),
    ('privacy_policy', '1.0', 'en',
     'Privacy Policy v1.0 — effective 2026-04-19. Full text at https://volaura.app/en/privacy',
     '',
     '2026-04-19T00:00:00Z'),
    ('privacy_policy', '1.0', 'az',
     'Məxfilik Siyasəti v1.0 — 2026-04-19 tarixindən qüvvədədir. Tam mətn: https://volaura.app/az/privacy',
     '',
     '2026-04-19T00:00:00Z'),
    ('ai_decision_notice', '1.0', 'en',
     'AI Decision Notice v1.0 — effective 2026-04-19. VOLAURA uses automated scoring (IRT/CAT + LLM) to compute AURA scores. This affects discoverability by organizations. You may request human review per GDPR Art. 22.',
     '',
     '2026-04-19T00:00:00Z'),
    ('ai_decision_notice', '1.0', 'az',
     'Süni İntellekt Qərar Bildirişi v1.0 — 2026-04-19. VOLAURA avtomatlaşdırılmış qiymətləndirmə (IRT/CAT + LLM) istifadə edərək AURA ballarını hesablayır. Bu, təşkilatlar tərəfindən tapılma imkanınıza təsir edir. GDPR Maddə 22-yə əsasən insan nəzarəti tələb edə bilərsiniz.',
     '',
     '2026-04-19T00:00:00Z')
ON CONFLICT ON CONSTRAINT policy_versions_unique DO NOTHING;
