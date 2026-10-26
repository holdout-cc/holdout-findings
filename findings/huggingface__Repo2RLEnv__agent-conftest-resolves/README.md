# pr_runtime test.sh: an agent-added conftest.py scores 1.0 with resolved=True

- Issue: [huggingface/Repo2RLEnv#211](https://github.com/huggingface/Repo2RLEnv/issues/211)
- Commit: [`27d04ee`](https://github.com/huggingface/Repo2RLEnv/tree/27d04ee8203cd5b2f20c3997d13836e5f5b64238) (`27d04ee8203cd5b2f20c3997d13836e5f5b64238`)
- Environment: `pr_runtime` / `commit_runtime` / `cve_patches` test script (`build_eval_script`)
- Pattern: agent-added conftest
- Severity: high
- Status (as of 2026-10-26): open; fix PR [#212](https://github.com/huggingface/Repo2RLEnv/pull/212) (ours, open)

## Summary

Before grading, the `test.sh` built by `build_eval_script` restores only the files that the hidden test patch touches. Every other file the agent added or changed stays in the working tree, including `conftest.py`, `pytest.ini` and the pytest section of `pyproject.toml`, and pytest loads them during the graded run. The docstring calls this reset the anti-tamper guard, and the docs say the agent cannot pass by editing tests, but a test-configuration change alone, with no source fix, can score 1.0 with `resolved=True`. By a static count, 101 of the 219 tasks in the published `FineEnvs/repo2rlenv-pr-runtime`, `-commit-runtime` and `-cve-patches` datasets run pytest and are probably affected; 9 of them were replayed, and all 9 were affected. Plain `--noconftest` is not a fix, because these repositories keep their fixtures in their own `tests/conftest.py`.

## Files

The issue has no reproduction script and no posted output. It describes the code path, links the lines involved and gives the counts above, so this folder holds only this summary.

## Run

There is nothing to run from this folder. The issue has the code links and the outline of the fix.
