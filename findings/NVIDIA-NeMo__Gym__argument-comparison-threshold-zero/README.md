# single_step_tool_use_with_argument_comparison: word_count_similarity_threshold 0.0 (SWE/Droid pivot configs) accepts any multi-word string, e.g. "echo done" for every bash command

- Issue: [NVIDIA-NeMo/Gym#4900](https://github.com/NVIDIA-NeMo/Gym/issues/4900)
- Commit: [`9240708`](https://github.com/NVIDIA-NeMo/Gym/tree/92407083ba1a8373b96ae660cbd4404cd874169c) (`92407083ba1a8373b96ae660cbd4404cd874169c`)
- Environment: single_step_tool_use_with_argument_comparison (SWE/Droid pivot configs)
- Pattern: fuzzy match threshold 0
- Severity: high
- Status: open (as of 2026-10-22)

## Summary

`ActionComparator._compare_strings` scores multi-word string arguments by word-count overlap and rejects only below `word_count_similarity_threshold`. The SWE and Droid pivot configs set that threshold to 0.0, so the check cannot fail and any string of two or more words matches any other. On the first 389 rows of the SWE pivot dataset, replacing every bash command with `echo done` passed 346/346 rows that have a multi-word argument. The repro calls the comparator directly with thresholds 0.0 and 0.1.

## Files

- `repro.py`: the reproduction script, exactly as posted in the issue.
- `output.txt`: the output, as posted in the issue.
- `output-linux.txt`: Re-run on Ubuntu 24.04 LTS (Linux 6.8), Python 3.12.3, network disabled, at `9240708`.

## Run

Run `python repro.py` from the repository root. The issue has the full context, the code links and the suggested fixes.
