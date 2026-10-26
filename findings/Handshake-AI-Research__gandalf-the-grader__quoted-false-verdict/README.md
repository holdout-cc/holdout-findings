# Quoted "false" judge verdicts are scored as true

- Issue: [Handshake-AI-Research/gandalf-the-grader#47](https://github.com/Handshake-AI-Research/gandalf-the-grader/issues/47)
- Commit: [`c087e67`](https://github.com/Handshake-AI-Research/gandalf-the-grader/tree/c087e67ab334574aabde25312bdd864c3923c16c) (`c087e67ab334574aabde25312bdd864c3923c16c`)
- Environment: judge verdict parsing (`Verdict.from_raw`)
- Pattern: judge parse default
- Severity: medium
- Status (as of 2026-10-26): open; fix PR [#48](https://github.com/Handshake-AI-Research/gandalf-the-grader/pull/48) (community, open)

## Summary

The judge is asked to write `"met": true` or `"met": false`, and `Verdict.from_raw` converts the value with Python truthiness. Any non-empty string is truthy, so a quoted `"false"` or `"no"` is stored as met. If a judge correctly fails every criterion but quotes its booleans, an empty workspace gets reward 1.0; on a negative-weight criterion the same error applies a penalty that was not triggered. The repro runs the real grader CLI with the judge session stubbed to write fixed verdict files; how often a live judge quotes its booleans was not measured.

## Files

- `repro.py`: the reproduction script, exactly as posted in the issue.
- `output.txt`: the output, as posted in the issue.

## Run

Save `repro.py` in the repository root and run `.venv/bin/python repro.py`. The issue has the full context, the code links and the suggested fixes.
