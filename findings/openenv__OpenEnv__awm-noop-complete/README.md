# agent_world_model_env: 1,681/10,000 code verifiers pass on untouched seeded databases

- Issue: [openenv/OpenEnv#1475](https://github.com/openenv/OpenEnv/issues/1475)
- Commit: [`612056b`](https://github.com/openenv/OpenEnv/tree/612056b569e99e1c358b02a49f1e8312ed20960c) (`612056b569e99e1c358b02a49f1e8312ed20960c`)
- Environment: agent_world_model_env
- Pattern: do-nothing pass
- Severity: high
- Status: open (as of 2026-10-22)

## Summary

Many code-mode verifiers in `agent_world_model_env` only check that a target row exists in the final database, and for many tasks the seed data already contains that row. Across the 10,000 tasks in the dataset, the code verifier returns `complete` on 1,681 freshly seeded, unchanged databases, so an immediate `verify` call can earn the default 1.0 on those tasks. The repro builds each database the way `reset()` does, takes no actions, and calls the same `run_verifier` function. The seed rows and verifiers come from the upstream dataset, so part of the fix may belong there.

Filed when the repository was at `huggingface/OpenEnv`; it has since moved to `openenv/OpenEnv`, and the old links redirect.

## Files

- `awm_noop.py`: the reproduction script, exactly as posted in the issue.
- `output.txt`: the output, as posted in the issue.

## Run

Run `PYTHONPATH=src:envs python awm_noop.py` (or `--all` for the full sweep) from the repository root. The data loader downloads the dataset on first use. The issue has the full context, the code links and the suggested fixes.
