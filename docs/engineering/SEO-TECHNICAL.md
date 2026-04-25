# SEO & Technical Implementation Guide

> See also: [[STATE-MANAGEMENT.md]], [[TESTING-STRATEGY.md]]

Volaura's primary SEO surface is public volunteer profiles (`/u/{username}`) and event pages (`/events/{id}`). All SEO implementation prioritizes discoverability, shareability, and Core Web Vitals.

---

## Public Profiles: The SEO Crown Jewel

### Why Public Profiles Matter

Public profiles are **the most valuable SEO asset**:
- Each volunteer becomes an indexable page (thousands of long-tail keywords)
- Profiles link to events, creating a dense semantic graph
- Volunteer bios are user-generated, long-form content (ideal for NLP)
- Share links (LinkedIn, WhatsApp) drive referral traffic

### Architecture: ISR + Structured Data

```typescript
// apps/web/src/app/[locale]/u/[username]/page.tsx
import { Metadata } from "next";
import { notFound } from "next/navigation";
import initTranslations from "@/app/i18n";
import { createClient } from "@/lib/supabase/server";

interface PageProps {
  params: Promise<{ locale: string; username: string }>;
}

export const revalidate = 60; // ISR: revalidate every 60 seconds

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { username, locale } = await params;

  const supabase = await createClient();
  const { data: profile, error } = await supabase
    .from("profiles")
    .select("*, aura_scores(*), competencies(*)")
    .eq("username", username)
    .single();

  if (error || !profile) return notFound();

  const { t } = await initTranslations(locale, ["profile"]);
  const title = `${profile.first_name} ${profile.last_name} — AURA ${profile.aura_scores.badge} | Volaura`;
  const description = `${profile.first_name} has a verified Volaura profile with AURA Score ${Math.round(
    profile.aura_scores.total
  )}. Specialties: ${profile.competencies.map((c) => c.name).join(", ")}.`;
  const ogImageUrl = `${process.env.NEXT_PUBLIC_API_URL}/api/v1/share/${username}/og-image`;

  return {
    title,
    description,
    openGraph: {
      title,
      description,
      type: "profile",
      url: `https://volaura.com/${locale}/u/${username}`,
      images: [
        {
          url: ogImageUrl,
          width: 1200,
          height: 630,
          alt: title,
        },
      ],
      authors: [profile.first_name],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: [ogImageUrl],
    },
    alternates: {
      languages: {
        az: `https://volaura.com/az/u/${username}`,
        en: `https://volaura.com/en/u/${username}`,
        "x-default": `https://volaura.com/az/u/${username}`,
      },
    },
  };
}

export async function generateStaticParams({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;

  // Pre-render top 1000 volunteers (sorted by AURA score)
  const supabase = await createClient();
  const { data: profiles } = await supabase
    .from("profiles")
    .select("username")
    .order("aura_scores.total", { ascending: false })
    .limit(1000);

  return (
    profiles?.map((p) => ({
      locale,
      username: p.username,
    })) || []
  );
}

export default async function ProfilePage({ params }: PageProps) {
  const { username, locale } = await params;
  const { t } = await initTranslations(locale, ["profile"]);

  const supabase = await createClient();
  const { data: profile } = await supabase
    .from("profiles")
    .select(
      `
      *,
      aura_scores(*),
      competencies(*),
      event_registrations(
        event:events(id, title, date)
      )
    `
    )
    .eq("username", username)
    .single();

  if (!profile) return notFound();

  return (
    <>
      {/* Structured Data */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(generatePersonSchema(profile, locale)),
        }}
      />

      <div className="container py-8">
        {/* Profile header, bio, AURA score, etc. */}
      </div>
    </>
  );
}

function generatePersonSchema(profile: Profile, locale: string) {
  return {
    "@context": "https://schema.org",
    "@type": "Person",
    name: `${profile.first_name} ${profile.last_name}`,
    url: `https://volaura.com/${locale}/u/${profile.username}`,
    description: profile.bio,
    image: profile.avatar_url,
    knowsAbout: profile.competencies.map((c) => c.name),
    hasCredential: {
      "@type": "EducationalOccupationalCredential",
      name: `AURA ${profile.aura_scores.badge} Badge`,
      credentialCategory: "Volunteer Competency",
      recognizedBy: {
        "@type": "Organization",
        name: "Volaura",
        url: "https://volaura.com",
      },
    },
    affiliation: profile.event_registrations.map((reg) => ({
      "@type": "Event",
      name: reg.event.title,
      startDate: reg.event.date,
    })),
    sameAs: [
      ...(profile.github_url ? [profile.github_url] : []),
      ...(profile.linkedin_url ? [profile.linkedin_url] : []),
    ],
  };
}
```

### OG Image Generation (Dynamic)

Volunteer profiles need unique OG images for social sharing. Generate these dynamically:

```typescript
// apps/api/app/routes/share.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import asyncio

