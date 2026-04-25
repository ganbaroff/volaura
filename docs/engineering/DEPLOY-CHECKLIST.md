# Volaura Deployment Checklist

**Target Launch:** Major Event in Baku, May 2026
**Tech Stack:** [[ARCHITECTURE.md|Next.js 14 on Vercel]] + [[ARCHITECTURE.md|FastAPI on Railway]] + [[DATABASE.md|Supabase PostgreSQL]]
**Owner:** Solo developer, AI-augmented

---

## Pre-Launch (1 Week Before)

### Infrastructure

- [ ] Supabase project created (Production tier, not free)
- [ ] All migrations applied to production DB (`supabase/migrations/`)
- [ ] RLS policies verified on **ALL** tables
  - [ ] `profiles` — SELECT/UPDATE own record
  - [ ] `assessment_sessions` — own records only
  - [ ] `question_responses` — session owner only
  - [ ] `aura_scores` — own profile only
  - [ ] `volunteer_embeddings` — own profile only
  - [ ] `notifications` — recipient only
  - [ ] `events` — public read, auth write
  - [ ] `event_registrations` — own records only
- [ ] Supabase Auth configured
  - [ ] Magic Link email auth enabled
  - [ ] Google OAuth provider added (client ID + secret)
  - [ ] Redirect URLs set (volaura.com + localhost for testing)
- [ ] Supabase Auth email templates customized
  - [ ] Welcome email (AZ + EN)
  - [ ] Magic link template (AZ + EN)
  - [ ] Subject lines localized
- [ ] Railway FastAPI deployment live
  - [ ] Environment variables injected (not in Dockerfile)
  - [ ] Health endpoint responds: `GET /api/v1/health`
  - [ ] Logs accessible in Railway dashboard
  - [ ] Alerts configured for failures
- [ ] Vercel project connected to main branch
  - [ ] Auto-deploy on push enabled
  - [ ] Build succeeds without warnings
- [ ] Custom domain configured
  - [ ] Domain registered (volaura.com)
  - [ ] DNS records pointing to Vercel
  - [ ] SSL certificate active (auto-provisioned)
  - [ ] DNS propagation verified (24-48 hours)
  - [ ] HTTPS works without browser warnings

### Environment Variables

**Vercel (Frontend):**
- [ ] `NEXT_PUBLIC_API_URL` = Railway API URL
- [ ] `NEXT_PUBLIC_SUPABASE_URL` = Supabase project URL
- [ ] `NEXT_PUBLIC_SUPABASE_ANON_KEY` = Supabase anon key
- [ ] `SENTRY_DSN` = frontend Sentry project DSN

**Railway (FastAPI Backend):**
- [ ] `SUPABASE_URL` = Supabase project URL
- [ ] `SUPABASE_SERVICE_KEY` = service role key (for admin operations)
- [ ] `SUPABASE_JWT_SECRET` = JWT secret from Supabase settings
- [ ] `GEMINI_API_KEY` = Google AI API key
- [ ] `OPENAI_API_KEY` = fallback (optional)
- [ ] `RESEND_API_KEY` = Resend email service key
- [ ] `SENTRY_DSN` = backend Sentry project DSN
- [ ] `LOG_LEVEL` = "INFO" (or "DEBUG" for troubleshooting)
- [ ] `CORS_ORIGINS` = volaura.com, localhost:3000

**Supabase (Settings):**
- [ ] JWT expiration set (default 1 hour is fine)
- [ ] Webhook signed with secret
- [ ] Backup schedule enabled (automatic daily)

### Security

- [ ] **No secrets in git history**
  - [ ] `git log --full-history --all -- .env*` returns empty
  - [ ] No API keys in commit messages
  - [ ] `.env.local` in `.gitignore`
- [ ] **RLS tested in real scenario**
  - [ ] Create 2 test users
  - [ ] User A cannot read User B's profile
  - [ ] User A cannot update User B's assessment
  - [ ] Try direct API calls with other user's ID — should 401
- [ ] **CORS configured**
  - [ ] FastAPI CORS middleware allows only volaura.com + localhost
  - [ ] Preflight requests (OPTIONS) handled
  - [ ] Credentials included in cross-origin requests
- [ ] **Rate limiting active**
  - [ ] `/auth/signup` — 5 requests/minute per IP
  - [ ] `/auth/login` — 5 requests/minute per IP
  - [ ] Assessment endpoints — 100 requests/minute per user
  - [ ] Public endpoints — 1000 requests/minute per IP
