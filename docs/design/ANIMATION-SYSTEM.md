# Volaura Animation System

**Last Updated:** 2026-03-22
**Framework:** Framer Motion (React)
**Purpose:** Define all micro-interactions, transitions, and decorative animations for Volaura platform
**Scope:** Web (Next.js 14) and PWA (with mobile-first responsive considerations)

---

## Global Animation Parameters

All animations use **Framer Motion**. Define these values in `apps/web/src/lib/animation/constants.ts`:

### Spring Presets

```typescript
// apps/web/src/lib/animation/constants.ts

export const ANIMATION_SPRINGS = {
  // Smooth, natural motion (default for most interactions)
  default: {
    type: "spring",
    stiffness: 260,
    damping: 20,
    mass: 1,
  },
  // Slower, more deliberate motion (entrances, exits)
  gentle: {
    type: "spring",
    stiffness: 120,
    damping: 14,
    mass: 1,
  },
  // Playful, with visible bounce (celebratory moments)
  bouncy: {
    type: "spring",
    stiffness: 400,
    damping: 10,
    mass: 0.8,
  },
  // Very stiff, almost immediate (subtle feedback)
  stiff: {
    type: "spring",
    stiffness: 500,
    damping: 30,
    mass: 1,
  },
} as const;
```

### Easing Curves

```typescript
export const ANIMATION_EASINGS = {
  // Default ease-in-out
  default: [0.25, 0.1, 0.25, 1],
  // Ease-in (accelerate)
  easeIn: [0.42, 0, 1, 1],
  // Ease-out (decelerate)
  easeOut: [0, 0, 0.58, 1],
  // Ease-in-out
  easeInOut: [0.42, 0, 0.58, 1],
} as const;
```

### Duration Presets

```typescript
export const ANIMATION_DURATIONS = {
  // Very quick feedback (button press, toggle)
  fast: 0.15, // 150ms
  // Standard interaction (page slide, fade)
  normal: 0.3, // 300ms
  // Deliberate, attention-grabbing (score counter, badge reveal)
  slow: 0.5, // 500ms
  // Extended, cinematic (hero animations, page transitions)
  slower: 0.8, // 800ms
} as const;
```

### Global Settings

```typescript
export const ANIMATION_CONFIG = {
  // Always respect prefers-reduced-motion
  respectReducedMotion: true,
  // Stagger increment for sequential animations (e.g., list items)
  staggerDelay: 0.05, // 50ms between items
  // Minimum animation duration for accessibility
  minDuration: 0.1, // 100ms
} as const;
```

---

## Animation Catalog

Each animation is identified by an **ID (Axx)**, has a **Name**, **Trigger**, **Spec**, and **Priority**.

### A01–A02: Page Transitions

#### A01: Page Fade

**ID:** A01
**Name:** Page Fade
**Trigger:** Route change (all pages)
**Priority:** Critical
**Trigger Condition:** `useEffect(() => { ... }, [pathname])`

**Spec:**
- **Element:** Full page container (div with `key={pathname}`)
- **Animation:** Opacity fade
- **Start:** `opacity: 0`
- **End:** `opacity: 1`
- **Duration:** 200ms
- **Easing:** `easeOut`
- **When disabled (prefers-reduced-motion):** Instant (no animation)

**Implementation:**

```tsx
// apps/web/src/components/PageTransition.tsx
"use client";

import { motion } from "framer-motion";
import { useReducedMotion } from "framer-motion";
import { usePathname } from "next/navigation";
import { ANIMATION_DURATIONS, ANIMATION_EASINGS } from "@/lib/animation/constants";

interface PageTransitionProps {
  children: React.ReactNode;
}

export function PageTransition({ children }: PageTransitionProps) {
  const pathname = usePathname();
  const prefersReduced = useReducedMotion();

  return (
    <motion.div
      key={pathname}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{
        duration: prefersReduced ? 0 : ANIMATION_DURATIONS.fast,
        ease: ANIMATION_EASINGS.easeOut,
      }}
    >
      {children}
    </motion.div>
  );
}
```

**Usage in Layout:**

```tsx
// apps/web/src/app/[locale]/layout.tsx
import { PageTransition } from "@/components/PageTransition";

export default async function Layout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  return (
    <PageTransition>
      {children}
    </PageTransition>
  );
}
```

---

#### A02: Page Slide (Mobile)

**ID:** A02
**Name:** Page Slide
**Trigger:** Route change on mobile (viewport < 768px)
**Priority:** High
**Device:** Mobile only (breakpoint: < 768px)

**Spec:**
- **Element:** Full page container
- **Animation:** Horizontal slide
- **Direction:** Previous page exits left, new page enters from right
- **Start:** `translateX(-100%)`
- **End:** `translateX(0)`
- **Duration:** 300ms
- **Spring:** default spring (stiffness: 260, damping: 20)
- **When disabled:** Fall back to A01 (Page Fade)

**Implementation:**

```tsx
// apps/web/src/components/PageSlide.tsx
"use client";

import { motion } from "framer-motion";
import { useReducedMotion } from "framer-motion";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ANIMATION_SPRINGS } from "@/lib/animation/constants";
import { useMediaQuery } from "@/lib/hooks/useMediaQuery";

interface PageSlideProps {
  children: React.ReactNode;
}

export function PageSlide({ children }: PageSlideProps) {
  const pathname = usePathname();
  const isMobile = useMediaQuery("(max-width: 768px)");
  const prefersReduced = useReducedMotion();
  const [direction, setDirection] = useState<1 | -1>(1);

  if (!isMobile || prefersReduced) {
    // Fall back to fade on desktop or if reduced motion
    return (
      <motion.div
        key={pathname}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.2, ease: "easeOut" }}
      >
        {children}
      </motion.div>
    );
  }

  return (
    <motion.div
      key={pathname}
      initial={{ x: direction > 0 ? 1000 : -1000, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: direction > 0 ? -1000 : 1000, opacity: 0 }}
      transition={{
        ...ANIMATION_SPRINGS.default,
      }}
    >
      {children}
    </motion.div>
  );
}
```

