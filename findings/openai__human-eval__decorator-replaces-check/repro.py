# Run with human-eval importable (e.g. from the repo root): python repro.py
# Scores three fixed completions on all 164 tasks with the unmodified
# evaluate_functional_correctness. No model or network calls.
import json
import os
import tempfile

from human_eval.data import read_problems, write_jsonl
from human_eval.evaluation import evaluate_functional_correctness

NOOP = "    pass\n"

# Same text for every task. It does not implement anything. The last line is a
# bare decorator (any expression is allowed since Python 3.9), which Python
# attaches to the test's `def check(candidate):` and turns into a no-op.
DECORATOR = "    return None\n@lambda _check: lambda candidate: None\n"

# Stop sequences described in the HumanEval paper.
# Truncating at them does not change this completion.
STOPS = ["\nclass", "\ndef", "\n#", "\nif", "\nprint"]
assert not any(s in DECORATOR for s in STOPS)

problems = read_problems()
out = tempfile.mkdtemp()

for name in ("canonical", "noop", "decorator"):
    rows = []
    for tid, p in problems.items():
        c = {"canonical": p["canonical_solution"], "noop": NOOP, "decorator": DECORATOR}[name]
        rows.append({"task_id": tid, "completion": c})
    path = os.path.join(out, f"{name}.jsonl")
    write_jsonl(path, rows)
    res = evaluate_functional_correctness(path, k=[1], n_workers=4, timeout=3.0)
    with open(path + "_results.jsonl") as f:
        passed = {r["task_id"] for r in map(json.loads, f) if r["passed"]}
    print(f"{name:10s} pass@1={res['pass@1']:.4f} ({len(passed)}/{len(problems)})")
    if name == "decorator":
        starts = {t for t, p in problems.items() if p["test"].lstrip().startswith("def check")}
        print(f"tasks whose test starts with 'def check': {len(starts)}; "
              f"decorator passed exactly those: {passed == starts}")
