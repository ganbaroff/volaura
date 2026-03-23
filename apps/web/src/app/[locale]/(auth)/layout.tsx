"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  const { locale } = useParams<{ locale: string }>();

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4">
      <Link href={`/${locale}`} className="mb-8 text-2xl font-bold tracking-tight text-foreground">
        Volaura
      </Link>
      <div className="w-full max-w-sm">{children}</div>
    </div>
  );
}