---

### A03–A05: Score Animations

#### A03: Score Counter

**ID:** A03
**Name:** Score Counter
**Trigger:** Score reveal on results page
**Priority:** Critical
**Component:** `ScoreDisplay` component

**Spec:**
- **Element:** Large number displaying AURA score (e.g., "87 / 100")
- **Animation:** Count up from 0 to final score
- **Duration:** 2 seconds
- **Easing:** `easeOut`
- **Font:** JetBrains Mono, 64px, bold
- **Details:**
  - Each digit ticks independently for visual interest
  - Number color: primary brand color (blue)
  - Opacity animates 0→1 simultaneously
  - Sound effect: optional subtle "tick" for each number change (accessibility consideration: provide visual feedback only if sound is unavailable)

**Implementation:**

```tsx
// apps/web/src/components/features/results/ScoreDisplay.tsx
"use client";

import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { ANIMATION_DURATIONS, ANIMATION_EASINGS } from "@/lib/animation/constants";

interface ScoreDisplayProps {
  score: number;
  maxScore?: number;
}

export function ScoreDisplay({ score, maxScore = 100 }: ScoreDisplayProps) {
  const [displayScore, setDisplayScore] = useState(0);

  useEffect(() => {
    const duration = 2; // seconds
    const steps = 60; // 60 frames @ 60fps ≈ 1 second smooth
    const increment = score / steps;
    let current = 0;

    const interval = setInterval(() => {
      current += increment;
      if (current >= score) {
        setDisplayScore(score);
        clearInterval(interval);
      } else {
        setDisplayScore(Math.floor(current));
      }
    }, (duration * 1000) / steps);

    return () => clearInterval(interval);
  }, [score]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: ANIMATION_DURATIONS.slow,
        ease: ANIMATION_EASINGS.easeOut,
      }}
      className="text-center"
    >
      <div className="font-mono text-6xl font-bold text-primary">
        {displayScore}
      </div>
      <div className="text-lg text-muted-foreground mt-2">
        / {maxScore}
      </div>
    </motion.div>
  );
}
```

---

#### A04: Badge Reveal

**ID:** A04
**Name:** Badge Reveal
**Trigger:** After score counter completes (A03)
**Priority:** Critical
**Component:** `BadgeCard` component

**Spec:**
- **Element:** Badge image/icon (Platinum/Gold/Silver/Bronze)
- **Animations:**
  1. Scale: 0 → 1.2 → 1 (with spring bouncy)
  2. Rotation: 0° → 15° → 0° (playful entrance)
  3. Color gradient sweep: gray → full color (300ms linear)
  4. Glow effect: 0 → 100% opacity (box-shadow)
- **Duration:** 600ms (spring), 300ms (color)
- **Delay after A03:** 200ms (wait for score to complete)
- **Spring:** bouncy preset (stiffness: 400, damping: 10)

**Implementation:**

```tsx
// apps/web/src/components/features/results/BadgeReveal.tsx
"use client";

import { motion } from "framer-motion";
import { BadgeTier } from "@/types/aura";
import { ANIMATION_SPRINGS, ANIMATION_DURATIONS } from "@/lib/animation/constants";

interface BadgeRevealProps {
  tier: BadgeTier;
  delay?: number; // delay after parent animation
}

const badgeColors = {
  platinum: "#e5e7eb",
  gold: "#fbbf24",
  silver: "#d1d5db",
  bronze: "#ea8c55",
  none: "#9ca3af",
};

export function BadgeReveal({ tier, delay = 0.2 }: BadgeRevealProps) {
  const badgeColor = badgeColors[tier];

  return (
    <motion.div
      initial={{ scale: 0, rotate: 0, opacity: 0 }}
      animate={{ scale: 1, rotate: 0, opacity: 1 }}
      transition={{
        ...ANIMATION_SPRINGS.bouncy,
        delay,
      }}
      className="relative"
    >
      {/* Badge glow effect */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{
          duration: ANIMATION_DURATIONS.normal,
          delay: delay + 0.1,
        }}
        className="absolute inset-0 blur-xl rounded-full"
        style={{
          background: badgeColor,
          opacity: 0.6,
        }}
      />

      {/* Badge image */}
      <motion.img
        src={`/badges/${tier}.png`}
        alt={`${tier} badge`}
        className="relative w-32 h-32 drop-shadow-lg"
        initial={{ filter: "grayscale(100%)" }}
        animate={{ filter: "grayscale(0%)" }}
        transition={{
          duration: ANIMATION_DURATIONS.normal,
          delay: delay + 0.1,
          ease: "linear",
        }}
      />

      {/* Sparkle particles (optional) */}
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          className="absolute w-2 h-2 rounded-full bg-white"
          initial={{
            opacity: 0,
            x: 0,
            y: 0,
          }}
          animate={{
            opacity: [1, 0],
            x: Math.cos((i / 3) * Math.PI * 2) * 60,
            y: Math.sin((i / 3) * Math.PI * 2) * 60,
          }}
          transition={{
            duration: 1,
            delay: delay + 0.3,
            ease: "easeOut",
          }}
        />
      ))}
    </motion.div>
  );
}
```

---

#### A05: Radar Chart Draw

**ID:** A05
**Name:** Radar Chart Draw
**Trigger:** Profile page loads or results page shows competency breakdown
**Priority:** High
**Component:** Recharts Radar (wrapped in Framer Motion)

