const { Document, Packer, Paragraph, TextRun, AlignmentType, BorderStyle, TabStopType, TabStopPosition, LevelFormat, HeadingLevel } = require("docx");
const fs = require("fs");

const N = "1B2A4A", A = "4A90D9", G = "666666";

function bullet(text) {
  return new Paragraph({ numbering: { reference: "b", level: 0 }, spacing: { after: 40 }, children: [new TextRun({ text, size: 20 })] });
}

function jobTitle(title, dates) {
  return new Paragraph({
    spacing: { before: 160, after: 40 },
    tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
    children: [
      new TextRun({ text: title, bold: true, size: 22, color: N }),
      new TextRun({ text: "\t" + dates, size: 20, color: G }),
    ]
  });
}

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Calibri", size: 22, color: "333333" } } },
    paragraphStyles: [{
      id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { size: 26, bold: true, font: "Calibri", color: N },
      paragraph: { spacing: { before: 300, after: 100 }, border: { bottom: { style: BorderStyle.SINGLE, size: 2, color: A } } }
    }]
  },
  numbering: { config: [{ reference: "b", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 720, right: 1080, bottom: 720, left: 1080 } } },
    children: [
      // Header
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 40 }, children: [new TextRun({ text: "YUSIF GANBAROV", bold: true, size: 40, color: N })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 40 }, children: [new TextRun({ text: "AI Product Leader & Senior Program Manager", size: 24, color: A, italics: true })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [new TextRun({ text: "Baku, Azerbaijan | +994 55 585 77 91 | yusif.ganbarov@gmail.com | linkedin.com/in/yusifganbarov", size: 18, color: G })] }),

      // Summary
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("SUMMARY")] }),
      new Paragraph({ spacing: { after: 200 }, children: [new TextRun({ text: "Experienced program manager with 10+ years delivering international events (WUF13 UN-Habitat, COP29 Azerbaijan PMO, CIS Games 2025). Simultaneously founded Volaura \u2014 an AI-powered talent verification platform built from zero to production in 12 days. Combines deep operational expertise (200+ vendors, 15,000+ guests, government relations) with hands-on AI product leadership (48-agent AI swarm, multi-model orchestration, neurocognitive architecture research).", size: 21 })] }),

      // Work Experience
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("WORK EXPERIENCE")] }),

      jobTitle("WUF13 \u2014 Operations Senior Manager, Guest Services", "Dec 2025 \u2013 Present"),
      bullet("Led guest operations across 3 venue zones: 35+ coordinators, 220+ volunteers, 15,000+ guests and VIP delegates"),
      bullet("Optimized volunteer workflows increasing operational efficiency by 20%"),
      bullet("Coordinated with government bodies and international organizations on protocol and VIP services"),
      bullet("Developed operational plans, org charts, WBS, and crowd management strategies"),

      jobTitle("CIS Games 2025 \u2014 Venue/SPS Coordinator, Ganja Olympic Venue", "Aug \u2013 Oct 2025"),
      bullet("Managed operations across 30+ venues with 200+ volunteers and 5,000+ athletes"),
      bullet("Coordinated cross-department operations with government bodies, maintained issue/risk logs"),

      jobTitle("COP29 Azerbaijan \u2014 Program Planning Manager, PMO", "Jun \u2013 Dec 2024"),
      bullet("Improved ClickUp data accuracy from 60% to 98%, reducing reporting time by 50%"),
      bullet("Tracked 170+ milestones per UN/UNFCCC requirements across 80+ coordination meetings"),
      bullet("Introduced unified reporting formats improving cross-department alignment and leadership visibility"),

      jobTitle("Megatransko LLC \u2014 Project Manager / Executive Director", "Aug 2019 \u2013 Present"),
      bullet("Delivered 40+ projects worth $50M+ on time and within budget"),
      bullet("Achieved 15% savings on $2M project through vendor negotiations and cost control"),

      jobTitle("I Step LLC \u2014 Director of Sales / Project Manager", "Mar 2016 \u2013 Aug 2019"),
      bullet("Founded Golden Byte \u2014 international IT championship ($20K prize pool, government partnerships, zero marketing budget)"),
      bullet("Developed KPIs and sales reports informing strategic decisions; coached sales and project teams"),

      // AI Projects
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("AI & TECHNOLOGY PROJECTS")] }),

      jobTitle("Volaura \u2014 Founder & AI Product Lead", "Mar 2026 \u2013 Present"),
      bullet("Designed and built verified talent platform: adaptive IRT/CAT assessment engine, AURA competency scoring, B2B talent discovery"),
      bullet("Built 48-agent AI swarm with multi-model orchestration (Gemini, Llama 405B, DeepSeek R1, local GPU inference)"),
      bullet("Implemented Toyota TPS quality standards with DORA metrics tracking"),
      bullet("Created Pulse Cognitive Architecture (emotional core for AI agents based on Global Workspace Theory)"),
      bullet("Stack: Next.js 14, FastAPI, Supabase (PostgreSQL + pgvector), Railway, Vercel, Langfuse, Ollama"),

      jobTitle("MindShift \u2014 Founder", "Mar 2026 \u2013 Present"),
      bullet("ADHD-aware productivity PWA with Capacitor mobile app, 330+ E2E Playwright tests, AI companion (Gemini)"),

      jobTitle("BrandedBy \u2014 Co-founder", "Mar 2026 \u2013 Aug 2026"),
      bullet("AI Twin platform: professional video generation from portrait + script. Built FAL API + SadTalker integration, personality inference engine"),
      bullet("Left due to team execution issues; technical architecture completed and handed over"),

      // Education & Skills
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("EDUCATION & SKILLS")] }),
      new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: "Education: ", bold: true, size: 20 }), new TextRun({ text: "Bachelor in Business Development (KHPI, Ukraine) | Front-End Web Dev Diploma (IT Step)", size: 20 })] }),
      new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: "Core: ", bold: true, size: 20 }), new TextRun({ text: "Program management, AI product strategy, event operations, budget control ($10M+), stakeholder management, government relations, team leadership (200+ people)", size: 20 })] }),
      new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: "Technical: ", bold: true, size: 20 }), new TextRun({ text: "Python, FastAPI, TypeScript, Next.js, Supabase, PostgreSQL, pgvector, AI/ML orchestration, LLM integration, Ollama/local GPU inference", size: 20 })] }),
      new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: "Methods: ", bold: true, size: 20 }), new TextRun({ text: "Agile, Kanban, PMP, Toyota TPS, DORA metrics", size: 20 })] }),
      new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: "Languages: ", bold: true, size: 20 }), new TextRun({ text: "Azerbaijani (native), Russian (native), English (fluent), Turkish (conversational)", size: 20 })] }),
      new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: "Certifications: ", bold: true, size: 20 }), new TextRun({ text: "PMP | IT Project Management | Google Project Management | IT Essentials (Cisco)", size: 20 })] }),
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("C:/Projects/VOLAURA/docs/Yusif_Ganbarov_CV_2026_v2.docx", buffer);
  console.log("CV SAVED: docs/Yusif_Ganbarov_CV_2026_v2.docx");
});
