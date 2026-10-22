"""Agent-side failures become INFRASTRUCTURE_ERROR and leave the 2.0 score's denominator.

Run from the repo root: uv run python repro.py  (no network, no API keys)

Real code: retail Orchestrator + LLMAgent + UserSimulator, run through
run_simulation and wrapped in run_with_retry as runner/batch.py does, then
scored with tau2.metrics.benchmark.summarize. The only stub is litellm's
`completion` in tau2.utils.llm_utils, which plays a scripted agent model and
user model. TaskTrial status uses the same rule as read_task_trials.
"""

import json
import os
import sys

os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

from litellm import ModelResponse
from loguru import logger

import tau2.utils.llm_utils as llm_utils
from tau2.agent.llm_agent import LLMAgent
from tau2.data_model.benchmark import BenchmarkFrame, CellFrame, TaskTrial, TrialStatus
from tau2.data_model.simulation import TerminationReason
from tau2.evaluator.evaluator import EvaluationType
from tau2.metrics.benchmark import describe_reward_gaps, summarize
from tau2.orchestrator.orchestrator import Orchestrator
from tau2.registry import registry
from tau2.runner.progress import run_with_retry
from tau2.runner.simulation import run_simulation
from tau2.user.user_simulator import UserSimulator

logger.remove()
logger.add(sys.stderr, level="ERROR")

# Two retail tasks graded only on DB state/actions (no NL judge), so fully deterministic.
tasks = [
    t
    for t in registry.get_tasks_loader("retail")()
    if not t.evaluation_criteria.nl_assertions
    and t.evaluation_criteria.actions
    and any(a.name.startswith(("cancel", "return", "exchange", "modify"))
            for a in t.evaluation_criteria.actions)
][:2]
EASY, HARD = tasks
AGENT_TOOLS = {t.name for t in registry.get_env_constructor("retail")().get_tools()}
STATE = {"mode": None, "task": None, "user_calls": 0}


def _resp(content=None, tool_calls=None, finish="stop"):
    msg = {"role": "assistant", "content": content}
    if tool_calls:
        msg["tool_calls"] = tool_calls
    return ModelResponse(
        model="o4-mini",
        choices=[{"index": 0, "finish_reason": finish, "message": msg}],
        usage={"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
    )


def fake_completion(model, messages, tools=None, tool_choice=None, **kwargs):
    if {t["function"]["name"] for t in (tools or [])} & AGENT_TOOLS:  # agent model
        mode = STATE["mode"]
        if mode == "gold":  # do the task's expected actions, then reply
            gold = STATE["task"].evaluation_criteria.actions
            n = sum(1 for m in messages if m.get("role") == "tool")
            if n < len(gold):
                return _resp(tool_calls=[{"id": f"g{n}", "type": "function", "function": {
                    "name": gold[n].name, "arguments": json.dumps(gold[n].arguments)}}])
            return _resp(content="All done, your request has been processed.")
        if mode == "wrong_answer":
            return _resp(content="Sorry, I can't help with that request.")
        if mode == "malformed_tool_json":  # tool call cut off, e.g. at max_tokens
            return _resp(tool_calls=[{"id": "c0", "type": "function", "function": {
                "name": "get_order_details", "arguments": '{"order_id": "#W12'}}],
                finish="length")
        if mode == "empty_reply":
            return _resp(content="")
        raise AssertionError(mode)
    STATE["user_calls"] += 1  # user model
    return _resp(content="Hi, I need help with my order." if STATE["user_calls"] == 1
                 else "Thanks. ###STOP###")


llm_utils.completion = fake_completion


def run_trial(task, mode):
    STATE.update(mode=mode, task=task)

    def _execute():
        STATE["user_calls"] = 0
        env = registry.get_env_constructor("retail")()
        agent = LLMAgent(tools=env.get_tools(), domain_policy=env.get_policy(), llm="o4-mini")
        user = UserSimulator(llm="o4-mini", instructions=str(task.user_scenario), tools=None)
        orch = Orchestrator(domain="retail", agent=agent, user=user, environment=env, task=task)
        return run_simulation(orch, evaluation_type=EvaluationType.ALL)

    return run_with_retry(_execute, task=task, trial=0, seed=0, max_retries=1,
                          retry_delay=0.0, console_display=False)


def to_trial(sim):
    # Same status rule as tau2.metrics.benchmark.read_task_trials.
    if sim.termination_reason in {TerminationReason.INFRASTRUCTURE_ERROR,
                                  TerminationReason.UNEXPECTED_ERROR}:
        status, reward = TrialStatus.ERROR, None
    elif sim.reward_info is None:
        status, reward = TrialStatus.UNSCORED, None
    else:
        status, reward = TrialStatus.SCORED, sim.reward_info.reward
    return TaskTrial(language="en", domain="retail", canonical_task_id=sim.task_id, trial=0,
                     condition_fingerprint="0" * 64, binding_revision="repro",
                     status=status, reward=reward)


frame = BenchmarkFrame(
    benchmark_version="repro", revision="repro", mode="text", trials=[0],
    cells=[CellFrame(language="en", domain="retail",
                     canonical_task_ids=[EASY.id, HARD.id], binding_revision="repro")],
)

easy = run_trial(EASY, "gold")
print(f"task {EASY.id} agent 'gold':                termination={easy.termination_reason.value:20s} "
      f"reward={easy.reward_info.reward}")
sims = {}
for mode in ("gold", "wrong_answer", "malformed_tool_json", "empty_reply"):
    sim = sims[mode] = run_trial(HARD, mode)
    reward = sim.reward_info.reward if sim.reward_info else None
    print(f"task {HARD.id} agent '{mode + "':":21s} termination={sim.termination_reason.value:20s} "
          f"reward={reward} error_type={(sim.info or {}).get('error_type')}")
print()
for mode, sim in sims.items():
    s = summarize(frame, [to_trial(easy), to_trial(sim)])
    print(f"task {HARD.id} = {mode:19s} -> cell complete={s.complete} score={s.score} "
          f"scored={s.scored_trials} error_trials={s.error_trials} gaps={describe_reward_gaps(s)}")
