/**
 * Mock data for Session 10 (landing + events).
 * Session 11: replace with real API calls via TanStack Query.
 * All functions return the same shape as the real API will return.
 */

export interface ImpactStats {
  totalVolunteers: number;
  totalEvents: number;
  totalHours: number;
}

export interface MockEvent {
  id: string;
  title: string;
  titleAz: string;
  description: string;
  descriptionAz: string;
  organizerName: string;
  location: string;
  locationAz: string;
  startDate: string; // ISO string
  endDate: string;
  currentVolunteers: number;
  maxVolunteers: number;
  status: "upcoming" | "live" | "past";
  isFree: boolean;
  tags: string[];
}

export interface BadgeTierStats {
  platinum: number;
  gold: number;
  silver: number;
  bronze: number;
  total: number;
}

// Impact ticker — will come from GET /api/stats/public in Session 11
export function getMockImpactStats(): ImpactStats {
  return {
    totalVolunteers: 1247,
    totalEvents: 83,
    totalHours: 18640,
  };
}

// Badge distribution — will come from GET /api/stats/badges in Session 11
export function getMockBadgeTierStats(): BadgeTierStats {
  return {
    platinum: 47,
    gold: 189,
    silver: 412,
    bronze: 599,
    total: 1247,
  };
}

// Events list — will come from GET /api/events in Session 11
export function getMockEvents(): MockEvent[] {
  return [
    {
      id: "evt-001",
      title: "Environmental Awareness Campaign",
      titleAz: "Ətraf Mühit Maarifçilik Kampaniyası",
      description:
        "Join volunteers across Baku to raise awareness about sustainable practices. Activities include community outreach, workshops, and park cleanup.",
      descriptionAz:
        "Dayanıqlı təcrübələr haqqında maarifçilik üçün Bakı könüllülərinə qoşulun. Fəaliyyətlərə icma ilə ünsiyyət, seminarlar və park təmizliyi daxildir.",
      organizerName: "Green Azerbaijan NGO",
      location: "Baku, Heydar Aliyev Center",
      locationAz: "Bakı, Heydər Əliyev Mərkəzi",
      startDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
      endDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000 + 6 * 60 * 60 * 1000).toISOString(),
      currentVolunteers: 34,
      maxVolunteers: 50,
      status: "upcoming",
      isFree: true,
      tags: ["environment", "community", "outdoor"],
    },
    {
      id: "evt-002",
      title: "Youth Tech Workshop",
      titleAz: "Gənclər Texnologiya Seminarı",
      description:
        "Teach coding fundamentals to high school students across Sumgait. No prior teaching experience needed — just enthusiasm and patience.",
      descriptionAz:
        "Sumqayıtdakı lisey şagirdlərinə proqramlaşdırmanın əsaslarını öyrədin. Əvvəlki tədris təcrübəsi tələb olunmur — yalnız həvəs lazımdır.",
      organizerName: "TechHub Baku",
      location: "Sumgait, Youth Center",
      locationAz: "Sumqayıt, Gənclər Mərkəzi",
      startDate: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString(),
      endDate: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000 + 4 * 60 * 60 * 1000).toISOString(),
      currentVolunteers: 12,
      maxVolunteers: 20,
      status: "upcoming",
      isFree: true,
      tags: ["education", "tech", "youth"],
    },
    {
      id: "evt-003",
      title: "Community Health Fair",
      titleAz: "İcma Sağlamlıq Sərgisi",
      description:
        "Support doctors and nurses at a free health screening event for underserved communities. Help with registration, translation (AZ/RU/EN), and logistics.",
      descriptionAz:
        "Pulsuz sağlamlıq müayinəsi tədbirində həkimlərə dəstək verin. Qeydiyyat, tərcümə (AZ/RU/İN) və logistika ilə kömək edin.",
      organizerName: "Health Azerbaijan Foundation",
      location: "Ganja, Central Park",
      locationAz: "Gəncə, Mərkəzi Park",
      startDate: new Date(Date.now() + 21 * 24 * 60 * 60 * 1000).toISOString(),
      endDate: new Date(Date.now() + 21 * 24 * 60 * 60 * 1000 + 8 * 60 * 60 * 1000).toISOString(),
      currentVolunteers: 28,
      maxVolunteers: 30,
      status: "upcoming",
      isFree: true,
      tags: ["health", "community", "translation"],
    },
    {
      id: "evt-004",
      title: "Cultural Heritage Documentation",
      titleAz: "Mədəni İrs Sənədləşdirilməsi",
      description:
        "Help document and preserve historical sites in the Sheki region. Photography, video, and writing skills welcome.",
      descriptionAz:
        "Şəki bölgəsindəki tarixi yerlərin sənədləşdirilməsinə kömək edin. Foto, video və yazı bacarıqları məmnuniyyətlə qarşılanır.",
      organizerName: "Azerbaijan Heritage Society",
      location: "Sheki, Old City",
      locationAz: "Şəki, Köhnə Şəhər",
      startDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
      endDate: new Date(Date.now() - 29 * 24 * 60 * 60 * 1000).toISOString(),
      currentVolunteers: 45,
      maxVolunteers: 45,
      status: "past",
      isFree: true,
      tags: ["culture", "heritage", "photography"],
    },
  ];
}

// Single event by ID — will come from GET /api/events/{id} in Session 11
export function getMockEventById(id: string): MockEvent | null {
  return getMockEvents().find((e) => e.id === id) ?? null;
}
