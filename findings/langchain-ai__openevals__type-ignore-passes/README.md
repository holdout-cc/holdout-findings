# pyright/mypy evaluators: a leading `# type: ignore` in the graded output makes code with type errors pass (pyright also passes syntax errors and prose)

- Issue: [langchain-ai/openevals#290](https://github.com/langchain-ai/openevals/issues/290)
- Commit: [`8a1ebcc`](https://github.com/langchain-ai/openevals/tree/8a1ebcc1c99d5507ce9e786a00714ecbeec26005) (`8a1ebcc1c99d5507ce9e786a00714ecbeec26005`)
- Environment: pyright / mypy code evaluators
- Pattern: suppression comment passes
- Severity: medium
- Status: open (as of 2026-10-23)

## Summary

The pyright and mypy evaluators write the graded output to a file as is and run the checker on it. A leading `# type: ignore` makes code with type errors score `True` under both; under pyright it also passes syntax errors and plain refusal text. Empty output passes both checkers, and with `markdown_code_blocks` an empty code block passes. The repro calls the real evaluators with default arguments and compares each case with and without the directive.

## Files

- `repro.py`: the reproduction script, exactly as posted in the issue.
- `output.txt`: the output, as posted in the issue.

## Run

Save as `python/repro.py` and run `uv run python repro.py` from `python/` after `uv sync`. The issue has the full context, the code links and the suggested fixes.
