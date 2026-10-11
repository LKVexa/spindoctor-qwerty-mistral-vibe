# E2E results - spindoctor-qwerty-mistral-vibe 1.1.0

Host: **the real Mistral Vibe CLI (vibe 2.26.1)**, installed with `pip install mistral-vibe` (free, Apache-2.0), no account. Model: a
**scripted stand-in** (`tests/stub_llm.py`) behind Vibe's built-in `llamacpp` provider - no real model, no network, no key. The
stub calls `search_tool_functions`, `run_typescript` (the plugin's MCP tools), `skill` and `bash` as a model would. Python 3.13.5.

Not tested: a real model choosing the tools, the interactive TUI (approval prompts, `/reload-plugins`), Windows, macOS.

## Host check: 29/29

| Result | Check |
|---|---|
| PASS | plugin.json: version 1.1.0, GPL-3.0-or-later, author, homepage/repository, ai.mistral.vibe schemaVersion 1 + toolNamespace spindoctorQwerty |
| PASS | Vibe's own validator (inspect_plugin): valid, no diagnostics, skill spindoctorQwerty:spindoctor-qwerty, knowledge spindoctorQwerty:spindoctor-qwerty |
| PASS | every .py file has a GPL-3.0-or-later SPDX header (27 files) |
| PASS | no symlinks in the package (Vibe refuses paths that leave the plugin root) |
| PASS | SKILL.md: guardrail, Vibe connector + run_typescript example, absolute-path rule, approval note |
| PASS | bash fallback: every CLI command in SKILL.md runs as written from the skill folder (6 commands) |
| PASS | tools/set_python.py: 'py' writes command py + args [-3, server] (still valid for Vibe); auto-pick restores the shipped python3 file byte for byte |
| PASS | Vibe's validator flags 5 broken variants (1.0's frontmatter-less KNOWLEDGE.md, reserved namespace 'vibe', env PLUGIN_ROOT, ../ command, skill name != folder) |
| PASS | real Vibe -p session ran to the end with the stub model (13 model requests, exit 0) |
| PASS | system prompt lists the plugin (spindoctor-qwerty) and its skill spindoctorQwerty:spindoctor-qwerty from Vibe's pinned copy |
| PASS | search_tool_functions finds all 6 tools in connector mcp_spindoctor_qwerty |
| PASS | details mode returns the spindoctor_test_theory declaration (source file/text/chat) |
| PASS | run_typescript -> spindoctor_functions: the Markdown function table |
| PASS | run_typescript -> spindoctor_run_script: Bell ok, reports in ~/spindoctor-workspace (1.0 put them in a per-session PLUGIN_DATA folder) |
| PASS | run_typescript -> spindoctor_run_preset qc-001 |
| PASS | run_typescript -> spindoctor_list_presets ghz |
| PASS | run_typescript -> spindoctor_report lists reports |
| PASS | run_typescript -> 298-qubit wide register with mcx7 (3.1.2 parity) |
| PASS | run_typescript -> theory extract from an absolute path in the pinned skill folder |
| PASS | run_typescript -> theory from the chat: supported, 2 excerpts, PDF written |
| PASS | skill tool loads spindoctorQwerty:spindoctor-qwerty (SKILL.md body: guardrail + run_typescript instructions) |
| PASS | bash fallback from the skill folder runs the CLI (Bell, ok) |
| PASS | installed plugin folder unchanged by tool use and the CLI fallback (Vibe pins its content digest) |
| PASS | second session after tool use: plugin re-pins cleanly (no plugin_pin_mismatch) and the tool works |
| PASS | without --auto-approve, -p denies the MCP call (tool_denied) - Vibe asks before plugin tools run |
| PASS | host quirk reproduced: without the bytecode guards (1.0's setup) the FIRST session fails with plugin_pin_mismatch and a __pycache__ appears in the plugin folder |
| PASS | knowledge folder: mounted, or (Vibe 2.26.1 on Linux) not mounted because Vibe copies it from its read-only pinned store and cannot rename the copy |
| PASS | project scope: .vibe/plugins/spindoctor-qwerty in a trusted project (--trust) loads and runs qc-002 |
| PASS | shared end-to-end suite against the server as mcp.json starts it: SUMMARY 12/12 passed in 13.5s |

## Shared end-to-end suite (server as mcp.json starts it): 12/12

| Result | Check |
|---|---|
| PASS | initialize (server spindoctor-qwerty 1.1.0) |
| PASS | tools/list exposes the 6 tools |
| PASS | function table (Markdown, 19 sections, 298-qubit limits listed) |
| PASS | 241 presets listed |
| PASS | one script per command family (16 families, every table example) |
| PASS | 298-qubit circuit with mcx7 (prepared-factor-Born-Z) |
| PASS | q.folder on mixed .txt/.csv/.json/.qasm folder (+ .md skipped) |
| PASS | theory from a file -> supported, TXT+PDF report |
| PASS | theory from a chat summary + quoted excerpts -> supported |
| PASS | theory from an exported chat transcript -> supported |
| PASS | presets qc-001..qc-025 match the updated 3.1.2 reference (20 identical, 5 documented differences) |
| PASS | TXT+PDF reports valid (255 PDFs, 255 TXT twins) |

## Runs

- Pre-push: real Mistral Vibe 2.26.1 + scripted local model, 29/29; shared suite 12/12.
