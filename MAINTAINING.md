# Maintaining the hub

## How it works

- `sources.json` declares each plugin and exactly which files are copied from which upstream repository.
- `sources.lock.json` pins every upstream to a full commit hash.
- `scripts/sync.py` fetches the pinned commits, copies the files byte for byte, writes each author's licence next to their work, and regenerates the manifests, both marketplace files and `CREDITS.md`.
- `scripts/validate.py` checks the result. CI runs it, and the tests, on every pull request.

Anything under `plugins/` that is copied from upstream is overwritten by the next sync. Original work lives in a few fixed places and is never touched by it:

- `plugins/design-core/agents/` and `plugins/design-core/skills/design-director/`
- `plugins/open-motion/skills/open-motion/`

## Commands

Use isolated mode, so nothing in a downloaded folder can shadow a Python module.

```bash
python -I scripts/sync.py                  # reproduce the pinned commits
python -I scripts/sync.py --update         # move every pin to the upstream's latest commit
python -I scripts/sync.py --only floorplan --update
python -I scripts/sync.py --generate-only  # rebuild manifests and credits without the network
python -I scripts/validate.py              # check everything
python -m pytest                           # run the tests (they run only this repo's own code)
```

Upstreams are cached in `.cache/upstream` (ignored by git). Set `DESIGN_HUB_CACHE` to a short path if Windows path-length limits cause trouble.

## Weekly updates

`.github/workflows/sync.yml` runs `sync.py --update` every week and opens a pull request if any upstream moved. **It never merges.** A skill is a set of instructions that runs with the user's permissions, so a compromised upstream would otherwise reach everyone who installs the hub.

Before merging an update pull request:

1. Read the diff for each plugin that changed. Look especially at new or changed scripts, anything that downloads or runs code, and changes to `SKILL.md` instructions.
2. Check the licence files did not change terms.
3. Confirm CI passed.

A sync that moves any pin raises the patch number in `VERSION`. That number goes into every generated manifest, and Claude Code only picks up a plugin update when its version changes.

## Adding a plugin or a source

1. Add the entry to `sources.json`. Use `copy` for chosen paths, or `mirrorExclude` to mirror a whole upstream plugin that already ships its own Claude Code and Codex manifests.
2. Run `python -I scripts/sync.py`, then `python -I scripts/validate.py`.
3. Add the plugin to the tables in `README.md`.

Only add work that has an open-source licence, and keep its licence file.

## Before the repository is made public

Run `python -I scripts/validate.py` (it includes a secret scan) and read `git status` for anything you do not recognise.
