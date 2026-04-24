export function getCallbackProfileRoute(
  locale: string,
  profileStatus: number | "network-error",
): string {
  if (profileStatus === 404) {
    return `/${locale}/onboarding`;
  }

  if (typeof profileStatus === "number" && profileStatus >= 200 && profileStatus < 300) {
    return `/${locale}/dashboard`;
  }

  return `/${locale}/login?message=oauth-error`;
}
