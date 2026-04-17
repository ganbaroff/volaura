import { notFound } from "next/navigation";
import { SampleProfileView } from "./sample-profile-view";

// Track G1.4 — feature flag (clean slate launch, CEO directive 2026-04-17).
// Default off in production. Set NEXT_PUBLIC_ENABLE_SAMPLE_PROFILE=true in env to re-enable.
const SAMPLE_PROFILE_ENABLED = process.env.NEXT_PUBLIC_ENABLE_SAMPLE_PROFILE === "true";

export default function SampleProfilePage() {
  if (!SAMPLE_PROFILE_ENABLED) {
    notFound();
  }
  return <SampleProfileView />;
}
