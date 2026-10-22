# Save as repro.py in the repo root, then: python repro.py  (no network or model calls)
import sys

sys.path.insert(0, "py")
from autoevals import NumericDiff


def score(output, expected, **opts):
    return NumericDiff().eval(output=output, expected=expected, **opts).score


print("SCORERS.md examples (documented score vs actual):")
print(f"  10.5 vs 10.0, max_diff=1.0    documented 0.5    actual {score(10.5, 10.0, max_diff=1.0):.4f}")
print(f"  10.5 vs 10.0, max_diff=0.01   documented 0.0    actual {score(10.5, 10.0, max_diff=0.01):.4f}")
print(f"  100 vs 110, relative=True     documented ~0.91  actual {score(100, 110, relative=True):.4f}")
print(f"  10.5 vs 10.0, no options                        actual {score(10.5, 10.0):.4f}")
print(f"  NumericDiff.partial(max_diff=0.01), 10.5 vs 10.0 actual "
      f"{NumericDiff.partial(max_diff=0.01)().eval(output=10.5, expected=10.0).score:.4f}")

print("\nA tight tolerance, max_diff=0.01 (gold, then wrong answers):")
for gold, out in [(2024, 2024), (2024, 2025), (1000, 999), (72, 70), (1000, 1100), (5, -5)]:
    print(f"  expected={gold:<5} output={out:<5} score={score(out, gold, max_diff=0.01):.4f}")