- [ ] **CSP headers configured**
  - [ ] Added to `next.config.js` (or middleware)
  - [ ] Allows Google fonts, Gemini API, Sentry
  - [ ] No unsafe-inline scripts
- [ ] **HTTPS enforced**
  - [ ] HTTP → HTTPS redirect in place
  - [ ] Vercel automatic redirect enabled
  - [ ] Test: `curl -I http://volaura.com` returns 308
- [ ] **Secrets rotated**
  - [ ] Old API keys revoked
  - [ ] Supabase service key regenerated

### Performance

- [ ] **ISR configured for public pages**
  - [ ] Landing page: `revalidate: 3600` (1 hour)
  - [ ] Public profiles: `revalidate: 60` (1 minute)
  - [ ] Leaderboard: `revalidate: 300` (5 minutes)
- [ ] **OG images generating**
  - [ ] Test profile share card generates correctly
  - [ ] Image size <200KB
  - [ ] Renders in Slack/Twitter preview
- [ ] **Lighthouse score**
  - [ ] Landing page: >90 overall
  - [ ] Accessibility: >95
  - [ ] Best Practices: >95
  - [ ] SEO: >95
- [ ] **Core Web Vitals**
  - [ ] LCP (Largest Contentful Paint) <2.5s
  - [ ] FID (First Input Delay) <100ms (or INP <200ms)
  - [ ] CLS (Cumulative Layout Shift) <0.1
  - [ ] Check via PageSpeed Insights after launch
- [ ] **Images optimized**
  - [ ] All `<img>` use `next/image` with `alt` text
  - [ ] WebP format served automatically
  - [ ] Lazy loading enabled
  - [ ] Placeholder blur/skeleton on slow networks
- [ ] **Bundle size**
  - [ ] Initial JS <300KB (gzipped)
  - [ ] Run: `npm run build && npm run analyze`
  - [ ] No unexpected large dependencies

### Functionality

- [ ] **Full assessment flow**
  - [ ] Sign up → lands on assessment start
  - [ ] Answer all required questions
  - [ ] Submit at end
  - [ ] Score page displays immediately
  - [ ] Badge renders correctly
- [ ] **AURA score calculation**
  - [ ] Test with known values (all 100 → AURA 100)
  - [ ] Weights: communication (0.20), reliability (0.15), etc.
  - [ ] Verify: `(score1 × 0.20) + (score2 × 0.15) + ... = AURA`
  - [ ] Badge tiers correct:
    - [ ] ≥90 = Platinum
    - [ ] ≥75 = Gold
    - [ ] ≥60 = Silver
    - [ ] ≥40 = Bronze
    - [ ] <40 = None
- [ ] **Profile page**
  - [ ] Displays user's name, AURA, badge, competencies
  - [ ] Real data populated from database
  - [ ] Avatar renders (or default)
  - [ ] Links to edit profile (auth required)
- [ ] **Public profile accessible**
  - [ ] Navigate to `/en/profile/[volunteer-id]` without login
  - [ ] Shows score, badge, event history
  - [ ] Share buttons visible (LinkedIn, Twitter, WhatsApp)
- [ ] **Share cards generate**
  - [ ] LinkedIn card: redirects to profile with pre-filled text
  - [ ] Twitter card: opens intent with text + score badge emoji
  - [ ] WhatsApp card: sends message with link + emoji
  - [ ] OG image included in share preview
- [ ] **Event listing**
  - [ ] Events page loads (`/en/events`)
  - [ ] Filters by date, category work
  - [ ] Pagination or infinite scroll loads more
- [ ] **Event registration**
  - [ ] Click "Register" button
  - [ ] Form validates email/phone
  - [ ] Submit creates row in `event_registrations`
  - [ ] Confirmation email sent
- [ ] **Notifications deliver**
  - [ ] Assessment complete → notification sent
  - [ ] Event reminder → 24 hours before
  - [ ] Notification appears in dashboard bell icon
  - [ ] Mark as read works
- [ ] **Leaderboard displays**
  - [ ] Top 100 volunteers by AURA score
  - [ ] Pagination or load more works
  - [ ] Badge icons render
  - [ ] Data updates every 5 minutes (ISR revalidate)
- [ ] **Offline assessment works**
  - [ ] Open assessment on venue WiFi
  - [ ] Disable network (Chrome DevTools → Offline)
  - [ ] Continue answering questions
  - [ ] Submit attempt → queued locally
  - [ ] Re-enable network → auto-syncs
  - [ ] Score appears on profile

### Internationalization (i18n)

- [ ] **All strings translated**
  - [ ] Run extraction: `pnpm i18next:extract`
  - [ ] Check `public/locales/az/common.json` for completeness
  - [ ] Check `public/locales/en/common.json` for completeness
  - [ ] No `[missing]` or empty values
