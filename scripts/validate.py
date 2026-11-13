#!/usr/bin/env python3
"""Check that the hub is complete, consistent and free of obvious secrets.

    python -I scripts/validate.py

Exit code 1 if any error is found. Warnings do not fail the run.
"""
from __future__ import annotations

import json
import logging
import re
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import NamedTuple

LOG = logging.getLogger("design-hub")
ROOT = Path(__file__).resolve().parent.parent
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
ROUTING_SECTION = re.compile(r"## Routing table\r?\n(.*?)\r?\n## ", re.S)
BACKTICKED_NAME = re.compile(r"`([a-z][a-z0-9-]+)`")
FRONTMATTER = re.compile(r"\A﻿?---\r?\n(.*?)\r?\n---", re.S)
SKIP_DIRS = frozenset({".git", ".cache", "__pycache__", ".pytest_cache", "node_modules"})
SKILL_DOC_DIRS = frozenset({"THIRD_PARTY", "examples", "assets", "references", "templates"})
MAX_SCAN_BYTES = 2_000_000
ERROR_FILE_BYTES = 50_000_000
WARN_FILE_BYTES = 20_000_000
PLACEHOLDER_WORDS = ("example", "your", "xxx", "placeholder", "replace", "<", "changeme", "dummy", "fake")

SECRET_PATTERNS: dict[str, re.Pattern[str]] = {
    "GitHub token": re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}\b"),
    "GitHub fine-grained token": re.compile(r"\bgithub_pat_[A-Za-z0-9_]{50,}\b"),
    "Anthropic key": re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b"),
    "OpenAI-style key": re.compile(r"\bsk-[A-Za-z0-9_-]{32,}\b"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "Google API key": re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    "Slack token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    "Private key block": re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----"),
    "Hard-coded credential": re.compile(
        r"(?i)\b(?:api[_-]?key|secret|password|token)\b\s*[:=]\s*['\"][A-Za-z0-9_\-/+=]{20,}['\"]"
    ),
}


class Problem(NamedTuple):
    level: str  # "error" or "warning"
    message: str


def error(message: str) -> Problem:
    return Problem("error", message)


def warning(message: str) -> Problem:
    return Problem("warning", message)


def read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def parse_frontmatter(text: str) -> dict[str, str]:
    """Top-level `key: value` pairs of a SKILL.md header. Block scalars come back as '|' or '>'."""
    match = FRONTMATTER.match(text)
    if not match:
        return {}
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        key, separator, value = line.partition(":")
        if separator and not line.startswith((" ", "\t")) and re.fullmatch(r"[A-Za-z_-]+", key):
            fields[key] = value.strip().strip("\"'")
    return fields


def iter_files(root: Path) -> Iterator[Path]:
    for path in sorted(root.rglob("*")):
        if path.is_file() and not (SKIP_DIRS & set(path.relative_to(root).parts)):
            yield path


def skill_files(plugin_dir: Path) -> list[Path]:
    found = []
    for path in plugin_dir.rglob("SKILL.md"):
        if not (SKILL_DOC_DIRS & set(path.relative_to(plugin_dir).parts[:-1])):
            found.append(path)
    return sorted(found)


# --------------------------------------------------------------------------- checks


def check_config(config: dict) -> list[Problem]:
    names = [plugin["name"] for plugin in config["plugins"]]
    problems = [error(f"duplicate plugin name: {name}") for name in sorted({n for n in names if names.count(n) > 1})]
    for plugin in config["plugins"]:
        for key in ("description", "shortDescription", "category", "license", "keywords", "sources"):
            if not plugin.get(key):
                problems.append(error(f"{plugin['name']}: missing '{key}' in sources.json"))
        identifiers = [("plugin name", plugin["name"])] + [("source id", s["id"]) for s in plugin.get("sources", [])]
        problems.extend(
            error(f"{kind} {value!r} must use lowercase letters, digits and hyphens only")
            for kind, value in identifiers
            if not NAME_PATTERN.match(value)
        )
    return problems


