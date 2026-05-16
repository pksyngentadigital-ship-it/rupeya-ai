# Rupeya.ai — Phase B1 Design System Audit

Source of truth: `prototype/style.css` + 8 prototype HTML pages.
Goal: faithfully port this system into Next.js + Tailwind without losing visual identity.

---

## 1. Design tokens (CSS variables → Tailwind theme)

### Colors (dark mode default)
| Token | Hex | Tailwind name | Purpose |
|---|---|---|---|
| `--bg` | `#0B0F14` | `background` | Page background |
| `--surface` | `#121821` | `surface` | Cards, nav background |
| `--surface-alt` | `#1A2230` | `surfaceAlt` | Hovered/pressed states, table row hover |
| `--border` | `#1F2A3A` | `border` | Default borders, hairlines |
| `--border-strong` | `#2A3850` | `borderStrong` | Form inputs, ghost button border |
| `--text` | `#E6EDF3` | `text` | Primary text (7.8:1 contrast on bg) |
| `--text-muted` | `#8B95A7` | `textMuted` | Secondary text, captions, kicker |
| `--accent` | `#16C784` | `accent` | Brand green, primary CTAs, success |
| `--accent-soft` | `#0F3A2A` | `accentSoft` | Accent backgrounds (chips, hover tint) |
| `--warn` | `#F0B72F` | `warn` | TRIM, dividend tag |
| `--danger` | `#EA3943` | `danger` | EXIT, errors |
| `--info` | `#4F8DF7` | `info` | HOLD, growth tag |

### Border radius
| Token | Value | Tailwind |
|---|---|---|
| `--radius-sm` | `6px` | `rounded-sm` (override) |
| `--radius` | `10px` | `rounded` (override) |
| `--radius-lg` | `14px` | `rounded-lg` (override) |
| `--radius-xl` | `20px` | `rounded-xl` (override) |

### Container width
- `--max: 1100px` → Tailwind `max-w-page` custom utility

### Fonts
- Sans: `ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Inter, sans-serif`
- Mono: `ui-monospace, "SF Mono", "Cascadia Code", Consolas, monospace`
- **No external font loads** — system stack only (matches blueprint Section 7.6: dark mode default, premium feel, fast)

---

## 2. Typography scale

| Element | Size | Line height | Weight | Mobile (≤700px) |
|---|---|---|---|---|
| h1 | 56px | 1.05 | 700 | 38px |
| h2 | 32px | 1.15 | 700 | 26px |
| h3 | 20px | 1.25 | 600 | unchanged |
| h4 | 16px | — | 600 | unchanged |
| body | 16px | 1.55 | 400 | unchanged |
| `.muted` | inherit | — | — | uses `text-muted` color |
| `.tiny` | 12px | — | — | uses `text-muted` color |
| `.kicker` | 12px | — | — | uppercase, letter-spaced, pill bg |

---

## 3. Layout primitives

| Class | Behavior |
|---|---|
| `.container` | `max-width: 1100px; margin: auto; padding: 0 24px` |
| `.section` | `padding: 64px 0` |
| `.section-tight` | `padding: 40px 0` |
| `.row` | flexbox horizontal, gap 16px, items center |
| `.col` | flexbox vertical, gap 16px |
| `.between` | `justify-content: space-between` |
| `.wrap` | flex-wrap |
| `.grid-3` | 3-col grid, gap 24px → 1-col below 800px |
| `.grid-2` | 2-col grid, gap 24px → 1-col below 800px |
| `.grid-4` | 4-col grid, gap 16px → 1-col below 800px |
| `.center` | text-align center |
| `.mb-{8,16,24,32}` | margin-bottom utilities |
| `.mt-{8,16,24,32}` | margin-top utilities |
| `.hr` | 1px horizontal rule |

---

## 4. Recurring components

### Nav (`<nav class="nav">`)
- Sticky top, backdrop-blur, semi-transparent bg
- Logo (gradient square `₨` mark + "Rupeya" text + green ".ai" suffix)
- Right side: link list + Sign in (ghost) + Get started (primary) on landing; reduced links on app pages

### Buttons
- `.btn` base + variants:
  - `.btn-primary` — green `var(--accent)` bg, dark text
  - `.btn-ghost` — transparent bg, `border-strong`, white text
  - `.btn-soft` — `surface-alt` bg, white text
- `.btn-lg` modifier — bigger padding, 16px font

### Chips
- `.chip` — pill, surface bg, muted text, 12px
- `.chip-accent` — accent-soft bg, accent text (Shariah ☪, "Most popular")

### Verdict badges (5 levels)
- `.badge-strong-buy` — green bg, dark text (highest emphasis)
- `.badge-buy` — accent-soft bg, green text
- `.badge-hold` — `#1E2A3D` bg, info-blue text
- `.badge-trim` — `#3A2D14` bg, warn-amber text
- `.badge-exit` — `#3A1A1F` bg, danger-red text
- All UPPERCASE, 11px, 700 weight, rounded 6px

### Stock-style tags (inline next to ticker name)
- `.tag-dividend` — amber on amber-tint (`💰 Dividend`)
- `.tag-growth` — info on blue-tint (`🚀 Growth`)
- `.tag-both` — accent on accent-soft (`⚖️ Both`)
- All 10.5px, 600 weight, tiny pill

