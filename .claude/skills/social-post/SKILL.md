---
name: social-post
description: "Write social media posts for LinkedIn, Telegram, X/Twitter — bilingual AZ+EN, VOLAURA ecosystem. Supports Series 1 (Claude as AI CTO diary) and Series 2 (Yusif's founder voice). Use whenever the user asks to write a post, LinkedIn post, social media post, пост, линкедин пост, 'what should I post today', caption, thread, or mentions content for social media. Also use for carousel outlines and newsletter snippets."
---

# Social Post Skill

Standalone skill for writing social media posts. For full content batches, use the content-factory skill.

## Before Writing

1. Read `../content-factory/references/social-formats.md` for format templates
2. Read `../content-factory/references/tone-rules.md` for voice rules and anti-AI filters
3. Determine:
   - **Platform:** LinkedIn, Telegram, X, or Newsletter?
   - **Language:** EN or AZ? (if LinkedIn: always produce BOTH, AZ is NOT a translation)
   - **Series:** Series 1 (Claude voice) or Series 2 (Yusif voice)?
   - **Topic:** What's the core idea?

## Series Selection Guide

| Signal | Series |
|--------|--------|
| About building the product, agent management, AI ops | Series 1 (Claude) |
| About Yusif's personal journey, volunteer industry, AZ tech | Series 2 (Yusif) |
| AZ language post | Almost always Series 2 |
| Technical behind-the-scenes | Series 1 |
| Cultural commentary, systemic observation | Series 2 |
| Funny AI failure story | Series 1 |

## Output Format

```
## [PLATFORM] — [LANGUAGE] — Series [1/2]

**Hook type:** [1 of 6]
**Product connection:** [product(s)]

---

[POST CONTENT]

---

**Hashtags:** [3-5]
**CTA:** [the one action]
**Best time to post:** [day + time]
**First comment:** [link + UTM if applicable]
**Quality check:** ✅/⚠️
```

## Bilingual Pair Output

When writing LinkedIn posts, ALWAYS produce both EN and AZ unless specifically asked for only one:

**EN version:** Global tech audience. Can be either Series 1 or 2.
**AZ version:** Baku/Azerbaijan audience. Different opening, different angle. Series 2 preferred.

These are TWO DIFFERENT POSTS sharing the same core idea. Not translations.

## Carousel Mode

When asked for a carousel:

```
SLIDE 1: [Hook text — large, bold]
SLIDE 2: [Context — 15-25 words]
SLIDE 3-7: [One idea per slide]
SLIDE 8: [Key insight — screenshot-worthy]
SLIDE 9: [CTA]
SLIDE 10: [Optional — profile card]

Design notes: No red. Purple/blue palette. One typeface. Mobile-first.
```

## Performance Insights (from real data)

- AZ posts: +67% impressions vs EN, more DM conversions
- Question CTA: 5 DMs. "DM me" CTA: 0 DMs.
- Carousel: 21.7% avg engagement (highest format)
- Post time: Tue/Thu 20:00 Baku (UTC+4)
- First 30 min comment responses: biggest engagement driver
- Post #001 (Mirofish, EN): 1,998 impressions, 64 reactions
- Post #002 (VOLAURA, AZ): 3,333 impressions, 44 reactions, 5 DMs

## Quality Checklist

- [ ] Passes Tinkoff/Aviasales benchmark?
- [ ] Zero banned phrases from anti-AI filter?
- [ ] Real numbers only?
- [ ] Humor present? (mandatory for Series 1, recommended for Series 2)
- [ ] AZ version is native, not translated?
- [ ] Hook type tracked and rotated?
- [ ] Link in first COMMENT, not in post body?
- [ ] One clear CTA?