**Spec:**
- **Element:** Radar chart axes (8 competencies)
- **Animation:** Each axis draws outward from center
- **Sequence:** Staggered, each axis starts 100ms after previous
- **Duration per axis:** 600ms
- **Spring:** gentle preset
- **Final state:** Full radar chart with all data visible

**Implementation:**

```tsx
// apps/web/src/components/features/profile/RadarChartAnimated.tsx
"use client";

import { motion } from "framer-motion";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
} from "recharts";
import { useReducedMotion } from "framer-motion";
import { ANIMATION_SPRINGS, ANIMATION_CONFIG } from "@/lib/animation/constants";

interface RadarChartAnimatedProps {
  data: Array<{
    name: string;
    value: number;
  }>;
}

export function RadarChartAnimated({ data }: RadarChartAnimatedProps) {
  const prefersReduced = useReducedMotion();

  // SVG path animation for each axis
  const axisVariants = {
    hidden: { pathLength: 0, opacity: 0 },
    visible: {
      pathLength: 1,
      opacity: 1,
      transition: {
        duration: prefersReduced ? 0 : 0.6,
        ease: "easeOut",
      },
    },
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="w-full h-96"
    >
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data} margin={{ top: 40, right: 120, bottom: 40, left: 120 }}>
          <motion.g
            initial="hidden"
            animate="visible"
            variants={{
              visible: {
                transition: {
                  staggerChildren: ANIMATION_CONFIG.staggerDelay,
                },
              },
            }}
          >
            <PolarGrid strokeDasharray="3 3" />
            <PolarAngleAxis dataKey="name" />
            <PolarRadiusAxis angle={90} domain={[0, 100]} />
          </motion.g>

          <Radar
            name="AURA Competencies"
            dataKey="value"
            stroke="hsl(var(--primary))"
            fill="hsl(var(--primary))"
            fillOpacity={0.6}
            animationDuration={600}
            animationEasing={prefersReduced ? "linear" : "ease"}
          />
        </RadarChart>
      </ResponsiveContainer>
    </motion.div>
  );
}
```

---

### A06–A09: Assessment Interactions

#### A06: Confetti Burst

**ID:** A06
**Name:** Confetti Burst
**Trigger:** Assessment completed successfully
**Priority:** High
**Component:** Full-page overlay or page element

**Spec:**
- **Element:** 50+ confetti particles with badge colors
- **Animation:** Particles burst from center, fall downward with gravity
- **Particle colors:** Badge tier color (gold, silver, bronze) + primary brand color
- **Lifetime:** 3 seconds
- **Physics simulation:**
  - Initial velocity: random, outward angle
  - Gravity: 9.8 m/s² (simulated with y-translation)
  - Rotation: random, spinning throughout lifetime
  - Opacity: 1 → 0 (fade at end)
- **When disabled:** Skip animation, show static success message

**Implementation:**

```tsx
// apps/web/src/components/features/assessment/ConfettiBurst.tsx
"use client";

import { motion } from "framer-motion";
import { useReducedMotion } from "framer-motion";

interface ConfettiBurstProps {
  duration?: number; // total animation time (ms)
}

const colors = ["#fbbf24", "#d1d5db", "#ea8c55", "#3b82f6", "#ec4899"];

function Particle({ index, duration }: { index: number; duration: number }) {
  const angle = (index / 50) * Math.PI * 2; // distribute around circle
  const velocity = 10 + Math.random() * 20; // pixels per second

  const x = Math.cos(angle) * velocity;
  const y = Math.sin(angle) * velocity;

  return (
    <motion.div
      key={index}
      initial={{
        x: 0,
        y: 0,
        opacity: 1,
        rotate: Math.random() * 360,
        scale: 1,
      }}
      animate={{
        x: x * (duration / 1000),
        y: y * (duration / 1000) + 100, // gravity effect
        opacity: 0,
        rotate: Math.random() * 720,
        scale: 0.5,
      }}
      transition={{
        duration: duration / 1000,
        ease: "easeOut",
      }}
      className="fixed w-3 h-3 rounded-full pointer-events-none"
      style={{
        backgroundColor: colors[index % colors.length],
        left: "50%",
        top: "50%",
        marginLeft: "-6px",
        marginTop: "-6px",
      }}
    />
  );
}

export function ConfettiBurst({ duration = 3000 }: ConfettiBurstProps) {
  const prefersReduced = useReducedMotion();

  if (prefersReduced) {
    return null; // Skip animation for accessibility
  }

  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden">
      {Array.from({ length: 50 }).map((_, i) => (
        <Particle key={i} index={i} duration={duration} />
      ))}
    </div>
  );
}
```

**Usage:**

```tsx
// In assessment completion screen
const { t } = useTranslation("assessment");
return (
  <>
    <ConfettiBurst duration={3000} />
    <h1>{t("assess.completeTitle")}</h1>
    {/* Rest of completion UI */}
  </>
);
```

---

#### A07: Question Transition

**ID:** A07
**Name:** Question Transition
**Trigger:** Next/Previous button clicked during assessment
**Priority:** High
**Component:** Assessment question container

**Spec:**
- **Current question:** Slides out to left (translateX: -100%)
- **New question:** Slides in from right (translateX: +100%)
- **Both:** Fade out/in simultaneously
- **Duration:** 300ms
- **Spring:** default preset
- **Stagger:** Slightly offset the exit and entrance (10ms)

**Implementation:**

