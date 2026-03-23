# State Management Architecture

> See also: [[TESTING-STRATEGY.md]], [[SEO-TECHNICAL.md]]

## Principles

Volaura uses a **layered state architecture** where each layer has a specific responsibility:

1. **Server State** (fetched data from API) → **TanStack Query**
2. **Client State** (UI, modals, sidebar, theme) → **Zustand**
3. **Form State** (input fields, validation) → **React Hook Form + Zod**
4. **URL State** (filters, pagination, search) → **Next.js `searchParams`**
5. **Auth State** → **Supabase Auth + Zustand sync**

### Why This Structure?
- **TanStack Query** handles caching, invalidation, and synchronization of server data
- **Zustand** is lightweight for ephemeral UI state without global Redux boilerplate
- **React Hook Form** manages form complexity while Zod provides type-safe validation
- **searchParams** makes filters bookmarkable and shareable
- **Supabase Auth** is the source of truth for identity; Zustand mirrors it for performance

---

## Server State: TanStack Query

### Query Keys Convention

Query keys are structured hierarchically to enable granular invalidation:

```typescript
// apps/web/src/lib/api/query-keys.ts
export const queryKeys = {
  // Auth
  auth: {
    me: ["auth", "me"] as const,
    session: ["auth", "session"] as const,
  },

  // Profiles
  profile: {
    me: ["profile", "me"] as const,
    public: (username: string) => ["profile", username] as const,
    mySkills: ["profile", "me", "skills"] as const,
  },

  // Assessment Sessions
  assessment: {
    all: ["assessments"] as const,
    list: (filters?: AssessmentFilters) => ["assessments", filters] as const,
    current: (sessionId: string) => ["assessment", sessionId] as const,
    nextQuestion: (sessionId: string) =>
      ["assessment", sessionId, "next"] as const,
    questions: (sessionId: string) =>
      ["assessment", sessionId, "questions"] as const,
    history: ["assessments", "history"] as const,
  },

  // AURA Scores
  scores: {
    me: ["scores", "me"] as const,
    leaderboard: (competency?: string) =>
      ["scores", "leaderboard", competency] as const,
    history: ["scores", "history"] as const,
    detail: (userId: string) => ["scores", userId] as const,
  },

  // Events
  events: {
    all: ["events"] as const,
    list: (filters?: EventFilters) => ["events", filters] as const,
    detail: (eventId: string) => ["events", eventId] as const,
    myEvents: ["events", "mine"] as const,
    registrations: ["events", "registrations"] as const,
  },

  // Notifications
  notifications: {
    all: ["notifications"] as const,
    unread: ["notifications", "unread"] as const,
  },

  // Search (for volunteer matching)
  search: {
    volunteers: (query: string) => ["search", "volunteers", query] as const,
    skills: (query: string) => ["search", "skills", query] as const,
  },
};
```

### Usage Patterns

**Fetching data:**

```typescript
"use client";
import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "@/lib/api/query-keys";
import { getProfile } from "@/lib/api/generated"; // from @hey-api/openapi-ts

export function ProfileCard({ username }: { username: string }) {
  const { data: profile, isLoading, error } = useQuery({
    queryKey: queryKeys.profile.public(username),
    queryFn: () => getProfile({ path: { username } }),
  });

  if (isLoading) return <Skeleton />;
  if (error) return <ErrorBoundary error={error} />;

  return <div>{profile.name}</div>;
}
```

**Mutations (form submission):**

```typescript
"use client";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { updateProfile } from "@/lib/api/generated";
import { queryKeys } from "@/lib/api/query-keys";

export function EditProfileForm() {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (data: UpdateProfilePayload) => updateProfile({ body: data }),
    onSuccess: () => {
      // Invalidate related queries so they refetch
      queryClient.invalidateQueries({
        queryKey: queryKeys.profile.me,
      });
    },
  });

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        mutation.mutate({ name: "New Name" });
      }}
    >
      <button disabled={mutation.isPending}>Save</button>
    </form>
  );
}
```

**Pagination & Filtering (with searchParams):**

