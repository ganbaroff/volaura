import { createBrowserClient } from "@supabase/ssr";

let client: ReturnType<typeof createBrowserClient> | null = null;

export function createClient() {
  if (client) return client;
  client = createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      // WHY (INC-018, 2026-04-17): default `detectSessionInUrl: true` causes the
      // browser client's `_initialize()` to auto-call exchangeCodeForSession when
      // it sees `?code=` in the URL (PKCE flow). On a fresh callback page load
      // after external OAuth redirect, the singleton is null in memory so a NEW
      // client is constructed — its `_initialize()` races the explicit call we
      // make in callback/page.tsx. The auto-exchange usually wins, consumes the
      // PKCE code_verifier cookie, and when our explicit call awaits past the
      // initialize lock it finds the verifier gone → "PKCE code verifier not
      // found in storage" error → user bounced back to /login with oauth-error.
      //
      // FIX: disable detectSessionInUrl globally. We own every ?code= exchange
      // via the explicit call in app/[locale]/callback/page.tsx. Magic-link /
      // verifyOtp flows use `?token_hash=` not `?code=`, so they are unaffected.
      // Session refresh/persistence remain enabled.
      auth: {
        detectSessionInUrl: false,
        flowType: "pkce",
        autoRefreshToken: true,
        persistSession: true,
      },
    }
  );
  return client;
}
