# In python/ after `uv sync` (dev group has pyright + mypy): uv run python repro.py
# No network or LLM calls. pyright/mypy are found on PATH, as the evaluators expect.
from openevals.code.mypy import create_mypy_evaluator
from openevals.code.pyright import create_pyright_evaluator

pyright = create_pyright_evaluator()
mypy = create_mypy_evaluator()
pyright_md = create_pyright_evaluator(code_extraction_strategy="markdown_code_blocks")

IGNORE = "# type: ignore\n"
TYPE_ERRORS = 'def add(a: int, b: int) -> int:\n    return a + b\n\nx: int = add("1", "2")\nundefined_name(1)\n'
CORRECT = "def add(a: int, b: int) -> int:\n    return a + b\n\nx: int = add(1, 2)\n"
SYNTAX_ERROR = "def add(a, b)\n    return a +\n"
REFUSAL = "I'm sorry, I can't write that code."

cases = [
    ("correct code", CORRECT),
    ("type errors", TYPE_ERRORS),
    ("type errors + '# type: ignore'", IGNORE + TYPE_ERRORS),
    ("syntax error", SYNTAX_ERROR),
    ("syntax error + '# type: ignore'", IGNORE + SYNTAX_ERROR),
    ("refusal prose", REFUSAL),
    ("refusal prose + '# type: ignore'", IGNORE + REFUSAL),
    ("empty string", ""),
]
print(f"{'output':36} pyright  mypy")
for name, code in cases:
    print(f"{name:36} {str(pyright(outputs=code)['score']):8} {mypy(outputs=code)['score']}")

print()
print("markdown_code_blocks strategy (pyright):")
for name, text in [
    ("refusal, no code block", REFUSAL),
    ("refusal + empty ```python block", REFUSAL + "\n```python\n```"),
]:
    print(f"  {name:34} {pyright_md(outputs=text)['score']}")
