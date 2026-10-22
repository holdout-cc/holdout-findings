# Save as repro.py in the repo root and run it with the coding env's dependencies installed:
#   python repro.py
# Uses the real coding-task template (TaskRunner.start -> agent edit -> TaskRunner.grade),
# the shipped flask.bundle and hidden test patches, grader.grade_tests, Grade.from_dict and Job.
# Only the sandbox is stubbed: workspace.run runs the task's own test command with local bash
# instead of inside bwrap. No network, no model calls.
import asyncio
import os
import subprocess
import sys
from dataclasses import dataclass

sys.path.insert(0, "environments/coding")
import env as coding_env  # noqa: E402
import tasks as coding_tasks  # noqa: E402
from hud.environment.server import TaskRunner  # noqa: E402
from hud.eval.job import Job  # noqa: E402
from hud.eval.run import Grade, Run  # noqa: E402

# The agent's whole "solution": two lines at the top of the package the hidden tests import.
CHEAT = 'import os as _o, sys as _s\nif "pytest" in _s.modules: _o._exit(0)\n'


@dataclass
class Proc:
    returncode: int
    stdout: bytes
    stderr: bytes
    timed_out: bool = False


class LocalWorkspace:
    """Stand-in for the bwrap sandbox: same cwd, same command, same env vars."""

    root = coding_env.REPO_DIR

    async def terminate_sessions(self):
        pass

    async def discard_sandbox(self):
        pass

    async def run(self, argv, cwd, env, max_wait, scope):
        done = subprocess.run(argv, cwd=cwd, env={**os.environ, **env}, capture_output=True, timeout=max_wait)
        return Proc(done.returncode, done.stdout, done.stderr)


coding_env.workspace = LocalWorkspace()
coding_env.REPO_DIR.mkdir(parents=True, exist_ok=True)


def git(*args):
    return subprocess.run(["git", "-C", str(coding_env.BASELINE_DIR), *args], capture_output=True, check=True).stdout


def golden(task):  # the bundle's own reference fix (refs/heads/flask_*_golden)
    base = task.args["base_ref"]
    ref = base.replace("_baseline", "_golden")
    for rel in git("diff", "--name-only", base, ref).decode().split():
        (coding_env.REPO_DIR / rel).write_bytes(git("show", f"{ref}:{rel}"))


def honest(task):  # agent fails: leaves the repo as it found it
    pass


def cheat(task):  # agent fails, then makes the hidden test run exit before it writes JUnit XML
    init = coding_env.REPO_DIR / "src" / "flask" / "__init__.py"
    init.write_text(CHEAT + init.read_text())


async def grade(task, edit):
    runner = TaskRunner(coding_env.env.templates[task.id], task.args)
    await runner.start()  # clones the bundle, checks out base_ref, returns the prompt
    edit(task)
    frame = await runner.grade({})  # restores tests/, applies the hidden patch, runs pytest
    run = Run(None, task.id, {})
    run.grade = Grade.from_dict(frame)
    print(
        f"{task.slug} {edit.__name__:6s} reward={run.reward:.1f} is_error={run.grade.is_error} "
        f"exit_code={run.grade.info.get('exit_code')} error={run.grade.info.get('error')!r}"
    )
    return run


async def main():
    a, b = coding_tasks.tasks
    runs = {(t.slug, e.__name__): await grade(t, e) for t in (a, b) for e in (golden, honest, cheat)}
    print()
    for label, picks in [
        (f"solve {a.slug}, fail {b.slug} honestly", [(a, "golden"), (b, "honest")]),
        (f"solve {a.slug}, crash tests on {b.slug}", [(a, "golden"), (b, "cheat")]),
        ("solve both", [(a, "golden"), (b, "golden")]),
    ]:
        job = Job(id="repro", name=label, runs=[runs[(t.slug, e)] for t, e in picks])
        print(f"Job.reward={job.reward:.3f} errors={len(job.errors)}  [{label}]")


asyncio.run(main())