```typescript
"use client";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "@/lib/api/query-keys";
import { listEvents } from "@/lib/api/generated";

export function EventsList() {
  const searchParams = useSearchParams();
  const page = parseInt(searchParams.get("page") ?? "1");
  const competency = searchParams.get("competency");

  const { data: events } = useQuery({
    queryKey: queryKeys.events.list({ page, competency }),
    queryFn: () =>
      listEvents({
        query: { page, competency: competency || undefined },
      }),
  });

  return <div>{events?.items.map((e) => <EventCard key={e.id} event={e} />)}</div>;
}
```

---

## Client State: Zustand Stores

Zustand stores manage transient UI state (modals, sidebar, theme) and cached auth context.

### Store Patterns

**1. Auth Store** (`stores/auth.ts`)

```typescript
import { create } from "zustand";
import { subscribeWithSelector } from "zustand/react";
import { createClient } from "@/lib/supabase/client";

export interface AuthState {
  user: User | null;
  session: Session | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  // Actions
  login: (email: string, password: string) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  logout: () => Promise<void>;
  refreshSession: () => Promise<void>;
  // Internal
  _setUser: (user: User | null) => void;
  _setSession: (session: Session | null) => void;
}

export const useAuthStore = create<AuthState>()(
  subscribeWithSelector((set) => {
    const supabase = createClient();

    // Hydrate from Supabase on mount
    supabase.auth.onAuthStateChange((_event, session) => {
      set({ session, user: session?.user ?? null, isLoading: false });
    });

    return {
      user: null,
      session: null,
      isLoading: true,
      isAuthenticated: false,

      login: async (email, password) => {
        const { data, error } = await supabase.auth.signInWithPassword({
          email,
          password,
        });
        if (error) throw error;
        set({ session: data.session, user: data.user });
      },

      loginWithGoogle: async () => {
        const { data, error } = await supabase.auth.signInWithOAuth({
          provider: "google",
        });
        if (error) throw error;
      },

      logout: async () => {
        await supabase.auth.signOut();
        set({ user: null, session: null });
      },

      refreshSession: async () => {
        const { data, error } = await supabase.auth.refreshSession();
        if (error) throw error;
        set({ session: data.session, user: data.user });
      },

      _setUser: (user) => set({ user }),
      _setSession: (session) => set({ session }),
    };
  })
);
```

**2. UI Store** (`stores/ui.ts`)

```typescript
import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface UIState {
  sidebarOpen: boolean;
  locale: "az" | "en";
  theme: "light" | "dark" | "system";
  toasts: Array<{ id: string; message: string; type: "success" | "error" }>;
  // Actions
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setLocale: (locale: "az" | "en") => void;
  setTheme: (theme: "light" | "dark" | "system") => void;
  addToast: (message: string, type: "success" | "error") => void;
  removeToast: (id: string) => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      locale: "az",
      theme: "system",
      toasts: [],

      toggleSidebar: () =>
        set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      setLocale: (locale) => set({ locale }),
      setTheme: (theme) => set({ theme }),

      addToast: (message, type) =>
        set((state) => ({
          toasts: [
            ...state.toasts,
            { id: crypto.randomUUID(), message, type },
          ],
        })),

      removeToast: (id) =>
        set((state) => ({
          toasts: state.toasts.filter((t) => t.id !== id),
        })),
    }),
    {
      name: "ui-store",
      partialize: (state) => ({
        locale: state.locale,
        theme: state.theme,
        sidebarOpen: state.sidebarOpen,
      }),
    }
  )
);
```

**3. Assessment Store** (`stores/assessment.ts`)

For managing ongoing assessment session state and offline sync:

```typescript
import { create } from "zustand";

export interface AssessmentState {
  sessionId: string | null;
  currentQuestion: Question | null;
  questionIndex: number;
  totalQuestions: number;
  answers: Map<string, SubmittedAnswer>;
  isOffline: boolean;
  pendingSync: SubmittedAnswer[];
  // Actions
  startAssessment: (sessionId: string) => Promise<void>;
  loadQuestion: (questionId: string) => Promise<void>;
  recordAnswer: (answer: SubmittedAnswer) => void;
  nextQuestion: () => Promise<void>;
  completeAssessment: () => Promise<void>;
  syncOfflineAnswers: () => Promise<void>;
  _setOffline: (offline: boolean) => void;
}

export const useAssessmentStore = create<AssessmentState>((set) => ({
  sessionId: null,
  currentQuestion: null,
  questionIndex: 0,
  totalQuestions: 0,
  answers: new Map(),
  isOffline: false,
  pendingSync: [],

  startAssessment: async (sessionId) => {
    // Fetch initial question from API
    set({ sessionId, questionIndex: 0 });
  },

  recordAnswer: (answer) =>
    set((state) => {
      const newAnswers = new Map(state.answers);
      newAnswers.set(answer.question_id, answer);
      if (state.isOffline) {
        return {
          answers: newAnswers,
          pendingSync: [...state.pendingSync, answer],
        };
      }
      return { answers: newAnswers };
    }),

  syncOfflineAnswers: async () => {
    // Submit all pending answers via API
    set({ pendingSync: [] });
  },

  _setOffline: (offline) => set({ isOffline: offline }),
}));
```

