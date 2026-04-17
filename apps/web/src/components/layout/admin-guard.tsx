"use client";

import { useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";
import { useAdminPing } from "@/hooks/queries/use-admin";
import { Skeleton } from "@/components/ui/skeleton";

/**
 * AdminGuard — blocks non-admin users from the (admin) route group.
 *
 * Two-layer check:
 * 1. Session must exist (inherits from auth-store)
 * 2. GET /api/admin/ping must return 200 (backend verifies is_platform_admin)
 *
 * Redirects to /dashboard on failure, not /login — to avoid leaking that
 * an admin panel exists to unauthenticated users who happen to guess the URL.
 */
export function AdminGuard({ children }: { children: React.ReactNode }) {
  const { locale } = useParams<{ locale: string }>();
  const router = useRouter();
  const { session, isLoading: sessionLoading } = useAuthStore();
  const { data: isAdmin, isLoading: pingLoading } = useAdminPing();

  const isLoading = sessionLoading || pingLoading;

  useEffect(() => {
    if (isLoading) return;
    if (!session) {
      router.replace(`/${locale}/login`);
      return;
    }
    if (isAdmin === false) {
      // Authenticated but not admin — redirect silently to dashboard
      router.replace(`/${locale}/dashboard`);
    }
  }, [isLoading, session, isAdmin, locale, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen p-8 space-y-6" role="status" aria-label="Loading">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-28 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  if (!session || !isAdmin) return null;

  return <>{children}</>;
}
