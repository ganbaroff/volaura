import { createServerClient, type CookieOptions } from "@supabase/ssr";
import { type NextRequest, NextResponse } from "next/server";

export async function updateSession(request: NextRequest, response: NextResponse) {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  // Graceful fallback: skip auth if Supabase not configured (prevents 500 on fresh deploy)
  if (!url || !key) {
    return response;
  }

  const supabase = createServerClient(
    url,
    key,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(
          cookiesToSet: { name: string; value: string; options?: CookieOptions }[]
        ) {
          cookiesToSet.forEach(({ name, value, options }) => {
            request.cookies.set(name, value);
            response.cookies.set(name, value, options);
          });
        },
      },
    }
  );

  const { pathname } = request.nextUrl;

  // Skip auth check on callback route — code hasn't been exchanged yet
  if (pathname.includes("/callback")) {
    return response;
  }

  // Refresh the auth token — this is the critical call.
  // Without it, server components get stale/expired sessions.
  const {
    data: { user },
  } = await supabase.auth.getUser();
  // Org/admin surfaces are added here so an ANONYMOUS Supabase session (introduced
  // by the screening candidate flow) cannot even render their UI shell. The backend
  // already fail-closes these for anon users (_get_owned_org → 403 NOT_ORG_OWNER,
  // require_platform_admin → 403 NOT_PLATFORM_ADMIN), so this is defense-in-depth on
  // the client. Note: this redirects *unauthenticated* visitors to /login; anonymous
  // sessions DO carry a Supabase user, so they are also kept out by the per-page
  // org-ownership / admin guards, which return empty/redirect for anon (see security_check).
  const isProtectedRoute =
    pathname.includes("/dashboard") ||
    pathname.includes("/aura") ||
    pathname.includes("/profile") ||
    pathname.includes("/settings") ||
    pathname.includes("/my-organization") ||
    pathname.includes("/admin");

  if (!user && isProtectedRoute) {
    // Extract locale from path (e.g., /az/dashboard → az)
    const segments = pathname.split("/").filter(Boolean);
    const locale = segments[0] === "az" || segments[0] === "en" ? segments[0] : "az";
    const loginUrl = request.nextUrl.clone();
    loginUrl.pathname = `/${locale}/login`;
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return response;
}
