# Rupeya.ai

Pakistan's first AI-powered long-term stock analyst for PSX investors.

This repo contains the production codebase. The full architecture and
product design lives in [`Rupeya_ai_project_blueprint.md`](./Rupeya_ai_project_blueprint.md).

**Non-coder founder?** Read [`SETUP.md`](./SETUP.md) first — it walks you
through running this on your machine in ~10 minutes.

## Stack (MVP)

- **Frontend / API:** Next.js 14 (App Router) + TypeScript + Tailwind CSS
- **Backend / DB / Auth:** Supabase (Postgres + Auth + Storage + RLS) — wiring up next
- **Quant engine + scrapers:** Python (added in next iteration)
- **AI:** Claude Haiku + Sonnet via Anthropic API (added when first AI feature lands)
- **Hosting:** Vercel (web) + Render free tier (Python services)

## Local development

```bash
npm install
npm run dev
```

Open http://localhost:3000

## Roadmap

See `Rupeya_ai_project_blueprint.md` Section 12 — Phase 1 MVP runs 14 weeks.
