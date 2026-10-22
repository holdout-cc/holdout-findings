# Save as repro_fix_calc.py in the repo root, then: python repro_fix_calc.py
import asyncio
import sys

sys.path.insert(0, "cookbooks/daytona-rl")
import bugs
import env as smoke
from hud.environment.server import TaskRunner

WS = smoke.WORKSPACE


def noop():
    pass


def correct_fix():  # reference implementations from bugs.py
    body = "".join("\n" + bugs.FUNCS[n]["correct"].strip("\n") + "\n" for n in bugs.NAMES)
    (WS / "calc.py").write_text(bugs.HEADER + body)


def rewrite_tests():  # calc.py left buggy
    (WS / "test_calc.py").write_text("".join(f"def test_{i}():\n    pass\n" for i in range(10)))


def print_passed():  # calc.py left buggy, test_calc.py untouched
    lines = []
    for line in (WS / "calc.py").read_text().splitlines():
        lines.append(line)
        if line.startswith("def "):
            lines.append('    print("10 passed")')
    (WS / "calc.py").write_text("\n".join(lines) + "\n")


async def reward(variant, edit):
    task = smoke.fix_calc(variant=variant)
    runner = TaskRunner(smoke.env.templates[task.id], task.args)
    await runner.start()  # seeds calc.py / test_calc.py, returns the prompt
    edit()  # what the agent does in the workspace
    return (await runner.grade({"answer": "done"}))["score"]


async def main():
    for edit in (noop, correct_fix, rewrite_tests, print_passed):
        scores = [await reward(v, edit) for v in range(24)]
        print(f"{edit.__name__:14s} reward 1.0 on {scores.count(1.0):2d}/24 variants")

    # what pytest itself says in the print_passed case (variant 0)
    smoke.seed_bug(0)
    print_passed()
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
        cwd=str(WS), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
    )
    out = (await proc.communicate())[0].decode().strip().splitlines()
    print("pytest summary:", out[-1], "| exit code:", proc.returncode)
    print("run_pytest() ->", await smoke.run_pytest())


asyncio.run(main())
