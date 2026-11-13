# Credits and licences

B30 Design Hub collects work by other people. Every component below keeps its author's licence,
which is stored next to it under `plugins/<plugin>/THIRD_PARTY/` (or at the plugin root for
whole-plugin mirrors). The hub's own original work is MIT licensed; see `LICENSE`.

| Plugin | Component | Author | Licence | Pinned commit |
|---|---|---|---|---|
| design-core | [impeccable](https://github.com/pbakaus/impeccable) | Paul Bakaus | Apache-2.0 | [`b4bff16`](https://github.com/pbakaus/impeccable/commit/b4bff1626c344067788c2679f048a20057c7cc5a) |
| design-core | [ui-ux-pro-max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | Next Level Builder | MIT | [`6ae86f6`](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/commit/6ae86f61f520d6ca229d2f40e070410638c908c5) |
| design-core | [frontend-design](https://github.com/anthropics/claude-plugins-official) | Anthropic | Apache-2.0 | [`e0ab6e5`](https://github.com/anthropics/claude-plugins-official/commit/e0ab6e51219eef74e417a0e1d89e5d53e5e763d4) |
| motion | [gsap-skills](https://github.com/greensock/gsap-skills) | GreenSock | MIT | [`aed9cfd`](https://github.com/greensock/gsap-skills/commit/aed9cfd3277740755f6bfc1155c7aa645403b760) |
| threejs | [threejs-graphics](https://github.com/scottstts/Threejs-Awesome-Graphics-Agent-Skills) | Scott Sun | MIT | [`53eb5a2`](https://github.com/scottstts/Threejs-Awesome-Graphics-Agent-Skills/commit/53eb5a24097425d82532ec33697ad472750132a4) |
| threejs | [threejs-game-skills](https://github.com/majidmanzarpour/threejs-game-skills) | Majid Manzarpour | MIT | [`8286774`](https://github.com/majidmanzarpour/threejs-game-skills/commit/8286774b22a2566bf894dbc825825c16921866af) |
| web-visuals | [everything-claude-code](https://github.com/affaan-m/everything-claude-code) | Affaan Mustafa | MIT | [`d2ef268`](https://github.com/affaan-m/everything-claude-code/commit/d2ef2680594f9a17526a6e1a2e18b3d242c5d17b) |
| ai-site-brand | [higgsfield-skills](https://github.com/higgsfield-ai/skills) | Higgsfield AI | MIT | [`2700040`](https://github.com/higgsfield-ai/skills/commit/27000402070db19d958789d05b3b52b6f4718d7c) |
| rea | [rea](https://github.com/morluto/rea) | morluto | MIT | [`d74549e`](https://github.com/morluto/rea/commit/d74549e495c58eb4a560279fd9f05508401ea0a0) |
| unslop | [unslop](https://github.com/heydamir/unslop) | Damir Sokolovsky | CC-BY-4.0 | [`97daa3e`](https://github.com/heydamir/unslop/commit/97daa3eb365670ea3f87ed85356cbfcee18105a5) |
| modern-web-guidance | [modern-web-guidance](https://github.com/GoogleChrome/modern-web-guidance) | Google Chrome | Apache-2.0 | [`4dd9683`](https://github.com/GoogleChrome/modern-web-guidance/commit/4dd968349e54ca45a05dd5c818fb035c9054b022) |
| floorplan | [floorplan](https://github.com/haydenschmitty/floorplan) | Hayden Smith | MIT | [`8195eb6`](https://github.com/haydenschmitty/floorplan/commit/8195eb6898c4f4403a4ee741fa3d3d570aa8c505) |
| craft-anything | [craft-anything](https://github.com/storytold/craft-anything) | ArtCraft Team and the Craft Anything contributors | MIT OR Apache-2.0 | [`4a4b06d`](https://github.com/storytold/craft-anything/commit/4a4b06d2813cd24821bd9bbdd670b75c21079804) |
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