router = APIRouter(prefix="/api/v1/share", tags=["share"])

@router.get("/{username}/og-image")
async def get_og_image(username: str, db: SupabaseUser):
    """Generate OG image for volunteer profile."""

    # Fetch profile
    profile_result = await db.table("profiles") \
        .select("*, aura_scores(*)") \
        .eq("username", username) \
        .single() \
        .execute()

    if not profile_result.data:
        raise HTTPException(status_code=404, detail="Profile not found")

    profile = profile_result.data

    # Create image
    img = Image.new("RGB", (1200, 630), color="#FFFFFF")
    draw = ImageDraw.Draw(img)

    # Fonts (ensure these exist in the API container)
    title_font = ImageFont.truetype("fonts/bold.ttf", 60)
    subtitle_font = ImageFont.truetype("fonts/regular.ttf", 40)
    badge_font = ImageFont.truetype("fonts/bold.ttf", 50)

    # Draw background gradient (simplified: solid color)
    # In production, use Pillow gradient library or pre-rendered backgrounds
    draw.rectangle([(0, 0), (1200, 630)], fill="#F3F4F6")

    # Draw name
    name = f"{profile['first_name']} {profile['last_name']}"
    draw.text((60, 80), name, fill="#000000", font=title_font)

    # Draw AURA score and badge
    aura = profile["aura_scores"]
    score_text = f"AURA {aura['badge'].upper()}"
    score_number = f"{int(aura['total'])}"

    draw.text((60, 200), score_number, fill="#3B82F6", font=badge_font)
    draw.text((60, 290), score_text, fill="#60A5FA", font=subtitle_font)

    # Draw competencies
    competencies_text = " • ".join(profile["competencies"][:3])
    draw.text((60, 400), competencies_text, fill="#6B7280", font=subtitle_font)

    # Draw Volaura logo + URL
    draw.text((60, 550), "volaura.com", fill="#9CA3AF", font=subtitle_font)

    # Convert to bytes
    img_bytes = BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    return StreamingResponse(
        iter([img_bytes.getvalue()]),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400"}, # 24h cache
    )
```

### Share Cards (LinkedIn, WhatsApp, etc.)

Include share buttons on profile page:

```typescript
// apps/web/src/components/ShareButtons.tsx
"use client";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";

interface ShareButtonsProps {
  profile: Profile;
  locale: string;
}

export function ShareButtons({ profile, locale }: ShareButtonsProps) {
  const { t } = useTranslation();
  const profileUrl = `https://volaura.com/${locale}/u/${profile.username}`;
  const ogImageUrl = `${process.env.NEXT_PUBLIC_API_URL}/api/v1/share/${profile.username}/og-image`;

  const shares = [
    {
      name: "LinkedIn",
      url: `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(
        profileUrl
      )}`,
      icon: "linkedin",
    },
    {
      name: "WhatsApp",
      url: `https://wa.me/?text=${encodeURIComponent(
        `Check out ${profile.first_name}'s Volaura profile: ${profileUrl}`
      )}`,
      icon: "whatsapp",
    },
    {
      name: "Twitter",
      url: `https://twitter.com/intent/tweet?url=${encodeURIComponent(
        profileUrl
      )}&text=${encodeURIComponent(
        `${profile.first_name} has a verified Volaura profile with AURA ${profile.aura_scores.badge} badge`
      )}`,
      icon: "twitter",
    },
    {
      name: "Email",
      url: `mailto:?subject=${encodeURIComponent(
        `Check out ${profile.first_name}'s Volaura profile`
      )}&body=${encodeURIComponent(profileUrl)}`,
      icon: "email",
    },
  ];

  return (
    <div className="flex gap-2">
      {shares.map((share) => (
        <Button
          key={share.name}
          variant="outline"
          size="sm"
          onClick={() => window.open(share.url, "_blank")}
        >
          {share.icon}
        </Button>
      ))}
    </div>
  );
}
```

---

## Sitemap & Discovery

### Dynamic Sitemap

