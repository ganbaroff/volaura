import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";

// ── Mocks ─────────────────────────────────────────────────────────────────────

vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    span: ({ children, ...props }: any) => <span {...props}>{children}</span>,
  },
  useReducedMotion: () => false,
}));

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, opts?: any) => opts?.defaultValue ?? key,
  }),
}));

vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: any) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

// ── Imports after mocks ───────────────────────────────────────────────────────

import { ProfileHeader, ProfileHeaderData } from "@/components/profile-view/profile-header";
import { SkillChips, CompetencyScore } from "@/components/profile-view/skill-chips";
import { ActivityTimeline, TimelineEvent } from "@/components/profile-view/activity-timeline";
import { ImpactMetrics, ImpactData } from "@/components/profile-view/impact-metrics";
import { ExpertVerifications, ExpertVerification } from "@/components/profile-view/expert-verifications";

// ── Helpers ───────────────────────────────────────────────────────────────────

function makeProfile(overrides: Partial<ProfileHeaderData> = {}): ProfileHeaderData {
  return {
    display_name: "Yusif Ganbarov",
    username: "yusif",
    bio: null,
    location: null,
    languages: [],
    is_public: true,
    avatar_url: null,
    badge_tier: "none",
    total_score: null,
    registration_number: null,
    registration_tier: null,
    ...overrides,
  };
}

// ── 1. ProfileHeader ──────────────────────────────────────────────────────────

describe("ProfileHeader — name display", () => {
  it("renders display_name when present", () => {
    render(<ProfileHeader profile={makeProfile({ display_name: "Yusif Ganbarov" })} locale="en" />);
    expect(screen.getByText("Yusif Ganbarov")).toBeInTheDocument();
  });

  it("falls back to username when display_name is null", () => {
    render(<ProfileHeader profile={makeProfile({ display_name: null, username: "yusif_g" })} locale="en" />);
    expect(screen.getByText("yusif_g")).toBeInTheDocument();
  });

  it("shows @username", () => {
    render(<ProfileHeader profile={makeProfile({ username: "yusif" })} locale="en" />);
    expect(screen.getByText("@yusif")).toBeInTheDocument();
  });
});

