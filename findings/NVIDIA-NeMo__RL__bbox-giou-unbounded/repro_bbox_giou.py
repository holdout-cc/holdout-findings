# Run from the repo root: python repro_bbox_giou.py  (needs numpy and math-verify; no GPU, network or Ray)
from nemo_rl.environments.rewards import bbox_giou_reward

gold = "[400, 400, 700, 700]"
cases = [
    ("gold box", "[400, 400, 700, 700]"),
    ("wrong box", "[300, 300, 600, 600]"),
    ("same wrong box, corners swapped", "[600, 600, 300, 300]"),
    ("constant [1000, 1000, 0, 0]", "[1000, 1000, 0, 0]"),
    ("constant [1e9, 1e9, -1e9, -1e9]", "[1e9, 1e9, -1e9, -1e9]"),
    ("nan", "[nan, nan, nan, nan]"),
    ("inf", "[inf, inf, -inf, -inf]"),
]
for label, box in cases:
    reward, correct = bbox_giou_reward(gold, f"<answer>{box}</answer>", giou_penalty_thres=0.5)
    print(f"{label:34s} reward={reward:.4g} correct={correct}")
