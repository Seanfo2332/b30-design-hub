"""End-to-end sync against a throwaway local upstream. No network is used."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

CRLF_BYTES = b"line one\r\nline two\r\n"


def git(args: list[str], cwd: Path, stdin: str | None = None) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, input=stdin, capture_output=True, text=True, encoding="utf-8", check=True
    )
    return result.stdout.strip()


def commit_all(repo: Path, message: str) -> None:
    git(["add", "-A"], repo)
    git(["commit", "-q", "-m", message], repo)


def write(path: Path, content: bytes | str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))


@pytest.fixture
def upstream(tmp_path: Path) -> Path:
    repo = tmp_path / "upstream"
    repo.mkdir()
    git(["init", "-q", "-b", "main"], repo)
    for key, value in (
        ("user.email", "t@example.com"),
        ("user.name", "t"),
        ("core.autocrlf", "false"),
        ("uploadpack.allowFilter", "true"),
        ("uploadpack.allowAnySHA1InWant", "true"),
    ):
        git(["config", key, value], repo)
    write(repo / "LICENSE", "MIT License\n")
    write(repo / "skills" / "alpha" / "SKILL.md", "---\nname: alpha\ndescription: a\n---\n")
    write(repo / "skills" / "alpha" / "tests" / "keep.txt", "nested tests stay\n")
    write(repo / "skills" / "beta" / "SKILL.md", "---\nname: beta\ndescription: b\n---\n")
    write(repo / "docs" / "tool.md", CRLF_BYTES)
    write(repo / "tests" / "top.txt", "top-level tests\n")
    write(repo / ".github" / "ci.yml", "name: ci\n")
    commit_all(repo, "initial")
    return repo


@pytest.fixture
def hub(sync, monkeypatch, tmp_path: Path, upstream: Path) -> Path:
    root = tmp_path / "hub"
    (root / "plugins").mkdir(parents=True)
    cache = tmp_path / "cache"
    monkeypatch.setattr(sync, "ROOT", root)

    def local_clone(source: dict) -> Path:
        repo_dir = cache / source["id"]
        if not (repo_dir / ".git").exists():
            cache.mkdir(parents=True, exist_ok=True)
            clone = ["clone", "--quiet", "--depth", "1", "--filter=blob:none", "--no-checkout"]
            sync.run_git([*clone, upstream.as_uri(), str(repo_dir)])
        for key, value in sync.GIT_CONFIG:
            sync.run_git(["config", key, value], cwd=repo_dir)
        return repo_dir

    monkeypatch.setattr(sync, "ensure_clone", local_clone)
    return root


COPY_SOURCE = {
    "id": "up",
    "repo": "owner/up",
    "author": "Author",
    "license": "MIT",
    "licenseFiles": ["LICENSE"],
    "copy": [
        {"from": "skills", "to": "skills", "children": True},
        {"from": "docs/tool.md", "to": "extra/tool.md"},
    ],
}


def test_copy_is_byte_for_byte_and_records_provenance(sync, hub):
    entry = sync.sync_source({"name": "p"}, COPY_SOURCE, {"sources": {}}, update=False)
    plugin = hub / "plugins" / "p"
    assert (plugin / "extra" / "tool.md").read_bytes() == CRLF_BYTES
    assert (plugin / "skills" / "alpha" / "tests" / "keep.txt").is_file()
    assert (plugin / "THIRD_PARTY" / "up" / "LICENSE").read_text() == "MIT License\n"
    note = (plugin / "THIRD_PARTY" / "up" / "SOURCE.md").read_text()
    assert entry["commit"] in note
    assert entry["installed"] == ["skills/alpha", "skills/beta", "extra/tool.md"]
    assert len(entry["commit"]) == 40


def test_second_sync_reproduces_the_pinned_commit_even_if_upstream_moves(sync, hub, upstream):
    first = sync.sync_source({"name": "p"}, COPY_SOURCE, {"sources": {}}, update=False)
    write(upstream / "skills" / "alpha" / "SKILL.md", "---\nname: alpha\ndescription: changed\n---\n")
    commit_all(upstream, "change")
    again = sync.sync_source({"name": "p"}, COPY_SOURCE, {"sources": {"up": first}}, update=False)
    assert again["commit"] == first["commit"]
    assert "changed" not in (hub / "plugins" / "p" / "skills" / "alpha" / "SKILL.md").read_text()


def test_update_moves_the_pin_and_removes_files_dropped_upstream(sync, hub, upstream):
    first = sync.sync_source({"name": "p"}, COPY_SOURCE, {"sources": {}}, update=False)
    git(["rm", "-q", "-r", "skills/beta"], upstream)
    commit_all(upstream, "drop beta")
    moved = sync.sync_source({"name": "p"}, COPY_SOURCE, {"sources": {"up": first}}, update=True)
    plugin = hub / "plugins" / "p"
    assert moved["commit"] != first["commit"]
    assert (plugin / "skills" / "alpha").is_dir()
    assert not (plugin / "skills" / "beta").exists()


def test_mirror_skips_ci_and_top_level_tests_but_keeps_nested_tests(sync, hub):
    source = {"id": "up", "repo": "owner/up", "author": "A", "license": "MIT", "mirrorExclude": [".github", "tests"]}
    sync.sync_source({"name": "mirrored"}, source, {"sources": {}}, update=False)
    plugin = hub / "plugins" / "mirrored"
    assert (plugin / "LICENSE").is_file()
    assert not (plugin / ".github").exists()
    assert not (plugin / "tests").exists()
    assert not (plugin / ".git").exists()
    assert (plugin / "skills" / "alpha" / "tests" / "keep.txt").is_file()


def add_script(upstream: Path) -> None:
    write(upstream / "skills" / "alpha" / "run.sh", "#!/bin/sh\necho hi\n")
    write(upstream / "skills" / "alpha" / "plain.txt", "not executable\n")
    git(["add", "-A"], upstream)
    git(["update-index", "--chmod=+x", "skills/alpha/run.sh"], upstream)
    git(["commit", "-q", "-m", "add script"], upstream)


def assert_executable(hub: Path, plugin: str, rel: str) -> None:
    """Windows keeps the bit in git's index; elsewhere it is a real permission bit."""
    path = hub / "plugins" / plugin / rel
    if os.name == "nt":
        staged = git(["ls-files", "-s", "--", f"plugins/{plugin}/{rel}"], hub)
        assert staged.startswith("100755"), staged
    else:
        assert path.stat().st_mode & 0o111