```typescript
// apps/web/src/app/sitemap.ts
import { MetadataRoute } from "next";
import { createClient } from "@/lib/supabase/server";

export const revalidate = 86400; // Revalidate daily

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const supabase = await createClient();

  // Fetch all public profiles
  const { data: profiles } = await supabase
    .from("profiles")
    .select("username, updated_at");

  // Fetch all public events
  const { data: events } = await supabase
    .from("events")
    .select("id, updated_at");

  // Static pages
  const staticPages: MetadataRoute.Sitemap = [
    {
      url: "https://volaura.com/en",
      changeFrequency: "weekly",
      priority: 1.0,
    },
    {
      url: "https://volaura.com/az",
      changeFrequency: "weekly",
      priority: 1.0,
    },
    {
      url: "https://volaura.com/en/about",
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: "https://volaura.com/en/events",
      changeFrequency: "daily",
      priority: 0.9,
    },
  ];

  // Profile pages
  const profilePages: MetadataRoute.Sitemap = (profiles || []).map(
    (profile) => ({
      url: `https://volaura.com/en/u/${profile.username}`,
      lastModified: profile.updated_at,
      changeFrequency: "weekly" as const,
      priority: 0.7,
    })
  );

  // Event pages
  const eventPages: MetadataRoute.Sitemap = (events || []).map((event) => ({
    url: `https://volaura.com/en/events/${event.id}`,
    lastModified: event.updated_at,
    changeFrequency: "daily" as const,
    priority: 0.8,
  }));

  return [...staticPages, ...profilePages, ...eventPages];
}
```

### robots.txt

```typescript
// apps/web/src/app/robots.ts
import { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: ["/api/", "/auth/", "/dashboard/", "/_next/"],
      },
    ],
    sitemap: "https://volaura.com/sitemap.xml",
  };
}
```

---

## Core Web Vitals Optimization

### Target Metrics

| Metric | Target | Tool |
|--------|--------|------|
| **LCP** (Largest Contentful Paint) | <2.5s (public), <1s (ISR) | Web Vitals API |
| **FID** (First Input Delay) | <100ms | Web Vitals API |
| **CLS** (Cumulative Layout Shift) | <0.1 | Web Vitals API |
| **TTFB** (Time to First Byte) | <100ms (Vercel edge) | Server timing |

### Measuring in Next.js

```typescript
// apps/web/src/app/layout.tsx
import { registerWebVitals } from "@/lib/vitals";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html>
      <body>
        {children}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              import('web-vitals').then(({ getCLS, getFID, getFCP, getLCP, getTTFB }) => {
                getCLS(console.log);
                getFID(console.log);
                getFCP(console.log);
                getLCP(console.log);
                getTTFB(console.log);
              });
            `,
          }}
        />
      </body>
    </html>
  );
}
```

### Optimization Strategies

**1. Image Optimization**

```typescript
// Profile avatars: lazy load, responsive sizes
import Image from "next/image";

<Image
  src={profile.avatar_url}
  alt={`${profile.first_name}'s profile`}
  width={200}
  height={200}
  quality={80}
  priority={false}
  placeholder="blur"
  blurDataURL={generateBlurhash(profile.avatar_hash)}
/>;
```

**2. Code Splitting**

```typescript
// Heavy components (charts, modals) use dynamic imports
import dynamic from "next/dynamic";

const AURARadarChart = dynamic(() =>
  import("@/components/AURARadarChart").then((mod) => mod.AURARadarChart)
);

export function ProfileHeader() {
  return (
    <Suspense fallback={<Skeleton />}>
      <AURARadarChart />
    </Suspense>
  );
}
```

**3. Font Optimization**

```typescript
// apps/web/src/app/layout.tsx
import { Inter } from "next/font/google";

const inter = Inter({
  subsets: ["latin"],
  display: "swap", // Use system font while loading
  preload: true,
});

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.className}>
      <body>{children}</body>
    </html>
  );
}
```

**4. CSS Optimization (Tailwind 4)**

```css
/* apps/web/src/app/globals.css */
@import "tailwindcss";