```tsx
// apps/web/src/components/features/assessment/QuestionSlide.tsx
"use client";

import { motion } from "framer-motion";
import { useReducedMotion } from "framer-motion";
import { ANIMATION_SPRINGS, ANIMATION_DURATIONS } from "@/lib/animation/constants";

interface QuestionSlideProps {
  question: any; // Question type from API
  direction: "next" | "previous"; // direction of navigation
  children: React.ReactNode;
}

export function QuestionSlide({
  question,
  direction,
  children,
}: QuestionSlideProps) {
  const prefersReduced = useReducedMotion();

  const slideVariants = {
    enter: (direction: string) => ({
      x: direction === "next" ? 1000 : -1000,
      opacity: 0,
    }),
    center: {
      zIndex: 1,
      x: 0,
      opacity: 1,
    },
    exit: (direction: string) => ({
      zIndex: 0,
      x: direction === "next" ? -1000 : 1000,
      opacity: 0,
    }),
  };

  return (
    <motion.div
      key={question.id}
      custom={direction}
      variants={slideVariants}
      initial="enter"
      animate="center"
      exit="exit"
      transition={
        prefersReduced
          ? { duration: 0 }
          : {
              ...ANIMATION_SPRINGS.default,
              duration: ANIMATION_DURATIONS.normal,
            }
      }
    >
      {children}
    </motion.div>
  );
}
```

---

#### A08: Progress Increment

**ID:** A08
**Name:** Progress Increment
**Trigger:** Answer submitted to current question
**Priority:** High
**Component:** Progress bar (at top of assessment)

**Spec:**
- **Element:** Horizontal progress bar (width: 0–100%)
- **Animation:** Incrementally fill based on `currentQuestion / totalQuestions`
- **Duration:** 400ms
- **Easing:** `easeOut`
- **Color:** Primary brand color (blue)
- **Appearance:** Smooth, continuous bar with rounded ends

**Implementation:**

```tsx
// apps/web/src/components/features/assessment/ProgressBar.tsx
"use client";

import { motion } from "framer-motion";
import { useReducedMotion } from "framer-motion";
import { ANIMATION_DURATIONS, ANIMATION_EASINGS } from "@/lib/animation/constants";

interface ProgressBarProps {
  current: number;
  total: number;
}

export function ProgressBar({ current, total }: ProgressBarProps) {
  const prefersReduced = useReducedMotion();
  const progress = (current / total) * 100;

  return (
    <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
      <motion.div
        className="h-full bg-primary rounded-full"
        initial={{ width: "0%" }}
        animate={{ width: `${progress}%` }}
        transition={{
          duration: prefersReduced ? 0 : ANIMATION_DURATIONS.normal,
          ease: ANIMATION_EASINGS.easeOut,
        }}
      />
    </div>
  );
}
```

---

#### A09: BARS Scale Hover

**ID:** A09
**Name:** BARS Scale Hover
**Trigger:** Mouse/touch hover over BARS option (1–7 scale)
**Priority:** Medium
**Component:** BARS scale button option

**Spec:**
- **Element:** Single scale option button (e.g., "4 – Neutral")
- **Hover animation:**
  - Scale: 1 → 1.05
  - Color: muted → primary brand color (smooth transition)
  - Shadow: none → subtle drop shadow
- **Duration:** 150ms
- **Easing:** `easeOut`
- **Feedback:** Immediately revert on mouse leave

**Implementation:**

```tsx
// apps/web/src/components/features/assessment/BARSScale.tsx
"use client";

import { motion } from "framer-motion";
import { ANIMATION_DURATIONS, ANIMATION_EASINGS } from "@/lib/animation/constants";

interface BARSOptionProps {
  value: number; // 1-7
  label: string;
  selected: boolean;
  onSelect: (value: number) => void;
}

export function BARSOption({
  value,
  label,
  selected,
  onSelect,
}: BARSOptionProps) {
  return (
    <motion.button
      onClick={() => onSelect(value)}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.98 }}
      transition={{
        duration: ANIMATION_DURATIONS.fast,
        ease: ANIMATION_EASINGS.easeOut,
      }}
      className={`
        px-4 py-3 rounded-lg border-2 transition-colors
        ${
          selected
            ? "border-primary bg-primary/10 text-primary"
            : "border-muted bg-white text-muted-foreground hover:border-primary/50"
        }
      `}
    >
      <div className="font-semibold text-sm">{value}</div>
      <div className="text-xs mt-1">{label}</div>
    </motion.button>
  );
}
```

---

### A10–A12: Navigation

#### A10: Sidebar Collapse

**ID:** A10
**Name:** Sidebar Collapse
**Trigger:** Toggle sidebar button (mobile and desktop)
**Priority:** High
**Component:** Sidebar navigation

**Spec:**
- **Element:** Sidebar container
- **Animation:**
  - Width: 280px ↔ 64px
  - Icons: stay visible, remain centered
  - Labels: fade out (opacity 0 → 1)
  - Duration:** 300ms
  - **Spring:** default preset
- **Variants:**
  - Collapsed: width 64px, icons only, labels hidden
  - Expanded: width 280px, full labels visible

**Implementation:**

```tsx
// apps/web/src/components/Sidebar.tsx
"use client";

import { motion } from "framer-motion";
import { useState } from "react";
import { useReducedMotion } from "framer-motion";
import { ANIMATION_SPRINGS, ANIMATION_DURATIONS } from "@/lib/animation/constants";

interface SidebarProps {
  defaultCollapsed?: boolean;
}

export function Sidebar({ defaultCollapsed = false }: SidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);
  const prefersReduced = useReducedMotion();

  return (
    <motion.aside
      animate={{ width: isCollapsed ? 64 : 280 }}
      transition={
        prefersReduced
          ? { duration: 0 }
          : { ...ANIMATION_SPRINGS.default, duration: ANIMATION_DURATIONS.normal }
      }
      className="bg-white border-r border-border h-screen overflow-hidden"
    >
      <div className="p-4">
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="w-full flex items-center justify-center py-2"
        >
          {/* Toggle icon */}
        </button>
      </div>

      <nav className="space-y-2 px-2">
        {/* Navigation items */}
        {[
          { icon: "dashboard", label: "Dashboard" },
          { icon: "assessment", label: "Assessment" },
          { icon: "events", label: "Events" },
          { icon: "profile", label: "Profile" },
        ].map((item) => (
          <motion.a
            key={item.label}
            href="#"
            className="flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-accent"
            whileHover={{ backgroundColor: "hsl(var(--accent))" }}
            transition={{ duration: 0.2 }}
          >
            <span className="w-6 h-6">{/* Icon */}</span>
            <motion.span
              animate={{ opacity: isCollapsed ? 0 : 1 }}
              transition={{
                duration: prefersReduced ? 0 : ANIMATION_DURATIONS.fast,
              }}
              className="text-sm font-medium"
            >
              {item.label}
            </motion.span>
          </motion.a>
        ))}
      </nav>
    </motion.aside>
  );
}
```