def test_the_executable_bit_survives_a_copy(sync, hub, upstream):
    add_script(upstream)
    git(["init", "-q"], hub)
    sync.sync_source({"name": "p"}, COPY_SOURCE, {"sources": {}}, update=False)
    assert_executable(hub, "p", "skills/alpha/run.sh")
    if os.name == "nt":
        assert "plain.txt" not in git(["ls-files", "-s"], hub)
    else:
        assert not (hub / "plugins" / "p" / "skills" / "alpha" / "plain.txt").stat().st_mode & 0o111


def test_the_executable_bit_survives_a_mirror(sync, hub, upstream):
    add_script(upstream)
    git(["init", "-q"], hub)
    source = {"id": "up", "repo": "owner/up", "author": "A", "license": "MIT", "mirrorExclude": [".github", "tests"]}
    sync.sync_source({"name": "mirrored"}, source, {"sources": {}}, update=False)
    assert_executable(hub, "mirrored", "skills/alpha/run.sh")


def test_a_hub_that_is_not_a_git_repo_still_syncs_on_windows(sync, hub, upstream):
    add_script(upstream)
    sync.sync_source({"name": "p"}, COPY_SOURCE, {"sources": {}}, update=False)
    assert (hub / "plugins" / "p" / "skills" / "alpha" / "run.sh").is_file()


def test_a_symlink_in_a_copied_path_is_refused(sync, hub, upstream):
    target = git(["hash-object", "-w", "--stdin"], upstream, stdin="skills/alpha")
    git(["update-index", "--add", "--cacheinfo", f"120000,{target},skills/link"], upstream)
    git(["commit", "-q", "-m", "add symlink"], upstream)
    with pytest.raises(RuntimeError, match="symlink"):
        sync.sync_source({"name": "p"}, COPY_SOURCE, {"sources": {}}, update=False)


def test_a_pinned_commit_that_vanished_upstream_gets_a_clear_message(sync, hub):
    lock = {"sources": {"up": {"commit": "f" * 40, "installed": []}}}
    with pytest.raises(RuntimeError, match="Run with --update"):
        sync.sync_source({"name": "p"}, COPY_SOURCE, lock, update=False)


