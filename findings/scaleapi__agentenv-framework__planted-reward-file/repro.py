"""RunContainerUnitTestsVerifierTaskStep in reward mode scores a reward file that was
already in the container before the verifier ran, even when the verifier exits non-zero.

Drives the real RunContainerUnitTestsVerifierTaskStep.execute(). Only the sandbox is
replaced: the task container's filesystem is a temp directory, and the command string the
step builds is run with real bash (paths are prefixed with $ROOT). No Docker, no network,
no LLM. `grep -qx 42 answer.txt` stands in for pytest.

Usage (from the repo root):  uv run python repro.py
"""
from __future__ import annotations

import asyncio
import os
import shlex
import shutil
import subprocess
import tempfile
import types
from pathlib import Path

STATE = Path(tempfile.mkdtemp(prefix="repro-state-"))
os.chdir(STATE)
os.environ["AGENT_ENV_OBJECT_STORE"] = "local"
os.environ["AGENT_ENV_DOCUMENT_STORE"] = "local"
for k in ("LITELLM_API_KEY", "LITELLM_BASE_URL"):
    os.environ.pop(k, None)

from agent_env.config import configure  # noqa: E402
from agent_env.providers.sandbox_providers import sandbox_provider  # noqa: E402
from agent_env.task_step.context import DeployedSandbox, TaskStepContext  # noqa: E402
from agent_env.task_step.task_steps.verifiers.run_container_unit_tests_verifier import (  # noqa: E402
    RunContainerUnitTestsVerifierTaskStep as Step,
)

configure()

REWARD = "/logs/verifier/reward.txt"

TEST_SH = {
    # fail-fast script: writes the reward only after the tests pass
    "set -e": 'set -e\ngrep -qx 42 "$ROOT/app/answer.txt"\necho 1 > "$ROOT/logs/verifier/reward.txt"\n',
    # writes the reward only on success, relying on "missing reward file = 0"
    "pass-only write": 'grep -qx 42 "$ROOT/app/answer.txt" && echo 1 > "$ROOT/logs/verifier/reward.txt"\n',
    # always writes 0 or 1 (control: the planted file is overwritten)
    "if/else always writes": 'if grep -qx 42 "$ROOT/app/answer.txt"; then echo 1 > "$ROOT/logs/verifier/reward.txt"; '
                             'else echo 0 > "$ROOT/logs/verifier/reward.txt"; fi\n',
}


class FakeSandbox:
    """A VM with one task container, backed by two temp dirs."""

    type = "local"

    def __init__(self, root: Path, vm: Path):
        self.root, self.vm = root, vm

    def scoped_name(self, name):
        return name

    def _vm(self, p):
        return self.vm / p.lstrip("/")

    async def exec_script(self, script, *, max_retries=0):
        parts = shlex.split(script)
        if parts[:2] == ["rm", "-f"]:
            self._vm(parts[2]).unlink(missing_ok=True)
        return ""

    async def exec_with_output(self, *args):
        if args[:2] == ("sudo", "cat"):
            p = self._vm(args[2])
            return (0, p.read_text(), "") if p.exists() else (1, "", "No such file")
        # ("sudo", "bash", "-c", "docker exec ... timeout ... bash -c <command>")
        inner = shlex.split(args[3])[-1]  # the command string the step built
        p = subprocess.run(["bash", "-c", inner], env={**os.environ, "ROOT": str(self.root)},
                           capture_output=True, text=True)
        return p.returncode, p.stdout, p.stderr

    async def docker_cp(self, source, destination, *, remove_source=False):
        src = self.root / source.split(":", 1)[1].lstrip("/")
        if not src.exists():
            raise RuntimeError(f"docker cp: no such file {source}")
        dst = self._vm(destination)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)


def run_case(variant: str, answer: str, plant: bool) -> dict:
    base = Path(tempfile.mkdtemp(prefix="repro-"))
    root, vm = base / "container", base / "vm"
    for d in ("tests", "app", "logs/verifier"):
        (root / d).mkdir(parents=True)
    vm.mkdir()
    (root / "tests/test.sh").write_text(TEST_SH[variant])
    # The agent's turn: it writes its answer and, in the exploit case, a reward file.
    (root / "app/answer.txt").write_text(answer + "\n")
    if plant:
        (root / "logs/verifier/reward.txt").write_text("1\n")

    sandbox = FakeSandbox(root, vm)
    sandbox_provider.build_sandbox_provider = lambda _t: types.SimpleNamespace(
        get_sandbox=lambda _id: asyncio.sleep(0, result=sandbox))
    ctx = TaskStepContext(deployed_sandboxes=[DeployedSandbox(
        sandbox_name="h", sandbox_id="local-x", sandbox_mode="vm", sandbox_type="local", tunnel_urls={})])
    ctx.metadata["deployed_docker_containers"] = [{"container_name": "task", "sandbox_name": "h"}]
    step = Step(id="verify", version=None, sandbox_name="h", container_name="task",
                command='bash "$ROOT/tests/test.sh"', reward_path=REWARD)
    # Skip the stdout/stderr artifact upload; it does not affect scoring.
    Step._upload_text_artifact = staticmethod(lambda text, artifact_id, description, object_url:
                                              types.SimpleNamespace(id=artifact_id, version=1, object_url=object_url))
    raised = None
    try:
        asyncio.run(step.execute(ctx))
    except Exception as e:
        raised = f"{type(e).__name__}: {e}"
    v = ctx.metadata["verifications"]["verify"]
    return {"score": v["score"], "result": v["results"][0]["result"], "exit_code": v["exit_code"],
            "raised": raised}


def main():
    cases = [
        ("correct answer (42)", "42", False),
        ("wrong answer (41)", "41", False),
        ("wrong answer (41) + planted reward.txt=1", "41", True),
    ]
    for variant in TEST_SH:
        print(f"\n=== test.sh: {variant} ===")
        for label, answer, plant in cases:
            r = run_case(variant, answer, plant)
            print(f"  {label:42s} -> score={r['score']} result={r['result']} "
                  f"exit_code={r['exit_code']} raised={r['raised']}")


if __name__ == "__main__":
    main()
