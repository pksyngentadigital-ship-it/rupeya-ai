# Rupeya.ai — Founder Setup Guide

This guide is for **you** (non-coder founder) to get the Rupeya.ai app
running on your own Windows machine, then push it live on the internet.
Total time: ~15 minutes the first time.

You don't need to understand the code. You just need to follow these steps.

---

## What we're doing right now

We've scaffolded a real Next.js website on your computer at:

```
C:\Users\Abdullah\Documents\Claude\Projects\Rupeya.ai
```

In the next few minutes, you'll see the Rupeya.ai landing page running
**on your own laptop**. After that, every change Claude makes to the code
will be visible there instantly.

---

## Step 1 — Confirm Node.js works (1 minute)

You said you have Node.js installed. Let's confirm it's a working version.

1. Press **Windows key + R**, type `cmd`, press Enter. (A black window opens.)
2. In that window, type:

   ```
   node --version
   ```

   Press Enter. You should see something like `v20.10.0` or higher.

3. Then type:

   ```
   npm --version
   ```

   You should see something like `10.2.4` or higher.

✅ If both show version numbers, you're good. Skip to Step 2.

❌ If you get "command not found" or a number lower than v18, install the
latest LTS Node from https://nodejs.org/en/download (pick "Windows Installer
64-bit"). Restart the cmd window after installing.

---

## Step 2 — Install the project's dependencies (3 minutes)

In the **same cmd window**, run:

```
cd C:\Users\Abdullah\Documents\Claude\Projects\Rupeya.ai
npm install
```

This downloads about ~250 MB of supporting libraries into a `node_modules`
folder. It only happens once. You'll see a progress bar. When it finishes,
your prompt comes back — that means it worked.

If you see warnings about "deprecated" packages, **ignore them**. Warnings
are normal. Errors (red text saying "ERROR") are not — tell Claude what it says.

---

## Step 3 — Run the website locally (30 seconds)

Same cmd window, run:

```
npm run dev
```

You'll see something like:

```
   ▲ Next.js 14.2.5
   - Local:        http://localhost:3000
   - ready in 1.8s
```

Open your browser and go to **http://localhost:3000**.

🎉 You should see the Rupeya.ai landing page — dark theme, headline, 3-step
explainer, pricing cards, disclaimer at the bottom. Take a screenshot. This
is your product, day one.

To stop the server, click on the cmd window and press **Ctrl + C**.

---

## Step 4 — What's next (we do these together)

Don't do these yet. Claude will walk you through each one when the time is right:

- **Install Git** (so we can save your code to GitHub) — 2 min
- **Install Python** (for the PSX scrapers) — 2 min
- **Create a free GitHub account** — 2 min
- **Create a free Supabase project** (database + auth) — 5 min
- **Create a free Vercel account** (puts your site on the real internet) — 3 min
- **Get an Anthropic API key** (powers the AI features) — 2 min

Each one is free. Total cost so far: PKR 0.

---

## Troubleshooting

**"npm install" fails with permission errors.**
Close the cmd window. Re-open as Administrator (right-click cmd → Run as
administrator), then re-run the commands.

**Browser shows "This site can't be reached."**
The dev server is not running. Go back to cmd, type `npm run dev`, wait
for "ready", refresh the browser.

**Page looks broken / no styling.**
Hard-refresh the browser with **Ctrl + Shift + R**.

**Anything else.**
Copy the exact error message into your chat with Claude. Don't try to fix
it alone.

---

## You don't need to understand any of the code

Your job: design decisions, validation, growth, cash, hiring.
Claude's job: write and fix the code. If a change feels too technical to
review, say "explain this to me like I've never coded" — Claude will.
