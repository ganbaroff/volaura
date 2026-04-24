export function buildLoginNextPath(locale: string, nextPath: string): string {
  return `/${locale}/login?next=${encodeURIComponent(nextPath)}`;
}