---

#### A11: Bottom Nav Active

**ID:** A11
**Name:** Bottom Nav Active
**Trigger:** Tap/click navigation item in mobile bottom nav
**Priority:** Medium
**Component:** Bottom navigation bar (mobile)

**Spec:**
- **Element:** Individual nav item (icon + label)
- **Animations:**
  - Icon scale: 1 → 1.2 (spring bouncy)
  - Label opacity: 0.6 → 1 (fade in)
  - Indicator dot: slides in from bottom
  - Background: subtle color change
- **Duration:** 200ms
- **Stagger:** All animations start simultaneously
- **Inactive state:** Scale 0.9, opacity 0.6

**Implementation:**

```tsx
// apps/web/src/components/BottomNav.tsx
"use client";

import { motion } from "framer-motion";
import { useReducedMotion } from "framer-motion";
import { usePathname } from "next/navigation";
import { ANIMATION_SPRINGS, ANIMATION_DURATIONS } from "@/lib/animation/constants";

interface BottomNavProps {
  items: Array<{ icon: React.ReactNode; label: string; href: string }>;
}

export function BottomNav({ items }: BottomNavProps) {
  const pathname = usePathname();
  const prefersReduced = useReducedMotion();
  const isActive = (href: string) => pathname.includes(href);

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-border flex justify-around md:hidden">
      {items.map((item) => {
        const active = isActive(item.href);

        return (
          <motion.a
            key={item.label}
            href={item.href}
            className="flex-1 flex flex-col items-center justify-center py-3 relative"
            animate={{
              backgroundColor: active ? "hsl(var(--accent))" : "transparent",
            }}
            transition={{
              duration: prefersReduced ? 0 : ANIMATION_DURATIONS.fast,
            }}
          >
            {/* Icon */}
            <motion.div
              animate={{
                scale: active ? 1.2 : 1,
                opacity: active ? 1 : 0.6,
              }}
              transition={{
                ...ANIMATION_SPRINGS.bouncy,
                duration: prefersReduced ? 0 : ANIMATION_DURATIONS.fast,
              }}
              className="w-6 h-6"
            >
              {item.icon}
            </motion.div>

            {/* Label */}
            <motion.span
              animate={{
                opacity: active ? 1 : 0.6,
              }}
              transition={{
                duration: prefersReduced ? 0 : ANIMATION_DURATIONS.fast,
              }}
              className="text-xs mt-1 font-medium"
            >
              {item.label}
            </motion.span>

            {/* Indicator dot */}
            {active && (
              <motion.div
                layoutId="bottomNavIndicator"
                className="absolute bottom-0 w-1 h-1 bg-primary rounded-full"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{
                  duration: prefersReduced ? 0 : ANIMATION_DURATIONS.fast,
                }}
              />
            )}
          </motion.a>
        );
      })}
    </div>
  );
}
```

---

#### A12: Notification Badge Pulse

**ID:** A12
**Name:** Notification Badge Pulse
**Trigger:** New notification arrives
**Priority:** Medium
**Component:** Notification badge (usually on bell icon)

**Spec:**
- **Element:** Red badge with notification count
- **Animations:**
  - Scale: 0 → 1.2 → 1 (spring bouncy on entry)
  - Pulse loop: 1 → 1.1 → 1 (infinite, 2s cycle)
  - Color glow: subtle box-shadow pulse
- **Initial animation:** Spring bouncy (one-time)
- **Loop animation:** Subtle pulse (continuous until dismissed)
- **Duration:** 300ms (entry), 2000ms (pulse loop)

**Implementation:**

```tsx
// apps/web/src/components/NotificationBadge.tsx
"use client";

import { motion } from "framer-motion";
import { ANIMATION_SPRINGS } from "@/lib/animation/constants";

interface NotificationBadgeProps {
  count: number;
}

export function NotificationBadge({ count }: NotificationBadgeProps) {
  if (count === 0) return null;

  return (
    <motion.div
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
      transition={ANIMATION_SPRINGS.bouncy}
      className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 rounded-full flex items-center justify-center text-white text-xs font-bold"
    >
      {/* Entry animation complete, now pulse */}
      <motion.div
        animate={{ scale: [1, 1.1, 1] }}
        transition={{
          repeat: Infinity,
          duration: 2,
          ease: "easeInOut",
        }}
        className="absolute inset-0"
      />
      <span className="relative z-10">{Math.min(count, 9)}+</span>
    </motion.div>
  );
}
```

---

### A13–A15: Decorative

#### A13: Floating Orbs

**ID:** A13
**Name:** Floating Orbs
**Trigger:** Landing page load (hero section)
**Priority:** Low (decorative, can be disabled)
**Component:** Hero background

**Spec:**
- **Element:** 3 gradient orbs (circles with blur)
- **Colors:** Brand primary (blue), accent (purple), secondary (pink)
- **Animations:**
  - Drift: slow floating motion (15s loop, continuous)
  - Rotation: gentle circular path (x, y offsets)
  - Blur:** 60px (subtle, background layer)
  - Blend mode:** `multiply`
  - Opacity:** 40–60% (semi-transparent)
