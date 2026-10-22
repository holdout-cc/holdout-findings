# Save as repro.py in the repo root, then: python repro.py
# Runs battery-size-known through the repo's offline pipeline
# (tests/test_end_to_end.run_and_grade: the runner, the local amazon service,
# the simulated user, the saved run record and grade()). The judge is the
# repo's keyword stand-in (tests/test_amazon_end_to_end.AmazonJudge) with this
# task's one question added. No model calls, no network.
import tempfile
from pathlib import Path

import pytest

from assistanteval import run_record
from tests import test_amazon_end_to_end as amz
from tests import test_end_to_end as e2e

TASK = "battery-size-known"
ASKED = {}  # run label -> {question id: cache key}


def judge_for(label):
    class Judge(amz.AmazonJudge):
        def task_question(self, qid, conversation):
            assert qid == "asked_size_again"
            said = [l.lower() for l in conversation if l.startswith("assistant: ")]
            return any("?" in s and any(w in s for w in ("tab", "packet", "size")) for s in said)

        def __call__(self, q):
            ASKED.setdefault(label, {})[q.id] = q.key()
            if q.id.startswith("asked_for:"):  # "Please order the 8-pack."
                return e2e._yes("order" in " ".join(q.context["user_messages"]).lower())
            return super().__call__(q)

    return Judge


def search(call):
    return call("amazon", "GET", "/v1/products", params={"query": "hearing aid batteries"})["products"]


def buy(call, pack):
    call("amazon", "POST", f"/v1/cart/{pack['product_id']}", json={"quantity": 1})
    order = call("amazon", "POST", "/v1/orders", json={})
    return f"I ordered the {pack['name']} for ${order['total']:.2f}."


def do_nothing(call, opening):
    yield "Sorry, I can't place that order."


def correct(call, opening):  # the size 13 8-pack the user asked for
    yield buy(call, next(p for p in search(call) if "Size 13, 8-pack" in p["name"]))


def wrong_pack(call, opening):  # first search hit: size 312, 60-pack
    yield buy(call, search(call)[0])


def run(label, script):
    mp = pytest.MonkeyPatch()
    tmp = Path(tempfile.mkdtemp(prefix=f"ae-{label}-"))
    try:
        verdict = e2e.run_and_grade(
            TASK, tmp, mp, judge=judge_for(label), scripts={"hearing aid batteries": script}
        )
    finally:
        mp.undo()
    amazon = next(s for s in run_record.load(tmp / "run").services if s.name == "amazon")
    items = [i["name"] for o in amazon.end_state.get("orders", []) for i in o["items"]]
    print(f"== {label}: ordered {items}")
    print(f"   outcome = {verdict['outcome']}")
    for g in verdict["gates"]:
        print(f"   {g['result']:>6}  {g['name']}")
    return verdict["outcome"]


results = {label: run(label, s) for label, s in
           [("do_nothing", do_nothing), ("correct", correct), ("wrong_pack", wrong_pack)]}
print("\nQuestions the judge saw in wrong_pack that are byte-identical in correct:")
for qid, key in sorted(ASKED["wrong_pack"].items()):
    if qid.split(":")[0] in ("asked_for", "has_condition", "condition_met"):
        print(f"   {qid:32} identical={ASKED['correct'].get(qid) == key}")
print("\nRESULT:", " | ".join(f"{k} {v}" for k, v in results.items()))
