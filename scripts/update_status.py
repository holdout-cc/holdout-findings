#!/usr/bin/env python3
"""Refresh findings.json from GitHub and regenerate everything derived from it.

findings.json is the source for published issue metadata and the generated pages; issues.txt is the
intake list for new issue URLs. One run:

  1. reads findings.json and issues.txt (one issue URL per line);
  2. adds a stub record, flagged `needs_writeup`, for any URL in issues.txt
     that is not in findings.json yet;
  3. re-reads every issue with `gh api graphql` and refreshes its title,
     state, state reason, fix pull requests and maintainer engagement;
  4. recomputes the totals and writes findings.json;
  5. regenerates, in README.md, the counts sentence, the "Status as of" line,
     the findings table and the severity sentence (each between
     `<!-- name:start -->` and `<!-- name:end -->` markers);
  6. regenerates the "- Status" line of each findings/*/README.md.

Fix pull requests are the pull requests with evidence that they fix the issue:
  - GitHub lists them as closing the issue (a closing keyword or a sidebar link);
  - a connected event links them to the issue and no later disconnected event
    removes the link (connected and disconnected events are applied in order);
  - they cross-reference the issue with a closing keyword; or
  - a line of their title or body references the issue with fix, close or
    resolve wording ("Fixes #12", "closes owner/repo#12", "fix for <issue URL>"),
    or their title is a fix ("fix(scope): ...") and the title or body
    references the issue.
A pull request that only mentions the issue is not recorded, and neither is one
whose link was removed by a disconnected event, unless GitHub still lists it as
closing the issue. Pull request numbers listed in a record's hand-written
excluded_prs are never recorded (for a PR the rules above match that does not
fix the issue). A pull request is "ours" when its author also filed the
issue. Its state is "open", "draft" (an open draft), "merged" or "closed".

maintainer_engaged is true only when someone with owner, member or
collaborator access (not a bot and not us) commented on the issue, or
commented on or reviewed one of its fix pull requests.

Status of each issue:
  fixed         closed as completed, or a fix pull request (with the evidence
                above) was merged
  closed        closed for any other reason
  acknowledged  open, and maintainer_engaged
  open          anything else

Usage, from the repository root (needs Python 3.9+ and an authenticated `gh`):
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
DATA = ROOT / "findings.json"
ISSUES = ROOT / "issues.txt"

MAINTAINER = {"OWNER", "MEMBER", "COLLABORATOR"}
PATTERNS_URL = "https://github.com/holdout-cc/reward-hack-patterns/tree/main/patterns/"
SEVERITIES = ("high", "medium", "low")
ISSUE_URL = re.compile(r"^https://github\.com/([\w.-]+)/([\w.-]+)/issues/(\d+)/?$")
FIELDS = ("org", "repo", "number", "url", "title", "environment", "pattern_tags", "pattern_slugs",
          "severity", "filed", "state", "state_reason", "status", "fix_prs", "maintainer_engaged",
          "finding_folder", "needs_writeup", "excluded_prs")

QUERY = """
fragment PR on PullRequest {
  url number state merged isDraft title body
  author { login }
  repository { nameWithOwner }
  reviews(first: 100) { nodes { authorAssociation author { login __typename } } }
  comments(first: 100) { nodes { authorAssociation author { login __typename } } }
}
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    issue(number: $number) {
      url title state stateReason createdAt
      author { login }
      repository { nameWithOwner }
      comments(first: 100) { nodes { authorAssociation author { login __typename } } }
      closedByPullRequestsReferences(first: 25, includeClosedPrs: true) { nodes { ...PR } }
      timelineItems(first: 100, itemTypes: [CONNECTED_EVENT, DISCONNECTED_EVENT, CROSS_REFERENCED_EVENT]) {
        nodes {
          __typename
          ... on ConnectedEvent { subject { ... on PullRequest { ...PR } } }
          ... on DisconnectedEvent { subject { ... on PullRequest { url } } }
          ... on CrossReferencedEvent { willCloseTarget source { ... on PullRequest { ...PR } } }
        }
      }
    }
  }
}
"""


# ---------------------------------------------------------------- GitHub

def fetch(org, repo, number):
    proc = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={QUERY}",
         "-f", f"owner={org}", "-f", f"name={repo}", "-F", f"number={number}"],
        capture_output=True,
    )
    if proc.returncode:
        raise RuntimeError(proc.stderr.decode("utf-8", "replace").strip() or f"gh exited {proc.returncode}")
    data = json.loads(proc.stdout.decode("utf-8"))
    issue = ((data.get("data") or {}).get("repository") or {}).get("issue")
    if not issue:
        raise RuntimeError(json.dumps(data.get("errors") or "issue not found"))
    return issue


def is_bot(actor):
    return bool(actor) and (actor.get("__typename") == "Bot" or actor.get("login", "").endswith("[bot]"))


def maintainer_in(nodes, ours):
    for node in nodes:
        who = node.get("author") or {}
        if node.get("authorAssociation") in MAINTAINER and not is_bot(who) and who.get("login") not in ours:
            return True
    return False


FIX_WORDS = re.compile(r"\b(?:fix|fixe[sd]|fixing|close[sd]?|closing|resolve[sd]?|resolving)\b", re.I)


def references_issue(text, issue, pr_repo):
    """True when `text` names the issue by URL, by owner/repo#N, or by #N from the same repository."""
    owner_repo = issue["repository"]["nameWithOwner"]
    number = ISSUE_URL.match(issue["url"]).group(3)
    forms = [rf"github\.com/{re.escape(owner_repo)}/issues/{number}\b",
             rf"(?<![\w.-]){re.escape(owner_repo)}#{number}\b"]
    if pr_repo.lower() == owner_repo.lower():
        forms.append(rf"(?<![\w/#&])#{number}\b")
    return any(re.search(form, text, re.I) for form in forms)