- **When disabled:** Hide completely (set `display: none`)

**Implementation:**

```tsx
// apps/web/src/components/landing/FloatingOrbs.tsx
"use client";

import { motion } from "framer-motion";
import { useReducedMotion } from "framer-motion";

export function FloatingOrbs() {
  const prefersReduced = useReducedMotion();

  if (prefersReduced) {
    return null;
  }

  const orbs = [
    { color: "from-blue-400 to-blue-600", delay: 0, size: "w-96 h-96" },
    {
      color: "from-purple-400 to-purple-600",
      delay: 2,
      size: "w-80 h-80",
      top: "30%",
      right: "10%",
    },
    {
      color: "from-pink-400 to-pink-600",
      delay: 4,
      size: "w-72 h-72",
      bottom: "10%",
      left: "10%",
    },
  ];

  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none">
      {orbs.map((orb, idx) => (
        <motion.div
          key={idx}
          className={`absolute ${orb.size} rounded-full bg-gradient-to-br ${orb.color} blur-3xl opacity-50`}
          style={{
            top: orb.top || "0%",
            right: orb.right || "0%",
            bottom: orb.bottom,
            left: orb.left,
            mixBlendMode: "multiply",
          }}
          animate={{
            x: [0, 50, 0],
            y: [0, -50, 0],
          }}
          transition={{
            duration: 15,
            repeat: Infinity,
            ease: "easeInOut",
            delay: orb.delay,
          }}
        />
      ))}
    </div>
  );
}
```

---

#### A14: Hero Text Stagger

**ID:** A14
**Name:** Hero Text Stagger
**Trigger:** Landing page hero section loads
**Priority:** Medium
**Component:** Hero headline

**Spec:**
- **Element:** Hero title text (e.g., "Discover Your Volunteer Potential")
- **Animation:** Each word fades in and translates up
- **Start:** `opacity: 0, translateY: 20px`
- **End:** `opacity: 1, translateY: 0`
- **Stagger:** 80ms delay between each word
- **Duration:** 400ms per word
- **Easing:** `easeOut`
- **When disabled:** All words appear instantly

**Implementation:**

```tsx
// apps/web/src/components/landing/HeroTextStagger.tsx
"use client";

import { motion } from "framer-motion";
import { useReducedMotion } from "framer-motion";
import { ANIMATION_DURATIONS, ANIMATION_EASINGS } from "@/lib/animation/constants";

interface HeroTextStaggerProps {
  text: string;
  className?: string;
}

export function HeroTextStagger({ text, className = "" }: HeroTextStaggerProps) {
  const prefersReduced = useReducedMotion();
  const words = text.split(" ");

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: prefersReduced ? 0 : 0.08,
      },
    },
  };

  const wordVariants = {
    hidden: { opacity: 0, y: prefersReduced ? 0 : 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: prefersReduced ? 0 : ANIMATION_DURATIONS.normal,
        ease: ANIMATION_EASINGS.easeOut,
      },
    },
  };

  return (
    <motion.h1
      className={className}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true }}
      variants={containerVariants}
    >
      {words.map((word, idx) => (
        <motion.span key={idx} variants={wordVariants} className="inline-block mr-2">
          {word}
        </motion.span>
      ))}
    </motion.h1>
  );
}
```

---

#### A15: Card Hover Lift

**ID:** A15
**Name:** Card Hover Lift
**Trigger:** Mouse hover over any card (event card, volunteer card, etc.)
**Priority:** Medium
**Component:** Card wrapper component

**Spec:**
- **Element:** Card container (e.g., EventCard, VolunteerCard)
- **Animations:**
  - TranslateY: 0 → -4px (lift up)
  - Shadow:** none → 0 0 16px rgba(0, 0, 0, 0.1) (increase shadow)
  - Transition:** smooth, 200ms
- **On leave:** Return to original state
- **Easing:** `easeOut`

**Implementation:**

```tsx
// apps/web/src/components/CardHoverLift.tsx
"use client";

import { motion } from "framer-motion";
import { ANIMATION_DURATIONS, ANIMATION_EASINGS } from "@/lib/animation/constants";

interface CardHoverLiftProps {
  children: React.ReactNode;
  className?: string;
}

export function CardHoverLift({ children, className = "" }: CardHoverLiftProps) {
  return (
    <motion.div
      whileHover={{
        y: -4,
        boxShadow: "0 0 16px rgba(0, 0, 0, 0.1)",
      }}
      transition={{
        duration: ANIMATION_DURATIONS.normal,
        ease: ANIMATION_EASINGS.easeOut,
      }}
      className={`rounded-lg border border-border bg-card ${className}`}
    >
      {children}
    </motion.div>
  );
}
```

**Usage:**

```tsx
<CardHoverLift>
  <div className="p-6">
    {/* Card content */}
  </div>
</CardHoverLift>
```

---

### A16–A18: Micro-interactions

#### A16: Button Press

**ID:** A16
**Name:** Button Press
**Trigger:** Click on any button
**Priority:** High
**Component:** All button elements (via `cn()` utility or dedicated wrapper)

**Spec:**
- **Element:** Button container
- **Animation:** Scale briefly on click
- **Start:** `scale: 1`
- **Press:** `scale: 0.97`
- **Return:** `scale: 1`
- **Duration:** 100ms press, 100ms return (total 200ms)
- **Easing:** `easeOut`

**Implementation:**

