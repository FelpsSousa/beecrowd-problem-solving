#!/usr/bin/env python3
"""Short commands for the branch -> commit -> PR -> merge cycle.

Usage:
    python scripts/flow.py start <type> <description...>   # update main, create <type>/<slug>
    python scripts/flow.py commit [summary...]             # draft a Conventional Commit, open the editor
    python scripts/flow.py pr [--draft]                    # push and open the PR with a generated body
    python scripts/flow.py merge <number>                  # squash-merge, delete the branch, update main
    python scripts/flow.py week --points P --rank R        # append a line to trackers/ranking-log.md

Every command accepts --dry-run, which prints what would happen and changes nothing.

The messages are drafted from facts the repository already holds (branch name,
staged paths, each problem's README metadata, test cases), never invented.
`commit` opens your editor on the draft, so the final wording is always yours.
When a subject cannot be derived (a script or docs change), pass the summary.

Exit code: 0 = done, 1 = refused (dirty tree, nothing staged, invalid input) or git/gh failed.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from repo_lib import parse_metadata, test_cases
from sync_index import collect_entries, read_title

REPO_ROOT = Path(__file__).resolve().parent.parent

# Conventional Commit types, same list as felpsxp-template's pr-title.yml.
COMMIT_TYPES: tuple[str, ...] = (
    "feat", "fix", "docs", "style", "refactor", "perf",
    "test", "build", "ci", "chore", "revert", "security",
)
# Branch prefixes that are not commit types map to (type, scope).
BRANCH_ALIASES: dict[str, tuple[str, str]] = {
    "migration": ("feat", "migration"),
    "problem": ("feat", "problems"),
}
# Top-level folder -> commit scope.
AREA_SCOPES: dict[str, str] = {
    "problems": "problems",
    "scripts": "scripts",
    "docs": "docs",
    "trackers": "trackers",
    "templates": "templates",
    ".github": "ci",
}
SUBJECT_MAX = 72
GIT_STATUS: dict[str, str] = {"A": "added", "M": "modified", "D": "deleted", "R": "renamed"}
RANKING_LOG = Path("trackers") / "ranking-log.md"
RANKING_HEADER = (
    "# Ranking Log\n\n"
    "Weekly snapshot of the public Beecrowd profile next to what this repository documents.\n"
    "Appended by `python scripts/flow.py week`.\n\n"
    "| Date | Points | World Rank | Solved in Repo |\n"
    "|------|--------|------------|----------------|\n"
)


class FlowError(Exception):
    """A refusal with a message meant for the person at the terminal."""


@dataclass(frozen=True)
class Change:
    status: str  # one of GIT_STATUS's values
    path: str


@dataclass(frozen=True)
class ProblemInfo:
    id: int
    title: str
    category: str
    difficulty: str
    language: str
    doc_level: str
    status: str
    tests: int
    removed: bool = False

    def line(self) -> str:
        if self.removed:
            return f"- {self.id}: removed"
        return (
            f"- {self.id} {self.title}: {self.language}, {self.category}, level {self.difficulty}, "
            f"{self.doc_level}, {self.tests} test case(s), status {self.status}"
        )


# --- Pure helpers (unit tested) ---------------------------------------------


def slugify(words: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", words.lower()).strip("-")
    if not slug:
        raise FlowError("the branch description is empty after removing symbols")
    return slug


def branch_name(kind: str, description: str) -> str:
    if kind not in COMMIT_TYPES and kind not in BRANCH_ALIASES:
        allowed = ", ".join((*COMMIT_TYPES, *BRANCH_ALIASES))
        raise FlowError(f"unknown branch type '{kind}'; use one of: {allowed}")
    return f"{kind}/{slugify(description)}"


def parse_name_status(lines: list[str]) -> list[Change]:
    """`git diff --name-status` lines -> changes (renames keep the new path)."""
    changes: list[Change] = []
    for line in lines:
        parts = line.split("\t")
        code = parts[0][:1]
        changes.append(Change(GIT_STATUS.get(code, "modified"), parts[-1]))
    return changes


def type_and_scope(branch: str, paths: list[str]) -> tuple[str, str]:
    prefix = branch.split("/", 1)[0]
    if prefix in BRANCH_ALIASES:
        return BRANCH_ALIASES[prefix]
    kind = prefix if prefix in COMMIT_TYPES else "chore"
    areas = {AREA_SCOPES.get(Path(p).parts[0], "repo") for p in paths}
    scope = areas.pop() if len(areas) == 1 else ""
    return kind, scope


def problem_folder(path: str) -> str | None:
    parts = Path(path).parts
    if len(parts) >= 3 and parts[0] == "problems":
        return "/".join(parts[:3])
    return None


def read_problem(root: Path, folder: str) -> ProblemInfo:
    problem_dir = root / folder
    raw_id = problem_dir.name.split("-", 1)[0]
    readme = problem_dir / "README.md"
    if not readme.is_file():
        return ProblemInfo(int(raw_id), "", "", "", "", "", "", 0, removed=True)
    text = readme.read_text(encoding="utf-8")
    meta = parse_metadata(text)
    return ProblemInfo(
        id=int(meta.get("Problem ID") or raw_id),
        title=read_title(text),
        category=meta.get("Category", "?"),
        difficulty=meta.get("Difficulty Level", "?"),
        language=meta.get("Primary Language", "?"),
        doc_level=meta.get("Documentation Level", "?"),
        status=meta.get("Status", "?"),
        tests=len(test_cases(problem_dir)),
    )


def problems_in(root: Path, changes: list[Change]) -> tuple[list[ProblemInfo], set[int]]:
    """Problems touched by `changes`, and the ids whose README was added (new problems)."""
    folders = sorted({f for c in changes if (f := problem_folder(c.path))})
    new_ids = {
        int(Path(c.path).parts[2].split("-", 1)[0])
        for c in changes
        if c.status == "added" and Path(c.path).name == "README.md" and problem_folder(c.path)
    }
    infos = sorted((read_problem(root, f) for f in folders), key=lambda p: p.id)
    return infos, new_ids


def id_list(ids: list[int]) -> str:
    if len(ids) <= 3:
        return ", ".join(map(str, ids))
    return f"{len(ids)} problems ({ids[0]} to {ids[-1]})"


def derive_subject(branch: str, problems: list[ProblemInfo], new_ids: set[int]) -> str | None:
    """A subject from the problems alone, or None when only a human can say what changed."""
    if not problems:
        return None
    ids = [p.id for p in problems]
    if branch.startswith("migration/"):
        return f"migrate {id_list(ids)} from the legacy repositories"
    if len(problems) == 1:
        p = problems[0]
        if p.removed:
            return f"remove {p.id}"
        verb = "add" if p.id in new_ids else "update"
        return f"{verb} {p.id} {p.title.lower()}"
    verb = "add" if set(ids) <= new_ids else "update"
    return f"{verb} {id_list(ids)}"


def format_header(kind: str, scope: str, subject: str) -> str:
    subject = subject.strip()
    subject = subject[:1].lower() + subject[1:]
    header = f"{kind}({scope}): {subject}" if scope else f"{kind}: {subject}"
    if len(header) > SUBJECT_MAX:
        raise FlowError(f"the subject line has {len(header)} characters; keep it within {SUBJECT_MAX}")
    return header


def file_summary(changes: list[Change]) -> str:
    counts = {label: sum(1 for c in changes if c.status == label) for label in GIT_STATUS.values()}
    parts = [f"{n} {label}" for label, n in counts.items() if n]
    return "Files: " + ", ".join(parts) + "."


def commit_message(header: str, problems: list[ProblemInfo], changes: list[Change]) -> str:
    body = [file_summary(changes)]
    if problems:
        body += ["", "Problems:", *(p.line() for p in problems)]
    return header + "\n\n" + "\n".join(body) + "\n"


def pr_title(branch: str, subjects: list[str]) -> str:
    """The only commit's header, or one built from the branch name."""
    if len(subjects) == 1:
        return subjects[0]
    prefix, _, rest = branch.partition("/")
    kind, scope = BRANCH_ALIASES.get(prefix, (prefix if prefix in COMMIT_TYPES else "chore", ""))
    id_range = re.fullmatch(r"(\d+)-(\d+)", rest)
    if prefix == "migration" and id_range:
        return format_header(kind, scope, f"migrate {id_range.group(1)} to {id_range.group(2)}")
    return format_header(kind, scope, rest.replace("-", " "))