describe("ProfileHeader — registration number", () => {
  it("shows registration number padded to 4 digits", () => {
    render(<ProfileHeader profile={makeProfile({ registration_number: 42 })} locale="en" />);
    expect(screen.getByText(/^#0042/)).toBeInTheDocument();
  });

  it("pads single-digit number to 4 chars", () => {
    render(<ProfileHeader profile={makeProfile({ registration_number: 7 })} locale="en" />);
    expect(screen.getByText(/^#0007/)).toBeInTheDocument();
  });

  it("hides registration row when registration_number is null", () => {
    render(<ProfileHeader profile={makeProfile({ registration_number: null })} locale="en" />);
    expect(screen.queryByText(/^#/)).not.toBeInTheDocument();
  });
});

describe("ProfileHeader — registration tier badges", () => {
  it("shows founding_100 badge text when registration_tier is founding_100", () => {
    render(
      <ProfileHeader
        profile={makeProfile({ registration_number: 1, registration_tier: "founding_100" })}
        locale="en"
      />
    );
    // t("profile.foundingMember") returns key since no defaultValue
    expect(screen.getByText("profile.foundingMember")).toBeInTheDocument();
  });

  it("shows founding_1000 badge text when registration_tier is founding_1000", () => {
    render(
      <ProfileHeader
        profile={makeProfile({ registration_number: 200, registration_tier: "founding_1000" })}
        locale="en"
      />
    );
    expect(screen.getByText("profile.founding1000")).toBeInTheDocument();
  });

  it("shows early_adopter badge text when registration_tier is early_adopter", () => {
    render(
      <ProfileHeader
        profile={makeProfile({ registration_number: 500, registration_tier: "early_adopter" })}
        locale="en"
      />
    );
    expect(screen.getByText("profile.earlyAdopter")).toBeInTheDocument();
  });

  it("does not show founding_100 badge when registration_number is null", () => {
    render(
      <ProfileHeader
        profile={makeProfile({ registration_number: null, registration_tier: "founding_100" })}
        locale="en"
      />
    );
    expect(screen.queryByText("profile.foundingMember")).not.toBeInTheDocument();
  });
});

describe("ProfileHeader — edit link", () => {
  it("shows edit link when isOwnProfile=true", () => {
    render(<ProfileHeader profile={makeProfile()} locale="en" isOwnProfile={true} />);
    expect(screen.getByRole("link", { name: "profile.editProfile" })).toBeInTheDocument();
  });

  it("edit link has correct locale href", () => {
    render(<ProfileHeader profile={makeProfile()} locale="az" isOwnProfile={true} />);
    expect(screen.getByRole("link", { name: "profile.editProfile" })).toHaveAttribute(
      "href",
      "/az/profile/edit"
    );
  });

  it("hides edit link when isOwnProfile=false", () => {
    render(<ProfileHeader profile={makeProfile()} locale="en" isOwnProfile={false} />);
    expect(screen.queryByRole("link", { name: "profile.editProfile" })).not.toBeInTheDocument();
  });

  it("hides edit link when isOwnProfile is undefined", () => {
    render(<ProfileHeader profile={makeProfile()} locale="en" />);
    expect(screen.queryByRole("link", { name: "profile.editProfile" })).not.toBeInTheDocument();
  });
});

describe("ProfileHeader — AURA score and badge", () => {
  it("shows AURA score rounded when total_score is present", () => {
    render(<ProfileHeader profile={makeProfile({ total_score: 87.6, badge_tier: "gold" })} locale="en" />);
    expect(screen.getByText("88")).toBeInTheDocument();
  });

  it("shows badge tier pill when badge_tier is not none", () => {
    render(<ProfileHeader profile={makeProfile({ badge_tier: "gold" })} locale="en" />);
    // t("badge.gold", { defaultValue: "gold" }) returns "gold" (defaultValue wins in mock)
    expect(screen.getByText("gold")).toBeInTheDocument();
  });

  it("hides AURA row when total_score is null and badge_tier is none", () => {
    render(
      <ProfileHeader profile={makeProfile({ total_score: null, badge_tier: "none" })} locale="en" />
    );
    // No score digit and no badge pill
    expect(screen.queryByText("badge.none")).not.toBeInTheDocument();
  });

  it("shows score 0 correctly", () => {
    render(<ProfileHeader profile={makeProfile({ total_score: 0, badge_tier: "bronze" })} locale="en" />);
    expect(screen.getByText("0")).toBeInTheDocument();
  });
});

describe("ProfileHeader — bio, location, languages, visibility", () => {
  it("shows bio when present", () => {
    render(<ProfileHeader profile={makeProfile({ bio: "Passionate about impact." })} locale="en" />);
    expect(screen.getByText("Passionate about impact.")).toBeInTheDocument();
  });

  it("hides bio when null", () => {
    const { container } = render(<ProfileHeader profile={makeProfile({ bio: null })} locale="en" />);
    expect(container.querySelector("p.text-sm.text-foreground")).toBeNull();
  });

  it("shows location with MapPin aria-hidden icon", () => {
    render(<ProfileHeader profile={makeProfile({ location: "Baku, AZ" })} locale="en" />);
    expect(screen.getByText("Baku, AZ")).toBeInTheDocument();
  });

  it("shows languages joined by comma", () => {
    render(<ProfileHeader profile={makeProfile({ languages: ["AZ", "EN", "RU"] })} locale="en" />);
    expect(screen.getByText("AZ, EN, RU")).toBeInTheDocument();
  });

  it("shows Discoverable text when is_public=true", () => {
    render(<ProfileHeader profile={makeProfile({ is_public: true })} locale="en" />);
    expect(screen.getByText("Discoverable by organizations")).toBeInTheDocument();
  });

  it("shows Private text when is_public=false", () => {
    render(<ProfileHeader profile={makeProfile({ is_public: false })} locale="en" />);
    expect(screen.getByText("profile.private")).toBeInTheDocument();
  });

  it("does not render Globe text when languages array is empty", () => {
    render(<ProfileHeader profile={makeProfile({ languages: [] })} locale="en" />);
    // No language comma-joined text, no Globe icon text
    expect(screen.queryByText(/,/)).not.toBeInTheDocument();
  });
});

// ── 2. SkillChips ─────────────────────────────────────────────────────────────

describe("SkillChips — empty state", () => {
  it("renders empty message when competencies is empty", () => {
    render(<SkillChips competencies={[]} />);
    expect(screen.getByText("aura.noScoreYet")).toBeInTheDocument();
  });

  it("does not render any chips when competencies is empty", () => {
    const { container } = render(<SkillChips competencies={[]} />);
    expect(container.querySelectorAll("span.rounded-full")).toHaveLength(0);
  });
});

describe("SkillChips — chip rendering", () => {
  it("renders one chip per competency", () => {
    const competencies: CompetencyScore[] = [
      { competency_id: "communication", score: 80 },
      { competency_id: "leadership", score: 65 },
    ];
    render(<SkillChips competencies={competencies} />);
    // t("competency.communication", { defaultValue: "communication" }) → "communication"
    expect(screen.getByText("communication")).toBeInTheDocument();
    expect(screen.getByText("leadership")).toBeInTheDocument();
  });

  it("displays competency label via i18n key", () => {
    render(<SkillChips competencies={[{ competency_id: "empathy_safeguarding", score: 50 }]} />);
    // defaultValue is competency_id, so mock returns competency_id
    expect(screen.getByText("empathy_safeguarding")).toBeInTheDocument();
  });

  it("displays score as integer (toFixed(0))", () => {
    render(<SkillChips competencies={[{ competency_id: "reliability", score: 72.7 }]} />);
    expect(screen.getByText("73")).toBeInTheDocument();
  });

  it("displays score 100 correctly", () => {
    render(<SkillChips competencies={[{ competency_id: "communication", score: 100 }]} />);
    expect(screen.getByText("100")).toBeInTheDocument();
  });
});

describe("SkillChips — tier styles", () => {
  it("applies platinum style class for score >= 90", () => {
    const { container } = render(
      <SkillChips competencies={[{ competency_id: "communication", score: 90 }]} />
    );
    const chip = container.querySelector("span.rounded-full");
    expect(chip?.className).toContain("violet");
  });

  it("applies gold style for score 75-89", () => {
    const { container } = render(
      <SkillChips competencies={[{ competency_id: "communication", score: 75 }]} />
    );
    const chip = container.querySelector("span.rounded-full");
    expect(chip?.className).toContain("yellow");
  });

  it("applies silver style for score 60-74", () => {
    const { container } = render(
      <SkillChips competencies={[{ competency_id: "communication", score: 60 }]} />
    );
    const chip = container.querySelector("span.rounded-full");
    expect(chip?.className).toContain("slate");
  });

  it("applies bronze style for score 40-59", () => {
    const { container } = render(
      <SkillChips competencies={[{ competency_id: "communication", score: 40 }]} />
    );
    const chip = container.querySelector("span.rounded-full");
    expect(chip?.className).toContain("amber");
  });

  it("applies none style for score < 40", () => {
    const { container } = render(
      <SkillChips competencies={[{ competency_id: "communication", score: 20 }]} />
    );
    const chip = container.querySelector("span.rounded-full");
    expect(chip?.className).toContain("bg-muted");
  });

  it("platinum boundary: score 89 gets gold not platinum", () => {
    const { container } = render(
      <SkillChips competencies={[{ competency_id: "communication", score: 89 }]} />
    );
    const chip = container.querySelector("span.rounded-full");
    expect(chip?.className).toContain("yellow");
    expect(chip?.className).not.toContain("violet");
  });

  it("bronze boundary: score 39 gets none not bronze", () => {
    const { container } = render(
      <SkillChips competencies={[{ competency_id: "communication", score: 39 }]} />
    );
    const chip = container.querySelector("span.rounded-full");
    expect(chip?.className).toContain("bg-muted");
    expect(chip?.className).not.toContain("amber");
  });
});

// ── 3. ActivityTimeline ───────────────────────────────────────────────────────

describe("ActivityTimeline — empty state", () => {
  it("renders empty state with noEventsYet text when events=[]", () => {
    render(<ActivityTimeline events={[]} />);
    expect(screen.getByText("profile.noEventsYet")).toBeInTheDocument();
  });

  it("does not render timeline rows when events=[]", () => {
    const { container } = render(<ActivityTimeline events={[]} />);
    expect(container.querySelectorAll(".flex.items-start.gap-3")).toHaveLength(0);
  });
});

describe("ActivityTimeline — event rendering", () => {
  const baseEvent: TimelineEvent = {
    id: "ev1",
    event_name: "COP29 Side Event",
    event_date: "2024-11-15T10:00:00Z",
    role: null,
    participated: false,
  };

  it("renders event names", () => {
    render(<ActivityTimeline events={[baseEvent]} />);
    expect(screen.getByText("COP29 Side Event")).toBeInTheDocument();
  });

  it("formats dates from ISO string", () => {
    render(<ActivityTimeline events={[baseEvent]} />);
    // Should render a date string (e.g. "Nov 15, 2024" depending on locale)
    const dateEl = document.querySelector("span.text-xs.text-muted-foreground");
    expect(dateEl).toBeInTheDocument();
    expect(dateEl?.textContent).toBeTruthy();
  });

  it("shows role when present", () => {
    render(
      <ActivityTimeline
        events={[{ ...baseEvent, role: "coordinator" }]}
      />
    );
    expect(screen.getByText("coordinator")).toBeInTheDocument();
  });

  it("shows role separator dot when role is present", () => {
    render(
      <ActivityTimeline events={[{ ...baseEvent, role: "coordinator" }]} />
    );
    // The separator "·" should be present
    expect(screen.getByText("·")).toBeInTheDocument();
  });

  it("hides role text when role is null", () => {
    render(<ActivityTimeline events={[{ ...baseEvent, role: null }]} />);
    expect(screen.queryByText("·")).not.toBeInTheDocument();
  });

  it("shows check-in indicator when participated=true", () => {
    render(<ActivityTimeline events={[{ ...baseEvent, participated: true }]} />);
    expect(screen.getByText(/events\.checkedIn/)).toBeInTheDocument();
  });

  it("does not show check-in indicator when participated=false", () => {
    render(<ActivityTimeline events={[{ ...baseEvent, participated: false }]} />);
    expect(screen.queryByText(/events\.checkedIn/)).not.toBeInTheDocument();
  });

  it("renders multiple events", () => {
    const events: TimelineEvent[] = [
      { id: "e1", event_name: "Event Alpha", event_date: "2024-01-01T00:00:00Z", role: null, participated: false },
      { id: "e2", event_name: "Event Beta", event_date: "2024-06-01T00:00:00Z", role: null, participated: false },
      { id: "e3", event_name: "Event Gamma", event_date: "2024-12-01T00:00:00Z", role: null, participated: true },
    ];
    render(<ActivityTimeline events={events} />);
    expect(screen.getByText("Event Alpha")).toBeInTheDocument();
    expect(screen.getByText("Event Beta")).toBeInTheDocument();
    expect(screen.getByText("Event Gamma")).toBeInTheDocument();
  });
});

// ── 4. ImpactMetrics ──────────────────────────────────────────────────────────

describe("ImpactMetrics — rendering", () => {
  const baseData: ImpactData = {
    events_count: 12,
    hours_volunteered: 48,
    verified_skills: 5,
  };

  it("renders 3 metric cards", () => {
    const { container } = render(<ImpactMetrics data={baseData} />);
    // Each card has text-center class
    expect(container.querySelectorAll(".text-center")).toHaveLength(3);
  });

  it("shows events_count value", () => {
    render(<ImpactMetrics data={baseData} />);
    expect(screen.getByText("12")).toBeInTheDocument();
  });

  it("shows hours_volunteered value", () => {
    render(<ImpactMetrics data={baseData} />);
    expect(screen.getByText("48")).toBeInTheDocument();
  });

  it("shows verified_skills value", () => {
    render(<ImpactMetrics data={baseData} />);
    expect(screen.getByText("5")).toBeInTheDocument();
  });

  it("all icons have aria-hidden", () => {
    const { container } = render(<ImpactMetrics data={baseData} />);
    const svgs = container.querySelectorAll("svg");
    svgs.forEach((svg) => {
      expect(svg).toHaveAttribute("aria-hidden", "true");
    });
  });

  it("renders zero values correctly", () => {
    render(<ImpactMetrics data={{ events_count: 0, hours_volunteered: 0, verified_skills: 0 }} />);
    const zeros = screen.getAllByText("0");
    expect(zeros).toHaveLength(3);
  });

  it("shows events_count i18n label", () => {
    render(<ImpactMetrics data={baseData} />);
    expect(screen.getByText("profile.eventsCount")).toBeInTheDocument();
  });

  it("shows hoursContributed i18n label", () => {
    render(<ImpactMetrics data={baseData} />);
    expect(screen.getByText("profile.hoursContributed")).toBeInTheDocument();
  });

  it("shows skills i18n label", () => {
    render(<ImpactMetrics data={baseData} />);
    expect(screen.getByText("profile.skills")).toBeInTheDocument();
  });
});

// ── 5. ExpertVerifications ────────────────────────────────────────────────────

describe("ExpertVerifications — empty state", () => {
  it("renders empty state when verifications=[]", () => {
    render(<ExpertVerifications verifications={[]} />);
    expect(screen.getByText("profile.noVerificationsYet")).toBeInTheDocument();
  });
});

describe("ExpertVerifications — verifier display", () => {
  const baseVerification: ExpertVerification = {
    id: "v1",
    verifier_name: "Anar Mammadov",
    verifier_org: "COP29 Secretariat",
    competency_id: "leadership",
    rating: 4,
    comment: null,
    verified_at: "2024-03-15T00:00:00Z",
  };

  it("shows verifier name", () => {
    render(<ExpertVerifications verifications={[baseVerification]} />);
    expect(screen.getByText("Anar Mammadov")).toBeInTheDocument();
  });

  it("shows initials from two-part name (first + last initial)", () => {
    render(<ExpertVerifications verifications={[baseVerification]} />);
    expect(screen.getByText("AM")).toBeInTheDocument();
  });

  it("shows initials from single-word name (first 2 chars uppercased)", () => {
    render(
      <ExpertVerifications
        verifications={[{ ...baseVerification, verifier_name: "Kamala" }]}
      />
    );
    expect(screen.getByText("KA")).toBeInTheDocument();
  });

  it("shows initials from multi-part name (first + last initial)", () => {
    render(
      <ExpertVerifications
        verifications={[{ ...baseVerification, verifier_name: "Ali Huseyn Bayramov" }]}
      />
    );
    expect(screen.getByText("AB")).toBeInTheDocument();
  });
});

describe("ExpertVerifications — rating dots", () => {
  const baseVerification: ExpertVerification = {
    id: "v1",
    verifier_name: "Anar Mammadov",
    verifier_org: null,
    competency_id: "leadership",
    rating: 3,
    comment: null,
    verified_at: "2024-03-15T00:00:00Z",
  };

  it("renders 5 rating dots total", () => {
    const { container } = render(<ExpertVerifications verifications={[baseVerification]} />);
    const ratingContainer = container.querySelector('[aria-label="Rating: 3 out of 5"]');
    expect(ratingContainer).toBeInTheDocument();
    expect(ratingContainer?.querySelectorAll("span")).toHaveLength(5);
  });

  it("aria-label on rating shows correct value", () => {
    const { container } = render(
      <ExpertVerifications verifications={[{ ...baseVerification, rating: 5 }]} />
    );
    expect(container.querySelector('[aria-label="Rating: 5 out of 5"]')).toBeInTheDocument();
  });

  it("rating 1 renders correct aria-label", () => {
    const { container } = render(
      <ExpertVerifications verifications={[{ ...baseVerification, rating: 1 }]} />
    );
    expect(container.querySelector('[aria-label="Rating: 1 out of 5"]')).toBeInTheDocument();
  });
});

describe("ExpertVerifications — org, competency, comment, date", () => {
  const baseVerification: ExpertVerification = {
    id: "v1",
    verifier_name: "Anar Mammadov",
    verifier_org: "COP29 Secretariat",
    competency_id: "leadership",
    rating: 4,
    comment: "Excellent communicator.",
    verified_at: "2024-03-15T00:00:00Z",
  };

  it("shows verifier_org when present", () => {
    render(<ExpertVerifications verifications={[baseVerification]} />);
    expect(screen.getByText("COP29 Secretariat")).toBeInTheDocument();
  });

  it("hides verifier_org when null", () => {
    render(
      <ExpertVerifications
        verifications={[{ ...baseVerification, verifier_org: null }]}
      />
    );
    expect(screen.queryByText("COP29 Secretariat")).not.toBeInTheDocument();
  });

  it("shows competency label via i18n key", () => {
    render(<ExpertVerifications verifications={[baseVerification]} />);
    // t("competency.leadership", { defaultValue: "leadership" }) → "leadership"
    expect(screen.getByText("leadership")).toBeInTheDocument();
  });

  it("shows comment when present", () => {
    render(<ExpertVerifications verifications={[baseVerification]} />);
    // Comment is rendered with ldquo/rdquo HTML entities in italic
    const commentEl = document.querySelector("p.italic");
    expect(commentEl).toBeInTheDocument();
    expect(commentEl?.textContent).toContain("Excellent communicator.");
  });

  it("hides comment when null", () => {
    render(
      <ExpertVerifications
        verifications={[{ ...baseVerification, comment: null }]}
      />
    );
    expect(document.querySelector("p.italic")).not.toBeInTheDocument();
  });

  it("shows date formatted as 'Mon YYYY'", () => {
    render(<ExpertVerifications verifications={[baseVerification]} />);
    // verified_at: 2024-03-15 → "Mar 2024" (locale-dependent but contains year)
    const dateEl = Array.from(document.querySelectorAll("span.text-xs.text-muted-foreground")).find(
      (el) => el.textContent?.includes("2024")
    );
    expect(dateEl).toBeInTheDocument();
  });

  it("renders multiple verifications", () => {
    const v2: ExpertVerification = {
      id: "v2",
      verifier_name: "Leyla Hasanova",
      verifier_org: null,
      competency_id: "communication",
      rating: 5,
      comment: null,
      verified_at: "2024-06-01T00:00:00Z",
    };
    render(<ExpertVerifications verifications={[baseVerification, v2]} />);
    expect(screen.getByText("Anar Mammadov")).toBeInTheDocument();
    expect(screen.getByText("Leyla Hasanova")).toBeInTheDocument();
    // t("competency.leadership", { defaultValue: "leadership" }) → "leadership"
    expect(screen.getByText("leadership")).toBeInTheDocument();
    // t("competency.communication", { defaultValue: "communication" }) → "communication"
    expect(screen.getByText("communication")).toBeInTheDocument();
  });
});