```tsx
// apps/web/src/components/ui/button-animated.tsx
"use client";

import { motion } from "framer-motion";
import React from "react";
import { Button, ButtonProps } from "@/components/ui/button"; // shadcn Button

interface AnimatedButtonProps extends ButtonProps {
  children: React.ReactNode;
}

export const AnimatedButton = React.forwardRef<
  HTMLButtonElement,
  AnimatedButtonProps
>(({ children, ...props }, ref) => (
  <motion.div whileTap={{ scale: 0.97 }} className="inline-block">
    <Button ref={ref} {...props}>
      {children}
    </Button>
  </motion.div>
));

AnimatedButton.displayName = "AnimatedButton";
```

---

#### A17: Toggle Switch

**ID:** A17
**Name:** Toggle Switch
**Trigger:** Click toggle switch component
**Priority:** Medium
**Component:** Toggle switch (settings, preferences)

**Spec:**
- **Element:** Toggle switch track + circle
- **Animations:**
  - Circle translateX: left (e.g., -10px) → right (e.g., +10px)
  - Background color: off (gray) ↔ on (primary blue)
- **Duration:** 200ms
- **Easing:** `easeOut`
- **Spring:** smooth, not bouncy

**Implementation:**

```tsx
// apps/web/src/components/ui/toggle-animated.tsx
"use client";

import { motion } from "framer-motion";
import { useState } from "react";
import { ANIMATION_DURATIONS, ANIMATION_EASINGS } from "@/lib/animation/constants";

interface ToggleAnimatedProps {
  isOn: boolean;
  onChange: (isOn: boolean) => void;
  label?: string;
}

export function ToggleAnimated({
  isOn,
  onChange,
  label,
}: ToggleAnimatedProps) {
  return (
    <div className="flex items-center space-x-3">
      {label && <span className="text-sm font-medium">{label}</span>}
      <motion.div
        onClick={() => onChange(!isOn)}
        animate={{
          backgroundColor: isOn
            ? "hsl(var(--primary))"
            : "hsl(var(--muted))",
        }}
        transition={{
          duration: ANIMATION_DURATIONS.normal,
          ease: ANIMATION_EASINGS.easeOut,
        }}
        className="relative w-12 h-6 rounded-full cursor-pointer bg-muted"
      >
        <motion.div
          animate={{ x: isOn ? 24 : 2 }}
          transition={{
            duration: ANIMATION_DURATIONS.normal,
            ease: ANIMATION_EASINGS.easeOut,
          }}
          className="absolute top-1 w-4 h-4 bg-white rounded-full"
        />
      </motion.div>
    </div>
  );
}
```

---

#### A18: Like / React Burst

**ID:** A18
**Name:** Like/React Burst
**Trigger:** Tap/click like/heart button
**Priority:** Low (engagement, decorative)
**Component:** Like button (volunteer cards, comments, etc.)

**Spec:**
- **Element:** Heart/star icon + particle burst
- **Animations:**
  1. Icon scale: 1 → 1.3 → 1 (spring bouncy)
  2. Particle burst: 5–10 small hearts explode outward
  3. Particle lifetime: 500ms, fade out + fly away
  4. Color: match badge tier or primary brand color
- **Total duration:** 600ms
- **When disabled:** Skip particle burst, show icon scale only

**Implementation:**

```tsx
// apps/web/src/components/features/LikeButton.tsx
"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";
import { Heart } from "lucide-react";
import { ANIMATION_SPRINGS, ANIMATION_DURATIONS } from "@/lib/animation/constants";

interface LikeButtonProps {
  liked: boolean;
  onToggle: () => void;
  count?: number;
}

function LikeParticle({ index }: { index: number }) {
  const angle = (index / 5) * Math.PI * 2;
  const distance = 80;
  const x = Math.cos(angle) * distance;
  const y = Math.sin(angle) * distance;

  return (
    <motion.div
      key={index}
      initial={{ opacity: 1, x: 0, y: 0, scale: 1 }}
      animate={{ opacity: 0, x, y, scale: 0.5 }}
      transition={{
        duration: ANIMATION_DURATIONS.slow,
        ease: "easeOut",
      }}
      className="absolute pointer-events-none text-red-500"
    >
      <Heart size={16} fill="currentColor" />
    </motion.div>
  );
}

export function LikeButton({ liked, onToggle, count = 0 }: LikeButtonProps) {
  const [isAnimating, setIsAnimating] = useState(false);

  const handleClick = () => {
    if (!liked) {
      setIsAnimating(true);
      setTimeout(() => setIsAnimating(false), 600);
    }
    onToggle();
  };

  return (
    <motion.div className="relative inline-block">
      {/* Icon */}
      <motion.button
        onClick={handleClick}
        whileTap={{ scale: 0.9 }}
        animate={{ scale: liked ? 1.3 : 1 }}
        transition={ANIMATION_SPRINGS.bouncy}
        className="flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-muted"
      >
        <Heart
          size={20}
          fill={liked ? "currentColor" : "none"}
          className={liked ? "text-red-500" : "text-muted-foreground"}
        />
        {count > 0 && <span className="text-sm font-medium">{count}</span>}
      </motion.button>

      {/* Particle burst */}
      <AnimatePresence>
        {isAnimating && (
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
            {Array.from({ length: 5 }).map((_, i) => (
              <LikeParticle key={i} index={i} />
            ))}
          </div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
```

---

## Accessibility Guidelines

### Respecting `prefers-reduced-motion`

**All animations MUST respect the user's motion preferences.** This is critical for users with motion sensitivity, vestibular disorders, or those who prefer minimal motion.

**Pattern:**

```tsx
"use client";

import { useReducedMotion } from "framer-motion";

export function MyComponent() {
  const prefersReduced = useReducedMotion();

  return (
    <motion.div
      animate={{ opacity: 1, y: 0 }}
      transition={
        prefersReduced
          ? { duration: 0 } // Instant transition
          : { duration: 0.3, ease: "easeOut" } // Normal animation
      }
    >
      Content
    </motion.div>
  );
}
```

