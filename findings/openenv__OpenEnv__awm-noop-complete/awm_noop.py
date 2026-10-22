"""agent_world_model_env: build the DB exactly as reset() does, take no actions, run the code verifier.

Run from the repo root:  PYTHONPATH=src:envs python awm_noop.py [--all]
"""
import shutil, sys, tempfile
from collections import Counter

from agent_world_model_env.server.data_loader import AWMDataLoader
from agent_world_model_env.server.db_manager import create_database, save_snapshot
from agent_world_model_env.server.verifier import run_verifier

loader = AWMDataLoader()  # downloads Snowflake/AgentWorldModel-1K on first use


def noop_verify(scenario, task_idx):
    entry = loader.get_verifier(scenario, task_idx, "code")
    if entry is None:
        return "no_verifier"
    d = tempfile.mkdtemp()
    try:
        db, initial = f"{d}/{scenario}.db", f"{d}/{scenario}_initial.db"
        create_database(db, loader.get_db_schema(scenario), loader.get_sample_data(scenario))  # reset()
        save_snapshot(db, initial)                                                             # reset()
        # no tool calls; then verify(verifier_mode="code") with no final_answer
        reward_type, _ = run_verifier(entry, "code", initial, db, final_answer=None)
        return reward_type
    finally:
        shutil.rmtree(d, ignore_errors=True)


if "--all" in sys.argv:
    counts = Counter()
    for s in loader.list_scenarios():
        for i in range(s["num_tasks"]):
            counts[noop_verify(s["name"], i)] += 1
    print(dict(counts), "tasks:", sum(counts.values()))
else:
    for scenario, i in [("accounting_finance_1", t) for t in range(10)] + [
        ("appointment_scheduling_1", 0), ("b2b_commerce_1", 0), ("analytics_dashboard_4", 0)]:
        print(f"{scenario} #{i}: {noop_verify(scenario, i):9}  {loader.get_tasks(scenario)[i][:90]}")
