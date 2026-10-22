# Run from the repo root: uv run python repro.py  (no Docker, network or LLM calls)
import os
import re
import shlex
import shutil
import subprocess
import tempfile
from functools import partial
from pathlib import Path
from types import SimpleNamespace

import yaml

os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")  # keep litellm's import offline

from tolokaforge.core.compose_materialisation import copy_compose_context
from tolokaforge.core.grading.kinds.test_execution import TestExecutionGraderKind
from tolokaforge.core.grading.substrate import InProcessGradingSubstrate
from tolokaforge.runner.service import RunnerServiceImpl
from tolokaforge_adapter_terminal_bench.adapter import TerminalBenchAdapter

TMP = Path(tempfile.mkdtemp())


def adapter(root, task_id):
    return TerminalBenchAdapter({"terminal_bench_dir": str(root), "task_ids": [task_id],
                                 "staging_root": str(TMP / "staging" / task_id)})


# 1) The shipped tasks: the agent's own container gets ./tests:/tests (no :ro), and the
#    test_execution grading has no `service`, so the suite runs in that same container.
for task_id in ["fix-billing-holds", "fix-airline-segmentation"]:
    a = adapter("examples/terminal_bench", task_id)
    env = a._environment(task_id)
    vols = yaml.safe_load(env.compose_file.read_text())["services"][env.agent_service]["volumes"]
    g = a.to_task_description(task_id).grading
    print(f"{task_id}: agent volumes {vols}, {g.grading_method}, "
          f"service={(g.grading_method_config or {}).get('service')}")

# 2) A tiny task in the same shape whose suite needs no Postgres, so it can really run.
task = TMP / "tasks" / "fix-add"
(task / "environment" / "app").mkdir(parents=True)
(task / "tests").mkdir()
(task / "task.yaml").write_text("instruction: Fix add() in /app/calc.py.\n")
(task / "docker-compose.yaml").write_text(
    "services:\n  main:\n    build: {context: ./environment}\n    command: [sleep, infinity]\n")
(task / "environment" / "Dockerfile").write_text("FROM python:3.12-slim\nCOPY app /app\n")
(task / "environment" / "app" / "calc.py").write_text("def add(a, b):\n    return a - b\n")
(task / "tests" / "test.sh").write_text(
    "#!/bin/bash\nmkdir -p /logs/verifier\n"
    "python3 -c 'import sys; sys.path.insert(0, \"/app\"); from calc import add; "
    "print(1.0 if add(2, 3) == 5 else 0.0)' > /logs/verifier/reward.txt\n")


class AgentContainer:
    """Stands in for `docker exec` into the agent container. Its /tests and /logs are the
    per-trial context's tests/ and _logs/ (the bind mounts above); /app is the image's code."""

    def __init__(self, ctx, app):
        self.paths = {"/tests": str(ctx / "tests"), "/logs": str(ctx / "_logs"), "/app": str(app)}

    def _map(self, text):
        return re.sub(r"(?<![\w.])/(tests|logs|app)\b", lambda m: self.paths[m[0]], text)

    def exec_in_env_with_exit_code(self, command, timeout_s):
        cmd = self._map(command)
        # `bash X.sh` runs the script as it is on the mount now, with its paths mapped too.
        cmd = re.sub(r"bash (\S+\.sh)",
                     lambda m: "bash -c " + shlex.quote(self._map(Path(m[1]).read_text())), cmd)
        p = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, timeout=timeout_s)
        return p.returncode, p.stdout + p.stderr

    def exec_in_env(self, command, timeout_s):
        return self.exec_in_env_with_exit_code(command, timeout_s)[1]


runner = RunnerServiceImpl(db_client=None)


def trial(n, label, agent_command):
    a = adapter(TMP / "tasks", "fix-add")
    desc = a.to_task_description("fix-add")
    ctx = TMP / "trials" / str(n)  # per-trial copy of the staged context, as provisioning does
    copy_compose_context(a._environment("fix-add").compose_file, ctx)
    app = shutil.copytree(task / "environment" / "app", TMP / "app" / str(n))
    box = AgentContainer(ctx, app)
    if agent_command:  # the agent's whole turn: one bash tool call in its container
        box.exec_in_env_with_exit_code(agent_command, 30)
    runner.trials["t1"] = SimpleNamespace(agent_tools={"bash": box})
    substrate = InProcessGradingSubstrate(
        db_reader=None, knowledge_search=None, filesystem_root=None,
        run_test_suite_impl=partial(runner._run_test_suite_via_agent_tools, trial_id="t1"))
    g = TestExecutionGraderKind().evaluate(
        substrate=substrate, task_config=desc.grading,
        kind_config=desc.grading.grading_method_config, trial_id="t1", agent_tools={}, logger=None)
    result = box.exec_in_env("python3 -c 'import sys; sys.path.insert(0, \"/app\"); "
                             "from calc import add; print(add(2, 3))'", 30).strip()
    print(f"{label:42} add(2, 3)={result}  score={g.score:.2f} pass={g.binary_pass}")


trial(1, "do nothing", None)
trial(2, "correct fix", "sed -i 's/a - b/a + b/' /app/calc.py")
trial(3, "rewrite /tests/test.sh, app untouched",
      "echo 'echo 1.0 > /logs/verifier/reward.txt' > /tests/test.sh")
