from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
pytestmark = pytest.mark.unit


def fake(*parts: str) -> str:
    """Build a secret-shaped string at runtime so this file never contains one."""
    return "".join(parts)


def put(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def put_json(path: Path, data: dict) -> None:
    put(path, json.dumps(data))


# --------------------------------------------------------------------------- frontmatter


def test_frontmatter_reads_plain_and_quoted_values(validate):
    text = "---\nname: alpha\ndescription: \"Does a thing\"\n---\nbody"
    assert validate.parse_frontmatter(text) == {"name": "alpha", "description": "Does a thing"}


def test_frontmatter_accepts_block_scalar_descriptions(validate):
    fields = validate.parse_frontmatter("---\nname: a\ndescription: |\n  long text\n  more\n---\n")
    assert fields["description"] == "|"


def test_frontmatter_ignores_nested_keys_and_a_byte_order_mark(validate):
    fields = validate.parse_frontmatter("﻿---\nname: a\nmetadata:\n  version: 2\n---\n")
    assert fields["name"] == "a"
    assert "version" not in fields


def test_frontmatter_missing_returns_empty(validate):
    assert validate.parse_frontmatter("# just a heading") == {}


# --------------------------------------------------------------------------- secrets


@pytest.mark.parametrize(
    ("kind", "secret"),
    [
        ("GitHub token", fake("gh", "p_", "a" * 36)),
        ("GitHub fine-grained token", fake("github", "_pat_", "B" * 60)),
        ("Anthropic key", fake("sk", "-ant-", "c" * 30)),
        ("OpenAI-style key", fake("sk", "-", "d" * 40)),
        ("AWS access key", fake("AKI", "A", "E" * 16)),
        ("Google API key", fake("AI", "za", "f" * 35)),
        ("Slack token", fake("xo", "xb-", "1" * 20)),
        ("Private key block", fake("-----BEGIN ", "RSA PRIVATE KEY", "-----")),
        ("Hard-coded credential", fake("api_key", " = '", "g" * 24, "'")),
    ],
)
def test_scan_finds_each_secret_kind(validate, kind, secret):
    hits = validate.scan_text(f"first line\nvalue {secret}\n")
    assert (2, kind) in hits


def test_scan_never_returns_the_secret_text(validate):
    secret = fake("gh", "p_", "z" * 36)
    assert all(secret not in str(hit) for hit in validate.scan_text(secret))


def test_scan_ignores_obvious_placeholders(validate):
    assert validate.scan_text("api_key = 'your_api_key_goes_here_please'") == []
    assert validate.scan_text("password: 'changeme-changeme-changeme'") == []


def test_scan_ignores_ordinary_prose(validate):
    assert validate.scan_text("Set the token in your environment before running.") == []


def test_secret_check_reports_the_file_and_line(validate, tmp_path):
    put(tmp_path / "docs" / "note.md", "ok\n" + fake("gh", "p_", "q" * 36) + "\n")
    problems = validate.check_secrets(tmp_path)
    assert [p.message for p in problems] == ["docs/note.md:2: possible GitHub token"]


def test_secret_check_skips_binary_files(validate, tmp_path):
    (tmp_path / "image.bin").write_bytes(b"\xff\xfe\x00\x01" * 100)
    assert validate.check_secrets(tmp_path) == []


# --------------------------------------------------------------------------- structure


def make_plugin(root: Path, name: str, version: str = "1.0.0") -> None:
    for client in (".claude-plugin", ".codex-plugin"):
        put_json(root / "plugins" / name / client / "plugin.json", {"name": name, "version": version})


CONFIG = {"plugins": [{"name": "alpha", "sources": [{"id": "up", "repo": "o/up", "licenseFiles": ["LICENSE"]}]}]}


def test_manifest_check_passes_for_a_consistent_plugin(validate, tmp_path):
    make_plugin(tmp_path, "alpha")
    assert validate.check_manifests(tmp_path, CONFIG, "1.0.0") == []


def test_manifest_check_flags_a_wrong_version_name_or_missing_file(validate, tmp_path):
    make_plugin(tmp_path, "alpha", version="9.9.9")
    put_json(tmp_path / "plugins" / "alpha" / ".codex-plugin" / "plugin.json", {"name": "wrong", "version": "1.0.0"})
    messages = [p.message for p in validate.check_manifests(tmp_path, CONFIG, "1.0.0")]
    assert any("version 9.9.9" in m for m in messages)
    assert any("name 'wrong'" in m for m in messages)
    (tmp_path / "plugins" / "alpha" / ".claude-plugin" / "plugin.json").unlink()
    assert any("missing" in p.message for p in validate.check_manifests(tmp_path, CONFIG, "1.0.0"))


def test_mirrored_plugins_keep_their_own_version(validate, tmp_path):
    make_plugin(tmp_path, "alpha", version="0.7.3")
    config = {"plugins": [{"name": "alpha", "mirror": True, "sources": []}]}
    assert validate.check_manifests(tmp_path, config, "1.0.0") == []


def test_skill_check_requires_name_and_description(validate, tmp_path):
    put(tmp_path / "plugins" / "alpha" / "skills" / "good" / "SKILL.md", "---\nname: good\ndescription: ok\n---\n")
    put(tmp_path / "plugins" / "alpha" / "skills" / "bad" / "SKILL.md", "---\nname: bad\n---\n")
    messages = [p.message for p in validate.check_skills(tmp_path, CONFIG)]
    assert messages == ["alpha/bad: SKILL.md needs 'name' and 'description' in its header"]


def test_skill_check_ignores_example_and_third_party_skill_files(validate, tmp_path):
    put(tmp_path / "plugins" / "alpha" / "skills" / "s" / "examples" / "demo" / "SKILL.md", "no header")
    put(tmp_path / "plugins" / "alpha" / "THIRD_PARTY" / "up" / "SKILL.md", "no header")
    assert validate.check_skills(tmp_path, CONFIG) == []


def test_skill_check_warns_on_duplicate_names_across_plugins(validate, tmp_path):
    config = {"plugins": [{"name": "alpha", "sources": []}, {"name": "beta", "sources": []}]}
    for plugin in ("alpha", "beta"):
        put(tmp_path / "plugins" / plugin / "skills" / "same" / "SKILL.md", "---\nname: same\ndescription: d\n---\n")
    problems = validate.check_skills(tmp_path, config)
    assert [p.level for p in problems] == ["warning"]


def test_licence_check_requires_the_copied_licence_and_provenance_note(validate, tmp_path):
    assert len(validate.check_licences(tmp_path, CONFIG)) == 2
    put(tmp_path / "plugins" / "alpha" / "THIRD_PARTY" / "up" / "SOURCE.md", "note")
    put(tmp_path / "plugins" / "alpha" / "THIRD_PARTY" / "up" / "LICENSE", "MIT")
    assert validate.check_licences(tmp_path, CONFIG) == []


def test_mirrored_plugins_need_a_licence_at_their_root(validate, tmp_path):
    config = {"plugins": [{"name": "alpha", "mirror": True, "sources": []}]}
    (tmp_path / "plugins" / "alpha").mkdir(parents=True)
    assert len(validate.check_licences(tmp_path, config)) == 1
    put(tmp_path / "plugins" / "alpha" / "LICENSE", "Apache")
    assert validate.check_licences(tmp_path, config) == []


def test_marketplace_check_flags_missing_and_wrong_entries(validate, tmp_path):
    (tmp_path / "plugins" / "alpha").mkdir(parents=True)
    claude_listing = {"plugins": [{"name": "alpha", "source": "./plugins/alpha"}]}
    put_json(tmp_path / ".claude-plugin" / "marketplace.json", claude_listing)
    put_json(tmp_path / ".agents" / "plugins" / "marketplace.json", {"plugins": []})
    messages = [p.message for p in validate.check_marketplaces(tmp_path, CONFIG)]
    assert len(messages) == 1
    assert messages[0].startswith("Codex marketplace lists")


def test_lock_check_needs_a_full_commit_hash(validate, tmp_path):
    put_json(tmp_path / "sources.lock.json", {"sources": {"up": {"commit": "abc123"}}})
    assert len(validate.check_lock(tmp_path, CONFIG)) == 1
    put_json(tmp_path / "sources.lock.json", {"sources": {"up": {"commit": "a" * 40}}})
    assert validate.check_lock(tmp_path, CONFIG) == []


def test_config_check_flags_duplicate_names_and_missing_fields(validate):
    config = {"plugins": [{"name": "a", "sources": []}, {"name": "a", "sources": []}]}
    messages = [p.message for p in validate.check_config(config)]
    assert "duplicate plugin name: a" in messages
    assert any("missing 'description'" in m for m in messages)


def test_config_check_flags_names_that_are_not_plain_slugs(validate):
    config = {
        "plugins": [
            {
                "name": "../bad",
                "description": "d",
                "shortDescription": "s",
                "category": "c",
                "license": "MIT",
                "keywords": ["k"],
                "sources": [{"id": "Bad Id"}],
            }
        ]
    }
    messages = [p.message for p in validate.check_config(config)]
    assert any("plugin name '../bad'" in m for m in messages)
    assert any("source id 'Bad Id'" in m for m in messages)


ROUTING_DOC = (
    "# Director\n\n"
    "## Routing table\n\n"
    "| Task | Use |\n|---|---|\n"
    "| a | `alpha` and `ghost` |\n"
    "| b | `beta` |\n\n"
    "## Rules\n\n"
    "See `unrelated`.\n"
)


def test_routing_check_flags_names_the_hub_does_not_have(validate, tmp_path):
    config = {"plugins": [{"name": "design-core", "sources": []}, {"name": "beta", "sources": []}]}
    skills = tmp_path / "plugins" / "design-core" / "skills"
    put(skills / "design-director" / "SKILL.md", ROUTING_DOC)
    put(skills / "alpha" / "SKILL.md", "---\nname: alpha\ndescription: d\n---\n")
    messages = [p.message for p in validate.check_routing_table(tmp_path, config)]
    assert messages == ["routing table names `ghost`, which is not a skill or plugin in the hub"]


def test_routing_check_requires_the_table_section(validate, tmp_path):
    config = {"plugins": [{"name": "design-core", "sources": []}]}
    put(tmp_path / "plugins" / "design-core" / "skills" / "design-director" / "SKILL.md", "# no table here\n")
    assert len(validate.check_routing_table(tmp_path, config)) == 1


def test_size_check_errors_on_files_too_big_for_github(validate, tmp_path, monkeypatch):
    monkeypatch.setattr(validate, "ERROR_FILE_BYTES", 10)
    monkeypatch.setattr(validate, "WARN_FILE_BYTES", 5)
    (tmp_path / "big.bin").write_bytes(b"x" * 20)
    (tmp_path / "medium.bin").write_bytes(b"x" * 7)
    levels = {Path(p.message.split(":")[0]).name: p.level for p in validate.check_sizes(tmp_path)}
    assert levels == {"big.bin": "error", "medium.bin": "warning"}


def test_authored_check_requires_the_three_agents(validate, tmp_path):
    assert len(validate.check_authored(tmp_path)) == 5
    agents = tmp_path / "plugins" / "design-core" / "agents"
    for name in ("design-director", "design-reviewer", "reference-analyst"):
        put(agents / f"{name}.md", f"---\nname: {name}\ndescription: d\n---\n")
    put(tmp_path / "plugins" / "design-core" / "skills" / "design-director" / "SKILL.md", "x")
    put(tmp_path / "plugins" / "open-motion" / "skills" / "open-motion" / "SKILL.md", "x")
    assert validate.check_authored(tmp_path) == []


# --------------------------------------------------------------------------- the real repository


def test_the_published_tree_passes_every_check(validate):
    errors = [p.message for p in validate.run_all(ROOT) if p.level == "error"]
    assert errors == []
