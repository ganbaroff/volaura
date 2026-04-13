# Multi-Product Ecosystem Design Research — 2026-03-28

**Cross-references:** [[ECOSYSTEM-REDESIGN-BRIEF-2026-04-14]] | [[adhd-first-ux-research]] | [[../ECOSYSTEM-CONSTITUTION]] | [[../design/COMPONENT-LIBRARY]] | [[../design/STITCH-DESIGN-SYSTEM]] | [[../LIFE-SIMULATOR-INTEGRATION-SPEC]]

## Winner Pattern: Discord Three-Rail + Duolingo Semantic Colors + Character-Centric Identity

## 10 Design Decisions

### 1. Navigation: Discord's Bottom Tab Pattern
- 5 tabs max: [Volaura] [Habits] [Life Sim] [AI Twin] [Character]
- Each tab = independent context with own sub-navigation
- NOT Notion sidebar (single product), NOT Atlassian waffle (enterprise)

### 2. App Switcher: Embedded in Character Avatar
- Tap character → bottom sheet with products + character stats
- Combines Atlassian "avatar menu" + "app switcher" into one gesture
- Precedent: Habitica

### 3. Color Strategy: Semantic Per Product
| Product | Color | Meaning |
|---------|-------|---------|
| Volaura | Indigo `#4F46E5` | Trust, credibility |
| Habits | Emerald `#10B981` | Growth, health |
| Life Sim | Purple `#7C3AED` | Fantasy, power |
| AI Twin | Sky `#0EA5E9` | Tech, intelligence |
| Hiring | Amber `#F59E0B` | Opportunity, action |
- Shared: same dark neutrals, same typography, same spacing tokens

### 4. Token Architecture: Atlaskit Semantic Pattern
```css
@theme {
  --color-brand-primary: #4F46E5;
  --color-text-default: #e2e8f0;
  --color-text-subtle: #94a3b8;
  --color-surface-raised: #1e293b;
  --color-surface-overlay: #0f172a;
  --color-status-success: #10B981;
  --color-status-warning: #F59E0B;
  --color-status-danger: #EF4444;
  --space-100: 4px;
  --space-200: 8px;
  --space-400: 16px;
  --space-600: 24px;
  --space-800: 32px;
}
```

### 5. Identity: Character IS the Identity
- Illustrated character (not photo) in nav
- Visual changes with AURA tier (Bronze → Platinum outfit)
- Active streak = glow effect
- Recent achievement = temporary badge

### 6. ADHD-First Nav Rules
- Max 4 visible bottom tabs (5th via character sheet)
- No hamburger menus — all primary destinations visible
- Active state: large filled icon + color + label always visible
- Every screen labeled with persistent header

### 7. Cross-Product Progress: Character Sheet
- Central "Character Sheet" view replacing dashboard
- Shows: AURA radar, streak, level, per-product XP contribution
- Emotional center of the product

### 8. Mobile-First: 375px Primary Breakpoint
- Mid-range Android (Samsung A-series, Xiaomi Redmi) is majority device
- 48px minimum tap targets
- Bottom nav within thumb reach
- WebP images, lazy load, <200KB initial JS bundle

### 9. Transitions: Character Animation
- Tab switch → 150ms character transition (Framer Motion)
- Character "changes outfit" per product context
- Navigation IS the game

### 10. The Differentiator
No multi-product platform treats navigation as character interaction.
Our navigation is gameplay. Every tab switch = character entering a world.

## Sources
- Atlassian unified nav 2025 (3 base components, token-driven)
- Google Material 3 Expressive (spring physics, vibrant blur)
- Discord bottom tab redesign (failed horizontal → successful vertical)
- Duolingo semantic color system (green=success, red=cost, yellow=premium)
- Notion sidebar pattern (rejected for multi-product)
