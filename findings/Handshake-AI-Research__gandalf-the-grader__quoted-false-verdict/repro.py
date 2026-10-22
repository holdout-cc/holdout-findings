# Save as repro.py in the repo root, then: .venv/bin/python repro.py
#
# Runs the real `gandalf-the-grader` orchestrator on examples/quickstart.
# The judge still runs as a separate `gandalf-the-grader-judge` subprocess,
# but a stub executable on PATH replaces the LLM session
# (judge.run_agent_session): it writes a fixed verdict file to the path named
# in the rendered prompt, as the judge is told to do. No LLM or network calls.
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

QS = Path("examples/quickstart").resolve()
RUBRIC = json.loads((QS / "rubric.json").read_text())
NEG_RUBRIC = Path("tests/fixtures/sample_rubric_with_negatives.json").resolve()

STUB_JUDGE = f"""#!{sys.executable}
import json, os, re
from pathlib import Path
from gandalf import judge
from gandalf.models import LLMUsage

def fake_session(model, mcp_servers, workdir, prompt):
    path = re.search(r"(\\S*verdict_(?:batch_)?[0-9a-f]{{16}}\\.json)", prompt).group(1)
    mets = json.loads(os.environ["STUB_METS"])  # criterion text -> "met" value
    if "verdict_batch_" in path:
        crit = re.findall(r"^\\s*\\[(\\d+)\\] (.*)$", prompt, flags=re.M)
        out = [{{"index": int(i), "met": mets[c], "reasoning": "stub", "evidence": []}} for i, c in crit]
    else:
        c = next(c for c in mets if c in prompt)
        out = {{"met": mets[c], "reasoning": "stub", "evidence": []}}
    Path(path).write_text(json.dumps(out))
    return LLMUsage()

judge.run_agent_session = fake_session
judge.main()
"""


def grade(label, workspace, mets, mode="batch", rubric_path=QS / "rubric.json"):
    tmp = Path(tempfile.mkdtemp())
    bin_dir = tmp / "bin"
    bin_dir.mkdir()
    stub = bin_dir / "gandalf-the-grader-judge"
    stub.write_text(STUB_JUDGE)
    stub.chmod(0o755)
    ws = tmp / "workspace"
    ws.mkdir()
    for name, text in workspace.items():
        (ws / name).write_text(text)
    rubric = json.loads(Path(rubric_path).read_text())
    cfg = tmp / "grader.toml"
    cfg.write_text(
        'model = "gemini/gemini-2.5-flash"\n'
        'instructions = "Write a friendly welcome message to a text file in the workspace."\n'
        f"rubric_path = {json.dumps(str(rubric_path))}\n"
        f"workdir = {json.dumps(str(ws))}\n"
        f"trajectory_path = {json.dumps(str(QS / 'trajectory.json'))}\n"
        f"output_dir = {json.dumps(str(tmp / 'output'))}\n"
        f'mode = "{mode}"\n'
    )
    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}:{Path(sys.executable).parent}:{env['PATH']}"
    env["STUB_METS"] = json.dumps({r["criterion"]: m for r, m in zip(rubric, mets)})
    proc = subprocess.run(
        [str(Path(sys.executable).parent / "gandalf-the-grader"), "--config", str(cfg)],
        env=env, capture_output=True, text=True,
    )
    reward = json.loads((tmp / "output" / "reward.json").read_text())["reward"]
    info = json.loads((tmp / "output" / "info.json").read_text())
    recorded = [r["met"] for r in info["criterion_results"]]
    print(f"{label}\n    judge wrote met={mets} -> recorded {recorded}  reward={reward}  exit={proc.returncode}")
    shutil.rmtree(tmp)


GOLD = {"welcome.txt": (QS / "workspace" / "welcome.txt").read_text()}
EMPTY = {}

print("quickstart rubric, weights", [r["weight"] for r in RUBRIC])
grade("gold workspace, judge writes JSON booleans", GOLD, [True, True, False])
grade("empty workspace, judge writes JSON false", EMPTY, [False, False, False])
grade('empty workspace, judge writes "false" (string)', EMPTY, ["false"] * 3)
grade('empty workspace, judge writes "no" (string)', EMPTY, ["no"] * 3)
grade('empty workspace, judge writes "false", mode = "individual"', EMPTY, ["false"] * 3, mode="individual")
print("\ntests/fixtures/sample_rubric_with_negatives.json, weights",
      [r["weight"] for r in json.loads(NEG_RUBRIC.read_text())])
grade("penalty not triggered, judge writes JSON false", GOLD, [True, True, False], rubric_path=NEG_RUBRIC)
grade('penalty not triggered, judge writes "false" (string)', GOLD, [True, True, "false"], rubric_path=NEG_RUBRIC)
