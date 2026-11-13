# B30 Design Hub

One place to install web design, motion, 3D and analysis skills for **Claude Code** and **Codex**.

The design-skill space is crowded and scattered. This hub collects the best open-source ones, keeps each author's licence and credit, and lets you install only the parts you need.

- 11 plugins, about 64 skills, plus 3 Claude Code agents
- Every upstream is pinned to an exact commit and refreshed through reviewed pull requests
- No plugin registers hooks or MCP servers, so nothing runs by itself when you install one or start a session. Some skills ship helper scripts that Claude runs when you use them; see "Things to know"

## Install

**Claude Code**

```
/plugin marketplace add Seanfo2332/b30-design-hub
/plugin install design-core@b30-design-hub
```

**Codex**

```bash
codex plugin marketplace add Seanfo2332/b30-design-hub
codex plugin add design-core@b30-design-hub
```

Replace `design-core` with any plugin name from the table. Start with `design-core`: it holds the main design skills and the director that tells you which other plugin to add.

## The plugins

| Plugin | What you get | Needs | Added to every session |
|---|---|---|---|
| `design-core` | Impeccable, UI UX Pro Max (7 skills), Anthropic's frontend-design, a `design-director` skill, and 3 agents (Claude Code only) | Node for Impeccable's scripts; Playwright for the reviewer agent | ~1,230 tokens |
| `motion` | The 8 official GSAP skills: core, timeline, ScrollTrigger, plugins, React, frameworks, utils, performance | Nothing | ~690 |
| `threejs` | 33 Three.js skills: procedural geometry, materials, water, clouds, atmosphere, shadows, cameras, post-processing, game systems, QA | About 80 MB of reference assets | ~3,270 |
| `web-visuals` | Animated slides, UI demo videos, monitoring dashboards, front-end patterns | Playwright for demo videos | ~260 |
| `ai-site-brand` | Higgsfield website builder and brand kit | The Higgsfield CLI and a Higgsfield account. They chain with Higgsfield's image and video skills, which are not included | ~500 |
| `unslop` | Turns AI-looking UI into a designed interface | Nothing | ~170 |
| `modern-web-guidance` | Google Chrome's modern web platform guidance, and Chrome extension guidance | Nothing | ~450 |
| `floorplan` | Draws an interactive map of how a codebase fits together | Node 18 or newer | ~240 |
| `rea` | Reverse engineering skill for REA | REA's own tools, installed separately (see below) | ~120 |
| `craft-anything` | Evidence-first investigation of shipped software | The Craft Anything app and MCP server, downloaded separately | ~70 |
| `open-motion` | A setup and usage guide for the OpenMotion motion runtime | Node 22.5 or newer, and OpenMotion itself from its repository | ~80 |

The last column is Claude Code's own estimate of what each plugin adds to every session, which is only the skill descriptions. A skill's full text is loaded when it is used. Installing everything adds about 7,000 tokens.

### Install everything

**Claude Code**

```
/plugin marketplace add Seanfo2332/b30-design-hub
/plugin install design-core@b30-design-hub
/plugin install motion@b30-design-hub
/plugin install threejs@b30-design-hub
/plugin install web-visuals@b30-design-hub
/plugin install ai-site-brand@b30-design-hub
/plugin install unslop@b30-design-hub
/plugin install modern-web-guidance@b30-design-hub
/plugin install floorplan@b30-design-hub
/plugin install rea@b30-design-hub
/plugin install craft-anything@b30-design-hub
/plugin install open-motion@b30-design-hub
```

**Codex**

```bash
codex plugin marketplace add Seanfo2332/b30-design-hub
codex plugin add design-core@b30-design-hub
codex plugin add motion@b30-design-hub
codex plugin add threejs@b30-design-hub
codex plugin add web-visuals@b30-design-hub
codex plugin add ai-site-brand@b30-design-hub
codex plugin add unslop@b30-design-hub
codex plugin add modern-web-guidance@b30-design-hub
codex plugin add floorplan@b30-design-hub
codex plugin add rea@b30-design-hub
codex plugin add craft-anything@b30-design-hub
codex plugin add open-motion@b30-design-hub
```

Install what you will use: every skill you add puts its description into each session (see the table above), and `threejs` is also the largest download at about 80 MB.

