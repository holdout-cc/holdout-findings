# skillsbench court-form-filling: a text-only PDF with no form fields scores 1.0 (all 12 checkbox tests skip)

- Issue: [UiPath/coder_eval#234](https://github.com/UiPath/coder_eval/issues/234)
- Commit: [`8d85394`](https://github.com/UiPath/coder_eval/tree/8d853946ba38f23556d367b7826986162baae0b5) (`8d853946ba38f23556d367b7826986162baae0b5`)
- Environment: skillsbench court-form-filling
- Pattern: skipped tests pass
- Severity: high
- Status: open (as of 2026-10-22)

## Summary

The task's verifier skips all 12 checkbox tests when no checkbox value can be extracted from the PDF, and pytest exits 0 when tests are skipped. A one-page PDF with the expected strings printed on it and no form fields at all scores 1.0, as does the real form with the text filled in and no box ticked. A correct fill with one wrong checkbox scores 0. The repro builds five candidate PDFs and grades each with the real `test_outputs.py` the way `test.sh` does.

## Files

- `repro.py`: the reproduction script, exactly as posted in the issue.
- `output.txt`: the output, as posted in the issue.

## Run

Save `repro.py` in the repository root and run `python repro.py` (needs pypdf, reportlab, cryptography, pytest and `pdftotext`). The issue has the full context, the code links and the suggested fixes.
