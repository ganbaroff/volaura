"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  getFeedApiLifesimFeedGet,
  getNextChoiceApiLifesimNextChoiceGet,
  purchaseShopItemApiLifesimPurchasePost,
  submitChoiceApiLifesimChoicePost,
} from "@/lib/api/generated";
import type {
  FeedResponse,
  NextChoiceResponse,
} from "@/lib/api/generated/types.gen";

/**
 * LifeSim queries + mutations — Life Feed MVP (sprint A7).
 *
 * Uses generated SDK from /api/lifesim/* — pure typed; no hand-written paths.
 * Mirrors the pattern in use-aura / use-assessment. All 4xx errors surface as
 * structured `detail.code` strings that the page renders as inline messages
 * (no exception boundaries needed for happy path).
 */

interface NextChoiceParams {
  age: number;
  intelligence?: number;
  social?: number;
  energy?: number;
  happiness?: number;
  health?: number;
  money?: number;
  work_experience?: number;
  category?: string;
}

export function useLifesimFeed(limit = 50) {
  return useQuery<FeedResponse>({
    queryKey: ["lifesim-feed", limit],
    queryFn: async () => {
      const { data, error } = await getFeedApiLifesimFeedGet({
        query: { limit },
      });
      if (error) throw new Error("Failed to fetch life feed");
      return (data ?? { data: [] }) as FeedResponse;
    },
    staleTime: 30 * 1000, // feed updates on each choice — short stale so UI reflects fast
  });
}

export function useLifesimNextChoice(params: NextChoiceParams, enabled = true) {
  return useQuery<NextChoiceResponse>({
    queryKey: ["lifesim-next-choice", params],
    queryFn: async () => {
      const { data, error } = await getNextChoiceApiLifesimNextChoiceGet({
        query: params,
      });
      if (error) throw new Error("Failed to fetch next choice");
      return (data ?? { event: null, pool_size: 0 }) as NextChoiceResponse;
    },
    enabled,
    // Don't auto-refetch — user pulls next choice explicitly via mutation follow-up
    staleTime: Infinity,
    refetchOnWindowFocus: false,
  });
}

interface SubmitChoiceArgs {
  event_id: string;
  choice_index: number;
  stats_before: Record<string, number>;
}

export function useLifesimSubmitChoice() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (args: SubmitChoiceArgs) => {
      const { data, error } = await submitChoiceApiLifesimChoicePost({
        body: args,
      });
      if (error) throw new Error("Choice submission failed");
      if (!data) throw new Error("Empty response from choice endpoint");
      return data;
    },
    onSuccess: () => {
      // Feed updated server-side — invalidate so next render shows new row
      queryClient.invalidateQueries({ queryKey: ["lifesim-feed"] });
      queryClient.invalidateQueries({ queryKey: ["lifesim-next-choice"] });
    },
  });
}

interface PurchaseArgs {
  shop_item: string;
  current_crystals: number;
}

export function useLifesimPurchase() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (args: PurchaseArgs) => {
      const { data, error } = await purchaseShopItemApiLifesimPurchasePost({
        body: args,
      });
      if (error) throw new Error("Crystal purchase failed");
      if (!data) throw new Error("Empty response from purchase endpoint");
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["lifesim-feed"] });
      queryClient.invalidateQueries({ queryKey: ["aura-score"] }); // crystal balance lives here
    },
  });
}