## The design-core agents

Agents are a Claude Code feature, so these three do not load in Codex. The director is also a skill, which does work in both.

| Agent | What it does |
|---|---|
| `design-director` | Reads your brief, checks which hub plugins you have, and returns a short plan: one primary skill, up to two supporting ones, the order, and any plugin you are missing. It plans; it does not design |
| `design-reviewer` | Screenshots a page at 320, 768, 1024 and 1440 px, measures horizontal overflow and console errors, checks the page without JavaScript, looks at the result, and returns a scored report with prioritised fixes. It never edits your project |
| `reference-analyst` | Studies a reference site you name, extracts its fonts, type scale, colours, radii and shadows, and returns a brief of design principles. It describes; it does not copy |

The reviewer and analyst need Playwright with Chromium. They check first, and they ask before installing anything.

## Things to know

**It collects other people's work.** Each author's licence and credit are kept: see [CREDITS.md](CREDITS.md). This hub is not affiliated with, or endorsed by, Anthropic, Google, Higgsfield or any other author listed.

**Already have an upstream plugin?** If you installed Impeccable, UI UX Pro Max, GSAP's skills or another one directly from its author, installing the same skill from here gives you two copies. Keep one.

**Some things are deliberately left out.**
- `design-core` includes Impeccable's skill but not its hooks or its four bundled agents, so the automatic checks after each edit are off. Install the full Impeccable plugin from its author if you want them.
- `rea` is only the skill. REA's own plugin also registers a large MCP server; this hub does not. Install REA's tools with its own setup command (`npx -y rea-agents setup`, see the skill's connection guide).
- `craft-anything` is only the skill. Download the app from the [Craft Anything releases](https://github.com/storytold/craft-anything).
- Impeccable's helper script downloads a native engine binary from the project's GitHub releases into `~/.impeccable` the first time it runs. It checks the SHA-256 against a manifest shipped inside the skill and refuses anything unverified.
- `threejs-game-director` includes a script that opens a login shell to read your shell profile and report whether three API-key variables are set. It prints `SET` or `MISSING`, never the value.
- Floorplan starts a local web server to show its map, and its Ask bar runs your own Claude or Codex CLI. Its own guide explains this.
- Impeccable, UI UX Pro Max and the others keep their own scripts and data. Read what you install.

**Use the analysis tools responsibly.** `rea`, `craft-anything`, `floorplan` and the `reference-analyst` agent are for software, sites and code you own or are authorised to examine. Matching another site's look too closely can cause legal and brand problems; learn the principles, do not copy assets or wording.

**Skills are instructions that run with your permissions.** Read a skill before installing it, as you would a script. Six plugins also bundle helper scripts that Claude may run when you use their skills: `design-core`, `floorplan`, `ai-site-brand`, `threejs`, `unslop` and `web-visuals`. This hub pins every upstream to an exact commit (see `sources.lock.json`), and updates arrive as pull requests that are read before merging.

## Troubleshooting

**Windows: "Filename too long" while adding the marketplace.** Windows limits paths to 260 characters, and a few Three.js example files are deeply nested (the longest path in this repository is 148 characters, before your client's own folder is added). Turn on Git's long-path support and try again:

```
git config --global core.longpaths true
```

If it still fails, enable Windows long paths (Group Policy "Enable Win32 long paths", or the registry value `LongPathsEnabled` set to 1), or install only the plugins you need after adding the marketplace from a shorter home folder.

## Repository layout

```
.claude-plugin/marketplace.json   marketplace for Claude Code
.agents/plugins/marketplace.json  marketplace for Codex
plugins/<name>/                   one folder per plugin
  .claude-plugin/plugin.json      Claude Code manifest
  .codex-plugin/plugin.json       Codex manifest
  skills/                         the skills
  agents/                         design-core only
  THIRD_PARTY/                    each author's licence and a provenance note
sources.json                      what is copied from where
sources.lock.json                 the exact upstream commits
scripts/                          sync, validate
CREDITS.md                        generated credits table
```

Maintaining the hub is covered in [MAINTAINING.md](MAINTAINING.md).

## Licence

The original work in this repository is MIT licensed, see [LICENSE](LICENSE). Everything copied from other authors keeps its own licence, see [CREDITS.md](CREDITS.md).
