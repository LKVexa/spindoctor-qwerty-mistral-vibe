#!/usr/bin/env python3
# SpinDoctor Qwerty 1.1.0 - SpinDoctor Qwerty plugin for Mistral Vibe: host check against the real Mistral Vibe CLI
# Copyright (C) 2026 RUSSELL PHILIP SMITHSON <russellsmithson77@outlook.com>
# SPDX-License-Identifier: GPL-3.0-or-later
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version. It is distributed WITHOUT ANY WARRANTY; see the LICENSE file for details.
"""Host check with the real Mistral Vibe CLI and a scripted local model. Run from the repo root:

  python3 tests/vibe_host_check.py --vibe /path/to/vibe                 # this folder as a user-scope plugin
  python3 tests/vibe_host_check.py --vibe /path/to/vibe --source https://github.com/LKVexa/spindoctor-qwerty-mistral-vibe

Mistral Vibe (Apache-2.0, `pip install mistral-vibe`, Python 3.12+) needs no account when it talks to a local OpenAI-compatible
server: this script writes a throwaway ~/.vibe/config.toml whose active model uses Vibe's built-in `llamacpp` provider pointed at
tests/stub_llm.py, a scripted stand-in model (no real model, no network, no key). The stub plays the model's part: it calls
search_tool_functions, run_typescript (which calls the plugin's MCP tools), skill and bash exactly as a model would, and logs
what Vibe sends back. Static checks use Vibe's own plugin validator (vibe.core.plugins.inspection.inspect_plugin).
Not tested: a real model choosing the tools, the interactive TUI (approval prompts, /reload-plugins), Windows, macOS. Stdlib only.
"""
import json, os, re, shutil, socket, subprocess, sys, tempfile, time
sys.dont_write_bytecode = True; os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
TOOLS = ["spindoctor_functions", "spindoctor_list_presets", "spindoctor_report", "spindoctor_run_preset", "spindoctor_run_script", "spindoctor_test_theory"]
NS = "mcp_spindoctor_qwerty"; SKILL = "spindoctorQwerty:spindoctor-qwerty"
R = []
OK = lambda s: bool(re.search(r'\\?"ok\\?":\s*true', s or ""))


def T(name, ok, detail=""):
    R.append({"check": name, "pass": bool(ok), "detail": str(detail)[:600]})
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else "  -- " + str(detail)[:500])); sys.stdout.flush()


def vibe_python(vibe):
    first = open(vibe, encoding="utf-8", errors="replace").readline()
    return first[2:].strip() if first.startswith("#!") else sys.executable


INSPECT = r"""
import json, sys
from pathlib import Path
from vibe.core.plugins.inspection import inspect_plugin
print(inspect_plugin(Path(sys.argv[1])).model_dump_json(by_alias=True))
"""


def inspect(vpy, path):
    r = subprocess.run([vpy, "-c", INSPECT, path], capture_output=True, text=True, timeout=120)
    try: return json.loads(r.stdout.strip().splitlines()[-1])
    except Exception: return {"valid": False, "diagnostics": [{"message": r.stderr[-300:]}]}