def says_it_fixes(pr, issue):
    """True when the PR's own words say it fixes the issue: a line of its title or body
    references the issue with fix, close or resolve wording, or its title is a fix
    ("fix: ...", "Fix the ...") and its title or body references the issue."""
    pr_repo = (pr.get("repository") or {}).get("nameWithOwner", "")
    title, body = pr.get("title") or "", pr.get("body") or ""
    for line in [title] + body.splitlines():
        if FIX_WORDS.search(line) and references_issue(line, issue, pr_repo):
            return True
    return bool(FIX_WORDS.search(title)) and references_issue(title + "\n" + body, issue, pr_repo)


def pr_state(pr):
    if pr["merged"]:
        return "merged"
    if pr.get("isDraft") and pr["state"] == "OPEN":
        return "draft"
    return pr["state"].lower()


def fix_prs(issue, ours, excluded=()):
    """Return the issue's fix pull requests, plus the raw nodes for engagement checks."""
    found = {}      # url -> PR node
    closing = set()  # GitHub lists the PR as closing the issue
    keyword = set()  # a cross-reference that will close the issue
    linked = {}     # url -> link state after the last connected/disconnected event
    for pr in issue["closedByPullRequestsReferences"]["nodes"]:
        found[pr["url"]] = pr
        closing.add(pr["url"])
    for ev in issue["timelineItems"]["nodes"]:  # oldest first, so a later event wins
        kind = ev["__typename"]
        if kind == "ConnectedEvent":
            pr = ev.get("subject") or {}
            if pr.get("number"):
                found.setdefault(pr["url"], pr)
                linked[pr["url"]] = True
        elif kind == "DisconnectedEvent":
            url = (ev.get("subject") or {}).get("url")
            if url:
                linked[url] = False
        elif kind == "CrossReferencedEvent":
            pr = ev.get("source") or {}
            if pr.get("number"):
                found.setdefault(pr["url"], pr)
                if ev.get("willCloseTarget"):
                    keyword.add(pr["url"])
    nodes = []
    for url, pr in found.items():
        if pr["number"] in excluded:
            continue  # checked by hand: not a fix for this issue
        if url in closing:
            nodes.append(pr)
        elif linked.get(url) is False:
            continue  # unlinked, and GitHub no longer lists it as closing the issue
        elif linked.get(url) or url in keyword or says_it_fixes(pr, issue):
            nodes.append(pr)
        # otherwise it only mentions the issue: not evidence of a fix
    nodes.sort(key=lambda pr: pr["number"])
    prs = []
    for pr in nodes:
        author = (pr.get("author") or {}).get("login")
        prs.append({
            "url": pr["url"],
            "number": pr["number"],
            "is_ours": author in ours,
            "state": pr_state(pr),
            "merged": bool(pr["merged"]),
            "draft": bool(pr.get("isDraft")),
        })
    return prs, nodes


def refresh(rec, issue):
    m = ISSUE_URL.match(issue["url"])
    rec["org"], rec["repo"], rec["number"] = m.group(1), m.group(2), int(m.group(3))
    rec["url"] = issue["url"]
    rec["title"] = issue["title"]
    rec["filed"] = issue["createdAt"][:10]
    rec["state"] = issue["state"].lower()
    rec["state_reason"] = issue["stateReason"].lower() if issue.get("stateReason") else None
    ours = {(issue.get("author") or {}).get("login")} - {None}
    rec["fix_prs"], pr_nodes = fix_prs(issue, ours, set(rec.get("excluded_prs") or []))
    rec["maintainer_engaged"] = maintainer_in(issue["comments"]["nodes"], ours) or any(
        maintainer_in(pr["comments"]["nodes"], ours) or maintainer_in(pr["reviews"]["nodes"], ours)
        for pr in pr_nodes)
    rec["status"] = status_of(rec)


