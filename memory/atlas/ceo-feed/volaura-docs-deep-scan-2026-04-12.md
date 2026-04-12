# VOLAURA Docs Deep Scan — Key Findings (2026-04-12)

## DEADLINES (HARD)
- May 2026: Major event in Baku, 5000+ attendees, 200+ signup target
- April 2026: Beta checklist completion (5 CEO action items pending)
- GITA Georgia: apply April 2026, up to $240K
- Astana Hub: apply May 2026, $5-20K
- Turkiye Tech Visa: June 2026

## BETA CHECKLIST — 5 ITEMS BLOCKING LAUNCH (CEO action required)
1. Railway APP_ENV=production (without it CORS only allows localhost)
2. Railway APP_URL=https://volaura.app
3. Supabase email confirmation OFF (testers get stuck)
4. supabase db push (4 pending migrations)
5. Supabase redirect URLs for password reset

## UNIT ECONOMICS (Month 12, realistic)
80 paying orgs → ~15,080 AZN/mo (~$8,870)
Annual gross: ~$106,450
Net after commissions + infra: ~$63,870/year
Conversion assumption: 5-8% (not 30% fantasy)

## GROWTH CHANNELS (no paid ads)
HR bouquet strategy → 50-300 registrations
LinkedIn 5-post series → 50-75 registrations  
TikTok 10 videos → 50-1000+ registrations
STEP IT alumni → 10-40
Conservative month 1: 300-500 signups

## NORTH STAR METRIC
MAAV = Monthly Active Assessed Users with valid AURA who logged in last 30 days
Launch target: 200 MAAV. M3: 600. M6: 2,000. M12: 5,000+

## KPIs
Time to First AURA: <15 min
Assessment Completion: >75%
D1 retention: >50%, D7: >35%, D30: >20%
K-Factor (viral): >1.2

## ARCHITECTURE DECISIONS (7 ADRs accepted)
Supabase-first + FastAPI hybrid (not pure Supabase or pure Next.js)
Pseudo-IRT CAT (8-10 adaptive questions, not fixed 40)
Hybrid AURA recalc (DB trigger + nightly cron)
Gemini 2.5 Flash for LLM evaluation
pgvector 768-dim (Gemini embeddings)
8 competencies, 7-point BARS

## LAUNCH DAY PLAN
Pre-warm ISR cache, test QR codes, offline mode verified
Monitor: Sentry real-time, Supabase connections, Railway logs
Leaderboard display on venue TV (updates every 30s)

## EXPANSION ROADMAP
Phase 1 (M1-6): Baku, 500+ users, Pasha Bank, 10+ orgs, apply GITA
Phase 2 (M6-12): 3 countries, 2000+ users, 30+ orgs
Phase 3 (M12-18): 5000+ users, UN agencies, MiroFish API
Phase 4 (M18-36): 10000+ users, 5+ countries, Series A

## CITY CHAPTER FRANCHISE
City Lead gets brand kit + 30% placement fees in their city
Sequence: Baku → Ganja+Sumgait → Tbilisi → Almaty → Istanbul