# ---------------------------------------------------------------- static
def static(vpy):
    m = json.load(open(os.path.join(ROOT, "plugin.json"), encoding="utf-8")); ext = m.get("extensions", {}).get("ai.mistral.vibe", {})
    T("plugin.json: version 1.1.0, GPL-3.0-or-later, author, homepage/repository, ai.mistral.vibe schemaVersion 1 + toolNamespace spindoctorQwerty",
      m.get("version") == "1.1.0" and m.get("license") == "GPL-3.0-or-later" and m["author"].get("name") == "RUSSELL PHILIP SMITHSON"
      and m.get("repository", "").endswith("/spindoctor-qwerty-mistral-vibe") and ext == {"schemaVersion": 1, "toolNamespace": "spindoctorQwerty"}, m)
    r = inspect(vpy, ROOT)
    T("Vibe's own validator (inspect_plugin): valid, no diagnostics, skill %s, knowledge %s" % (SKILL, SKILL),
      r.get("valid") and not r.get("diagnostics") and [s["name"] for s in r.get("skills", [])] == [SKILL]
      and [k["name"] for k in r.get("knowledge", [])] == [SKILL], r.get("diagnostics"))
    src = [os.path.join(d, f) for d, _, fs in os.walk(ROOT) if "/.git" not in d and "__pycache__" not in d for f in fs if f.endswith(".py")]
    bad = [x for x in src if "SPDX-License-Identifier: GPL-3.0-or-later" not in open(x, encoding="utf-8").read(2500)]
    T("every .py file has a GPL-3.0-or-later SPDX header (%d files)" % len(src), not bad, bad[:3])
    links = [os.path.join(d, f) for d, ds, fs in os.walk(ROOT) for f in fs + ds if os.path.islink(os.path.join(d, f))]
    T("no symlinks in the package (Vibe refuses paths that leave the plugin root)", not links, links)
    sk = os.path.join(ROOT, "skills", "spindoctor-qwerty"); t = open(os.path.join(sk, "SKILL.md"), encoding="utf-8").read()
    T("SKILL.md: guardrail, Vibe connector + run_typescript example, absolute-path rule, approval note", "not a\nquantum computer" in t
      and "tools.mcp_spindoctor_qwerty.spindoctor_run_preset" in t and "ABSOLUTE paths" in t and "--auto-approve" in t)
    cmds = [ln.split("  #")[0].strip() for blk in re.findall(r"```bash\n(.*?)```", t, re.S) for ln in blk.splitlines() if ln.startswith("python3 scripts/")]
    ws = tempfile.mkdtemp(prefix="sdq_cli_"); bad = []
    for cm in cmds:
        argv = cm.split(" ", 2); rest = re.findall(r'"[^"]*"|\S+', argv[2])
        rr = subprocess.run([sys.executable, argv[1], "--workspace", ws] + [x.strip('"') for x in rest], cwd=sk, capture_output=True, timeout=300)
        if rr.returncode: bad.append((cm, rr.stderr[-200:]))
    T("bash fallback: every CLI command in SKILL.md runs as written from the skill folder (%d commands)" % len(cmds), cmds and not bad, bad)
    shutil.rmtree(ws, ignore_errors=True)
    # tools/set_python.py on a scratch copy
    tmp = tempfile.mkdtemp(prefix="sdq_sp_"); c = os.path.join(tmp, "p"); shutil.copytree(ROOT, c, ignore=shutil.ignore_patterns(".git", "spindoctor", "examples", "tests"))
    sp = os.path.join(c, "tools", "set_python.py"); orig = open(os.path.join(c, "mcp.json"), "rb").read()
    a = subprocess.run([sys.executable, sp, "py"], capture_output=True, text=True); j = json.load(open(os.path.join(c, "mcp.json")))["mcpServers"]["spindoctor-qwerty"]
    ok1 = j["command"] == "py" and j["args"] == ["-3", "${PLUGIN_ROOT}/skills/spindoctor-qwerty/scripts/spindoctor_mcp.py"]
    v1 = inspect(vpy, c).get("valid")
    subprocess.run([sys.executable, sp], capture_output=True, text=True)
    ok2 = open(os.path.join(c, "mcp.json"), "rb").read() == orig  # on this Linux box the first working choice is python3 = the shipped file
    T("tools/set_python.py: 'py' writes command py + args [-3, server] (still valid for Vibe); auto-pick restores the shipped python3 file byte for byte",
      ok1 and v1 and ok2, (a.stdout, j))
    shutil.rmtree(tmp, ignore_errors=True)
    negative(vpy)