def status_of(rec):
    if rec.get("state") == "closed" and rec.get("state_reason") == "completed":
        return "fixed"
    if any(pr["merged"] for pr in rec.get("fix_prs") or []):
        return "fixed"
    if rec.get("state") == "closed":
        return "closed"
    return "acknowledged" if rec.get("maintainer_engaged") else "open"


# ---------------------------------------------------------------- data

def stub(url):
    org, repo, number = ISSUE_URL.match(url).groups()
    return {"org": org, "repo": repo, "number": int(number), "url": url, "title": None,
            "environment": None, "pattern_tags": [], "pattern_slugs": [], "severity": None,
            "filed": None, "state": None, "state_reason": None, "status": None, "fix_prs": [],
            "maintainer_engaged": False, "finding_folder": None, "needs_writeup": True,
            "excluded_prs": []}


def read_issue_list():
    if not ISSUES.exists():
        return []
    urls = []
    for line in ISSUES.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if not ISSUE_URL.match(line):
            sys.exit(f"issues.txt: not a GitHub issue URL: {line}")
        urls.append(line.rstrip("/"))
    return urls


OPEN_STATES = ("open", "draft")


def has_open_pr(rec, ours=None):
    return any(pr["state"] in OPEN_STATES and (ours is None or pr["is_ours"] == ours) for pr in rec["fix_prs"])


def totals(records):
    fixed = [r for r in records if r["status"] == "fixed"]
    unfixed = [r for r in records if r["status"] != "fixed"]
    with_pr = [r for r in unfixed if has_open_pr(r)]
    severity = Counter(r["severity"] or "unrated" for r in records)
    return {
        "filed": len(records),
        "fixed": len(fixed),
        "with_open_pr": len(with_pr),
        "with_open_pr_ours": sum(1 for r in with_pr if has_open_pr(r, ours=True)),
        "no_pr": len(unfixed) - len(with_pr),
        "maintainer_engaged": sum(1 for r in records if r["maintainer_engaged"]),
        "needs_writeup": sum(1 for r in records if r.get("needs_writeup")),
        "repos": len({(r["org"].lower(), r["repo"].lower()) for r in records}),
        "orgs": len({r["org"].lower() for r in records}),
        "by_severity": {s: severity[s] for s in (*SEVERITIES, "unrated") if severity[s] or s in SEVERITIES},
        "by_status": {s: sum(1 for r in records if r["status"] == s)
                      for s in ("open", "acknowledged", "fixed", "closed")},
    }


def sort_key(rec):
    return rec["org"].lower(), rec["repo"].lower(), rec["number"]


# ---------------------------------------------------------------- rendering

def pr_label(pr):
    who = "ours" if pr["is_ours"] else "community"
    return f"[#{pr['number']}]({pr['url']}) ({who}, {pr['state']})"


def table(records):
    rows = ["| Org/repo | Environment | Bug pattern | Severity | Issue | Status | Fix PR |",
            "|---|---|---|---|---|---|---|"]
    for r in records:
        env = r["environment"] or "write-up pending"
        if r.get("finding_folder"):
            env = f"[{env}]({r['finding_folder']})"
        if r["pattern_tags"]:
            links = ", ".join(f"[{slug[:2]}]({PATTERNS_URL}{slug})" for slug in r["pattern_slugs"])
            pattern = ", ".join(r["pattern_tags"]) + (f" ({links})" if links else "")
        else:
            pattern = "—"
        prs = "<br>".join(pr_label(pr) for pr in r["fix_prs"]) or "—"
        rows.append(f"| {r['org']}/{r['repo']} | {env} | {pattern} | {r['severity'] or '—'} "
                    f"| [#{r['number']}]({r['url']}) | {r['status']} | {prs} |")
    return "\n".join(rows)


def day(iso):
    d = datetime.date.fromisoformat(iso)
    return f"{d.day} {d:%B %Y}"


def plural(n, word, many=None):
    return f"{n} {word if n == 1 else (many or word + 's')}"


def counts_sentence(records, t):
    dates = sorted(r["filed"] for r in records if r["filed"])
    if not dates:
        when = ""
    elif dates[0] == dates[-1]:
        when = f" on {day(dates[0])}"
    else:
        first, last = datetime.date.fromisoformat(dates[0]), datetime.date.fromisoformat(dates[-1])
        if (first.year, first.month) == (last.year, last.month):
            when = f" between {first.day} and {day(dates[-1])}"
        else:
            when = f" between {day(dates[0])} and {day(dates[-1])}"
    return (f"This repository collects the {plural(t['filed'], 'issue')} we filed in "
            f"{plural(t['repos'], 'repository', 'repositories')} across "
            f"{plural(t['orgs'], 'organisation')}{when}.")


