# Frontend Rules (Next.js 14 + shadcn + i18n)

## App Router Only
- All pages in `app/[locale]/` directory
- Use `generateStaticParams` for locale segments
- Server Components by default, `"use client"` only when needed
- Use `params: Promise<{}>` pattern (Next.js 14.2+)

## i18n
```tsx
// Server Component
import initTranslations from "@/app/i18n";

export default async function Page({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  const { t } = await initTranslations(locale, ["common"]);
  return <h1>{t("landing.title")}</h1>;
}

// Client Component
"use client";
import { useTranslation } from "react-i18next";

export function MyComponent() {
  const { t } = useTranslation();
  return <p>{t("common.loading")}</p>;
}
```

## Component Patterns
- Use shadcn/ui for base components
- Compose features in `components/features/`
- Use `cn()` from `@/lib/utils/cn` for conditional classes
- Props interfaces above component definition

## State Management
- Server state: TanStack Query (fetching, caching, mutations)
- Client state: Zustand stores in `stores/`
- Form state: React Hook Form + Zod

## Supabase (Browser)
```typescript
import { createClient } from "@/lib/supabase/client";
const supabase = createClient();
```

## Supabase (Server Component)
```typescript
import { createClient } from "@/lib/supabase/server";
const supabase = await createClient();
```

## API Calls
Use generated types from @hey-api/openapi-ts:
```typescript
import { getHealth } from "@/lib/api/generated";
```

## Tailwind CSS 4
- Use `@import "tailwindcss"` in globals.css
- Theme via `@theme {}` block
- No tailwind.config.js needed
