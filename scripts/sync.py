#!/usr/bin/env python3
"""Sync upstream sources into plugins/ and regenerate manifests, marketplaces and CREDITS.md.

Run with isolated mode so nothing in a downloaded folder can shadow a module:

    python -I scripts/sync.py                 # reproduce the commits pinned in sources.lock.json
    python -I scripts/sync.py --update        # move every pin to the upstream's current HEAD
    python -I scripts/sync.py --only floorplan --update
    python -I scripts/sync.py --generate-only # rebuild manifests and credits, no network

Copied files are never edited. Each upstream is cloned into a cache folder outside the
published tree and read from a plain checkout with line-ending conversion switched off,
so the bytes in plugins/ are the bytes upstream published.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path, PurePosixPath

LOG = logging.getLogger("design-hub")
ROOT = Path(__file__).resolve().parent.parent
SOURCES_FILE = ROOT / "sources.json"
LOCK_FILE = ROOT / "sources.lock.json"
VERSION_FILE = ROOT / "VERSION"
CACHE_ENV = "DESIGN_HUB_CACHE"
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
GIT_CONFIG = (("core.autocrlf", "false"), ("core.symlinks", "false"), ("core.longpaths", "true"))
SPECIAL_MODES = ("120000", "160000")  # symlink, submodule


# --------------------------------------------------------------------------- helpers


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, data: object) -> None:
    write_text(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def run_git(args: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", check=False
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def safe_relative(path_text: str) -> PurePosixPath:
    """Reject absolute paths and parent traversal in any path taken from sources.json."""
    path = PurePosixPath(path_text)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError(f"unsafe path in sources.json: {path_text!r}")
    return path


def checked_name(kind: str, value: str) -> str:
    """Plugin names and source ids become folder names, so keep them to plain slugs."""
    if not NAME_PATTERN.match(value):
        raise ValueError(f"{kind} {value!r} must use lowercase letters, digits and hyphens only")
    return value


def fs_path(path: Path) -> str:
    """Extended-length form so deep upstream trees copy on Windows (MAX_PATH is 260)."""
    resolved = str(path.resolve())
    if os.name == "nt" and not resolved.startswith("\\\\?\\"):
        return "\\\\?\\" + resolved
    return resolved


def cache_root() -> Path:
    override = os.environ.get(CACHE_ENV)
    return Path(override) if override else ROOT / ".cache" / "upstream"


def read_version() -> str:
    return VERSION_FILE.read_text(encoding="utf-8").strip()


def bump_patch(version: str) -> str:
    major, minor, patch = (int(part) for part in version.split("."))
    return f"{major}.{minor}.{patch + 1}"


# --------------------------------------------------------------------------- fetching


def ensure_clone(source: dict) -> Path:
    repo_dir = cache_root() / source["id"]
    if not (repo_dir / ".git").exists():
        repo_dir.parent.mkdir(parents=True, exist_ok=True)
        url = f"https://github.com/{source['repo']}.git"
        run_git(["clone", "--quiet", "--depth", "1", "--filter=blob:none", "--no-checkout", url, str(repo_dir)])
    for key, value in GIT_CONFIG:
        run_git(["config", key, value], cwd=repo_dir)
    return repo_dir


def choose_commit(source: dict, lock: dict, update: bool, repo_dir: Path) -> str:
    pinned = lock.get("sources", {}).get(source["id"], {}).get("commit")
    use_pin = bool(pinned) and not update
    commit = pinned if use_pin else run_git(["ls-remote", "origin", "HEAD"], cwd=repo_dir).split()[0]
    if not SHA_PATTERN.match(commit):
        raise RuntimeError(f"{source['id']}: not a full commit hash: {commit!r}")
    return commit


def wanted_paths(source: dict) -> list[str] | None:
    """Sparse-checkout patterns, or None to take the whole tree (mirrors)."""
    if source.get("mirrorExclude") is not None:
        return None
    paths = [entry["from"] for entry in source.get("copy", [])] + list(source.get("licenseFiles", []))
    return [f"/{safe_relative(p)}" for p in paths]


def checkout(repo_dir: Path, commit: str, patterns: list[str] | None) -> None:
    try:
        run_git(["fetch", "--quiet", "--depth", "1", "--filter=blob:none", "origin", commit], cwd=repo_dir)
    except RuntimeError as error:
        raise RuntimeError(
            f"cannot fetch pinned commit {commit}; it may have been removed upstream. "
            f"Run with --update to move the pin. ({error})"
        ) from error
    if patterns is None:
        run_git(["sparse-checkout", "disable"], cwd=repo_dir)
    else:
        run_git(["sparse-checkout", "set", "--no-cone", *patterns], cwd=repo_dir)
    run_git(["checkout", "--quiet", "--force", commit], cwd=repo_dir)


def assert_plain_files(repo_dir: Path, commit: str, patterns: list[str] | None) -> None:
    """Fail loudly on symlinks or submodules, which would not copy faithfully."""
    scope = [] if patterns is None else ["--", *(p.lstrip("/") for p in patterns)]
    listing = run_git(["ls-tree", "-r", commit, *scope], cwd=repo_dir)
    bad = [line.split("\t", 1)[-1] for line in listing.splitlines() if line.split(" ", 1)[0] in SPECIAL_MODES]
    if bad:
        raise RuntimeError(f"symlink or submodule in a copied path: {', '.join(bad[:5])}")


# --------------------------------------------------------------------------- copying


def top_level_ignore(root: Path, exclude: frozenset[str]) -> Callable[[str, list[str]], set[str]]:
    def ignore(directory: str, names: list[str]) -> set[str]:
        rel = Path(directory).relative_to(root).as_posix()
        prefix = "" if rel == "." else f"{rel}/"
        return {name for name in names if name == ".git" or f"{prefix}{name}" in exclude}

    return ignore


def remove_path(path: Path) -> None:
    target = fs_path(path)
    if os.path.isdir(target):
        shutil.rmtree(target)
    elif os.path.exists(target):
        os.unlink(target)


def copy_path(src: Path, dst: Path) -> None:
    remove_path(dst)
    if src.is_dir():
        shutil.copytree(fs_path(src), fs_path(dst), ignore=shutil.ignore_patterns(".git"))
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(fs_path(src), fs_path(dst))


def copy_entry(repo_dir: Path, plugin_dir: Path, entry: dict) -> list[str]:
    """Copy one 'copy' entry. Returns the destinations written, relative to the plugin."""
    src = repo_dir / safe_relative(entry["from"])
    if not src.exists():
        raise FileNotFoundError(f"missing in upstream: {entry['from']}")
    dst_rel = safe_relative(entry["to"])
    if not entry.get("children"):
        copy_path(src, plugin_dir / dst_rel)
        return [dst_rel.as_posix()]
    written = []
    for child in sorted(p for p in src.iterdir() if p.is_dir() and p.name != ".git"):
        copy_path(child, plugin_dir / dst_rel / child.name)
        written.append((dst_rel / child.name).as_posix())
    return written


def mirror_tree(repo_dir: Path, plugin_dir: Path, exclude: list[str]) -> None:
    remove_path(plugin_dir)
    ignore = top_level_ignore(Path(fs_path(repo_dir)), frozenset(exclude))
    shutil.copytree(fs_path(repo_dir), fs_path(plugin_dir), ignore=ignore)


def source_note(source: dict, commit: str, written: list[str]) -> str:
    lines = [
        f"# {source['id']}",
        "",
        f"- Source: https://github.com/{source['repo']}",
        f"- Author: {source['author']}",
        f"- Licence: {source['license']}",
        f"- Pinned commit: {commit}",
    ]
    if written:
        lines.append("- Copied into this plugin: " + ", ".join(f"`{path}`" for path in written))
    if source.get("notes"):
        lines.append(f"- Notes: {source['notes']}")
    footer = (
        "Files are copied byte for byte from the pinned commit. Nothing in them was edited."
        if written
        else "No upstream files are copied by this plugin."
    )
    return "\n".join(lines) + f"\n\n{footer}\n"


def write_third_party(repo_dir: Path, plugin_dir: Path, source: dict, commit: str, written: list[str]) -> None:
    target = plugin_dir / "THIRD_PARTY" / source["id"]
    remove_path(target)
    for name in source.get("licenseFiles", []):
        src = repo_dir / safe_relative(name)
        target.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, target / PurePosixPath(name).name)
    write_text(target / "SOURCE.md", source_note(source, commit, written))


def sync_source(plugin: dict, source: dict, lock: dict, update: bool) -> dict:
    """Fetch and copy one source. Returns its new lock entry."""
    checked_name("source id", source["id"])
    plugin_dir = ROOT / "plugins" / checked_name("plugin name", plugin["name"])
    previous = lock.get("sources", {}).get(source["id"], {})
    for old in previous.get("installed", []):
        remove_path(plugin_dir / safe_relative(old))
    repo_dir = ensure_clone(source)
    commit = choose_commit(source, lock, update, repo_dir)
    patterns = wanted_paths(source)
    checkout(repo_dir, commit, patterns)
    assert_plain_files(repo_dir, commit, patterns)
    if patterns is None:
        mirror_tree(repo_dir, plugin_dir, source["mirrorExclude"])
        written: list[str] = []
    else:
        written = [path for entry in source["copy"] for path in copy_entry(repo_dir, plugin_dir, entry)]
        write_third_party(repo_dir, plugin_dir, source, commit, written)
    date = run_git(["show", "-s", "--format=%cs", commit], cwd=repo_dir).strip()
    return {"repo": source["repo"], "commit": commit, "commitDate": date, "installed": written}


# --------------------------------------------------------------------------- generated files


def display_name(plugin: dict) -> str:
    return plugin.get("displayName") or plugin["name"].replace("-", " ").title()


def build_claude_manifest(hub: dict, plugin: dict, version: str) -> dict:
    repo_url = f"https://github.com/{hub['repo']}"
    return {
        "name": plugin["name"],
        "version": version,
        "description": plugin["description"],
        "author": hub["author"],
        "homepage": repo_url,
        "repository": repo_url,
        "license": plugin["license"],
        "keywords": plugin["keywords"],
    }


def build_codex_manifest(hub: dict, plugin: dict, version: str) -> dict:
    return {
        **build_claude_manifest(hub, plugin, version),
        "skills": "./skills/",
        "interface": {
            "displayName": display_name(plugin),
            "shortDescription": plugin["shortDescription"],
            "longDescription": plugin["description"],
            "developerName": hub["author"]["name"],
            "category": plugin["category"],
            "capabilities": ["Read"],
        },
    }


def build_claude_marketplace(hub: dict, plugins: list[dict]) -> dict:
    return {
        "name": hub["name"],
        "owner": hub["author"],
        "metadata": {"description": hub["description"]},
        "plugins": [
            {
                "name": plugin["name"],
                "source": f"./plugins/{plugin['name']}",
                "description": plugin["description"],
                "category": plugin["category"],
                "keywords": plugin["keywords"],
                "license": plugin["license"],
            }
            for plugin in plugins
        ],
    }


def build_codex_marketplace(hub: dict, plugins: list[dict]) -> dict:
    return {
        "name": hub["name"],
        "interface": {"displayName": hub["displayName"]},
        "plugins": [
            {
                "name": plugin["name"],
                "source": {"source": "local", "path": f"./plugins/{plugin['name']}"},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                "category": plugin["category"],
            }
            for plugin in plugins
        ],
    }


def credits_rows(plugins: list[dict], lock: dict) -> list[str]:
    rows = []
    for plugin in plugins:
        for source in plugin["sources"]:
            entry = lock.get("sources", {}).get(source["id"], {})
            commit = entry.get("commit", "")
            short = f"[`{commit[:7]}`](https://github.com/{source['repo']}/commit/{commit})" if commit else "n/a"
            rows.append(
                f"| {plugin['name']} | [{source['id']}](https://github.com/{source['repo']}) "
                f"| {source['author']} | {source['license']} | {short} |"
            )
    return rows


def credits_notes(plugins: list[dict]) -> list[str]:
    return [
        f"- **{source['id']}**: {source['notes']}"
        for plugin in plugins
        for source in plugin["sources"]
        if source.get("notes")
    ]


def build_credits(plugins: list[dict], lock: dict) -> str:
    header = [
        "# Credits and licences",
        "",
        "Design Hub collects work by other people. Every component below keeps its author's licence,",
        "which is stored next to it under `plugins/<plugin>/THIRD_PARTY/` (or at the plugin root for",
        "whole-plugin mirrors). The hub's own original work is MIT licensed; see `LICENSE`.",
        "",
        "| Plugin | Component | Author | Licence | Pinned commit |",
        "|---|---|---|---|---|",
    ]
    notes = ["", "## Notes", "", *credits_notes(plugins), ""]
    return "\n".join([*header, *credits_rows(plugins, lock), *notes])


def write_generated(config: dict, lock: dict, version: str) -> None:
    hub, plugins = config["hub"], config["plugins"]
    for plugin in plugins:
        if plugin.get("mirror"):
            continue
        plugin_dir = ROOT / "plugins" / plugin["name"]
        write_json(plugin_dir / ".claude-plugin" / "plugin.json", build_claude_manifest(hub, plugin, version))
        write_json(plugin_dir / ".codex-plugin" / "plugin.json", build_codex_manifest(hub, plugin, version))
    write_json(ROOT / ".claude-plugin" / "marketplace.json", build_claude_marketplace(hub, plugins))
    write_json(ROOT / ".agents" / "plugins" / "marketplace.json", build_codex_marketplace(hub, plugins))
    write_text(ROOT / "CREDITS.md", build_credits(plugins, lock))


# --------------------------------------------------------------------------- orchestration


def changed_pins(old: dict, new: dict) -> list[str]:
    old_sources, new_sources = old.get("sources", {}), new.get("sources", {})
    return sorted(
        key for key, entry in new_sources.items() if old_sources.get(key, {}).get("commit") != entry["commit"]
    )


def sync_all(config: dict, lock: dict, only: set[str], update: bool) -> dict:
    new_sources = dict(lock.get("sources", {}))
    for plugin in config["plugins"]:
        if only and plugin["name"] not in only:
            continue
        for source in plugin["sources"]:
            LOG.info("sync %s/%s ...", plugin["name"], source["id"])
            new_sources[source["id"]] = sync_source(plugin, source, lock, update)
    return {"sources": new_sources}


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--update", action="store_true", help="move pins to each upstream's current HEAD")
    parser.add_argument("--only", action="append", default=[], metavar="PLUGIN", help="sync only this plugin")
    parser.add_argument("--generate-only", action="store_true", help="rebuild generated files without fetching")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config = read_json(SOURCES_FILE)
    lock = read_json(LOCK_FILE) if LOCK_FILE.exists() else {"sources": {}}
    version = read_version()
    if not args.generate_only:
        new_lock = sync_all(config, lock, set(args.only), args.update)
        moved = changed_pins(lock, new_lock)
        if moved and args.update and LOCK_FILE.exists():
            version = bump_patch(version)
            write_text(VERSION_FILE, version + "\n")
            LOG.info("pins moved: %s -> version %s", ", ".join(moved), version)
        write_json(LOCK_FILE, new_lock)
        lock = new_lock
    write_generated(config, lock, version)
    LOG.info("done")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        sys.exit(main())
    except (RuntimeError, FileNotFoundError, ValueError) as error:
        LOG.error("error: %s", error)
        sys.exit(1)