/* Exclude unused utilities with @layer */
@layer utilities {
  /* Only load utilities used in components */
}
```

---

## Internationalization (i18n) & hreflang

### URL Structure

```
/az/               → Azerbaijani (default)
/en/               → English
/az/u/username     → Azerbaijani profile
/en/u/username     → English profile
```

### Canonical & hreflang

```typescript
export async function generateMetadata({
  params,
}: PageProps): Promise<Metadata> {
  const { locale, username } = await params;

  const canonicalUrl = `https://volaura.com/az/u/${username}`;

  return {
    alternates: {
      canonical: canonicalUrl,
      languages: {
        az: `https://volaura.com/az/u/${username}`,
        en: `https://volaura.com/en/u/${username}`,
        "x-default": canonicalUrl,
      },
    },
  };
}
```

### Language Detection & Redirect

```typescript
// apps/web/src/middleware.ts
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // If root path, redirect to preferred language
  if (pathname === "/") {
    const locale = request.headers.get("accept-language")?.startsWith("en")
      ? "en"
      : "az";

    return NextResponse.redirect(new URL(`/${locale}`, request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    "/((?!_next/static|_next/image|favicon.ico).*)",
  ],
};
```

---

## JSON-LD Schemas

### Person Schema (Profile Page)

```typescript
{
  "@context": "https://schema.org",
  "@type": "Person",
  "name": "Leyla Aliyeva",
  "url": "https://volaura.com/en/u/leyla",
  "description": "Verified profile specializing in community outreach",
  "image": "https://volaura.com/avatars/leyla.jpg",
  "knowsAbout": ["Community Outreach", "Leadership", "English"],
  "hasCredential": {
    "@type": "EducationalOccupationalCredential",
    "name": "AURA Gold Badge",
    "credentialCategory": "Professional",
    "recognizedBy": {
      "@type": "Organization",
      "name": "Volaura",
      "url": "https://volaura.com"
    }
  },
  "affiliation": [
    {
      "@type": "Event",
      "name": "Launch Event Baku",
      "startDate": "2026-05-15"
    }
  ]
}
```

### Event Schema (Event Page)

```typescript
{
  "@context": "https://schema.org",
  "@type": "Event",
  "name": "Launch Event Opening Ceremony",
  "startDate": "2026-05-15T09:00:00Z",
  "endDate": "2026-05-15T17:00:00Z",
  "url": "https://volaura.com/en/events/launch-event",
  "description": "Join us for the opening ceremony of our major launch event in Baku",
  "image": "https://volaura.com/events/event-preview.jpg",
  "location": {
    "@type": "Place",
    "name": "Baku Convention Center",
    "address": {
      "@type": "PostalAddress",
      "streetAddress": "...",
      "addressLocality": "Baku",
      "addressCountry": "AZ"
    }
  },
  "organizer": {
    "@type": "Organization",
    "name": "Volaura",
    "url": "https://volaura.com"
  },
  "eventAttendanceMode": "OfflineEventAttendanceMode",
  "eventStatus": "EventScheduled"
}
```

---

## Search Console & Analytics Setup

### Google Search Console

1. Add both `/az/` and `/en/` as separate properties
2. Submit sitemaps:
   - `https://volaura.com/sitemap.xml`
3. Monitor:
   - Coverage (indexed pages)
   - Performance (CTR, impressions, position)
   - Indexing errors

### GA4 Setup

```typescript
// apps/web/src/app/layout.tsx
import { GoogleAnalytics } from "@next/third-parties/google";

export default function RootLayout() {
  return (
    <html>
      <body>
        <GoogleAnalytics gaId={process.env.NEXT_PUBLIC_GA_ID} />
      </body>
    </html>
  );
}
```

Track volunteer profile views:

```typescript
// Track when profile is viewed
useEffect(() => {
  gtag.event("view_profile", {
    profile_id: profile.id,
    aura_badge: profile.aura_scores.badge,
    competencies: profile.competencies.length,
  });
}, [profile.id]);
```

---

## Preventing SEO Issues

### ❌ Don't: Index Protected Pages

```typescript
// WRONG: Dashboard pages should NOT be indexed
export const metadata: Metadata = {
  // Missing robots: { index: false }
};
```

```typescript
// CORRECT: Explicitly prevent indexing
export const metadata: Metadata = {
  robots: {
    index: false,
    follow: false,
  },
};
```

### ❌ Don't: Duplicate Content Across Languages

```typescript
// WRONG: Same content, no hreflang
<head>
  <title>Profile</title>
  {/* No alternates */}
</head>
```

```typescript
// CORRECT: Signal language alternates
export const metadata: Metadata = {
  alternates: {
    languages: {
      az: "https://volaura.com/az/u/...",
      en: "https://volaura.com/en/u/...",
    },
  },
};
```

### ❌ Don't: Slow down with Blocking Resources

```typescript
// WRONG: Blocks FCP
<script src="tracking.js" />{/* no async */}

// CORRECT: Use defer or dynamic loading
<script src="tracking.js" defer />
```

---

## Monitoring & Continuous Improvement

### Automated Checks

```bash
# Check for SEO issues in CI
pnpm run seo:check

# Audit lighthouse scores
pnpm run lighthouse:ci --url https://volaura.com/en
```

### Monthly Reviews

- Top 50 pages by traffic in Search Console
- Pages with low CTR (< 2%) — improve title/description
- Pages with low position (> 50) — improve content quality
- New profiles not indexed — check visibility settings

---

## References

- [[STATE-MANAGEMENT.md]]
- [[TESTING-STRATEGY.md]]
- Next.js Metadata API: https://nextjs.org/docs/app/building-your-application/optimizing/metadata
- Next.js ISR: https://nextjs.org/docs/app/building-your-application/data-fetching/incremental-static-regeneration
- schema.org: https://schema.org
- Google Search Central: https://developers.google.com/search
- Core Web Vitals Guide: https://web.dev/vitals/

