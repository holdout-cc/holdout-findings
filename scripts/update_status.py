#!/usr/bin/env python3
"""Refresh the status of every filed issue.

Reads each issue linked from the table in README.md with `gh api graphql`,
classifies it, and rewrites:

  - the Status column of the README table,
  - the "Status as of <date>" line above it,
  - the "- Status:" line in each findings/*/README.md.

Status rules:
  fixed         closed as completed, or a linked pull request was merged
  closed        closed for any other reason
  acknowledged  open, and a maintainer (owner, member or collaborator) commented,
                or someone other than the issue author or a bot applied a label
  open          anything else

Usage, from the repository root (needs an authenticated `gh`):
    python scripts/update_status.py
"""
import datetime
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
FINDINGS = ROOT / "findings"

ISSUE_URL = re.compile(r"https://github\.com/([\w.-]+)/([\w.-]+)/issues/(\d+)")
MAINTAINER = {"OWNER", "MEMBER", "COLLABORATOR"}

QUERY = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    issue(number: $number) {
      state
      stateReason
      author { login }
      comments(first: 100) {
        nodes { authorAssociation author { login __typename } }
      }
      timelineItems(first: 100, itemTypes: [LABELED_EVENT, CONNECTED_EVENT, CROSS_REFERENCED_EVENT]) {
        nodes {
          __typename
          ... on LabeledEvent { actor { login __typename } }
          ... on ConnectedEvent { subject { ... on PullRequest { merged } } }
          ... on CrossReferencedEvent { willCloseTarget source { ... on PullRequest { merged } } }
        }
      }
      closedByPullRequestsReferences(first: 20, includeClosedPrs: true) {
        nodes { merged }
      }
    }
  }
}
"""


def fetch(owner, name, number):
    out = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={QUERY}",
         "-f", f"owner={owner}", "-f", f"name={name}", "-F", f"number={number}"],
        capture_output=True, check=True,
    ).stdout
    return json.loads(out.decode("utf-8"))["data"]["repository"]["issue"]


def is_bot(actor):
    return bool(actor) and (actor.get("__typename") == "Bot" or actor.get("login", "").endswith("[bot]"))


def classify(issue):
    if issue["state"] == "CLOSED":
        return "fixed" if issue.get("stateReason") == "COMPLETED" else "closed"

    merged = any(pr.get("merged") for pr in issue["closedByPullRequestsReferences"]["nodes"])
    for ev in issue["timelineItems"]["nodes"]:
        if ev["__typename"] == "ConnectedEvent" and (ev.get("subject") or {}).get("merged"):
            merged = True
        if (ev["__typename"] == "CrossReferencedEvent" and ev.get("willCloseTarget")
                and (ev.get("source") or {}).get("merged")):
            merged = True
    if merged:
        return "fixed"

    author = (issue.get("author") or {}).get("login")
    for c in issue["comments"]["nodes"]:
        who = c.get("author") or {}
        if c.get("authorAssociation") in MAINTAINER and who.get("login") != author and not is_bot(who):
            return "acknowledged"
    for ev in issue["timelineItems"]["nodes"]:
        if ev["__typename"] == "LabeledEvent":
            actor = ev.get("actor") or {}
            if actor.get("login") and actor.get("login") != author and not is_bot(actor):
                return "acknowledged"
    return "open"


def main():
    text = README.read_text(encoding="utf-8")
    statuses = {}
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if not line.startswith("|"):
            continue
        m = ISSUE_URL.search(line)
        if not m:
            continue
        owner, name, number = m.group(1), m.group(2), int(m.group(3))
        status = classify(fetch(owner, name, number))
        statuses[m.group(0)] = status
        cells = line.rstrip().rstrip("|").split("|")
        cells[-1] = f" {status} "
        lines[i] = "|".join(cells) + "|"
        print(f"{owner}/{name}#{number}: {status}")

    if not statuses:
        sys.exit("no issue links found in the README table")

    today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    counts = Counter(statuses.values())
    summary = ", ".join(f"{counts.get(s, 0)} {s}" for s in ("open", "acknowledged", "fixed", "closed"))
    lines = [f"Status as of {today}: {summary}." if l.startswith("Status as of ") else l for l in lines]
    README.write_text("\n".join(lines), encoding="utf-8", newline="\n")

    for readme in sorted(FINDINGS.glob("*/README.md")):
        body = readme.read_text(encoding="utf-8")
        m = ISSUE_URL.search(body)
        if not m or m.group(0) not in statuses:
            continue
        new = re.sub(r"^- Status: .*$", f"- Status: {statuses[m.group(0)]} (as of {today})", body, count=1, flags=re.M)
        if new != body:
            readme.write_text(new, encoding="utf-8", newline="\n")

    print(f"Status as of {today}: {summary}.")


if __name__ == "__main__":
    main()
