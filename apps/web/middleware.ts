import { i18nRouter } from "next-i18n-router";
import { type NextRequest } from "next/server";
import i18nConfig from "@/i18nConfig";
import { updateSession } from "@/lib/supabase/middleware";

export async function middleware(request: NextRequest) {
  // Step 1: i18n routing (locale detection + redirect)
  const i18nResponse = i18nRouter(request, i18nConfig);

  // If i18nRouter issued a redirect (301/302) — return immediately.
  // Don't run Supabase session refresh on redirect responses — they have no cookies.
  if (i18nResponse.status === 301 || i18nResponse.status === 302) {
    return i18nResponse;
  }

  // Step 2: Supabase session refresh + auth guard on non-redirect responses
  return await updateSession(request, i18nResponse);
}

export const config = {
  matcher: "/((?!api|static|.*\\..*|_next).*)",
};