### No Information Hidden in Animation

- **Never** convey critical information **only** through animation
- **Always** provide a visual indicator (color change, icon, text) alongside animated state changes
- Example: Button press scale (A16) should have `:active` CSS state as fallback

### Color-Independent Feedback

- Avoid relying solely on color to indicate state (animation, icon, or text must also change)
- Example: Toggle switch (A17) should move the circle **and** change background color

### Disabled Animations = Instant Feedback

When `prefers-reduced-motion` is enabled, transitions should be instant (`duration: 0`), but interactions should feel responsive:

```tsx
transition={
  prefersReduced
    ? { duration: 0 } // Instant
    : { duration: 0.3, delay: 0.1 } // Normal
}
```

---

## Performance Optimization

### Use `layoutId` for Shared Layout Animations

When animating layout changes (e.g., sidebar collapse), use Framer Motion's `layoutId`:

```tsx
<motion.div layoutId="sidebar">
  {/* Content */}
</motion.div>
```

This prevents janky reflows.

### Debounce Rapid Animations

For frequently-triggered animations (scroll, resize), debounce the handler:

```tsx
const debouncedScroll = useMemo(
  () => debounce(() => setScrolled(true), 100),
  []
);
```

### Use `will-change` Sparingly

Avoid adding `will-change: transform` to all animated elements. Use it only for expensive animations (e.g., confetti):

```tsx
className="will-change-transform" // Only when needed
```

### Test on Low-End Devices

Confetti, particle bursts, and floating orbs are CPU-intensive. Test on:
- iPhone 6s / SE
- Mid-range Android
- Throttled network (DevTools)

Consider **disabling** decorative animations on mobile for performance.

---

## Testing Checklist

- [ ] All animations respect `prefers-reduced-motion`
- [ ] No animation duration < 100ms (too snappy)
- [ ] No animation duration > 1s without good reason
- [ ] Animations don't block user interaction (use `pointerEvents: "none"` for overlays)
- [ ] Animations work on mobile (test on real device)
- [ ] Animations work on slow networks (DevTools throttle 4G)
- [ ] Confetti and particle effects don't cause jank (use `will-change` sparingly)
- [ ] Button press feedback is immediate (< 150ms)
- [ ] No animation flicker on route change
- [ ] Color transitions are smooth (use `transition` not `style` changes)
- [ ] Hover animations don't trigger on touch devices (use `whileHover` for mouse only)
- [ ] Staggered animations have consistent delays (50–100ms recommended)

---

## Implementation Patterns

### Hook: `useAnimationPreference`

Create a custom hook to simplify reduced-motion logic:

```tsx
// apps/web/src/lib/hooks/useAnimationPreference.ts
import { useReducedMotion } from "framer-motion";

export function useAnimationPreference() {
  const prefersReduced = useReducedMotion();

  return {
    prefersReduced,
    duration: (normal: number, reduced: number = 0) =>
      prefersReduced ? reduced : normal,
    transition: (normal: any, reduced: any = { duration: 0 }) =>
      prefersReduced ? reduced : normal,
  };
}
```

**Usage:**

```tsx
const anim = useAnimationPreference();

<motion.div
  animate={{ x: 100 }}
  transition={anim.transition(
    { duration: 0.3, ease: "easeOut" },
    { duration: 0 }
  )}
>
  Animated content
</motion.div>
```

### Wrapper: `<AnimatedCard />`

Reuse A15 (Card Hover Lift) across the app:

```tsx
// apps/web/src/components/AnimatedCard.tsx
export function AnimatedCard({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <motion.div
      whileHover={{ y: -4 }}
      transition={{ duration: 0.2 }}
      className="rounded-lg border border-border bg-card p-6"
      {...props}
    >
      {children}
    </motion.div>
  );
}
```

---

## Browser Compatibility

- **Chrome / Edge:** ✅ Full support
- **Firefox:** ✅ Full support
- **Safari (14+):** ✅ Full support
- **Safari (< 14):** ⚠️ No `will-change` optimization, test
- **Mobile Safari (iOS 14+):** ✅ Full support
- **Android Chrome:** ✅ Full support

---

## Future Enhancements

- [ ] Gesture-based animations for swipe nav (Hammer.js)
- [ ] Scroll-triggered animations (Intersection Observer)
- [ ] SVG morphing for logo/badge animations
- [ ] 3D transforms for depth perception (perspectival cards)
- [ ] Sound design integration (haptic feedback on mobile)

---

## Related Documentation

- [[UX-COPY-AZ-EN.md]] — Toast and button state copy (animate with feedback messages)
- [[../../CLAUDE.md]] — Tech stack verification (Framer Motion is standard)
- [[../DECISIONS.md]] — Rationale for animation choices
- Framer Motion Docs: https://www.framer.com/motion/

---

## Animation Library Maintenance

| Animation ID | Last Tested | Status | Notes |
|--------------|-------------|--------|-------|
| A01 | 2026-03-22 | ✅ | Page fade works on all routes |
| A02 | 2026-03-22 | ✅ | Mobile slide tested on iOS/Android |
| A03 | 2026-03-22 | ⚠️ | Performance OK on desktop, may need throttle on older devices |
| A04 | 2026-03-22 | ✅ | Badge reveal completes after score counter |
| A05 | 2026-03-22 | ✅ | Radar stagger timing verified |
| A06 | 2026-03-22 | ⚠️ | Confetti CPU-intensive; consider disabling on mobile |
| A07–A18 | 2026-03-22 | ✅ | All implemented and tested |

---

## Revision History

| Date | Author | Changes |
|------|--------|---------|
| 2026-03-22 | Design System | Initial comprehensive catalog v1.0 |