def status_line(today, t):
    line = (f"Status as of {today}: {t['fixed']} fixed, {t['with_open_pr']} with an open fix PR "
            f"({t['with_open_pr_ours']} of them ours), {t['no_pr']} with no open fix PR. "
            f"A maintainer has commented on, or reviewed a fix for, {plural(t['maintainer_engaged'], 'issue')}.")
    if t["needs_writeup"]:
        line += f" {plural(t['needs_writeup'], 'issue')} still {'needs' if t['needs_writeup'] == 1 else 'need'} a write-up."
    return line


def severity_sentence(t):
    parts = [f"{t['by_severity'].get(s, 0)} {s}" for s in SEVERITIES]
    if t["by_severity"].get("unrated"):
        parts.append(f"{t['by_severity']['unrated']} not yet rated")
    return "Severity (high, medium, low) is our own rating from our tracker: " + ", ".join(parts) + "."


def replace_block(text, name, content):
    pattern = re.compile(rf"(<!-- {name}:start -->)(.*?)(<!-- {name}:end -->)", re.S)
    if not pattern.search(text):
        sys.exit(f"README.md: missing <!-- {name}:start --> / <!-- {name}:end --> markers")
    return pattern.sub(lambda m: m.group(1) + content + m.group(3), text, count=1)


def finding_status(rec, today):
    prs = "; fix PR " + ", ".join(pr_label(pr) for pr in rec["fix_prs"]) if rec["fix_prs"] else "; no fix PR yet"
    return f"- Status (as of {today}): {rec['status']}{prs}"


def write_file(path, text):
    # open() rather than Path.write_text(..., newline=), which needs Python 3.10.
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def write(path, text):
    if path.read_text(encoding="utf-8") != text:
        write_file(path, text)


# ---------------------------------------------------------------- main

def main():
    data = json.loads(DATA.read_text(encoding="utf-8")) if DATA.exists() else {"issues": []}
    records = data["issues"]
    by_url = {r["url"]: r for r in records}

    failed = []
    for url in read_issue_list():
        if url in by_url:
            continue
        org, repo, number = ISSUE_URL.match(url).groups()
        try:
            canonical = fetch(org, repo, int(number))["url"]
        except RuntimeError as err:
            failed.append(f"{url}: {err}")
            continue
        if canonical in by_url:
            continue  # an old URL of a moved repository
        rec = stub(canonical)
        records.append(rec)
        by_url[canonical] = rec
        print(f"new issue, needs a write-up: {canonical}")

    for rec in records:
        try:
            refresh(rec, fetch(rec["org"], rec["repo"], rec["number"]))
        except RuntimeError as err:
            failed.append(f"{rec['url']}: {err}")
            continue
        prs = ", ".join(f"#{p['number']} ({'ours' if p['is_ours'] else 'community'}, {p['state']})"
                        for p in rec["fix_prs"]) or "no PR"
        print(f"{rec['org']}/{rec['repo']}#{rec['number']}: {rec['status']}; {prs}")

    if failed:
        print("\n".join(["could not read:"] + failed), file=sys.stderr)
        sys.exit(1)

    records = sorted(({k: rec.get(k) for k in FIELDS} for rec in records), key=sort_key)
    for rec in records:
        rec["needs_writeup"] = bool(rec["needs_writeup"])
        rec["pattern_tags"] = rec["pattern_tags"] or []
        rec["pattern_slugs"] = rec["pattern_slugs"] or []
        rec["excluded_prs"] = rec["excluded_prs"] or []
    t = totals(records)
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    today = now.date().isoformat()

    write_file(DATA, json.dumps({"generated_at": now.isoformat().replace("+00:00", "Z"), "totals": t,
                                 "issues": records}, indent=2, ensure_ascii=False) + "\n")

    text = README.read_text(encoding="utf-8")
    text = replace_block(text, "counts", counts_sentence(records, t))
    text = replace_block(text, "status", status_line(today, t))
    text = replace_block(text, "table", "\n" + table(records) + "\n")
    text = replace_block(text, "severity", severity_sentence(t))
    write(README, text)

    for rec in records:
        if not rec["finding_folder"]:
            continue
        readme = ROOT / rec["finding_folder"] / "README.md"
        body = readme.read_text(encoding="utf-8")
        new, n = re.subn(r"^- Status\b.*$", finding_status(rec, today), body, count=1, flags=re.M)
        if not n:
            print(f"warning: no '- Status' line in {readme.relative_to(ROOT)}", file=sys.stderr)
        write(readme, new)

    print(status_line(today, t))


if __name__ == "__main__":
    main()
