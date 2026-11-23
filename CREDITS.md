# Credits and licences

B30 Design Hub collects work by other people. Every component below keeps its author's licence,
which is stored next to it under `plugins/<plugin>/THIRD_PARTY/` (or at the plugin root for
whole-plugin mirrors). The hub's own original work is MIT licensed; see `LICENSE`.

| Plugin | Component | Author | Licence | Pinned commit |
|---|---|---|---|---|
| design-core | [impeccable](https://github.com/pbakaus/impeccable) | Paul Bakaus | Apache-2.0 | [`b49177d`](https://github.com/pbakaus/impeccable/commit/b49177d32788f2dc585c42831d845dacf1ebed2c) |
| design-core | [ui-ux-pro-max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | Next Level Builder | MIT | [`281e453`](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/commit/281e4537afb11333ac9947783779aaf314ebfbf2) |
| design-core | [frontend-design](https://github.com/anthropics/claude-plugins-official) | Anthropic | Apache-2.0 | [`73c8cf3`](https://github.com/anthropics/claude-plugins-official/commit/73c8cf3ea7e296057b467990f2f5d61b4c922260) |
| motion | [gsap-skills](https://github.com/greensock/gsap-skills) | GreenSock | MIT | [`aed9cfd`](https://github.com/greensock/gsap-skills/commit/aed9cfd3277740755f6bfc1155c7aa645403b760) |
| threejs | [threejs-graphics](https://github.com/scottstts/Threejs-Awesome-Graphics-Agent-Skills) | Scott Sun | MIT | [`53eb5a2`](https://github.com/scottstts/Threejs-Awesome-Graphics-Agent-Skills/commit/53eb5a24097425d82532ec33697ad472750132a4) |
| threejs | [threejs-game-skills](https://github.com/majidmanzarpour/threejs-game-skills) | Majid Manzarpour | MIT | [`8286774`](https://github.com/majidmanzarpour/threejs-game-skills/commit/8286774b22a2566bf894dbc825825c16921866af) |
| web-visuals | [everything-claude-code](https://github.com/affaan-m/everything-claude-code) | Affaan Mustafa | MIT | [`4adeee6`](https://github.com/affaan-m/everything-claude-code/commit/4adeee6732a12d1540f49a4d50a38ce8c97f9a53) |
| ai-site-brand | [higgsfield-skills](https://github.com/higgsfield-ai/skills) | Higgsfield AI | MIT | [`2700040`](https://github.com/higgsfield-ai/skills/commit/27000402070db19d958789d05b3b52b6f4718d7c) |
| rea | [rea](https://github.com/morluto/rea) | morluto | MIT | [`07b6a3d`](https://github.com/morluto/rea/commit/07b6a3dc5f496081c60f4d122d08bad292a21509) |
| unslop | [unslop](https://github.com/heydamir/unslop) | Damir Sokolovsky | CC-BY-4.0 | [`620163e`](https://github.com/heydamir/unslop/commit/620163eedb3529d9cd23a3994ed8d287d06f760d) |
| modern-web-guidance | [modern-web-guidance](https://github.com/GoogleChrome/modern-web-guidance) | Google Chrome | Apache-2.0 | [`64a6d70`](https://github.com/GoogleChrome/modern-web-guidance/commit/64a6d708f5a43f2cd3fde5d4d7db3905ba1bdf65) |
| floorplan | [floorplan](https://github.com/haydenschmitty/floorplan) | Hayden Smith | MIT | [`94f81b4`](https://github.com/haydenschmitty/floorplan/commit/94f81b463b7617e06d873ac71323ce71644c8399) |
| craft-anything | [craft-anything](https://github.com/storytold/craft-anything) | ArtCraft Team and the Craft Anything contributors | MIT OR Apache-2.0 | [`3d5eb25`](https://github.com/storytold/craft-anything/commit/3d5eb2577397ac632fb6dfffd94aa9787ad17acc) |
| open-motion | [open-motion](https://github.com/Yuan-ManX/open-motion) | Yuan-Man | MIT | [`1c93d99`](https://github.com/Yuan-ManX/open-motion/commit/1c93d99b064e8674f244a8f24227358ec6f61618) |

## Notes

- **impeccable**: Only the skill folder is included. The upstream plugin's hooks and its four bundled agents are not, so automatic checks after each edit are off. The skill falls back to its documented degraded mode. Install the full upstream plugin if you want them.
- **frontend-design**: Anthropic does not endorse or sponsor this hub.
- **rea**: Only the skill is included. The upstream plugin also registers an MCP server with a large tool set; this hub does not.
- **unslop**: Licensed under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). The material is copied without changes.
- **modern-web-guidance**: Mirrored whole, minus CI files. Google and Chrome do not endorse or sponsor this hub.
- **floorplan**: Mirrored whole, minus CI files and tests, byte for byte so its CHECKSUMS.txt still verifies.
- **craft-anything**: Only the skill text is included, renamed from the file names used inside the upstream setup crate. The ArtCraft name and logos are trademarks and are not included.
- **open-motion**: Nothing is copied. The skill in this plugin is an original guide written for this hub.