def check_routing_table(root: Path, config: dict) -> list[Problem]:
    """Every skill or plugin the design director routes to must exist in the hub."""
    path = root / "plugins" / "design-core" / "skills" / "design-director" / "SKILL.md"
    if not path.is_file():
        return []  # check_authored reports the missing file
    match = ROUTING_SECTION.search(path.read_text(encoding="utf-8"))
    if not match:
        return [error("design-director SKILL.md has no '## Routing table' section")]
    skills = {p.parent.name for plugin in config["plugins"] for p in skill_files(root / "plugins" / plugin["name"])}
    known = skills | {plugin["name"] for plugin in config["plugins"]}
    unknown = sorted(set(BACKTICKED_NAME.findall(match.group(1))) - known)
    return [error(f"routing table names `{name}`, which is not a skill or plugin in the hub") for name in unknown]


def check_manifests(root: Path, config: dict, version: str) -> list[Problem]:
    problems: list[Problem] = []
    for plugin in config["plugins"]:
        name, plugin_dir = plugin["name"], root / "plugins" / plugin["name"]
        if not plugin_dir.is_dir():
            problems.append(error(f"{name}: plugin folder is missing"))
            continue
        for client in (".claude-plugin", ".codex-plugin"):
            manifest = read_json(plugin_dir / client / "plugin.json")
            if manifest is None:
                problems.append(error(f"{name}: {client}/plugin.json is missing or not valid JSON"))
            elif manifest.get("name") != name:
                problems.append(error(f"{name}: {client}/plugin.json has name {manifest.get('name')!r}"))
            elif not plugin.get("mirror") and manifest.get("version") != version:
                problems.append(error(f"{name}: {client} version {manifest.get('version')} != VERSION {version}"))
    return problems


def check_skills(root: Path, config: dict) -> list[Problem]:
    problems: list[Problem] = []
    seen: dict[str, str] = {}
    for plugin in config["plugins"]:
        for path in skill_files(root / "plugins" / plugin["name"]):
            fields = parse_frontmatter(path.read_text(encoding="utf-8", errors="replace"))
            label = f"{plugin['name']}/{path.parent.name}"
            if not fields.get("name") or not fields.get("description"):
                problems.append(error(f"{label}: SKILL.md needs 'name' and 'description' in its header"))
                continue
            if fields["name"] != path.parent.name:
                problems.append(warning(f"{label}: skill name {fields['name']!r} differs from its folder"))
            if fields["name"] in seen:
                other = seen[fields["name"]]
                problems.append(warning(f"skill name {fields['name']!r} appears in {other} and {plugin['name']}"))
            seen[fields["name"]] = plugin["name"]
    return problems


def check_licences(root: Path, config: dict) -> list[Problem]:
    problems: list[Problem] = []
    for plugin in config["plugins"]:
        plugin_dir = root / "plugins" / plugin["name"]
        if plugin.get("mirror"):
            if not any((plugin_dir / n).exists() for n in ("LICENSE", "LICENSE.md", "LICENSE.txt")):
                problems.append(error(f"{plugin['name']}: mirrored plugin has no LICENSE file"))
            continue
        for source in plugin["sources"]:
            target = plugin_dir / "THIRD_PARTY" / source["id"]
            if not (target / "SOURCE.md").is_file():
                problems.append(error(f"{plugin['name']}/{source['id']}: provenance note SOURCE.md is missing"))
            for name in source.get("licenseFiles", []):
                if not (target / Path(name).name).is_file():
                    problems.append(error(f"{plugin['name']}/{source['id']}: licence file {name} was not copied"))
            if not source.get("licenseFiles"):
                problems.append(error(f"{plugin['name']}/{source['id']}: no licenseFiles declared"))
    return problems


def check_marketplaces(root: Path, config: dict) -> list[Problem]:
    expected = sorted(plugin["name"] for plugin in config["plugins"])
    problems: list[Problem] = []
    claude = read_json(root / ".claude-plugin" / "marketplace.json") or {}
    codex = read_json(root / ".agents" / "plugins" / "marketplace.json") or {}
    claude_paths = {p["name"]: p.get("source") for p in claude.get("plugins", [])}
    codex_paths = {p["name"]: p.get("source", {}).get("path") for p in codex.get("plugins", [])}
    for label, listed in (("Claude Code", claude_paths), ("Codex", codex_paths)):
        if sorted(listed) != expected:
            problems.append(error(f"{label} marketplace lists {sorted(listed)}, expected {expected}"))
        for name, rel in listed.items():
            if not rel or not (root / rel).is_dir():
                problems.append(error(f"{label} marketplace: path for {name} does not exist: {rel}"))
    return problems


