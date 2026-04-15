import { AuthGuard } from "@/components/layout/auth-guard";
import { BottomTabBar } from "@/components/navigation/bottom-tab-bar";
import { Sidebar } from "@/components/layout/sidebar";
import { RealtimeNotificationsProvider } from "@/components/layout/realtime-notifications";
import { Toaster } from "@/components/ui/toast";
import { EnergyInit } from "@/components/layout/energy-init";
import { SkipToContent } from "@/components/layout/skip-to-content";

export default function DashboardLayout({ children }: { children: React.ReactNode; }) {
  return (
    <AuthGuard>
      {/* T0-5 (ghost-audit a11y P0-5, 2026-04-15): WCAG 2.4.1 bypass block —
          keyboard users can skip the 11-item sidebar + 5-tab bottom nav. */}
      <SkipToContent />
      {/* Energy mode: reads localStorage and sets data-energy on <html> */}
      <EnergyInit />
      {/* Sprint C: Supabase Realtime subscription — instant notification count updates */}
      <RealtimeNotificationsProvider />
      {/* Constitution Law 1: toast system (purple errors, amber warnings) */}
      <Toaster />
      <div className="flex h-screen overflow-hidden bg-background">
        <Sidebar />
        {/* pb-20 prevents content from hiding under bottom tab bar */}
        <div className="flex flex-1 flex-col overflow-hidden pb-20 md:pb-0">
          <main id="main-content" tabIndex={-1} className="flex-1 overflow-y-auto">{children}</main>
        </div>
      </div>
      {/* Mobile: ecosystem product tab bar (hidden md:+) */}
      <BottomTabBar />
    </AuthGuard>
  );
}
