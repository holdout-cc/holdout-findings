# Holdout findings

Holdout audits RL environments and agent benchmarks for reward hacks and grader bugs: ways an agent can score well without doing the task, and places where the grader scores work incorrectly. This repository collects the 23 findings we reported on 22 October 2026 to 17 repositories across 15 organisations. Every finding was filed publicly as a GitHub issue on the affected repository, with a reproduction script and its output. Each folder under [`findings/`](findings/) holds a short summary, the script exactly as posted, and the posted output.

## Findings

Status as of 2026-10-22: 23 open, 0 acknowledged, 0 fixed, 0 closed.

| Org/repo | Environment | Bug pattern | Severity | Issue | Status |
|---|---|---|---|---|---|
| braintrustdata/autoevals | [NumericDiff (Python and JS)](findings/braintrustdata__autoevals__numericdiff-ignored-options/) | documented options ignored | medium | [#251](https://github.com/braintrustdata/autoevals/issues/251) | open |
| GeneralReasoning/env-r2e-gym | [env-r2e-gym (`parse_log`)](findings/GeneralReasoning__env-r2e-gym__parse-log-passed-substring/) | stdout scraping | high | [#11](https://github.com/GeneralReasoning/env-r2e-gym/issues/11) | open |
| Handshake-AI-Research/ATLAS-Finance | [pass@k (`scripts/pass_at_k.py`)](findings/Handshake-AI-Research__ATLAS-Finance__skipped-critical-criteria/) | skipped criteria pass | high | [#12](https://github.com/Handshake-AI-Research/ATLAS-Finance/issues/12) | open |
| Handshake-AI-Research/gandalf-the-grader | [judge verdict parsing (`Verdict.from_raw`)](findings/Handshake-AI-Research__gandalf-the-grader__quoted-false-verdict/) | judge parse default | medium | [#47](https://github.com/Handshake-AI-Research/gandalf-the-grader/issues/47) | open |
| hud-evals/hud-python | [cookbooks/daytona-rl `fix_calc`](findings/hud-evals__hud-python__fix-calc-editable-tests/) | agent-writable tests, stdout scraping | high | [#736](https://github.com/hud-evals/hud-python/issues/736) | open |
| hud-evals/hud-python | [coding environment / `Job.reward`](findings/hud-evals__hud-python__coding-error-dropped-from-mean/) | errors dropped from mean | medium | [#737](https://github.com/hud-evals/hud-python/issues/737) | open |
| langchain-ai/openevals | [pyright / mypy code evaluators](findings/langchain-ai__openevals__type-ignore-passes/) | suppression comment passes | medium | [#290](https://github.com/langchain-ai/openevals/issues/290) | open |
| METR/inspect-agents | [`reward_hacking_scanner` over `metr_agents` transcripts](findings/METR__inspect-agents__scanner-misses-trimmed-history/) | judge sees trimmed history | high | [#136](https://github.com/METR/inspect-agents/issues/136) | open |
| NVIDIA-NeMo/Gym | [single_step_tool_use_with_argument_comparison (SWE/Droid pivot configs)](findings/NVIDIA-NeMo__Gym__argument-comparison-threshold-zero/) | fuzzy match threshold 0 | high | [#4900](https://github.com/NVIDIA-NeMo/Gym/issues/4900) | open |
| NVIDIA-NeMo/Gym | [scicode](findings/NVIDIA-NeMo__Gym__scicode-systemexit/) | early exit passes | high | [#4901](https://github.com/NVIDIA-NeMo/Gym/issues/4901) | open |
| openai/human-eval | [HumanEval execution harness](findings/openai__human-eval__decorator-replaces-check/) | harness override | high | [#71](https://github.com/openai/human-eval/issues/71) | open |
| openenv/OpenEnv | [agent_world_model_env](findings/openenv__OpenEnv__awm-noop-complete/) | do-nothing pass | high | [#1475](https://github.com/openenv/OpenEnv/issues/1475) | open |
| ORO-AI/assistanteval | [battery-size-known](findings/ORO-AI__assistanteval__battery-wrong-pack/) | purchase not checked | high | [#6](https://github.com/ORO-AI/assistanteval/issues/6) | open |
| PrimeIntellect-ai/verifiers | [proposer_solver](findings/PrimeIntellect-ai__verifiers__proposer-solver-unverified-answer/) | unverified label | high | [#2947](https://github.com/PrimeIntellect-ai/verifiers/issues/2947) | open |
| PrimeIntellect-ai/verifiers | [deepwiki, scratchpad](findings/PrimeIntellect-ai__verifiers__deepwiki-scratchpad-substring/) | substring match | low | [#2948](https://github.com/PrimeIntellect-ai/verifiers/issues/2948) | open |
| scaleapi/agentenv-framework | [container unit-test verifier (reward mode)](findings/scaleapi__agentenv-framework__planted-reward-file/) | planted reward file | medium | [#305](https://github.com/scaleapi/agentenv-framework/issues/305) | open |
| scaleapi/rsi-benchmark | [samples/nano-gpt-data-curation](findings/scaleapi__rsi-benchmark__nano-gpt-failure-scores-best/) | failure scores best | medium | [#102](https://github.com/scaleapi/rsi-benchmark/issues/102) | open |
| scaleapi/rsi-benchmark | [samples/on-policy-self-distillation](findings/scaleapi__rsi-benchmark__opsd-step-cap-unenforced/) | budget not enforced | high | [#103](https://github.com/scaleapi/rsi-benchmark/issues/103) | open |
| sierra-research/tau2-bench | [2.0 benchmark score (`metrics/benchmark.py`)](findings/sierra-research__tau2-bench__agent-errors-excluded/) | errors dropped from mean | medium | [#672](https://github.com/sierra-research/tau2-bench/issues/672) | open |
| Toloka/tolokaforge | [examples/native/coding](findings/Toloka__tolokaforge__coding-source-substring/) | substring match | high | [#1933](https://github.com/Toloka/tolokaforge/issues/1933) | open |
| Toloka/tolokaforge | [terminal_bench adapter (2.1-shape tasks)](findings/Toloka__tolokaforge__terminal-bench-writable-tests/) | agent-writable tests | high | [#1934](https://github.com/Toloka/tolokaforge/issues/1934) | open |
| UiPath/coder_eval | [skillsbench 3d-scan-calc](findings/UiPath__coder_eval__3d-scan-calc-writable-input/) | agent-writable ground truth | high | [#233](https://github.com/UiPath/coder_eval/issues/233) | open |
| UiPath/coder_eval | [skillsbench court-form-filling](findings/UiPath__coder_eval__court-form-skipped-checkboxes/) | skipped tests pass | high | [#234](https://github.com/UiPath/coder_eval/issues/234) | open |

Severity (high, medium, low) is our own rating from our tracker: 15 high, 7 medium, 1 low.

Status values: **open** (no maintainer response yet), **acknowledged** (a maintainer commented or applied a label), **fixed** (closed as completed, or a linked pull request was merged), **closed** (closed for another reason). Bot-applied labels and labels we set ourselves from an issue template do not count.

## How we test

- We run the repository's own scoring code at a pinned commit. Each finding records the commit, and the repro calls the real grader, verifier or metric rather than a re-implementation of it.
- Repros run on Ubuntu 24.04 with the network disabled.
- No model or API calls. Where a grader uses an LLM judge, the judge is stubbed with fixed outputs, and the finding says so. Other stand-ins (for example a GPU training run replaced by a stub) are described in the finding as well.
- Each repro shows a control that fails, a correct solution that passes, and the shortcut that passes, where the task allows all three. A few repros (a do-nothing sweep, or a direct call to a scoring function) show the shortcut against the scoring code alone.
- Every report gets an independent second review before filing.
- Before filing, we check for duplicates against the repository's existing issues and pull requests.

## Layout

- `findings/<org>__<repo>__<slug>/`: `README.md` (summary, commit, pattern, severity, status), the repro script(s), and `output.txt`.
- `scripts/update_status.py`: re-reads each issue with `gh api` and rewrites the status column. Run `python scripts/update_status.py` from the repository root with an authenticated `gh`.

## Contact

hello@holdout.cc · https://holdout.cc
