from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

HUB = {
    "name": "design-hub",
    "displayName": "Design Hub",
    "repo": "owner/design-hub",
    "description": "A hub.",
    "author": {"name": "owner", "url": "https://github.com/owner"},
}
PLUGIN = {
    "name": "motion-kit",
    "category": "Design",
    "license": "MIT",
    "keywords": ["motion"],
    "description": "Motion skills.",
    "shortDescription": "Motion",
    "sources": [
        {
            "id": "gsap",
            "repo": "greensock/gsap-skills",
            "author": "GreenSock",
            "license": "MIT",
            "notes": "A note.",
        }
    ],
}
SHA = "a" * 40


@pytest.mark.parametrize("text", ["../escape", "/absolute", "a/../b", ""])
def test_safe_relative_rejects_unsafe_paths(sync, text):
    with pytest.raises(ValueError):
        sync.safe_relative(text)


def test_safe_relative_accepts_nested_path(sync):
    assert sync.safe_relative("plugins/x/skills").as_posix() == "plugins/x/skills"


@pytest.mark.parametrize("name", ["../evil", "Upper", "has space", "-leading", "a/b", "", "dot."])
def test_checked_name_rejects_anything_but_plain_slugs(sync, name):
    with pytest.raises(ValueError, match="lowercase"):
        sync.checked_name("plugin name", name)


def test_checked_name_accepts_slugs(sync):
    assert sync.checked_name("plugin name", "web-visuals2") == "web-visuals2"


def test_sync_source_refuses_a_bad_plugin_name_before_touching_the_disk_or_network(sync):
    with pytest.raises(ValueError, match="plugin name"):
        sync.sync_source({"name": "../escape"}, {"id": "ok"}, {"sources": {}}, update=False)
    with pytest.raises(ValueError, match="source id"):
        sync.sync_source({"name": "ok"}, {"id": "../escape"}, {"sources": {}}, update=False)


def test_a_tampered_lock_cannot_delete_outside_the_plugin_folder(sync):
    for installed in ("../x", "/abs", "."):
        with pytest.raises(ValueError):
            sync.safe_relative(installed)


COPIES = [
    {"from": "skills", "to": "skills", "children": True},
    {"from": "docs/tool.md", "to": "extra/tool.md"},
    {"from": ".claude/skills/brand", "to": "skills/brand"},
]


@pytest.mark.parametrize(
    ("upstream_path", "expected"),
    [
        ("skills/alpha/run.sh", "skills/alpha/run.sh"),
        ("docs/tool.md", "extra/tool.md"),
        (".claude/skills/brand/scripts/a.cjs", "skills/brand/scripts/a.cjs"),
        ("other/file.sh", None),
        ("skillsX/file.sh", None),
    ],
)
def test_destination_for_maps_upstream_paths_into_the_plugin(sync, upstream_path, expected):
    assert sync.destination_for(upstream_path, COPIES) == expected


def test_bump_patch_increments_only_the_patch_number(sync):
    assert sync.bump_patch("0.1.9") == "0.1.10"


def test_top_level_ignore_skips_git_everywhere_and_excluded_names_only_at_top(sync, tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "skills" / "tests").mkdir(parents=True)
    ignore = sync.top_level_ignore(tmp_path, frozenset({"tests"}))
    assert ignore(str(tmp_path), ["tests", "skills", ".git"]) == {"tests", ".git"}
    assert ignore(str(tmp_path / "skills"), ["tests", ".git"]) == {".git"}


def test_claude_manifest_carries_version_and_license(sync):
    manifest = sync.build_claude_manifest(HUB, PLUGIN, "1.2.3")
    assert manifest["name"] == "motion-kit"
    assert manifest["version"] == "1.2.3"
    assert manifest["license"] == "MIT"
    assert manifest["repository"] == "https://github.com/owner/design-hub"


def test_codex_manifest_adds_skills_path_and_interface(sync):
    manifest = sync.build_codex_manifest(HUB, PLUGIN, "1.2.3")
    assert manifest["skills"] == "./skills/"
    assert manifest["interface"]["displayName"] == "Motion Kit"
    assert manifest["interface"]["category"] == "Design"
    assert manifest["version"] == "1.2.3"


def test_marketplaces_list_every_plugin_with_the_right_path(sync):
    claude = sync.build_claude_marketplace(HUB, [PLUGIN])
    codex = sync.build_codex_marketplace(HUB, [PLUGIN])
    assert claude["plugins"][0]["source"] == "./plugins/motion-kit"
    assert codex["plugins"][0]["source"] == {"source": "local", "path": "./plugins/motion-kit"}
    assert claude["name"] == codex["name"] == "design-hub"


def test_credits_link_the_pinned_commit(sync):
    lock = {"sources": {"gsap": {"commit": SHA}}}
    rows = sync.credits_rows([PLUGIN], lock)
    assert len(rows) == 1
    assert "GreenSock" in rows[0]
    assert f"/commit/{SHA}" in rows[0]


def test_credits_without_a_pin_say_not_available(sync):
    assert sync.credits_rows([PLUGIN], {"sources": {}})[0].rstrip().endswith("n/a |")


def test_credits_include_source_notes(sync):
    assert "A note." in sync.build_credits([PLUGIN], {"sources": {}})


def test_changed_pins_reports_new_and_moved_sources(sync):
    old = {"sources": {"a": {"commit": "1" * 40}, "b": {"commit": "2" * 40}}}
    new = {"sources": {"a": {"commit": "1" * 40}, "b": {"commit": "3" * 40}, "c": {"commit": "4" * 40}}}
    assert sync.changed_pins(old, new) == ["b", "c"]


def test_source_note_states_when_nothing_is_copied(sync):
    source = {"id": "x", "repo": "o/r", "author": "A", "license": "MIT"}
    assert "No upstream files are copied" in sync.source_note(source, SHA, [])
    assert "byte for byte" in sync.source_note(source, SHA, ["skills/x"])


def test_choose_commit_keeps_the_pin_unless_updating(sync):
    source = {"id": "gsap"}
    lock = {"sources": {"gsap": {"commit": SHA}}}
    assert sync.choose_commit(source, lock, update=False, repo_dir=Path(".")) == SHA


def test_wanted_paths_anchor_each_path_and_mirrors_take_everything(sync):
    source = {"copy": [{"from": "skills/a", "to": "skills/a"}], "licenseFiles": ["LICENSE"]}
    assert sync.wanted_paths(source) == ["/skills/a", "/LICENSE"]
    assert sync.wanted_paths({"mirrorExclude": []}) is None