- [ ] **Language switcher works**
  - [ ] Toggle AZ ↔ EN in header
  - [ ] URL changes: `/az/...` ↔ `/en/...`
  - [ ] Content re-renders
  - [ ] Preference persists (localStorage)
- [ ] **Azerbaijani characters render**
  - [ ] ə, ğ, ı, ö, ü, ş, ç display correctly
  - [ ] Check metadata: `<meta charset="utf-8" />`
  - [ ] Font supports Extended Latin (Google Fonts)
- [ ] **Date/number formatting**
  - [ ] Dates: `dd.MM.yyyy` for AZ, `MM/dd/yyyy` for EN
  - [ ] Numbers: `1.234,56` for AZ, `1,234.56` for EN
  - [ ] Verify in leaderboard, profile stats
- [ ] **Email templates localized**
  - [ ] Welcome email in AZ + EN (based on user preference)
  - [ ] Magic link in correct language
  - [ ] Score ready notification in correct language

### Email

- [ ] **Resend account verified**
  - [ ] Account created and active
  - [ ] Domain authenticated (DKIM, SPF, DMARC)
  - [ ] Check Resend dashboard for DNS records
  - [ ] Records propagated (24-48 hours)
- [ ] **Welcome email sends**
  - [ ] Sign up new user
  - [ ] Email arrives within 5 minutes
  - [ ] Links work
  - [ ] Branding looks correct
- [ ] **Magic link email**
  - [ ] Click "Send Magic Link" on login
  - [ ] Email arrives within 30 seconds
  - [ ] Link valid for 24 hours
  - [ ] Click link → signed in, redirected to dashboard
- [ ] **Score ready email**
  - [ ] Complete assessment
  - [ ] Email notification sent
  - [ ] Includes score, badge, AURA
  - [ ] CTA button links to public profile
- [ ] **Email rendering**
  - [ ] Test in major clients: Gmail, Outlook, Apple Mail, mobile
  - [ ] Use Litmus or similar preview tool
  - [ ] Images load
  - [ ] Buttons clickable
  - [ ] Text readable on small screens

### Monitoring

- [ ] **Sentry configured**
  - [ ] Frontend Sentry project created
  - [ ] Backend Sentry project created
  - [ ] DSN added to Vercel + Railway env vars
  - [ ] Test error reporting: intentional error in UI → appears in Sentry
  - [ ] Test backend error: intentional 500 → captured in Sentry
- [ ] **Vercel Analytics enabled**
  - [ ] Web Vitals dashboard shows data
  - [ ] Real user metrics visible
  - [ ] Slowest pages identified
- [ ] **Health endpoint responds**
  - [ ] `GET https://api.volaura.com/api/v1/health`
  - [ ] Response: `{"status": "ok"}`
  - [ ] HTTP 200
- [ ] **Error alerting configured**
  - [ ] Sentry → email notification on critical error
  - [ ] Sentry → Slack webhook (optional)
  - [ ] Test: intentional 500 → notification arrives
- [ ] **Uptime monitoring**
  - [ ] UptimeRobot (free tier) or similar
  - [ ] Monitor: volaura.com + api.volaura.com
  - [ ] Ping interval: 5 minutes
  - [ ] Alert if down for >5 minutes

---

## Launch Day (Major Event)

### Before Doors Open

- [ ] **Scale infrastructure if needed**
  - [ ] Check Railway resource usage (CPU, RAM)
  - [ ] If >80% utilization → upgrade instance
  - [ ] Check Supabase connection limit (free tier = 100)
  - [ ] Estimate max concurrent users expected
  - [ ] Be ready to upgrade Supabase → Pro if needed
- [ ] **Pre-warm ISR cache**
  - [ ] Script to hit all public profile URLs
  - [ ] Hit leaderboard page
  - [ ] Hit event listing page
  - [ ] Ensures fast initial load at venue
- [ ] **Test QR codes at venue**
  - [ ] Print QR codes redirect to `/en/start`
  - [ ] Scan with multiple phones (iOS + Android)
  - [ ] Opens app correctly, doesn't blank screen
  - [ ] Assessment loads in <3 seconds on venue WiFi
- [ ] **Leaderboard display connected**
  - [ ] Venue display (TV/projector) shows live leaderboard
  - [ ] Data updates every 30 seconds
  - [ ] Top 10 volunteers visible
  - [ ] Badge icons render correctly
