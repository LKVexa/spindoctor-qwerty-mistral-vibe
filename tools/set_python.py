#!/usr/bin/env python3
# SpinDoctor Qwerty 1.1.0 - SpinDoctor Qwerty plugin for Mistral Vibe: choose how mcp.json starts Python
# Copyright (C) 2026 RUSSELL PHILIP SMITHSON <russellsmithson77@outlook.com>
# SPDX-License-Identifier: GPL-3.0-or-later
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version. It is distributed WITHOUT ANY WARRANTY; see the LICENSE file for details.
"""mcp.json starts the server with `python3`, which many Windows PCs do not have. Run this once in the installed plugin folder:

  py -3 tools\\set_python.py            # pick the first that works: py -3, python, python3 (Windows) / python3, python
  py -3 tools\\set_python.py py         # or name one: py | python | python3
  python3 tools/set_python.py --show    # print what mcp.json uses now

Agent Plugins needs `command` to be one executable name, so `py -3` is written as command "py" with "-3" as the first argument.
Then type /reload-plugins in Vibe (or start a new session). Only mcp.json changes."""
import json, os, shutil, subprocess, sys
sys.dont_write_bytecode = True
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); MCP = os.path.join(ROOT, "mcp.json"); SID = "spindoctor-qwerty"
SERVER = "${PLUGIN_ROOT}/skills/spindoctor-qwerty/scripts/spindoctor_mcp.py"
CHOICES = {"py": ["py", "-3"], "python": ["python"], "python3": ["python3"]}


def works(argv):
    if not shutil.which(argv[0]): return False
    try: r = subprocess.run(argv + ["-c", "import sys; print(sys.version_info[0])"], capture_output=True, text=True, timeout=20)
    except Exception: return False
    return r.returncode == 0 and r.stdout.strip() == "3"  # the Windows Store "python" alias exists but prints nothing


def main(a):
    c = json.load(open(MCP, encoding="utf-8")); s = c["mcpServers"][SID]
    if a[:1] == ["--show"]: print(" ".join([s["command"]] + s.get("args", []))); return 0
    if a:
        if a[0] not in CHOICES: print("choose one of: py, python, python3"); return 2
        pick = CHOICES[a[0]]
    else:
        order = ["py", "python", "python3"] if os.name == "nt" else ["python3", "python"]
        pick = next((CHOICES[k] for k in order if works(CHOICES[k])), None)
        if not pick: print("No working Python 3 found (tried %s). Install Python 3.8+ from python.org." % ", ".join(order)); return 1
    s["command"] = pick[0]; s["args"] = pick[1:] + [SERVER]
    open(MCP, "w", encoding="utf-8", newline="\n").write(json.dumps(c, indent=2) + "\n")
    print("mcp.json now starts: " + " ".join([s["command"]] + s["args"]) + "\nType /reload-plugins in Vibe (or start a new session).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
