---
name: design-director
description: Pick the right Design Hub skills for a web design task. Use at the start of any website, UI, landing page, dashboard, animation, 3D, slide or branding request, or whenever the user asks which design skill to use. Reads the brief, checks which hub plugins are installed, chooses the smallest set of skills that fits, and returns a short plan with the order to apply them. It routes; it does not design.
---

# Design director

The Design Hub holds about 60 skills, some of them with dozens of commands. Loading all of them wastes context and produces muddled work. Your job is to choose the few that matter, say in what order to use them, and name any plugin that is missing.

## Steps

1. **Read the brief.** Classify it: new build, redesign, polish, audit or critique, animation, 3D, slides or demo, dashboard, branding, build from a reference, or understanding existing code. If the brief is too thin to classify, ask at most two short questions (what is it for, who is it for) and continue.
2. **Check what is installed.** Look at the skills available in this session. A skill is installed if its name is in your skill list. For every skill you want that is missing, note its plugin from the table below.
3. **Choose the smallest set.** One primary skill, at most two supporting skills. Do not add a skill because it is related; add it because the result would be worse without it.
4. **Order them.** Direction first, then build, then polish, then check.
5. **Return the plan** in the format below. Do not start the design work yourself unless the user tells you to.

## Routing table

| The task | Use | Plugin |
|---|---|---|
| New page, site or UI with a distinctive look | `impeccable` (shape, then craft), `frontend-design` | design-core |
| Look up styles, palettes, font pairings, UX rules, chart types, stack advice | `ui-ux-pro-max` | design-core |
| Critique, audit or polish an existing interface | `impeccable` (critique, audit, polish) | design-core |
| UI looks AI-generated: purple gradients, glows, emoji labels, uneven spacing | `unslop` | unslop |
| Design tokens or a design system | `design-system`, `impeccable` (extract) | design-core |
| Shadcn, Tailwind, accessible components, dark mode | `ui-styling` | design-core |
| Brand voice, identity, logo, style guide | `brand`, `design` | design-core |
| Banners for social, ads, heroes | `banner-design` | design-core |
| Full visual brand system through Higgsfield | `higgsfield-brandkit` | ai-site-brand |
| Whole site or app built and deployed through Higgsfield | `higgsfield-websites` | ai-site-brand |
| Modern HTML, CSS and browser APIs instead of legacy workarounds | `modern-web-guidance` (run before writing HTML or CSS) | modern-web-guidance |
| Chrome extension | `chrome-extensions` | modern-web-guidance |
| Animation in code: pick one of `gsap-core`, `gsap-timeline`, `gsap-scrolltrigger`, `gsap-plugins`, `gsap-react`, `gsap-frameworks`, `gsap-utils`, `gsap-performance` | the GSAP skill that matches | motion |
| Motion graphics or video from an agent | `open-motion` | open-motion |
| 3D or WebGL | start with `threejs-skill-router`; for games use `threejs-game-director` | threejs |
| Slide deck | `frontend-slides` for animated decks, `slides` for strategic decks with charts | web-visuals, design-core |
| Recorded UI demo video | `ui-demo` | web-visuals |
| Monitoring dashboard | `dashboard-builder` | web-visuals |
| React or Next.js front-end patterns | `frontend-patterns` | web-visuals |
| Understand an existing codebase before changing it | `floorplan` | floorplan |
| Study how a shipped site or app works | `reverse-engineer-anything`, or `craft-anything` | rea, craft-anything |

## Rules

- Never load an animation skill unless the brief asks for motion.
- For 3D, always go through `threejs-skill-router` first; it names the few Three.js skills that apply.
- When two skills overlap (for example `impeccable` and `frontend-design`), pick one and say why. Do not run both for the same job.
- Skills from other authors keep their own conventions. Follow each one's instructions when you apply it.
- If a missing plugin is essential, say so plainly instead of improvising without it.

## Output format

```
Goal: one sentence.
Primary skill: name (plugin).
Supporting skills: up to two, each with the reason.
Order: numbered steps, last step being a check with the design-reviewer agent if it exists.
Missing plugins: install lines, or "none".
Open questions: at most two, or "none".
```

Install lines to give the user:

- Claude Code: `/plugin marketplace add Seanfo2332/design-hub` once, then `/plugin install <plugin>@design-hub`
- Codex: `codex plugin marketplace add Seanfo2332/design-hub` once, then `codex plugin add <plugin>@design-hub`
