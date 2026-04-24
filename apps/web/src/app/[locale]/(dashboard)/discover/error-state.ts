import { ApiError } from "@/lib/api/client";

export interface DiscoverErrorState {
  title: string;
  description: string;
  actionLabel: string | null;
  action: "login" | "retry" | null;
}

export function getDiscoverBrowseErrorState(error: unknown): DiscoverErrorState {
  if (error instanceof ApiError && error.status === 401) {
    return {
      title: "Session expired",
      description: "Please sign in again to continue talent discovery.",
      actionLabel: "Sign in again",
      action: "login",
    };
  }

  if (error instanceof ApiError && error.status === 403) {
    return {
      title: "Organization access required",
      description: "Talent discovery is available to organization accounts only.",
      actionLabel: null,
      action: null,
    };
  }

  return {
    title: "Could not load professionals",
    description: "Please try again.",
    actionLabel: "Retry",
    action: "retry",
  };
}

export function getDiscoverSearchErrorState(error: unknown): DiscoverErrorState {
  if (error instanceof ApiError && error.status === 401) {
    return {
      title: "Session expired",
      description: "Please sign in again to continue smart search.",
      actionLabel: "Sign in again",
      action: "login",
    };
  }

  if (error instanceof ApiError && error.status === 403) {
    return {
      title: "Organization access required",
      description: "Smart search is available to organization accounts only.",
      actionLabel: null,
      action: null,
    };
  }

  return {
    title: "Search failed",
    description: "Please try again.",
    actionLabel: "Retry",
    action: "retry",
  };
}