def pr_body(branch: str, subjects: list[str], problems: list[ProblemInfo], changes: list[Change], gate: str) -> str:
    lines = ["## Summary", "", *(f"- {s}" for s in subjects), ""]
    active = [p for p in problems if not p.removed]
    if active:
        lines += [
            "## Problems",
            "",
            "| ID | Title | Category | Level | Language | Doc | Tests | Status |",
            "|----|-------|----------|-------|----------|-----|-------|--------|",
            *(
                f"| {p.id} | {p.title} | {p.category} | {p.difficulty} | {p.language} | "
                f"{p.doc_level} | {p.tests} | {p.status} |"
                for p in active
            ),
            "",
        ]
    lines += ["## Verification", "", f"- `python scripts/check_all.py`: {gate}", f"- {file_summary(changes)}", ""]
    if branch.startswith("migration/"):
        lines += [
            "## Migration checklist",
            "",
            "- [ ] Every problem resubmitted and accepted with the code in this PR",
            "- [ ] Language kept as originally accepted, or the reason written in the README",
            "- [ ] Samples copied from the statement; edge cases added per doc level",
            "- [ ] Legacy header, social links and license lines removed",
            "- [ ] Mistakes from the legacy history recorded in `trackers/mistakes-log.md`",
            "",
        ]
    lines += [
        "## Checklist",
        "",
        "- [ ] I can explain every change in this PR without looking at it",
        "- [ ] `Status: Solved` is used only for code accepted by the judge",
        "- [ ] Public content is in English",
    ]
    return "\n".join(lines) + "\n"


