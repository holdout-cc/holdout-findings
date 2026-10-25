from verl.utils.reward_score import default_compute_score

# every numina_* data source (Eurus-2-RL-Data math rows) is routed to prime_math.compute_score
DATA_SOURCE = "numina_cn_k12"

cases = [
    # (case, ground truth, answer, expected score)
    ("wrong interval", "[1,2)", "[1,2]", 0),
    ("wrong interval", "(-\\infty, \\frac{1}{2}]", "(-\\infty, \\frac{1}{2})", 0),
    ("correct interval", "[1,2)", "[1,2)", 1),
    ("100x gold", "22500", "2250000", 0),
    ("1/100x gold", "22500", "225", 0),
    ("gold + 1", "22500", "22501", 0),
    ("correct integer", "22500", "22500", 1),
    ("equation gold echoed", "x - \\sqrt{3}y + 2 = 0", "x - \\sqrt{3}y + 2 = 0", 1),
    ("equation gold echoed", "\\dfrac{x^{2}}{18} + \\dfrac{y^{2}}{9} = 1", "\\dfrac{x^{2}}{18} + \\dfrac{y^{2}}{9} = 1", 1),
    ("equation gold echoed", "S_{max}=-6", "S_{max}=-6", 1),
    ("equation gold echoed", "y = x - 1", "y = x - 1", 1),
]

for case, gold, answer, expected in cases:
    response = f"The answer is $\\boxed{{{answer}}}$."
    score = default_compute_score(DATA_SOURCE, response, gold)
    print(f"{case:21} expected={expected} score={score}  gold={gold!r}  answer={answer!r}")
