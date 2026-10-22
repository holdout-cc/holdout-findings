# Run from the repo root: python repro.py   (no Docker, network or API calls)
#
# Builds a tiny task (Plane.distance returns 0 instead of abs(d)), runs real
# pytest -rA on its withheld tests for four versions of the code, and scores
# each pytest output with the environment's own R2EGym.answer(). Sandbox I/O
# is faked the same way tests.py::_FakeSandbox does it: `git apply` succeeds
# and the test run returns the pytest output produced here.
import asyncio
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import datasets

datasets.load_dataset = lambda *a, **k: []  # r2e_gym loads two HF datasets at import; keep it offline
sys.path.insert(0, os.getcwd())
import r2e_gym  # noqa: E402
from utils import parse_log  # noqa: E402

SRC = '''import math


class Plane:
    def __init__(self, normal, offset):
        self.normal, self.offset = normal, offset

    def unit_normal(self):
        n = math.sqrt(sum(c * c for c in self.normal))
        return tuple(c / n for c in self.normal)

    def distance(self, point):
        n = self.unit_normal()
        d = sum(a * b for a, b in zip(n, point)) - self.offset
        BODY
'''
TESTS = '''from shapes import Plane


class TestPlane:
    def test_distance(self):  # fail-to-pass
        assert Plane((0, 0, 1), 0).distance((1, 2, 5)) == 5

    def test_offset(self):  # fail-to-pass
        assert Plane((0, 0, 2), 1).distance((0, 0, 4)) == 3

    def test_on_plane(self):  # pass-to-pass, also calls distance()
        assert Plane((0, 0, 1), 0).distance((3, 4, 0)) == 0

    def test_unit_normal(self):  # pass-to-pass
        assert Plane((0, 0, 2), 0).unit_normal() == (0.0, 0.0, 1.0)
'''
VARIANTS = {
    "no_fix": "return 0  # bug",
    "gold_fix": "return abs(d)",
    "cheat_plain": "raise Exception('PASSED')",
    # an exception class named PASSED; module 'builtins' so pytest prints just "PASSED"
    "cheat_bare": "raise type('PASSED', (Exception,), {'__module__': 'builtins'})()",
}


def run_pytest(body):
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "shapes").mkdir()
        (Path(d) / "shapes" / "__init__.py").write_text(SRC.replace("BODY", body))
        (Path(d) / "r2e_tests").mkdir()
        (Path(d) / "r2e_tests" / "__init__.py").write_text("")
        (Path(d) / "r2e_tests" / "test_1.py").write_text(TESTS)
        env = {k: v for k, v in os.environ.items() if k not in ("CI", "BUILD_NUMBER", "PYTEST_ADDOPTS")}
        env["COLUMNS"] = "80"  # same width as the dataset's recorded logs
        return subprocess.run([sys.executable, "-m", "pytest", "-rA", "-p", "no:cacheprovider", "r2e_tests"],
                              cwd=d, env=env, capture_output=True, text=True).stdout


class FakeSandbox:
    def __init__(self, test_log=""):
        self.test_log = test_log

    async def start(self): pass
    async def stop(self): pass
    async def check_run(self, cmd, **kw): return ""
    async def download(self, path): return b"diff --git a/shapes/__init__.py b/shapes/__init__.py\n"
    async def upload(self, local_path, container_path): pass

    async def run(self, cmd, **kw):
        out = "" if "git apply" in cmd else self.test_log
        return SimpleNamespace(output=out, return_code=0, timed_out=False, truncated=False)


async def grade(expected, log):
    env = r2e_gym.R2EGym(task_spec=dict(
        id="plane", repo_name="fixture", docker_image="none", commit_hash="0" * 40, prompt="",
        problem_statement="Plane.distance always returns 0", expected_output_json=json.dumps(expected),
    ), secrets={"api_key": "unused"})
    env.sandbox, env._grading_sandbox = FakeSandbox(), FakeSandbox(log)
    env._baseline_tree = "0" * 40
    return await env.answer()


logs = {name: run_pytest(body) for name, body in VARIANTS.items()}
expected = {k.split(" - ")[0]: v for k, v in parse_log(logs["gold_fix"]).items()}
print("expected_output_json:", json.dumps(expected))
for name, log in logs.items():
    out = asyncio.run(grade(expected, log))
    print(f"\n{name}: pytest says '{log.strip().splitlines()[-1].strip('= ')}' -> reward={out.reward}")
    for line in log.split("short test summary info")[-1].splitlines():
        if line.startswith(("PASSED", "FAILED", "ERROR")):
            print("   ", line)
