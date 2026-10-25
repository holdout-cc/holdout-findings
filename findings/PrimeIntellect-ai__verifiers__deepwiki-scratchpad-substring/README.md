# deepwiki and scratchpad examples: substring rewards pass without calling the tool they're meant to test

- Issue: [PrimeIntellect-ai/verifiers#2948](https://github.com/PrimeIntellect-ai/verifiers/issues/2948)
- Commit: [`8859385`](https://github.com/PrimeIntellect-ai/verifiers/tree/885938574b10969f9ea55c79b0f486faf0de6819) (`885938574b10969f9ea55c79b0f486faf0de6819`)
- Environment: deepwiki, scratchpad
- Pattern: substring match
- Severity: low
- Status (as of 2026-10-25): open; fix PR [#2958](https://github.com/PrimeIntellect-ai/verifiers/pull/2958) (community, open)

## Summary

Two example environments grade the final reply with a bare substring check and never look at the tool calls. In `deepwiki`, a reply that lists several languages, or says "It is Rust, not Python", scores 1.0 without calling `deepwiki_ask_question`. In `scratchpad`, the target word is in the prompt, so echoing it without calling `scratchpad_roundtrip` scores 1.0 on 20/20 tasks. The repro uses the environments' real tasksets and `Task.score`.

## Files

- `repro.py`: the reproduction script, exactly as posted in the issue.
- `output.txt`: the output, as posted in the issue.
- `output-linux.txt`: Re-run on Ubuntu 24.04 LTS (Linux 6.8), Python 3.12.3, network disabled, at `8859385`.

## Run

The issue has the full context, the code links and the suggested fixes.
