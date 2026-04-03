"use client";

import { useEffect } from "react";
import { AdminOverview } from "@/components/admin/admin-overview";

export default function AdminPage() {
  useEffect(() => {
    document.title = "Admin — Volaura";
  }, []);

  return <AdminOverview />;
}