def test_a_missing_upstream_path_is_reported(sync, hub):
    source = {**COPY_SOURCE, "copy": [{"from": "skills/nope", "to": "skills/nope"}]}
    with pytest.raises(FileNotFoundError, match="skills/nope"):
        sync.sync_source({"name": "p"}, source, {"sources": {}}, update=False)


def hub_config(*plugin_names: str) -> dict:
    return {
        "hub": {
            "name": "design-hub",
            "displayName": "Design Hub",
            "repo": "owner/design-hub",
            "description": "A hub.",
            "author": {"name": "owner"},
        },
        "plugins": [
            {
                "name": name,
                "category": "Design",
                "license": "MIT",
                "keywords": ["x"],
                "description": f"Plugin {name}.",
                "shortDescription": name,
                "sources": [{**COPY_SOURCE, "id": f"up-{name}"}],
            }
            for name in plugin_names
        ],
    }


@pytest.fixture
def hub_files(sync, hub, monkeypatch) -> Path:
    monkeypatch.setattr(sync, "SOURCES_FILE", hub / "sources.json")
    monkeypatch.setattr(sync, "LOCK_FILE", hub / "sources.lock.json")
    monkeypatch.setattr(sync, "VERSION_FILE", hub / "VERSION")
    (hub / "VERSION").write_text("0.1.0\n", encoding="utf-8")
    sync.write_json(hub / "sources.json", hub_config("p", "q"))
    return hub


def test_main_generate_only_needs_no_network_or_lock(sync, hub_files):
    sync.write_json(hub_files / "sources.lock.json", {"sources": {}})
    assert sync.main(["--generate-only"]) == 0
    assert (hub_files / ".claude-plugin" / "marketplace.json").is_file()
    assert not (hub_files / "plugins" / "p" / "skills").exists()


def test_first_sync_writes_the_lock_without_bumping_the_version(sync, hub_files):
    assert sync.main([]) == 0
    lock = sync.read_json(hub_files / "sources.lock.json")
    assert sorted(lock["sources"]) == ["up-p", "up-q"]
    assert (hub_files / "VERSION").read_text().strip() == "0.1.0"


def test_update_bumps_the_version_only_when_a_pin_moves(sync, hub_files, upstream):
    sync.main([])
    assert sync.main(["--update"]) == 0
    assert (hub_files / "VERSION").read_text().strip() == "0.1.0"
    write(upstream / "skills" / "alpha" / "SKILL.md", "---\nname: alpha\ndescription: new\n---\n")
    commit_all(upstream, "change")
    assert sync.main(["--update"]) == 0
    assert (hub_files / "VERSION").read_text().strip() == "0.1.1"
    manifest = sync.read_json(hub_files / "plugins" / "p" / ".claude-plugin" / "plugin.json")
    assert manifest["version"] == "0.1.1"


def test_only_limits_the_sync_to_the_named_plugin(sync, hub_files):
    assert sync.main(["--only", "p"]) == 0
    assert (hub_files / "plugins" / "p" / "skills" / "alpha").is_dir()
    assert not (hub_files / "plugins" / "q" / "skills").exists()


def test_write_generated_produces_manifests_marketplaces_and_credits(sync, hub):
    config = {
        "hub": {
            "name": "design-hub",
            "displayName": "Design Hub",
            "repo": "owner/design-hub",
            "description": "A hub.",
            "author": {"name": "owner"},
        },
        "plugins": [
            {
                "name": "p",
                "category": "Design",
                "license": "MIT",
                "keywords": ["x"],
                "description": "Plugin p.",
                "shortDescription": "P",
                "sources": [COPY_SOURCE],
            }
        ],
    }
    sync.write_generated(config, {"sources": {}}, "0.1.0")
    assert (hub / "plugins" / "p" / ".claude-plugin" / "plugin.json").is_file()
    assert (hub / "plugins" / "p" / ".codex-plugin" / "plugin.json").is_file()
    assert (hub / ".claude-plugin" / "marketplace.json").is_file()
    assert (hub / ".agents" / "plugins" / "marketplace.json").is_file()
    assert "owner/up" in (hub / "CREDITS.md").read_text()