def check_lock(root: Path, config: dict) -> list[Problem]:
    lock = read_json(root / "sources.lock.json") or {}
    pinned = lock.get("sources", {})
    problems = []
    for plugin in config["plugins"]:
        for source in plugin["sources"]:
            commit = pinned.get(source["id"], {}).get("commit", "")
            if not SHA_PATTERN.match(commit):
                problems.append(error(f"{source['id']}: no full commit hash in sources.lock.json"))
    return problems


def check_authored(root: Path) -> list[Problem]:
    problems = []
    core = root / "plugins" / "design-core"
    for agent in ("design-director", "design-reviewer", "reference-analyst"):
        path = core / "agents" / f"{agent}.md"
        fields = parse_frontmatter(path.read_text(encoding="utf-8")) if path.is_file() else {}
        if fields.get("name") != agent or not fields.get("description"):
            problems.append(error(f"design-core agent {agent}: file or header is missing or wrong"))
    original_skills = (
        "plugins/design-core/skills/design-director/SKILL.md",
        "plugins/open-motion/skills/open-motion/SKILL.md",
    )
    for rel in original_skills:
        if not (root / rel).is_file():
            problems.append(error(f"original skill missing: {rel}"))
    return problems


def check_docs(root: Path, config: dict) -> list[Problem]:
    problems = []
    readme = (root / "README.md").read_text(encoding="utf-8") if (root / "README.md").is_file() else ""
    credits = (root / "CREDITS.md").read_text(encoding="utf-8") if (root / "CREDITS.md").is_file() else ""
    for plugin in config["plugins"]:
        if f"`{plugin['name']}`" not in readme:
            problems.append(error(f"README.md does not mention plugin {plugin['name']}"))
        for source in plugin["sources"]:
            if source["repo"] not in credits:
                problems.append(error(f"CREDITS.md does not credit {source['repo']}"))
    for name in ("LICENSE", "MAINTAINING.md"):
        if not (root / name).is_file():
            problems.append(error(f"{name} is missing"))
    return problems


def check_sizes(root: Path) -> list[Problem]:
    problems = []
    for path in iter_files(root):
        size = path.stat().st_size
        rel = path.relative_to(root).as_posix()
        if size > ERROR_FILE_BYTES:
            problems.append(error(f"{rel}: {size // 1_000_000} MB is too large for a normal GitHub push"))
        elif size > WARN_FILE_BYTES:
            problems.append(warning(f"{rel}: {size // 1_000_000} MB"))
    return problems


def is_placeholder(text: str) -> bool:
    lowered = text.lower()
    return any(word in lowered for word in PLACEHOLDER_WORDS)


def scan_text(text: str) -> list[tuple[int, str]]:
    """Return (line number, kind) for each possible secret. The secret itself is never returned."""
    hits = []
    for number, line in enumerate(text.splitlines(), start=1):
        for kind, pattern in SECRET_PATTERNS.items():
            match = pattern.search(line)
            if match and not (kind == "Hard-coded credential" and is_placeholder(match.group(0))):
                hits.append((number, kind))
    return hits


def check_secrets(root: Path) -> list[Problem]:
    problems: list[Problem] = []
    for path in iter_files(root):
        if path.stat().st_size > MAX_SCAN_BYTES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(root).as_posix()
        problems.extend(error(f"{rel}:{line}: possible {kind}") for line, kind in scan_text(text))
    return problems


# --------------------------------------------------------------------------- main


def run_all(root: Path) -> list[Problem]:
    config = read_json(root / "sources.json")
    if config is None:
        return [error("sources.json is missing or not valid JSON")]
    version = (root / "VERSION").read_text(encoding="utf-8").strip() if (root / "VERSION").is_file() else ""
    checks = (
        check_config(config),
        check_manifests(root, config, version),
        check_skills(root, config),
        check_licences(root, config),
        check_marketplaces(root, config),
        check_lock(root, config),
        check_authored(root),
        check_routing_table(root, config),
        check_docs(root, config),
        check_sizes(root),
        check_secrets(root),
    )
    return [problem for group in checks for problem in group]


def main() -> int:
    problems = run_all(ROOT)
    for problem in problems:
        (LOG.error if problem.level == "error" else LOG.warning)("%s: %s", problem.level, problem.message)
    errors = sum(1 for problem in problems if problem.level == "error")
    LOG.info("%d error(s), %d warning(s)", errors, len(problems) - errors)
    return 1 if errors else 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    sys.exit(main())
