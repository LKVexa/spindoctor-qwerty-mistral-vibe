# Changelog

## 1.1.0 - 2026-10-11

- Engine 1.1.0 at parity with the updated SpinDoctor 3.1.2: 1-298 logical qubits (59 per entangled factor), the `mcx7` gate,
  wide-register Born-Z sampling, `q.folder` with 3.1.2 semantics, CSV report copies and measurement-CSV fitting equations. All 241
  presets replayed. Tools `spindoctor_functions` (function table, marked read-only) and `spindoctor_test_theory`. 1.0 described
  SpinDoctor 3.0.3 and a 29-qubit cap.
- **First session no longer fails.** Vibe starts a plugin's MCP server from the plugin folder while it pins a content digest of
  that folder. 1.0's server wrote `__pycache__` there, so the first session after installing failed with
  `plugin_pin_mismatch`. `mcp.json` now sets `PYTHONDONTWRITEBYTECODE=1` and both scripts set `sys.dont_write_bytecode`.
- **Knowledge folder loads.** 1.0's `KNOWLEDGE.md` had no frontmatter, so Vibe rejected it (`plugin.knowledge.invalid`). It now
  has `name`/`description`/`display_name` and is a short reference (limits, gates, command families, reports, honesty rules)
  instead of a copy of SKILL.md.
- **Reports in one place.** 1.0 set `SPINDOCTOR_WORKSPACE` to a `workspace` folder inside `${PLUGIN_DATA}`; in Vibe 2.26 that is a per-session folder
  under `~/.vibe/logs/session/plugins/data/<session>/`, so every session started from scratch and reports were hard to find. Now
  `~/spindoctor-workspace` (or a `workspace` argument).
- **SKILL.md speaks Vibe.** Vibe offers plugin MCP tools through `run_typescript` (connector `mcp_spindoctor_qwerty`), not as
  direct tools; the skill now shows the call, names the connector, explains approval (`-p` needs `--auto-approve`), absolute paths
  (the server runs from a read-only pinned copy) and the `bash` fallback.
- **Windows.** `tools/set_python.py` rewrites `mcp.json` to start `py -3` (command `py`, argument `-3`), `python` or `python3` -
  whichever really runs Python 3 - since many Windows PCs have no `python3`.
- Removed the empty `ai.mistral.vibe/hooks.toml` (no hooks). No agents are shipped.
- The repo root is the plugin (1.0 used a `spindoctor-qwerty/` subfolder). plugin.json: author email/url, homepage, repository,
  license GPL-3.0-or-later, keywords.
- Tests: `tests/vibe_host_check.py` runs the real Mistral Vibe CLI against a scripted local model (`tests/stub_llm.py`).
- License changed from MIT to GPL-3.0-or-later. Author RUSSELL PHILIP SMITHSON. README, NOTICE, COPYRIGHT and SPDX headers added.

## 1.0.0

- First release: `spindoctor-qwerty/` folder with plugin.json, mcp.json, skill, empty hooks.toml and a knowledge copy of SKILL.md;
  engine described as SpinDoctor 3.0.3.
