# Open Questions Resolved — Atlas Decisions

**Date:** 2026-04-14
**Authority:** CTO decision (within Constitution envelope, CEO can override)

---

## Q1: Figma file status
**Decision:** B30q4nqVq5VjdqAVVYRh3t IS the correct file. Old 57 variables were created via Plugin API (Session 87) and were a draft. Cowork should rebuild from scratch using the 3-tier token architecture from the redesign brief. Old variables can be deleted.

## Q2: Liquid Glass technical approach
**Decision:** CSS-only.
```css
.aura-radar-container {
  backdrop-filter: blur(12px);
  background: linear-gradient(135deg, rgba(192,193,255,0.08), rgba(192,193,255,0.02));
  border: 1px solid rgba(192,193,255,0.12);
  box-shadow: 0 8px 32px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.05);
  border-radius: 24px;
}
```
Fallback for no backdrop-filter: `background: rgba(31,31,39,0.95)`.
No WebGL, no Canvas. CSS handles this.

## Q3: Character avatar system
**Decision:** Phase 1 = Static illustrated SVG. One illustration per badge tier (Bronze/Silver/Gold/Platinum), differentiated by color/glow.
- Bronze: muted, no glow
- Silver: subtle border shimmer
- Gold: warm glow (#E9C400 at 0.3 opacity)
- Platinum: full glow + particle effect (CSS only, 3 particles max)

Composable Habitica-style parts = Phase 2, after Life Simulator v1.0.

## Q4: Energy mode persistence
**Decision:** Supabase `profiles.energy_level` column (text enum: 'full'|'mid'|'low').
- Already exists in assessment flow (StartAssessmentRequest.energy_level)
- localStorage cache key: `volaura_energy_level` for instant load
- Sync to Supabase on change
- Three visual states:
  - **Full:** Standard UI, all animations, full information density
  - **Mid:** Reduce animations to opacity-only, larger touch targets (min 48px), hide secondary actions
  - **Low:** Single CTA per screen, max 3 elements visible, large text, zero animation, muted colors

## Q5: Crystal economy monetary policy
**Decision (provisional — CEO can override):**
- Daily earn cap: 50 crystals (15 from MindShift + 35 from VOLAURA)
- Sinks: avatar cosmetics (Life Sim), queue skip (BrandedBy 10-25 crystals)
- No direct purchase of crystals for money (anti-pay-to-win)
- Inactive decay: 1% per week after 30 days of zero activity (prevents hoarding)
- Exchange rate: NOT convertible to real money (regulatory simplicity)
- Launch rule (Crystal Law 8): do NOT activate earning until at least ONE spend path exists in production