---

## Form State: React Hook Form + Zod

All forms use React Hook Form for state management and Zod for validation. Schema definitions live in `lib/schemas/`.

```typescript
// apps/web/src/lib/schemas/profile.ts
import { z } from "zod";

export const updateProfileSchema = z.object({
  first_name: z.string().min(2, "First name too short"),
  last_name: z.string().min(2, "Last name too short"),
  bio: z.string().max(500, "Bio too long"),
  github_url: z.string().url("Invalid GitHub URL").optional(),
});

export type UpdateProfileFormData = z.infer<typeof updateProfileSchema>;
```

```typescript
// apps/web/src/components/forms/UpdateProfileForm.tsx
"use client";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { updateProfile } from "@/lib/api/generated";
import {
  updateProfileSchema,
  type UpdateProfileFormData,
} from "@/lib/schemas/profile";
import { queryKeys } from "@/lib/api/query-keys";

export function UpdateProfileForm() {
  const queryClient = useQueryClient();
  const form = useForm<UpdateProfileFormData>({
    resolver: zodResolver(updateProfileSchema),
    defaultValues: {
      first_name: "",
      last_name: "",
      bio: "",
    },
  });

  const mutation = useMutation({
    mutationFn: (data: UpdateProfileFormData) =>
      updateProfile({ body: data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.profile.me });
    },
  });

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit((data) => mutation.mutate(data))}>
        <FormField
          control={form.control}
          name="first_name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>First Name</FormLabel>
              <FormControl>
                <Input {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button type="submit" disabled={mutation.isPending}>
          Save
        </Button>
      </form>
    </Form>
  );
}
```

---

## URL State: searchParams

Filters, sorting, and pagination are always reflected in the URL for:
- Bookmarkability
- Shareability
- Back-button behavior

```typescript
"use client";
import { useRouter, useSearchParams } from "next/navigation";
import { useTransition } from "react";

export function EventsFilter() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isPending, startTransition] = useTransition();

  const competency = searchParams.get("competency");
  const page = searchParams.get("page") ?? "1";

  const handleFilterChange = (newCompetency: string) => {
    const params = new URLSearchParams(searchParams);
    params.set("competency", newCompetency);
    params.set("page", "1"); // Reset pagination on filter change

    startTransition(() => {
      router.push(`?${params.toString()}`);
    });
  };

  return (
    <select value={competency ?? ""} onChange={(e) => handleFilterChange(e.target.value)}>
      <option value="">All Competencies</option>
      <option value="communication">Communication</option>
      <option value="leadership">Leadership</option>
    </select>
  );
}
```

---

## React Server Components (RSC) + TanStack Query Pattern

### Server Component (data fetching)

```typescript
// apps/web/src/app/[locale]/events/page.tsx
import initTranslations from "@/app/i18n";
import { createClient } from "@/lib/supabase/server";
import { EventsList } from "./EventsList";

export default async function EventsPage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ competency?: string; page?: string }>;
}) {
  const { locale } = await params;
  const { competency, page } = await searchParams;
  const { t } = await initTranslations(locale, ["events"]);

  const supabase = await createClient();
  const { data: events, error } = await supabase
    .from("events")
    .select("*")
    .eq("competency", competency || "")
    .range((parseInt(page || "1") - 1) * 20, parseInt(page || "1") * 20 - 1);

  if (error) throw error;

  return (
    <div>
      <h1>{t("events.title")}</h1>
      <EventsList initialEvents={events} />
    </div>
  );
}
```

### Client Component (reactivity + mutations)

