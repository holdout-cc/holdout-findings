# Reward-hacking scanner can miss actions removed by handoff or context trimming

- Issue: [METR/inspect-agents#136](https://github.com/METR/inspect-agents/issues/136)
- Commit: [`56105e5`](https://github.com/METR/inspect-agents/tree/56105e54fc076b9a19a7a58b823365e54a767464) (`56105e54fc076b9a19a7a58b823365e54a767464`)
- Environment: `reward_hacking_scanner` over `metr_agents` transcripts
- Pattern: judge sees trimmed history
- Severity: high
- Status: open (as of 2026-10-23)

## Summary

`reward_hacking_scanner` builds its judge prompt from the sample's final message list. Handoff in `react_with_handoff_submit` and Inspect's context trimming remove earlier turns from that list while keeping them in `sample.events`. In the repro a scripted agent overwrites the tests: with no handoff the evidence reaches the judge prompt, but after a handoff or a context-overflow trim none of it does, and after the handoff the judge sees the agent's own summary claiming honest work. The judge is stubbed with a fixed verdict, so the repro checks only what evidence reaches the prompt, not what a real judge would decide.

## Files

- `repro.py`: the reproduction script, exactly as posted in the issue.
- `output.txt`: the output, as posted in the issue.

## Run

Save `repro.py` in the repository root and run `uv run python repro.py`. The issue has the full context, the code links and the suggested fixes.
