# SpinDoctor Qwerty for Mistral Vibe

A native [Mistral Vibe](https://github.com/mistralai/mistral-vibe) plugin (Agent Plugins 1.0 + the `ai.mistral.vibe` extension) that
runs the **SpinDoctor 3.1.2 quantum-circuit simulator** on your computer: `q.*` circuit scripts (1-298 logical qubits), the 241
built-in presets, folders of command files (`q.folder`), and theory tests from a file, pasted text or the chat, each with TXT, PDF,
JSON and CSV reports. It brings a local MCP server (6 tools), a skill and a knowledge folder.

> **Honest limits.** SpinDoctor is a classical FP64 simulator. It is not a quantum computer, does not connect to quantum hardware,
> and gives no quantum speed-up or advantage. One entangled group is limited to 59 qubits and dense groups are limited by memory
> (2^n x 16 bytes). Registers wider than 29 qubits sample in basis Z only. Histograms are seeded Born samples.

Version 1.1.0 - engine 1.1.0 (SpinDoctor 3.1.2 parity) - Python 3.8+, standard library only - no network, no account, no keys.
Tested with the real Mistral Vibe CLI 2.26.1 and a scripted local model; see [Testing](#testing).

## Install

Vibe loads every folder in `~/.vibe/plugins/` (all projects) or `.vibe/plugins/` in a trusted project:

```bash
git clone https://github.com/LKVexa/spindoctor-qwerty-mistral-vibe ~/.vibe/plugins/spindoctor-qwerty
```

Start a new session, or type `/reload-plugins` in a running one. The plugin shows up as `spindoctor-qwerty` (namespace
`spindoctorQwerty`): skill `spindoctorQwerty:spindoctor-qwerty`, MCP connector `mcp_spindoctor_qwerty`, knowledge
`spindoctorQwerty:spindoctor-qwerty`. For one project only, clone into `<project>/.vibe/plugins/spindoctor-qwerty` and trust the folder.

**Windows:** `mcp.json` starts `python3`, which many Windows PCs do not have. Run once, then `/reload-plugins`:

```bat
py -3 %USERPROFILE%\.vibe\plugins\spindoctor-qwerty\tools\set_python.py
```

It writes the first of `py -3`, `python`, `python3` that really runs Python 3 into `mcp.json` (`--show` prints the current
choice; `py`, `python` or `python3` as an argument picks one). Updating with `git pull` afterwards needs
`git checkout mcp.json` first, then run it again.

**Keep the folder clean.** Vibe pins a content digest of the plugin folder for each session. Don't run tools that write into it
(the bundled scripts never write bytecode or reports there); if a session ever fails with `plugin_pin_mismatch`, delete any
`__pycache__` folders inside the plugin and start again.

## What's in the repo

| Path | What it is |
|---|---|
| `plugin.json` | Agent Plugins manifest with `extensions.ai.mistral.vibe` (`schemaVersion` 1, `toolNamespace` `spindoctorQwerty`) |
| `mcp.json` | MCP server `spindoctor-qwerty`: `python3 ${PLUGIN_ROOT}/skills/spindoctor-qwerty/scripts/spindoctor_mcp.py` |
| `skills/spindoctor-qwerty/` | Skill (`SKILL.md`), the bundled engine (`spindoctor/`), CLI and MCP server (`scripts/`), examples, LICENSE |
| `ai.mistral.vibe/knowledge/spindoctor-qwerty/KNOWLEDGE.md` | Short reference: limits, gates, command families, reports, honesty rules |
| `tools/set_python.py` | Points `mcp.json` at `py -3` / `python` / `python3` (Windows) |
| `FUNCTIONS.md` | The full function table with a runnable example for every command |
| `tests/` | Real-Vibe host check, scripted local model, shared end-to-end suite, reference outputs |

No hooks and no agents are shipped; nothing runs unless you ask for it.

## Using it

- Ask in plain language: "show the SpinDoctor functions", "run a 3-qubit GHZ circuit", "test the Bell state theory we discussed".
- **How Vibe calls the tools.** Vibe 2.26 offers plugin MCP tools through `run_typescript` (after `search_tool_functions`), as
  `tools.mcp_spindoctor_qwerty.spindoctor_run_preset({ preset_id: "qc-001" })` and so on; the skill tells the model this.
  Tools: `spindoctor_functions`, `spindoctor_run_script`, `spindoctor_run_preset`, `spindoctor_list_presets`, `spindoctor_report`,
  `spindoctor_test_theory`.
- **Approval.** Vibe asks before a plugin tool runs. In programmatic mode (`vibe -p`) there is nobody to ask, so the calls are
  denied unless you pass `--auto-approve` (or `--yolo`, or `--agent auto-approve`). The per-tool allow rules we tried in `config.toml`
  (keyed by connector route or by server alias) did not apply to plugin tools in `-p` runs of Vibe 2.26.1.
- The server runs from Vibe's read-only, pinned copy of the plugin, so give **absolute paths** for files and folders. Reports and
  state go to `~/spindoctor-workspace` unless a call passes `workspace`.
- Without the tools, the skill tells the model to run the same commands with `bash` and `scripts/spindoctor_cli.py`.
- **Knowledge folder.** It passes Vibe's validator. On Linux, Vibe 2.26.1 did not mount it in our tests (Vibe copies knowledge
  from its read-only pinned store and then cannot rename the read-only copy), so the model did not see it there; the skill carries
  the same rules, so nothing is lost. Windows was not tested.

## SpinDoctor Qwerty - plugin tools

| Function | What it does | Command to type |
|---|---|---|
| Function table (spindoctor_functions) | Show this table in chat | Ask: "show the SpinDoctor functions" |
| Run a script (spindoctor_run_script) | Run any q.* lines above; returns results + TXT/JSON/CSV/PDF report paths | Ask: "run q.circuit new bell 2 / q.circuit add h 0 / ..." |
| Run a preset (spindoctor_run_preset) | Run qc-001..qc-241 with overrides | Ask: "run preset qc-067 with shots=64" |
| List presets (spindoctor_list_presets) | Search the 241 presets | Ask: "list presets about Grover" |
| Read a report (spindoctor_report) | List/read TXT reports (PDF/JSON paths alongside) | Ask: "show the newest SpinDoctor report" |
| Test a theory from a file (spindoctor_test_theory source=file) | Read a .txt/.md/.pdf/.py/.json/.csv/.q attachment, then hypothesis -> prediction -> q.* script -> run -> verdict + TXT/PDF theory report | Ask: "test the theory in C:/notes/theory.md" (the host must pass the file path/content) |
| Test a theory from text (spindoctor_test_theory source=text) | Same pipeline for pasted text | Ask: "test this theory: a Hadamard on \|0> gives 50/50" |
| Test the theory we discussed (spindoctor_test_theory source=chat) | The AI summarises the theory from the conversation (claims, assumptions, variables, prediction), you confirm, then it is tested; quoted excerpts go in the report under 'Source: chat history'. An exported chat transcript (.txt/.md/.json/.html) also works | Ask: "test the theory we discussed" or "test the theory in my exported chat C:/chats/conversation.json" |

Every command family is listed with a runnable example in **[FUNCTIONS.md](FUNCTIONS.md)** (the exact table the tool shows):
circuits (`q.circuit`, including 298-qubit wide registers and the `mcx7` gate), queries (`q.query`), the tranche register
(`q.tranche`), the procedural grid, presets and sequences, resource planning, math calculators, physics models, lessons, noise, error
correction, compilation, algorithms, inputs/folders/history (`q.input`, `q.folder`, `q.history`) and the cartridge commands.

## Theory testing

`spindoctor_test_theory` turns a claim into a test: hypothesis -> measurable prediction -> `q.*` script -> run -> compare -> a TXT +
JSON + PDF **theory test report** with the hypothesis, script, raw results, verdict (*supported*, *not supported* or *inconclusive*)
and limits.

- **From a file:** .txt, .md, .pdf, .py, .json, .csv or .q. Give the file's absolute path on your computer (the server runs in the plugin folder), or paste the text.
- **From pasted text.**
- **From the chat history:** say *"test the theory we discussed"*. The model writes a short summary (claims, assumptions, variables,
  measurable prediction), shows it to you to confirm or correct, then passes it with optional quoted excerpts; the report records them
  under *Source: chat history*. Exported chat transcripts (.txt/.md/.json/.html from ChatGPT, Claude and others) also work.
- The plugin cannot read your conversation or attachments by itself: only the model sees them, and very long conversations may already
  be truncated by the context window.

Sample theory files and chat transcripts are in `skills/spindoctor-qwerty/examples/theory/`. The two sample
PDFs are stored as text; run `python3 skills/spindoctor-qwerty/examples/theory/make_sample_pdfs.py` to
recreate them.

## Folder ingestion (`q.folder`)

`q.folder run path="<folder>"` runs every supported file at the top level of a folder (.txt, .csv, .json, .qasm, .qasm2, .circuit,
.pdf) in ordinal name order: 1-128 supported files, at most 4 MiB per file, 1-128 commands per file and 4096 characters per command,
strict UTF-8. Other files (for example .md) are skipped and listed. The first failing file stops the job.


## Testing

| Test | Command |
|---|---|
| Host check, real Vibe (this folder) | `python3 tests/vibe_host_check.py --vibe $(which vibe)` |
| Same, installing from GitHub | `python3 tests/vibe_host_check.py --vibe $(which vibe) --source https://github.com/LKVexa/spindoctor-qwerty-mistral-vibe` |
| End-to-end suite only | `python3 tests/e2e_mcp.py --server python3 skills/spindoctor-qwerty/scripts/spindoctor_mcp.py --examples skills/spindoctor-qwerty/examples/theory` |

**Real host, stand-in model.** Mistral Vibe is free (Apache-2.0, `pip install mistral-vibe`, Python 3.12+) and needs no account
when it talks to a local OpenAI-compatible server. `tests/vibe_host_check.py` writes a throwaway `~/.vibe/config.toml` whose model
uses Vibe's built-in `llamacpp` provider pointed at `tests/stub_llm.py`, a scripted stand-in model (no real model, no network, no
key), installs the plugin in a throwaway home and runs `vibe -p`. The stub plays the model: `search_tool_functions` (finds all 6
tools), `run_typescript` calls of every tool (function table, Bell, qc-001, GHZ presets, reports, a 298-qubit `mcx7` circuit, a
theory from a file and from the chat: verdict *supported*, PDF written), the `skill` tool and the `bash` fallback. It also checks:
Vibe's own validator accepts the plugin (and flags five broken variants, including 1.0's knowledge file), the folder is unchanged
after use and a second session re-pins cleanly, `-p` without `--auto-approve` denies the calls, the 1.0-style setup without
bytecode guards fails its first session with `plugin_pin_mismatch`, project scope with `--trust`, and the shared end-to-end suite.
**Not tested:** a real model choosing the tools, the interactive TUI (approval prompts, `/reload-plugins`), Windows, macOS.
Results: [E2E_RESULTS.md](E2E_RESULTS.md).

## Author and license

Author: **RUSSELL PHILIP SMITHSON** <russellsmithson77@outlook.com>

Copyright (C) 2026 RUSSELL PHILIP SMITHSON. Licensed under the GNU General Public License v3.0 or later (`GPL-3.0-or-later`): see
[LICENSE](LICENSE), [NOTICE](NOTICE) and [COPYRIGHT](COPYRIGHT). Mistral Vibe is Apache-2.0 software by Mistral AI; this project
is not affiliated with Mistral AI.
