import { i18nRouter } from "next-i18n-router";
import { type NextRequest, NextResponse } from "next/server";
import i18nConfig from "@/i18nConfig";
import { updateSession } from "@/lib/supabase/middleware";

export async function middleware(request: NextRequest) {
  // Step 1: i18n routing — redirects / → /az, handles locale detection
  const i18nResponse = i18nRouter(request, i18nConfig);

  // If i18nRouter issued a redirect (3xx), return it immediately
  if (i18nResponse.status >= 300 && i18nResponse.status < 400) {
    return i18nResponse;
  }

  // Step 2: Supabase auth session refresh + protected route guard
  return await updateSession(request, i18nResponse);
}

export const config = {
  matcher: [
    // Match all paths except static files, api routes, and Next.js internals
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico|css|js)$).*)",
  ],
};