```typescript
// apps/web/src/app/[locale]/events/EventsList.tsx
"use client";
import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "@/lib/api/query-keys";
import { listEvents } from "@/lib/api/generated";

export function EventsList({ initialEvents }: { initialEvents: Event[] }) {
  // Client-side query for real-time updates and pagination changes
  const { data = initialEvents } = useQuery({
    queryKey: queryKeys.events.list(),
    queryFn: () => listEvents(),
    initialData: initialEvents,
  });

  return (
    <div>
      {data.map((event) => (
        <EventCard key={event.id} event={event} />
      ))}
    </div>
  );
}
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ User Action (click, input, navigate)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
    Form Input   Sidebar Toggle   Filter Change
        │              │              │
        │              │              │
    React Hook      Zustand UI     searchParams
    Form + Zod      Store           (URL)
        │              │              │
        ├──────────────┼──────────────┘
        │              │
        ▼              ▼
   Validate    ┌─────────────────┐
   + Mutate    │ Update URL      │
        │      └────────┬────────┘
        │               │
        ▼               ▼
    API Call ◄────  TanStack Query
        │       (invalidate + refetch)
        │
        └──────────────────►  Supabase API
                             (FastAPI)
                             (Database)
                                 │
                                 ▼
                        Update cache + UI
```

---

## Avoiding Common Pitfalls

### ❌ Don't: Use Zustand for server data
```typescript
// WRONG: Zustand shouldn't cache API responses
const store = create(() => ({
  users: [], // This will be stale!
  fetchUsers: async () => { /* ... */ },
}));
```

### ✅ Do: Use TanStack Query for server data
```typescript
// CORRECT: Let TanStack Query handle caching
const { data: users } = useQuery({
  queryKey: ["users"],
  queryFn: () => getUsers(),
});
```

### ❌ Don't: Prop-drill Zustand state deeply
```typescript
// WRONG: Too many intermediate props
<Parent store={store}>
  <Child store={store}>
    <Grandchild store={store} />
  </Child>
</Parent>
```

### ✅ Do: Access store directly in components
```typescript
// CORRECT: Each component accesses what it needs
function Child() {
  const sidebarOpen = useUIStore((state) => state.sidebarOpen);
  return <div>{sidebarOpen ? "open" : "closed"}</div>;
}
```

---

## Auth Sync Strategy

When a user logs in via Supabase, auth state flows through multiple layers:

1. **Supabase Auth** emits `onAuthStateChange` event
2. **useAuthStore** listens and updates `user` + `session`
3. **TanStack Query** sees auth context change and invalidates user-specific queries
4. **Components** re-render with updated auth state

```typescript
// Initialize auth on app load
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { isLoading } = useAuthStore();

  if (isLoading) return <LoadingScreen />;

  return <>{children}</>;
}
```

---

## Testing State Management

See [[TESTING-STRATEGY.md#Frontend Testing]] for detailed test patterns.

**Zustand store tests:**

```typescript
import { renderHook, act } from "@testing-library/react";
import { useUIStore } from "@/stores/ui";

it("toggles sidebar", () => {
  const { result } = renderHook(() => useUIStore());

  act(() => {
    result.current.toggleSidebar();
  });

  expect(result.current.sidebarOpen).toBe(false);
});
```

**TanStack Query integration tests (with MSW):**

```typescript
import { renderHook, waitFor } from "@testing-library/react";
import { useQuery } from "@tanstack/react-query";
import { server } from "@/test/mocks/server";
import { http, HttpResponse } from "msw";

it("fetches profile data", async () => {
  server.use(
    http.get("/api/profile/me", () =>
      HttpResponse.json({ id: "1", name: "John" })
    )
  );

  const { result } = renderHook(() =>
    useQuery({
      queryKey: ["profile", "me"],
      queryFn: () => fetch("/api/profile/me").then((r) => r.json()),
    }),
    { wrapper: QueryClientProvider }
  );

  await waitFor(() => expect(result.current.isLoading).toBe(false));
  expect(result.current.data.name).toBe("John");
});
```

---

## References

- [[TESTING-STRATEGY.md]]
- [[SEO-TECHNICAL.md]]
- TanStack Query docs: https://tanstack.com/query/latest
- Zustand docs: https://github.com/pmndrs/zustand
- React Hook Form docs: https://react-hook-form.com
- Next.js App Router: https://nextjs.org/docs/app
