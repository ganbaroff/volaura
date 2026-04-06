import { redirect } from "next/navigation";

// Leaderboard removed — G9/G46 Constitution violation.
// Public ranking creates comparative anxiety; contradicts shame-free design principles.
// Crystals and AURA scores are private by default; discovery is opt-in.
export default async function LeaderboardPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  redirect(`/${locale}/dashboard`);
}
