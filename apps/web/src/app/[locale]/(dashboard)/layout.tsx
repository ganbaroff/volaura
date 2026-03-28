import { AuthGuard } from "@/components/layout/auth-guard";
import { BottomNav } from "@/components/layout/bottom-nav";
import { Sidebar } from "@/components/layout/sidebar";

export default function DashboardLayout({ children }: { children: React.ReactNode; }) {
  return (
    <AuthGuard>
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
