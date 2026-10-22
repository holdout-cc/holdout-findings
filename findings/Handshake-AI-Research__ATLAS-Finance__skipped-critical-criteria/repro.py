"""pass_at_k.py counts a trial as PASS when its critical criteria were skipped by a failed section gate.

Usage: python repro.py <ATLAS-Finance checkout> <generated datasets/atlas dir>

Runs the verifier's real grader (gandalf-finance v1.1.0, with the task's own
patch_gate_reuse.py applied, as tests/Dockerfile does) on each task's real
tests/grader.toml, rubric.json, instruction.md and judge_guidance.md. Only the
LLM judge call (gandalf.orchestrator.run_judge) is replaced by fixed verdicts.
The grader output is laid out as a Harbor trial the way tests/test.sh does it
(verifier/grader/info.json + verifier/reward.json) and scored with the repo's
scripts/pass_at_k.py. No network, no model calls, no Docker.
"""

import contextlib
import io
import json
import os
import sys
import tempfile
from pathlib import Path

os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"  # keep litellm's import offline

ATLAS = Path(sys.argv[1]).resolve()
TASKS_DIR = Path(sys.argv[2]).resolve()
sys.path.insert(0, str(ATLAS / "scripts"))

import openpyxl  # noqa: E402
import pass_at_k as pk  # noqa: E402
from gandalf import orchestrator as orch  # noqa: E402
from gandalf.models import LLMUsage, Verdict, load_rubric  # noqa: E402


def grade(task: Path, verdict, work: Path) -> Path:
    """Run gandalf on one trial. verdict(kind, text) -> bool is the stubbed judge; it stands in for
    what the judge would say about the work, so the workbook itself is blank in every scenario."""
    rubric = load_rubric(str(task / "tests" / "rubric.json"))
    gates = {g for gs in orch.collect_section_gates(rubric).values() for g in gs}
    known = gates | {it.criterion for it in rubric}

    def ask(text: str) -> bool:
        # the judge prompt wraps the rubric text (tolerance notes, penalty polarity); find which item it is
        item = max((k for k in known if k in text), key=len)
        return verdict("gate" if item in gates else "criterion", item)

    def fake_run_judge(judge_input, sandbox_user, trace_path, timeout=300, clone_parent_dir=None):
        texts = getattr(judge_input, "criteria", None) or [judge_input.criterion]
        return [Verdict(met=ask(t), reasoning="stub") for t in texts], LLMUsage()

    orch.run_judge = fake_run_judge
    (work / "grade" / "workspace").mkdir(parents=True)
    openpyxl.Workbook().save(work / "grade" / "workspace" / "submitted_output.xlsx")  # passes test.sh's load gate
    (work / "grade" / "trajectory.json").write_text('{"steps": []}')
    cfg = (task / "tests" / "grader.toml").read_text()
    cfg = cfg.replace('"/tests/', f'"{task}/tests/').replace('"/grade/', f'"{work}/grade/')
    cfg = cfg.replace('"/logs/grader"', f'"{work}/logs/grader"')
    (work / "grader.toml").write_text(cfg)
    sys.argv = ["gandalf-the-grader", "--config", str(work / "grader.toml")]
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        try:
            orch.main()
        except SystemExit as e:
            if e.code not in (0, None):
                raise
    return work / "logs" / "grader"


def harbor_trial(job: Path, task: str, out: Path) -> None:
    """Lay out one trial the way tests/test.sh publishes it."""
    t = job / f"{task}__trial"
    (t / "verifier" / "grader").mkdir(parents=True)
    (t / "result.json").write_text(json.dumps({"task_id": {"path": f"datasets/atlas/{task}"}}))
    for f in ("info.json", "reward.json"):
        (t / "verifier" / "grader" / f).write_bytes((out / f).read_bytes())
    reward = json.loads((out / "reward.json").read_text())["reward"]
    (t / "verifier" / "reward.json").write_text(json.dumps({"reward": reward}))


def scenarios(task: Path):
    rubric = load_rubric(str(task / "tests" / "rubric.json"))
    weight = {it.criterion: it.weight for it in rubric}
    section_gates = orch.collect_section_gates(rubric)
    gate_texts = {g for gs in section_gates.values() for g in gs}
    critical = [it for it in rubric if it.weight >= 3 and it.criterion not in gate_texts]
    # a gated section holding critical criteria whose gate is not itself a weight >= 3 rubric item
    section = next(s for s in section_gates
                   if not any(it.criterion in section_gates[s] and it.weight >= 3 for it in rubric)
                   and any(it.section == s for it in critical))
    miss = [it.criterion for it in critical if it.section == section][-1]
    correct = lambda kind, t: kind == "gate" or weight.get(t, 0) >= 0  # noqa: E731 (no penalty triggered)
    return section, {
        # all gates met, every criterion met, no penalty triggered
        "fully_correct": correct,
        # as fully_correct, but one critical criterion in that section is missed
        "one_critical_miss": lambda kind, t: correct(kind, t) and t != miss,
        # as fully_correct, but that section is not attempted, so its gate is not met
        "skip_section": lambda kind, t: correct(kind, t) and t not in section_gates[section],
        # blank workbook: every gate and every criterion the judge is asked about is not met
        "blank_workbook": lambda kind, t: False,
    }


def main() -> None:
    root = Path(tempfile.mkdtemp())
    for name in ["kestrel-env2__task_02", "rookhaven-env9__task_01"]:
        section, cases = scenarios(TASKS_DIR / name)
        print(f"\n{name}, section: {section}")
        print(f"  {'scenario':18} {'reward':>6} {'skipped w>=3':>12}  passed  fail reasons")
        for sname, verdict in cases.items():
            out = grade(TASKS_DIR / name, verdict, root / name / sname)
            job = root / "jobs" / f"{name}-{sname}"
            harbor_trial(job, name, out)
            info = json.loads((out / "info.json").read_text())
            skipped = sum(1 for c in info["criterion_results"] if c.get("skipped") and c["weight"] >= 3)
            [tr] = pk.load_trials([job], min_weight=3.0, errored_policy="fail")
            print(f"  {sname:18} {info['reward']:6.3f} {skipped:12d}  {str(tr.passed):6}  {len(tr.reasons)}")

    # the blank workbook on every task, as one Harbor job, through pass_at_k's aggregate
    job = root / "jobs" / "blank-all"
    for task in sorted(p for p in TASKS_DIR.iterdir() if (p / "tests" / "rubric.json").is_file()):
        harbor_trial(job, task.name, grade(task, lambda kind, t: False, root / "all" / task.name))
    trials = pk.load_trials([job], min_weight=3.0, errored_policy="fail")
    out = pk.aggregate(trials, [1, 3])
    s = out["summary"]
    print(f"\nblank workbook, all tasks: tasks={s['tasks']} mean_reward={s['mean_reward']:.3f} "
          f"pass@1={s['pass@1']:.3f}")
    print("passing:", ", ".join(t for t, v in out["tasks"].items() if v["passes"]))


if __name__ == "__main__":
    main()