- [ ] **Quick Mode enabled**
  - [ ] Assessment can complete in <10 minutes
  - [ ] Verify IRT/CAT algorithm speeds up on high confidence
  - [ ] Test: Fast mode should ask ~8-10 questions, not 40
- [ ] **Offline mode verified**
  - [ ] Test on venue WiFi (spotty/slow network)
  - [ ] Disable network → complete assessment → re-enable
  - [ ] Sync completes without errors
  - [ ] Score appears immediately after sync

### During Event

- [ ] **Monitor Sentry real-time**
  - [ ] Open Sentry dashboard on second screen
  - [ ] Watch for errors as volunteers complete assessments
  - [ ] Note patterns (e.g., all Android users getting X error)
  - [ ] Screenshot critical errors for post-mortems
- [ ] **Watch Supabase connection limit**
  - [ ] Supabase dashboard → Usage tab
  - [ ] If connections approaching 100 → upgrade to Pro immediately
  - [ ] Connection limit is strict (no automatic downgrade)
- [ ] **Check Railway logs**
  - [ ] Railway dashboard → Logs tab
  - [ ] Look for API 500 errors
  - [ ] Look for timeout errors (Supabase latency)
  - [ ] Look for LLM evaluation failures (Gemini quota)
- [ ] **Monitor assessment completion rate**
  - [ ] Track: signups vs. completions
  - [ ] Track: avg time per assessment
  - [ ] Track: score distribution
  - [ ] If >70% abandon → investigate UI/performance bottleneck (during event hours)
- [ ] **Be ready to patch**
  - [ ] Have git/GitHub open for hot fixes
  - [ ] Laptop ready to deploy in <5 minutes
  - [ ] Test patch locally before pushing to main
  - [ ] Communicate status to venue staff

---

## Post-Launch (1 Week After)

- [ ] **Review Sentry errors**
  - [ ] Filter by "Last 7 days"
  - [ ] Group by issue, identify top 5
  - [ ] Assess severity: critical vs. minor
  - [ ] File GitHub issues for each
  - [ ] Prioritize: fix critical bugs affecting >1% of users
- [ ] **Analyze user analytics**
  - [ ] Total signups during launch event
  - [ ] Total assessment completions
  - [ ] Completion rate (%)
  - [ ] Avg score distribution
  - [ ] Top 10 volunteers by AURA
  - [ ] Most common questions answered
  - [ ] Share button clicks by platform (LinkedIn > Twitter > WhatsApp?)
- [ ] **Check email delivery rates**
  - [ ] Resend dashboard → analytics
  - [ ] Delivery rate (should be >95%)
  - [ ] Bounce rate (should be <2%)
  - [ ] Open rate (watch for low engagement)
  - [ ] Investigate any hard bounces
- [ ] **Review Core Web Vitals**
  - [ ] Google Analytics → Web Vitals report
  - [ ] Real user data (not lab data)
  - [ ] Check LCP, FID/INP, CLS
  - [ ] If any metric yellow/red → optimize that page
- [ ] **Gather user feedback**
  - [ ] Send post-event survey (within 24 hours)
  - [ ] Questions: ease of use, technical issues, likelihood to recommend
  - [ ] Review email replies + support tickets
  - [ ] Note feature requests vs. bug reports
- [ ] **Plan patches for top issues**
  - [ ] Prioritize bugs affecting >5 users
  - [ ] Estimate fix time for each
  - [ ] Schedule sprints: hotfixes (same day) vs. enhancements (this week)
- [ ] **Send follow-up emails**
  - [ ] To all launch event attendees (opt-in list)
  - [ ] Subject: "Here's your AURA score — see how you ranked"
  - [ ] Include: personal score, badge, leaderboard link, share CTA
  - [ ] Personalized template per user
- [ ] **Begin org outreach**
  - [ ] Data points: total volunteers, avg AURA, top performers
  - [ ] Outreach email to event organizers: "Thanks for hosting, here's the impact"
  - [ ] Outreach to top profiles: "Featured in our leaderboard, thank you"
  - [ ] Offer: become official "Volaura Partner" org

---

## Reference Links

- [[ARCHITECTURE.md|Architecture Overview]]
- [[../../../.claude/rules/backend.md|Backend Rules]]
- [[../../../.claude/rules/database.md|Database Rules]]
- [[../../../.claude/rules/frontend.md|Frontend Rules]]
- [Supabase RLS Policies](https://supabase.com/docs/guides/auth/row-level-security)
- [Vercel Deployment](https://vercel.com/docs/concepts/deployments/overview)
- [Railway Documentation](https://railway.app/docs)
- [Sentry Setup](https://docs.sentry.io/)

