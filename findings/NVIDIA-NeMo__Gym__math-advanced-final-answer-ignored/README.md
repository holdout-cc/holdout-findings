# math_advanced_calculations: verify() never reads the final answer, so a wrong or missing final answer can still get reward 1.0

- Issue: [NVIDIA-NeMo/Gym#5011](https://github.com/NVIDIA-NeMo/Gym/issues/5011)
- Commit: [`754c2f6`](https://github.com/NVIDIA-NeMo/Gym/tree/754c2f6c3b074eb4842a35cad38e51adf255c640) (`754c2f6c3b074eb4842a35cad38e51adf255c640`)
- Environment: math_advanced_calculations
- Pattern: final answer not read
- Severity: high
- Status (as of 2026-10-25): open; fix PR [#5012](https://github.com/NVIDIA-NeMo/Gym/pull/5012) (ours, open)

## Summary

`MultiVerseMathHardResourcesServer.verify` gives 1.0 when every gold value appears among the trajectory's `function_call_output` items, and it never reads the assistant's final message. Once the right tool calls have been made, a reply that reports different values, a reply that quotes the tool results and then replaces them, and no reply at all all score 1.0. Controls with no tool calls, or with ordinary-math values passed through `return_constant`, score 0.0, so the tool outputs are checked but the reply is not. The repro uses the first row of `data/example.jsonl`, the environment's own tool functions and the real `verify()`; the same holds for all 5 example rows.

## Files

- `repro.py`: the reproduction script, exactly as posted in the issue.
- `output.txt`: the output, as posted in the issue (Ubuntu 24.04, Python 3.13.14, at `754c2f6`).

## Run

Run `python repro.py` from the repository root. It needs no model or network. The issue has the full context, the code links and the suggested fixes.
