---
name: open-motion
description: Set up and use OpenMotion, an open-source AI-native motion graphics runtime with an MCP server. Use when the user wants to animate, build motion graphics, export animation as HTML/CSS, React, JSON, MP4, GIF or WebM, or asks to install, start, connect or troubleshoot OpenMotion.
---

# OpenMotion: setup and use

OpenMotion is a separate open-source project (MIT, by Yuan-ManX, https://github.com/Yuan-ManX/open-motion). It is a Node app with a web canvas and an MCP server that agents can drive. This skill does not contain OpenMotion. It explains how to install, start and connect it, and how to work with it once connected.

## First: is it already connected?

Look at your tool list for tools from an MCP server named `openmotion`. If they are there, skip to "Working with it". If not, the server is not registered or not running. Do not guess tool names.

## Setup (ask before running anything)

Offer these steps and run them only when the user agrees. Never clone into the user's current project folder; ask where the tool should live.

Requirements: Node.js 22.5 or newer, git.

```bash
git clone https://github.com/Yuan-ManX/open-motion.git
cd open-motion
npm install
npm run dev
```

`npm run dev` starts two things: the API and MCP server on port 7000, and the web UI on port 4000 (open http://localhost:4000).

### Protect the server with an API key

With no key set, OpenMotion runs in dev mode and every request is accepted. Anything on the user's machine or local network that can reach the port can then drive it. Recommend a key:

1. Generate one: `node -e "console.log(require('crypto').randomBytes(24).toString('hex'))"`
2. Store it as the environment variable `OPENMOTION_API_KEY` before starting the server (a launcher script or the shell profile, never a file inside a git repository).
3. When set, clients must send it as an `X-API-Key` header or an `Authorization: Bearer <key>` header. `/api/health` stays open.

Never print the key into the chat, a commit or a log.

### Register the MCP server

The MCP endpoint is `http://localhost:7000/api/mcp`.

Claude Code:

```bash
claude mcp add --transport http openmotion http://localhost:7000/api/mcp -H "X-API-Key: <the key>"
```

Codex (reads the key from the environment variable, so it is not written to the config):

```bash
codex mcp add openmotion --url http://localhost:7000/api/mcp --bearer-token-env-var OPENMOTION_API_KEY
```

`claude mcp add -H` saves the header, key included, in Claude Code's own config file in plain text, so keep that file private and never paste the key into the chat. The Codex form reads the key from the environment and does not write it to its config.

Leave off the header or the variable if the server runs without a key. Restart the client afterwards so it loads the new server.

### Check it works

- `http://localhost:7000/api/health` should respond.
- `ECONNREFUSED` means the server is not running: start `npm run dev` again.
- A `401 unauthorized` means the key sent does not match `OPENMOTION_API_KEY`.
- The web UI only accepts requests from `localhost:4000` and `127.0.0.1:4000` by default.

## Working with it

Use the tool list the connected server actually advertises, not the project's README, because the server may be newer or older than this skill. In general:

- Describe the motion in plain language, build it step by step, and review the result in the web UI at http://localhost:4000.
- OpenMotion supports checkpoints, so prefer making a checkpoint before a large change and rolling back if it goes wrong.
- It can critique motion for accessibility, performance, aesthetics and consistency. Run the critique before export.
- Exports include HTML/CSS, React, JSON, MP4, GIF and WebM.
- Respect `prefers-reduced-motion` in anything shipped to a website, whichever export is used.

If the user only needs ordinary web animation inside their own code (scroll effects, timelines, React), the GSAP skills in the `motion` plugin are usually the simpler fit.

## Honest limits

OpenMotion is a young third-party project. Check its repository for current status before relying on it for client work. This plugin is not affiliated with it.
