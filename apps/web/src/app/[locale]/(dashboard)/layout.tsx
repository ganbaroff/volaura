import { AuthGuard } from "@/components/layout/auth-guard";
import { BottomNav } from "@/components/layout/bottom-nav";
import { Sidebar } from "@/components/layout/sidebar";
import { RealtimeNotificationsProvider } from "@/components/layout/realtime-notifications";

export default function DashboardLayout({ children }: { children: React.ReactNode; }) {
  return (
    <AuthGuard>
      {/* Sprint C: Supabase Realtime subscription — instant notification count updates */}
      <RealtimeNotificationsProvider />
      <div className="flex h-screen overflow-hidden bg-background">
        <Sidebar />
        {/* pb-[72px] prevents content from hiding under the 72px mobile bottom nav */}
        <div className="flex flex-1 flex-col overflow-hidden pb-[72px] md:pb-0">
          <main className="flex-1 overflow-y-auto">{children}</main>
        </div>
      </div>
      {/* Mobile-only bottom navigation (hidden md:+) */}
      <BottomNav />
    </AuthGuard>
  );
}
