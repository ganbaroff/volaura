"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api/client";
import { useAuthToken } from "./use-auth-token";

export interface SubscriptionStatus {
  status: "trial" | "active" | "expired" | "cancelled";
  trial_ends_at: string | null;
  subscription_ends_at: string | null;
  days_remaining: number;
  is_active: boolean;
}

export interface UseSubscriptionResult {
  status: SubscriptionStatus["status"] | undefined;
  daysRemaining: number | undefined;
  isActive: boolean;
  isTrial: boolean;
  isExpired: boolean;
  trialEndsAt: string | null | undefined;
  subscriptionEndsAt: string | null | undefined;
  isLoading: boolean;
  error: Error | null;
}

/**
 * Fetches the current user's subscription status from GET /api/subscription/status.
 * Auth token obtained via Supabase session.
 */
export function useSubscription(): UseSubscriptionResult {
  const getToken = useAuthToken();

  const { data, isLoading, error } = useQuery<SubscriptionStatus | null>({
    queryKey: ["subscription-status"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) return null;
      return apiFetch<SubscriptionStatus>("/api/subscription/status", { token });
    },
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });

  return {
    status: data?.status,
    daysRemaining: data?.days_remaining,
    isActive: data?.is_active ?? false,
    isTrial: data?.status === "trial",
    isExpired: data?.status === "expired",
    trialEndsAt: data?.trial_ends_at,
    subscriptionEndsAt: data?.subscription_ends_at,
    isLoading,
    error: error as Error | null,
  };
}
