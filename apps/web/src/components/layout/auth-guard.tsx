"use client";

import { useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { useAuthStore } from "@/stores/auth-store";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { locale } = useParams<{ locale: string }>();
  const router = useRouter();
  const { session, isLoading, setSession, setLoading } = useAuthStore();

  useEffect(() => {
    const supabase = createClient();

    // Get initial session
    supabase.auth.getSession().then(({ data }) => {
      const cachedSession = useAuthStore.getState().session;
      const effectiveSession = data.session ?? cachedSession;
      if (data.session) {
        setSession(data.session);
      } else if (!effectiveSession) {
        setSession(null);
      }
      setLoading(false);
      if (!effectiveSession) {
        router.replace(`/${locale}/login`);
      }
    });

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      if (session) {
        setSession(session);
        return;
      }

      // Supabase can emit INITIAL_SESSION with null while browser storage is
      // still catching up after login. Only an explicit sign-out should eject.
      if (event === "SIGNED_OUT") {
        setSession(null);
        router.replace(`/${locale}/login`);
      }
    });

    return () => subscription.unsubscribe();
  }, [locale, router, setSession, setLoading]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center" role="status" aria-label="Loading">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!session) return null;

  return <>{children}</>;
}
