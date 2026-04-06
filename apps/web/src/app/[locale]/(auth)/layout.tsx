"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  const { locale } = useParams<{ locale: string }>();

  return (
    <div className="flex min-h-screen flex-col items-center justify-center mesh-gradient-hero px-4">
      <Link href={`/${locale}`} className="mb-8 text-2xl font-bold tracking-tight text-primary">
        Volaura
      </Link>
      <div className="w-full max-w-md">{children}</div>
    </div>
  );
}
