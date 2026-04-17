import { createBrowserClient } from "@supabase/ssr";

let client: ReturnType<typeof createBrowserClient> | null = null;

export function createClient() {
  if (client) return client;
  client = createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );
  return client;
  // NOTE (INC-018, 2026-04-17): DO NOT pass `auth: { detectSessionInUrl: false }`
  // here — `@supabase/ssr` 0.6.0's `createBrowserClient` HARDCODES
  // `detectSessionInUrl: isBrowser()` AFTER spreading user options (see
  // node_modules/@supabase/ssr/dist/module/createBrowserClient.js line ~30),
  // so any override is silently ignored. The fix for the PKCE double-exchange
  // race lives in `app/[locale]/callback/page.tsx` instead — see INC-018.
}