def ranking_line(date: dt.date, points: float, rank: int, solved_in_repo: int) -> str:
    return f"| {date.isoformat()} | {points:.2f} | {rank} | {solved_in_repo} |\n"


# --- Git and gh (thin wrappers) ---------------------------------------------


def run(cmd: list[str], dry_run: bool = False, capture: bool = False) -> str:
    if dry_run:
        print("would run:", " ".join(cmd))
        return ""
    try:
        result = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=capture, check=True)
    except FileNotFoundError as exc:
        raise FlowError(f"'{cmd[0]}' was not found on PATH") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "").strip() if capture else ""
        raise FlowError(f"'{' '.join(cmd)}' failed" + (f": {detail}" if detail else "")) from exc
    return result.stdout or ""


def git_lines(*args: str) -> list[str]:
    return [line for line in run(["git", *args], capture=True).splitlines() if line]


def current_branch() -> str:
    branch = run(["git", "branch", "--show-current"], capture=True).strip()
    if not branch:
        raise FlowError("not on a branch (detached HEAD)")
    return branch


def require_feature_branch() -> str:
    branch = current_branch()
    if branch == "main":
        raise FlowError("you are on main; start a branch first: python scripts/flow.py start <type> <description>")
    return branch


def run_gate() -> str:
    result = subprocess.run([sys.executable, "scripts/check_all.py"], cwd=REPO_ROOT, capture_output=True, text=True)
    return "passed" if result.returncode == 0 else "FAILED"


# --- Commands ---------------------------------------------------------------


def cmd_start(args: argparse.Namespace) -> None:
    branch = branch_name(args.type, " ".join(args.description))
    if git_lines("status", "--porcelain", "--untracked-files=no"):
        raise FlowError("tracked files have uncommitted changes; commit or stash them first")
    run(["git", "switch", "main"], args.dry_run)
    run(["git", "pull", "--ff-only"], args.dry_run)
    run(["git", "switch", "-c", branch], args.dry_run)
    print(f"on {branch}")


