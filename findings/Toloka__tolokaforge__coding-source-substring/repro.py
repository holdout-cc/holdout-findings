# Run from the repo root: python repro.py
from datetime import datetime, timezone
from pathlib import Path

import yaml

from tolokaforge.core.grading.combine import GradingEngine
from tolokaforge.core.models import Message, MessageRole, ToolCall, Trajectory
from tolokaforge.core.models.task_config import GradingConfig
from tolokaforge.runner.models import RecordedToolCall, ToolExecutionStatus, ToolExecutorIdentity

TASK = Path("examples/native/coding/dataset/tasks/coding/coding_public_example_01")
cfg = GradingConfig.model_validate(yaml.safe_load((TASK / "grading.yaml").read_text()))
orig = (TASK / "fixtures/buggy_math.py").read_text()
note = "Root cause: tax was subtracted. Edge case: tax_rate passed as a percentage.\n"

# Same transcript for every submission; it satisfies the transcript rules.
now = datetime.now(timezone.utc)
calls = [("c1", "bash", {"command": "cat buggy_math.py"}),
         ("c2", "write_file", {"path": "submissions/note.md", "content": note})]
traj = Trajectory(
    task_id="coding_public_example_01", trial_index=0, start_ts=now, end_ts=now,
    messages=[
        Message(role=MessageRole.USER, content="Please patch buggy_math.py and write a handoff note."),
        Message(role=MessageRole.ASSISTANT, content="",
                tool_calls=[ToolCall(id=i, name=n, arguments=a) for i, n, a in calls]),
        *[Message(role=MessageRole.TOOL, content="ok", tool_call_id=i) for i, _, _ in calls],
        Message(role=MessageRole.ASSISTANT, content="Fixed the tax bug; root cause is in the note."),
    ],
    tool_log=[RecordedToolCall(call_id=i, sequence=k, tool_name=n, arguments=a, output="ok",
                               executor=ToolExecutorIdentity.AGENT, status=ToolExecutionStatus.SUCCESS,
                               latency_seconds=0.0, timestamp=now)
              for k, (i, n, a) in enumerate(calls)],
)

submissions = {
    "unfixed + expected snippet in a comment": orig + "\n# TODO: amount * (1 + tax_rate)\n",
    "correct minimal fix (1.0 - -> 1.0 +)": orig.replace("1.0 - tax_rate", "1.0 + tax_rate"),
    "unfixed, no comment": orig,
}
for label, src in submissions.items():
    ns = {}
    exec(src, ns)
    state = {"filesystem": {"/env/fs/agent-visible/buggy_math.py": src,
                            "/env/fs/agent-visible/submissions/note.md": note}}
    g = GradingEngine(cfg).grade_trajectory(traj, state)
    print(f"{label:40} add_tax(100, 0.08)={ns['add_tax'](100.0, 0.08):6.1f}  "
          f"score={g.score:.3f} pass={g.binary_pass}")
