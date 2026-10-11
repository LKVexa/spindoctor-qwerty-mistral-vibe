---
name: spindoctor-qwerty
description: SpinDoctor 3.1.2 simulator facts - limits, gate set, q.* command families, report files and honesty rules for answering questions about it.
display_name: SpinDoctor Qwerty reference
---

# SpinDoctor Qwerty reference (engine 1.1.0, SpinDoctor 3.1.2 parity)

Use this when answering questions about SpinDoctor itself. To run anything, use the `spindoctor-qwerty` skill and the
`mcp_spindoctor_qwerty` tools.

## What it is

- A classical FP64 state-vector simulator running on this computer. Not a quantum computer, no quantum hardware, no quantum
  speed-up or advantage. Say so whenever results could be mistaken for hardware results.
- Histograms are seeded Born samples: counts fluctuate around the exact probabilities.

## Limits

- Circuits: 1-298 logical qubits. One entangled factor is limited to 59 qubits; dense factors are limited by the memory budget
  (2^n x 16 bytes for n entangled qubits; `q.circuit memory MiB` sets it).
- Registers wider than 29 qubits sample in basis Z only (wide-register Born-Z sampling).
- 241 presets, qc-001..qc-241. Up to 64 saved circuits by default (`q.circuit capacity N`).

## Gates

h x y z s sdg t tdg i sx sxdg rx ry rz p u (3 angles), cx cy cz ch swap cp crx cry crz ccx cswap, and `mcx7` (seven-control X:
operands 0..6 control operand 7). Angles are radians; q0 is the least-significant bit.

## Command families

`q.circuit` (build/run/inspect circuits), `q.query`, `q.tranche`, the procedural grid (`q.prepare`, `q.gate`, `q.state`, `q.verify`,
`q.measure`, `q.reset`, `q.export`), `q.preset`, `q.resource`, `q.math`, `q.model`, `q.lesson`, `q.noise`, `q.qec`, `q.compile`,
`q.algorithm`, `q.input`, `q.folder` (process a folder of command files), `q.history`. `q.help` lists everything. The full table with
a runnable example per command is what `spindoctor_functions` returns.

## Reports

Every run writes TXT, JSON and PDF reports (plus CSV copies, and fitting equations for measurement CSVs) under
`~/spindoctor-workspace/reports/` unless a `workspace` is given. Theory tests add a theory report with hypothesis, script, raw
results, verdict (supported / not supported / inconclusive) and limits.

## Theory tests from the chat

The plugin cannot read the chat. Summarise the theory (claims, assumptions, variables, one measurable prediction), get the user's
confirmation, then pass the summary and verbatim excerpts to `spindoctor_test_theory` with `source="chat"`.