def cmd_commit(args: argparse.Namespace) -> None:
    branch = require_feature_branch()
    changes = parse_name_status(git_lines("diff", "--cached", "--name-status"))
    if not changes:
        raise FlowError("nothing is staged; use git add first")
    problems, new_ids = problems_in(REPO_ROOT, changes)
    subject = " ".join(args.summary) or derive_subject(branch, problems, new_ids)
    if not subject:
        raise FlowError('no problem changed, so describe the change: python scripts/flow.py commit "add the flow cli"')
    kind, scope = type_and_scope(branch, [c.path for c in changes])
    message = commit_message(format_header(kind, scope, subject), problems, changes)
    if args.dry_run:
        print(message, end="")
        return
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as handle:
        handle.write(message)
    try:
        run(["git", "commit", "-F", handle.name] + ([] if args.no_edit else ["--edit"]))
    finally:
        Path(handle.name).unlink(missing_ok=True)


def cmd_pr(args: argparse.Namespace) -> None:
    branch = require_feature_branch()
    subjects = list(reversed(git_lines("log", "--format=%s", "main..HEAD")))
    if not subjects:
        raise FlowError("this branch has no commits ahead of main")
    changes = parse_name_status(git_lines("diff", "--name-status", "main...HEAD"))
    problems, _new = problems_in(REPO_ROOT, changes)
    gate = run_gate()
    title = pr_title(branch, subjects)
    body = pr_body(branch, subjects, problems, changes, gate)
    if gate != "passed" and not args.dry_run:
        raise FlowError("python scripts/check_all.py failed; fix it before opening the PR")
    if args.dry_run:
        print(f"title: {title}\n\n{body}", end="")
        return
    run(["git", "push", "-u", "origin", branch])
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as handle:
        handle.write(body)
    try:
        cmd = ["gh", "pr", "create", "--base", "main", "--title", title, "--body-file", handle.name]
        run(cmd + (["--draft"] if args.draft else []))
    finally:
        Path(handle.name).unlink(missing_ok=True)


def cmd_merge(args: argparse.Namespace) -> None:
    run(["gh", "pr", "merge", str(args.number), "--squash", "--delete-branch"], args.dry_run)
    run(["git", "switch", "main"], args.dry_run)
    run(["git", "pull", "--ff-only"], args.dry_run)
    run(["git", "fetch", "--prune"], args.dry_run)


def cmd_week(args: argparse.Namespace) -> None:
    line = ranking_line(dt.date.today(), args.points, args.rank, len(collect_entries(REPO_ROOT)))
    if args.dry_run:
        print(line, end="")
        return
    log = REPO_ROOT / RANKING_LOG
    text = log.read_text(encoding="utf-8") if log.is_file() else RANKING_HEADER
    log.write_text(text + line, encoding="utf-8")
    print(f"appended to {RANKING_LOG.as_posix()}: {line}", end="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    start = sub.add_parser("start", help="update main and create a branch")
    start.add_argument("type", help=f"one of: {', '.join((*COMMIT_TYPES, *BRANCH_ALIASES))}")
    start.add_argument("description", nargs="+")
    start.set_defaults(func=cmd_start)

    commit = sub.add_parser("commit", help="draft a Conventional Commit from the staged changes")
    commit.add_argument("summary", nargs="*", help="subject text; optional when only problems changed")
    commit.add_argument("--no-edit", action="store_true", help="commit the draft without opening the editor")
    commit.set_defaults(func=cmd_commit)

    pr = sub.add_parser("pr", help="push the branch and open a pull request")
    pr.add_argument("--draft", action="store_true")
    pr.set_defaults(func=cmd_pr)

    merge = sub.add_parser("merge", help="squash-merge a PR and return to an updated main")
    merge.add_argument("number", type=int)
    merge.set_defaults(func=cmd_merge)

    week = sub.add_parser("week", help="log this week's Beecrowd points and rank")
    week.add_argument("--points", type=float, required=True)
    week.add_argument("--rank", type=int, required=True)
    week.set_defaults(func=cmd_week)

    for sp in (start, commit, pr, merge, week):
        sp.add_argument("--dry-run", action="store_true", help="print what would happen, change nothing")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except FlowError as exc:
        print(f"flow: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