def negative(vpy):
    """Vibe's validator must flag what 1.0 got wrong and what this plugin avoids (so the clean result above means something)."""
    base = tempfile.mkdtemp(prefix="sdq_vneg_"); hits = []
    def variant(edit):
        d = os.path.join(base, str(len(hits))); shutil.copytree(ROOT, d, ignore=shutil.ignore_patterns(".git", "spindoctor", "examples", "tests", "__pycache__"))
        edit(d); r = inspect(vpy, d); return (not r.get("valid")) or bool(r.get("diagnostics"))
    def jedit(d, f, fn):
        p = os.path.join(d, f); j = json.load(open(p)); fn(j); json.dump(j, open(p, "w"))
    def kn(d):  # 1.0's KNOWLEDGE.md had no frontmatter
        p = os.path.join(d, "ai.mistral.vibe/knowledge/spindoctor-qwerty/KNOWLEDGE.md"); s = open(p).read(); open(p, "w").write(s[s.index("\n---\n", 4) + 5:])
    hits.append(variant(kn))
    hits.append(variant(lambda d: jedit(d, "plugin.json", lambda j: j["extensions"]["ai.mistral.vibe"].update(toolNamespace="vibe"))))
    hits.append(variant(lambda d: jedit(d, "mcp.json", lambda j: j["mcpServers"]["spindoctor-qwerty"]["env"].update(PLUGIN_ROOT="/x"))))
    hits.append(variant(lambda d: jedit(d, "mcp.json", lambda j: j["mcpServers"]["spindoctor-qwerty"].update(command="../python3"))))
    def skname(d):
        p = os.path.join(d, "skills/spindoctor-qwerty/SKILL.md"); s = open(p).read(); open(p, "w").write(s.replace("name: spindoctor-qwerty", "name: spindoctor", 1))
    hits.append(variant(skname))
    shutil.rmtree(base, ignore_errors=True)
    T("Vibe's validator flags 5 broken variants (1.0's frontmatter-less KNOWLEDGE.md, reserved namespace 'vibe', env PLUGIN_ROOT, ../ command, skill name != folder)",
      all(hits), hits)


# ---------------------------------------------------------------- real Vibe
def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


