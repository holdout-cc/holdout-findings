# bbox_giou_reward is unbounded: reversed-corner or NaN boxes score far above 1 (RefCOCO env)

- Issue: [NVIDIA-NeMo/RL#4871](https://github.com/NVIDIA-NeMo/RL/issues/4871)
- Commit: [`f0639c6`](https://github.com/NVIDIA-NeMo/RL/tree/f0639c60422ca477268bc678f6e00f35eda778a9) (`f0639c60422ca477268bc678f6e00f35eda778a9`)
- Environment: RefCOCO (`bbox_giou_reward`)
- Pattern: unbounded similarity score
- Severity: high
- Status (as of 2026-10-25): open; fix PR [#4872](https://github.com/NVIDIA-NeMo/RL/pull/4872) (ours, open)

## Summary

`bbox_giou_reward` parses the predicted box but never checks that it is well-formed. With reversed corners (`x2 < x1` and `y2 < y1`) the box area is a positive product of two negatives, the intersection clips to 0, and when the reversed box lies within the gold box's span the convex hull collapses to the gold box. The GIoU then works out to the ratio of the two areas, which can be far above 1. NaN and inf coordinates give NaN, inf or huge rewards. Over the 3,811 RefCOCO validation items, scored with the shipped `env.refcoco` weights, the same answer `[1000, 1000, 0, 0]` for every image averaged 7.03, against 1.0 for the gold box, and `[nan, nan, nan, nan]` averaged 1.8e8. RefCOCO is opt-in in `vlm_grpo_3B.yaml`, so this affects runs that select it, not the default run. The repro calls `bbox_giou_reward` directly on seven boxes.

## Files

- `repro_bbox_giou.py`: the reproduction script, exactly as posted in the issue.
- `output.txt`: the output, as posted in the issue (Ubuntu 24.04 LTS, Python 3.12.3, at `f0639c6`).

## Run

Run `python repro_bbox_giou.py` from the repository root. It needs only `numpy` and `math-verify`, and makes no network, GPU or Ray calls. The issue has the full context, the code links, the RefCOCO validation counts and the suggested fix.
