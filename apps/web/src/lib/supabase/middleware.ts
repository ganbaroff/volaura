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

  // Refresh the auth token — this is the critical call.
  // Without it, server components get stale/expired sessions.
  const {
    data: { user },
  } = await supabase.auth.getUser();

  // If user is NOT logged in and tries to access protected routes → redirect to login
  const { pathname } = request.nextUrl;
  const isProtectedRoute =
    pathname.includes("/dashboard") ||
    pathname.includes("/aura") ||
    pathname.includes("/profile") ||
    pathname.includes("/settings");

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