class Host:
    def __init__(self, vibe, source):
        self.vibe = vibe; self.home = tempfile.mkdtemp(prefix="sdq_vibe_"); self.proj = os.path.join(self.home, "proj"); os.makedirs(self.proj)
        self.port = free_port(); self.log = os.path.join(self.home, "stub.jsonl"); self.script = os.path.join(self.home, "script.json")
        self.env = dict(os.environ, HOME=self.home, USERPROFILE=self.home); self.env.pop("SPINDOCTOR_WORKSPACE", None); self.env.pop("MISTRAL_API_KEY", None)
        os.makedirs(os.path.join(self.home, ".vibe", "plugins"))
        open(os.path.join(self.home, ".vibe", "config.toml"), "w").write(
            'active_model = "stub"\nenable_telemetry = false\n\n[[providers]]\nname = "llamacpp"\napi_base = "http://127.0.0.1:%d/v1"\napi_key_env_var = ""\n\n'
            '[[models]]\nname = "stub"\nprovider = "llamacpp"\nalias = "stub"\n' % self.port)
        src = source or ROOT
        if re.match(r"https://github\.com/", src):
            tmp = os.path.join(self.home, "clone"); subprocess.run(["git", "clone", "-q", "--depth", "1", src, tmp], check=True); src = tmp
        self.src = src
        self.plugin = os.path.join(self.home, ".vibe", "plugins", "spindoctor-qwerty")
        shutil.copytree(src, self.plugin, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", "e2e_results.json", "host_check.json"))
        self.stub = None

    def run(self, steps, prompt="use spindoctor", extra=(), cwd=None):
        if self.stub: self.stub.terminate(); self.stub.wait()
        json.dump(steps, open(self.script, "w")); open(self.log, "w").close()
        self.stub = subprocess.Popen([sys.executable, os.path.join(HERE, "stub_llm.py"), str(self.port), self.log, self.script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(50):
            try: socket.create_connection(("127.0.0.1", self.port), 0.2).close(); break
            except OSError: time.sleep(0.1)
        p = subprocess.run([self.vibe, "-p", prompt] + list(extra), cwd=cwd or self.proj, env=self.env, capture_output=True, text=True, timeout=900)
        recs = [json.loads(l) for l in open(self.log) if l.strip()]
        return p, recs

    def close(self):
        if self.stub: self.stub.terminate(); self.stub.wait()
        for d, ds, fs in os.walk(self.home):  # Vibe's pinned package store is read-only
            for x in ds + fs:
                try: os.chmod(os.path.join(d, x), 0o755)
                except OSError: pass
        shutil.rmtree(self.home, ignore_errors=True)


def tree(root):
    return sorted(os.path.relpath(os.path.join(d, f), root) for d, _, fs in os.walk(root) for f in fs)


def ts(tool, args):
    return {"tool": "run_typescript", "args": {"code": "async function main() { return await tools.%s.%s(%s); }" % (NS, tool, json.dumps(args))}}


def results(recs):
    return recs[-1]["tool_results"] if recs else []


def hosted(vibe, source):
    h = Host(vibe, source)
    try:
        before = tree(h.plugin)
        sk_th = "$SKILLDIR/examples/theory/hadamard_theory.txt"
        steps = [{"tool": "search_tool_functions", "args": {"mode": "best_match", "query": "spindoctor quantum circuit"}},
                 {"tool": "search_tool_functions", "args": {"mode": "details", "functions": [NS + ".spindoctor_test_theory"]}},
                 ts("spindoctor_functions", {}),
                 ts("spindoctor_run_script", {"script": "q.circuit new bell 2\nq.circuit add h 0\nq.circuit add cx 0 1\nq.circuit run shots 1000 basis z"}),
                 ts("spindoctor_run_preset", {"preset_id": "qc-001"}),
                 ts("spindoctor_list_presets", {"filter": "ghz"}),
                 ts("spindoctor_report", {}),
                 ts("spindoctor_run_script", {"script": "q.circuit new big 298\nq.circuit add h 0\nq.circuit add mcx7 0 1 2 3 4 5 6 297\nq.circuit run shots 64 basis z"}),
                 ts("spindoctor_test_theory", {"action": "extract", "source": "file", "path": sk_th}),
                 ts("spindoctor_test_theory", {"action": "run", "source": "chat", "text": "From our chat: H then CX makes a Bell state.",
                    "excerpts": ["User: does H then CNOT give 50/50 on 00 and 11?", "Assistant: yes, that is a Bell state."],
                    "hypothesis": "H(0) then CX(0,1) gives P(00) = P(11) = 0.5", "prediction": "P(11) = 0.5 +/- 0.05 over 4000 shots",
                    "script": "q.circuit new bt 2\nq.circuit add h 0\nq.circuit add cx 0 1\nq.circuit run shots 4000 basis z",
                    "checks": [{"kind": "probability", "outcome": "11", "expected": 0.5, "tolerance": 0.05}]}),
                 {"tool": "skill", "args": {"name": SKILL}},
                 {"tool": "bash", "args": {"command": "cd '$SKILLDIR' && python3 scripts/spindoctor_cli.py run 'q.circuit new b 2' 'q.circuit add h 0' 'q.circuit add cx 0 1' 'q.circuit run shots 100 basis z'"}},
                 {"text": "SpinDoctor done."}]
        p, recs = h.run(steps, extra=["--auto-approve"])
        res = results(recs); sysmsg = (recs[0]["system"] if recs else "") or ""
        T("real Vibe -p session ran to the end with the stub model (%d model requests, exit %s)" % (len(recs), p.returncode),
          p.returncode == 0 and "SpinDoctor done." in p.stdout and len(res) == len(steps) - 1, (p.stdout[-300:], p.stderr[-300:], len(res)))
        if len(res) < len(steps) - 1: return
        m = re.search(r"<path>([^<]+)</path>", sysmsg[sysmsg.find("<name>spindoctor-qwerty</name>"):])
        T("system prompt lists the plugin (spindoctor-qwerty) and its skill %s from Vibe's pinned copy" % SKILL,
          "<name>spindoctor-qwerty</name>" in sysmsg and "<name>%s</name>" % SKILL in sysmsg and m and "/plugins/packages/" in m.group(1))
        T("search_tool_functions finds all 6 tools in connector %s" % NS, all("%s.%s" % (NS, t) in res[0] for t in TOOLS), res[0][:400])
        T("details mode returns the spindoctor_test_theory declaration (source file/text/chat)", "spindoctor_test_theory" in res[1] and "chat" in res[1], res[1][:300])
        T("run_typescript -> spindoctor_functions: the Markdown function table", "| Function | What it does | Command to type |" in res[2], res[2][:200])
        ws = os.path.join(h.home, "spindoctor-workspace")
        T("run_typescript -> spindoctor_run_script: Bell ok, reports in ~/spindoctor-workspace (1.0 put them in a per-session PLUGIN_DATA folder)", OK(res[3]) and ws in res[3], res[3][:300])
        T("run_typescript -> spindoctor_run_preset qc-001", OK(res[4]) and "qc-001" in res[4], res[4][:200])
        T("run_typescript -> spindoctor_list_presets ghz", OK(res[5]) and "ghz" in res[5].lower(), res[5][:200])
        T("run_typescript -> spindoctor_report lists reports", OK(res[6]) and ".txt" in res[6], res[6][:200])
        T("run_typescript -> 298-qubit wide register with mcx7 (3.1.2 parity)", OK(res[7]), res[7][:200])
        T("run_typescript -> theory extract from an absolute path in the pinned skill folder", OK(res[8]), res[8][:200])
        pdf = re.findall(r'([^"\\\s]+theory[^"\\\s]*\.pdf)', res[9])
        T("run_typescript -> theory from the chat: supported, 2 excerpts, PDF written", "supported" in res[9] and "excerptsRecorded" in res[9]
          and pdf and os.path.isfile(pdf[0]) and open(pdf[0], "rb").read(5) == b"%PDF-", res[9][:300])
        T("skill tool loads %s (SKILL.md body: guardrail + run_typescript instructions)" % SKILL, "not a" in res[10] and "run_typescript" in res[10], res[10][:200])
        T("bash fallback from the skill folder runs the CLI (Bell, ok)", OK(res[11]) or '"ok": true' in res[11], res[11][-300:])
        T("installed plugin folder unchanged by tool use and the CLI fallback (Vibe pins its content digest)", tree(h.plugin) == before, set(tree(h.plugin)) ^ set(before))
        # second session: the pin must still match
        p2, recs2 = h.run([ts("spindoctor_functions", {}), {"text": "again"}], extra=["--auto-approve"])
        T("second session after tool use: plugin re-pins cleanly (no plugin_pin_mismatch) and the tool works", p2.returncode == 0 and "again" in p2.stdout
          and "| Function |" in "".join(results(recs2)), (p2.stdout[-200:], p2.stderr[-200:]))
        # default agent, programmatic: MCP calls need approval and -p cannot ask
        p3, recs3 = h.run([ts("spindoctor_functions", {}), {"text": "denied"}])
        T("without --auto-approve, -p denies the MCP call (tool_denied) - Vibe asks before plugin tools run", "tool_denied" in "".join(results(recs3)), results(recs3))
        # why mcp.json and the scripts never write bytecode: Vibe starts the server from the user's plugin folder while it pins a
        # content digest of that folder, so a __pycache__ written then makes the session fail (1.0 hit this on its first session)
        h2 = Host(h.vibe, h.src if source else None)
        try:
            mj = os.path.join(h2.plugin, "mcp.json"); j = json.load(open(mj)); j["mcpServers"]["spindoctor-qwerty"]["env"].pop("PYTHONDONTWRITEBYTECODE", None); json.dump(j, open(mj, "w"))
            sm = os.path.join(h2.plugin, "skills", "spindoctor-qwerty", "scripts", "spindoctor_mcp.py"); t = open(sm).read(); open(sm, "w").write(t.replace("sys.dont_write_bytecode = True", "pass"))
            p4, _ = h2.run([{"text": "x"}])
            pyc = [d for d, ds, fs in os.walk(h2.plugin) if d.endswith("__pycache__")]
        finally:
            h2.close()
        T("host quirk reproduced: without the bytecode guards (1.0's setup) the FIRST session fails with plugin_pin_mismatch and a __pycache__ appears in the plugin folder",
          "plugin_pin_mismatch" in (p4.stdout + p4.stderr) and pyc, ((p4.stdout + p4.stderr)[-200:], pyc[:1]))
        # knowledge: validated above; record whether this Vibe could mount it
        mounted = "<available-knowledge-folders>" in sysmsg and SKILL in sysmsg.split("<available-knowledge-folders>")[-1]
        left = [d for d, ds, fs in os.walk(os.path.join(h.home, ".vibe")) for x in ds if x.startswith(".spindoctor-qwerty-")]
        T("knowledge folder: mounted, or (Vibe 2.26.1 on Linux) not mounted because Vibe copies it from its read-only pinned store and cannot rename the copy",
          mounted or bool(left), "mounted" if mounted else "not mounted; leftover temp copy: %s" % bool(left))
        # project scope: .vibe/plugins in a trusted project
        proj2 = os.path.join(h.home, "proj2"); os.makedirs(os.path.join(proj2, ".vibe", "plugins"))
        shutil.move(h.plugin, os.path.join(proj2, ".vibe", "plugins", "spindoctor-qwerty"))
        p5, recs5 = h.run([ts("spindoctor_run_preset", {"preset_id": "qc-002"}), {"text": "project"}], extra=["--auto-approve", "--trust"], cwd=proj2)
        T("project scope: .vibe/plugins/spindoctor-qwerty in a trusted project (--trust) loads and runs qc-002", p5.returncode == 0 and OK("".join(results(recs5))),
          (p5.stdout[-200:], results(recs5)))
        shutil.move(os.path.join(proj2, ".vibe", "plugins", "spindoctor-qwerty"), h.plugin)
        # shared end-to-end suite against the server exactly as mcp.json starts it
        out = os.path.join(HERE, "e2e_results.json")
        rr = subprocess.run([sys.executable, os.path.join(HERE, "e2e_mcp.py"), "--server", "python3", os.path.join(h.plugin, "skills", "spindoctor-qwerty", "scripts", "spindoctor_mcp.py"),
                             "--examples", os.path.join(h.plugin, "skills", "spindoctor-qwerty", "examples", "theory"), "--out", out], env=h.env, cwd=h.plugin, capture_output=True, text=True, timeout=3600)
        last = [l for l in rr.stdout.splitlines() if l.strip()][-1:] or [""]
        T("shared end-to-end suite against the server as mcp.json starts it: " + last[0][:60], rr.returncode == 0, rr.stdout[-400:])
    finally:
        h.close()


def main():
    a = sys.argv[1:]; opt = dict(zip(a[::2], a[1::2]))
    vibe = opt.get("--vibe") or shutil.which("vibe")
    if not vibe or not (os.path.isfile(vibe) and os.access(vibe, os.X_OK)):
        print("Mistral Vibe not found: pip install mistral-vibe (Python 3.12+), then pass --vibe PATH"); return 2
    vpy = vibe_python(vibe)
    ver = subprocess.run([vibe, "--version"], capture_output=True, text=True).stdout.strip()
    static(vpy); hosted(vibe, opt.get("--source"))
    json.dump({"python": sys.version.split()[0], "vibe": ver, "checks": R}, open(opt.get("--out", os.path.join(HERE, "host_check.json")), "w"), indent=1)
    n = sum(r["pass"] for r in R); print("%s: %d/%d passed" % (ver, n, len(R))); return 0 if n == len(R) else 1


if __name__ == "__main__":
    sys.exit(main())