### Cards
- `.card` — surface bg, border, radius-lg, padding 22px
- `.card-hl` — accent border + gradient overlay (highlighted plan, recommended pick)

### Score bars (`.scorebar`)
- Horizontal track (8px) with accent fill
- `.warn` and `.danger` fill variants (for color-coded pillar scores)

### Status dots (`.dot`)
- 8px round
- `.dot-good` (accent), `.dot-warn` (amber), `.dot-bad` (danger)

### Forms
- `.input`, `.textarea`, `.select` — surface bg, border-strong, radius
- Focus state: border-accent
- `.option` — quiz answer cards with hover + selected states

### Footer
- `border-top`, surface bg, 36px vertical padding
- `.disclaimer` block (12px, muted, 640px max-width) — required on every page per blueprint Section 16

---

## 5. Per-page section inventory

### `index.html` — Landing
1. Nav (logo + links + Sign in + Get started)
2. Hero (kicker, h1 with green accent on "AI stock analyst", subhead, 2 CTAs, disclaimer line)
3. Trust band (4 status-dot claims)
4. How it works (3 numbered cards)
5. Stock of the Day preview
6. Pricing (3 cards: Monthly / 6mo / Annual — middle highlighted)
7. Footer with full disclaimer

### `onboarding.html` — Investor profile quiz
1. Nav (minimal)
2. Progress bar
3. Active question card (one at a time, .option list)
4. Back / Next nav
5. (End) profile summary card + "Build my portfolio" CTA

### `dashboard.html` — Returning user
1. Nav
2. Top: Portfolio Health card (big number + traffic light + 1-line action)
3. Today's Insights row (≤3 cards)
4. Holdings table with mini-verdicts
5. Right rail: Ask Rupeya entry

### `portfolio-builder.html` — AI-built portfolio result
1. Header: portfolio summary (count, sectors, blended MoS)
2. Per-stock cards (6–7 rec'd, expandable to 8–9 per blueprint Section 6.2)
3. Sector mix visualization
4. **Runners-up watchlist** section (per updated blueprint)
5. Save / accept CTAs

### `portfolio-doctor.html` — Holdings analysis
1. Holdings input area
2. Per-stock verdict cards
3. Strengths section
4. Weaknesses section
5. Diversification map
6. Overvalued holdings
7. Undervalued opportunities
8. Action plan (ranked moves)

### `stock.html` — Single stock detail
1. Stock header (ticker, name, sector, Shariah chip, style tag, current price)
2. Price chart vs intrinsic value
3. RupeyaScore breakdown (4 pillars + composite)
4. Key fundamentals table
5. News list
6. AI summary paragraph

### `compare.html` — 2–4 stock comparison
1. Ticker selector
2. Comparison matrix (rows: Verdict & Score, Valuation, Quality, Income, Risk)
3. AI synthesis paragraph
4. "Add winner to portfolio" CTA

### `ask-rupeya.html` — Agent chat
1. Conversation thread
2. Message input
3. Example query chips
4. Collapsed "Research trace" panel showing tool calls

---

## 6. Accessibility / quality notes for the React port

- **No alt text** on most decorative SVGs in the prototype — fix with `aria-hidden="true"` on icon spans
- **Color contrast** — `text-muted #8B95A7` on `bg #0B0F14` is **5.2:1** (passes WCAG AA for normal text); on `surface #121821` it's **4.7:1** (borderline; verify case-by-case)
- **Form labels** — `.option` quiz answers should be `<label>` wrapping a hidden radio for keyboard nav
- **Focus states** — only `.input:focus` is defined; need to add visible focus rings on buttons and links
- **Mobile breakpoints** — only 800px (grid collapse) and 700px (h1/h2 shrink); we'll add 380px-specific tweaks during the port

---

## 7. Data shapes the React components will need

```ts
type Verdict = "STRONG BUY" | "BUY" | "HOLD" | "TRIM" | "EXIT";
type Style = "dividend" | "growth" | "both" | "cyclical";

interface Stock {
  ticker: string;
  name: string;
  sector: string;
  isShariahCompliant: boolean;
  style: Style;
  price: number;
  intrinsicValue: number;
  marginOfSafety: number;
  score: { businessQuality: number; financialHealth: number; valuation: number; catalysts: number; composite: number };
  verdict: Verdict;
  flags?: string[];
}

interface Portfolio {
  id: string; name: string;
  holdings: Array<{ stock: Stock; weight: number; quantity?: number; avgCost?: number }>;
  healthScore: number; // 0-100
  blendedMarginOfSafety: number;
  sectorMix: Array<{ sector: string; weight: number }>;
  runnersUp: Array<{ stock: Stock; reason: string }>;
}

interface InvestorProfile {
  horizonYears: number;
  riskScore: number;
  incomeVsGrowth: "income" | "growth" | "balanced";
  monthlySipPkr: number;
  lumpSumPkr: number;
  experience: "novice" | "1-2y" | "3+y";
  shariahOnly: boolean;
  goalText: string;
}
```
