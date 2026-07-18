---
name: oss-pr-lifecycle
description: End-to-end and continuous open-source contribution workflow for discovering upstream issues, maintaining a contribution backlog, autonomously exploring codebases for contribution points, implementing prioritized fixes on separate branches, opening PRs with GitHub CLI, and monitoring/responding to community feedback over time. Use when the user asks Codex to scout OSS opportunities, run a long-lived autonomous contributor loop, solve upstream issues by priority, submit PRs, or continuously monitor and respond to PR/repository feedback.
---

# OSS PR Lifecycle

## Overview

Use this skill to run either a one-shot OSS contribution push or a long-lived autonomous contribution program. The continuous mode should keep watching upstream, maintain a ranked backlog, open small independent PRs, follow through on review feedback, and periodically report what changed.

## Operating Modes

- **One-shot mode**: Use when the user asks to find issues, solve a specified set, open PRs, or monitor a known PR list. Complete the requested queue and stop after a clear handoff.
- **Continuous mode**: Use when the user wants ongoing autonomous contribution. Create recurring automation that repeatedly scouts upstream, refreshes the backlog, chooses the next safe task, implements it, opens a PR, and follows feedback until resolved.
- **Hybrid mode**: Use when the user names a starting set of issues but also wants long-term follow-up. Finish the named queue first, then switch to continuous scouting and backlog management.

## Inputs And Defaults

- Resolve the target repository from the user's URL or current checkout. If only a local checkout is provided, inspect `git remote -v`; prefer `upstream` as canonical, otherwise infer the fork parent with `gh repo view --json parent` when available.
- Default branch prefix: `codex/`.
- Default PR base: upstream default branch, usually `main`.
- Default contribution style: small, issue-backed, tested, independently reviewable PRs.
- Default continuous limits: at most 3 active open PRs per repository unless the user explicitly asks for more; do not create noisy PR volume.
- Ask only when the upstream is ambiguous, credentials are unavailable, the work is security-sensitive, or an intended action crosses a decision gate.

## Persistent State

For continuous mode, maintain durable state under `.codex/oss-pr-lifecycle-state/` in the target workspace. Create the directory if missing and keep files small, readable, and safe to commit-ignore.

- `repos.json`: watched upstream/fork/base configuration and contribution rules summary.
- `backlog.json`: candidate issues and code-derived opportunities with priority, difficulty, confidence, source evidence, status, last reviewed time, and next action.
- `prs.json`: created PRs, branch names, commit hashes, CI status, review state, and merge/close outcome.
- `feedback.json`: seen issue comments, review IDs, review comments, and reply/action status to prevent duplicate replies.
- `decisions.md`: concise notes on deferred items, user escalation requests, and rationale for autonomous choices.

Never store tokens, secrets, private credentials, or raw sensitive logs in state files.

## Recurring Cadence

When scheduling is available, create recurring automation for continuous mode. Use these cadences unless the user specifies otherwise:

- **Hourly PR follow-up**: check open PR comments, reviews, requested changes, CI failures, merge conflicts, and maintainer questions.
- **Daily upstream scout**: fetch new/updated issues, labels, milestones, maintainer comments, recent merged PRs, and release notes; refresh backlog scores.
- **Weekly code exploration**: scan the codebase for localized contribution points such as missing tests, skipped/flaky tests, TODO/FIXME/HACK with impact evidence, duplicated logic, outdated docs, brittle error handling, and small feature gaps.
- **Weekly report**: summarize active PRs, merged/closed items, new top backlog entries, autonomous actions taken, blockers, and recommended next moves.

If scheduling is unavailable, perform a one-shot run and tell the user what could not be automated.

## Phase 1: Scout And Rank

1. Read contribution rules first: `AGENTS.md`, `CONTRIBUTING*`, `CODE_OF_CONDUCT*`, `SECURITY*`, issue/PR templates, CI workflows, release notes, roadmap docs, and README contribution notes.
2. If `$oss-contribution-scout` is available, read and apply it for upstream issue collection and scoring. Otherwise, recreate its essentials:
   - Collect open issues with `gh issue list --repo OWNER/REPO --state open --limit 200 --json number,title,labels,comments,updatedAt,url`.
   - Inspect promising issues with `gh issue view`.
   - Inspect recently merged PRs to infer maintainer preferences and project direction.
   - Scan code with `rg` for localized defects, TODO/FIXME/HACK, skipped tests, known failures, and small feature gaps.
3. Rank candidates by:
   - Priority: user impact, maintainer signal, recurrence, CI/project leverage.
   - Difficulty: touched modules, test scope, review complexity.
   - Confidence: issue clarity, reproduction path, code evidence, maintainer guidance.
   - Fit: good first PR, focused PR, needs maintainer confirmation, avoid/defer.
4. Update `backlog.json` instead of producing only an ephemeral report. Preserve skipped/deferred rationale so future runs do not rediscover the same dead ends.

## Phase 2: Autonomous Backlog Selection

When the user has not named the next task, choose autonomously from the backlog using this order:

1. Maintainer-requested changes on already-open PRs.
2. CI failures or merge conflicts on already-open PRs that are caused by the PR and locally fixable.
3. Clear high-confidence issue-backed bugs with small blast radius.
4. Missing regression tests or docs updates directly tied to active issues or recent maintainer comments.
5. Code-derived opportunities only when evidence is concrete and the patch can stay small.

Do not select:

- Security-sensitive findings that require private disclosure.
- Broad rewrites, architecture migrations, dependency churn, or style-only mass changes.
- Product-direction changes without maintainer signal.
- Work that would push the active PR count above the configured limit.

## Phase 3: Implement Sequentially

For each selected task, finish the current PR before starting the next:

1. Start clean:
   - `git status --short --branch`
   - Fetch upstream/base and branch from a clean base unless the user asks for stacked PRs.
2. Create a dedicated branch:
   - Format: `codex/issue-<number>-<short-slug>` for issue-backed work.
   - Use one branch and one commit series per PR.
3. Inspect the smallest relevant area before editing:
   - Read nearby implementation, tests, docs, and existing patterns.
   - Prefer existing project abstractions and style.
4. Implement the smallest reviewable fix:
   - Do not rewrite broad modules to solve a narrow issue.
   - Preserve user changes and unrelated work.
   - Avoid public exploit details; use private disclosure paths for security findings.
5. Add focused tests:
   - Add regression tests that fail before the change when practical.
   - Use targeted pytest/unit tests first; broaden only when the touched surface is shared.
6. Verify before committing:
   - Run targeted tests and lint/format commands used by the repo.
   - If a full suite is impractical or blocked by external services, run the most relevant subset and document the limitation.
7. Commit with a concise subject:
   - Mention the behavior, not implementation mechanics.
   - Remove generated lockfiles/caches unless the repo tracks them.
8. Update state:
   - Mark the backlog item in progress/done/deferred.
   - Record branch, commit hash, tests run, and caveats.

## Phase 4: Push And Open PRs

Use GitHub CLI when available. Install or authenticate `gh` only with user authorization and never print tokens.

1. Push every completed branch to the user's fork:
   - `git push -u origin <branch>`
2. Create PRs against upstream:
   - Use `gh pr create --repo OWNER/REPO --base <base> --head <fork-owner>:<branch> --title <title> --body-file <file>`.
   - Prefer `--body-file` over inline `--body` to avoid shell quoting issues.
3. PR body structure:
   - `## Summary` with 2-4 bullets.
   - `Fixes #NNN` or `Refs #NNN` when appropriate.
   - `## Testing` with exact commands run.
   - Known caveats such as external API rate limits or flaky unrelated tests.
4. Verify creation:
   - `gh pr list --repo OWNER/REPO --author @me --state open --json number,title,headRefName,url,baseRefName`
   - Record PR URLs in `prs.json`.

## Phase 5: Monitor And Reply

Each monitor run checks only the configured repository/PRs unless continuous mode explicitly includes upstream scouting.

1. Read state first so comments and reviews are not processed twice.
2. Check:
   - Issue comments: `gh api repos/OWNER/REPO/issues/<number>/comments`
   - Reviews: `gh api repos/OWNER/REPO/pulls/<number>/reviews`
   - Review comments: `gh api repos/OWNER/REPO/pulls/<number>/comments`
   - PR metadata and mergeability: `gh pr view <number> --repo OWNER/REPO --json state,mergeable,reviewDecision,comments,latestReviews,statusCheckRollup`
   - CI status: `gh pr checks <number> --repo OWNER/REPO`
3. Reply only when useful:
   - Post concise acknowledgements, answers, or status updates for clear maintainer/community feedback.
   - Do not post generic "checking" comments.
   - Do not reply defensively or repeatedly.
   - Do not expose tokens, logs with secrets, private local paths, or security-sensitive details.
4. If feedback requests a code change:
   - Switch to that PR branch.
   - Confirm the worktree is clean or contains only monitor-owned changes.
   - Implement the smallest appropriate fix.
   - Run targeted tests/lint, commit, push.
   - Reply with what changed and what was tested.
5. If feedback is ambiguous, conflicting, asks for a broad redesign, or involves security/policy concerns:
   - Do not guess.
   - Avoid a public reply unless a safe acknowledgement is clearly helpful.
   - Summarize the blocker in `decisions.md` and in the monitor output for the user.
6. Update `feedback.json` and `prs.json` after every processed item.

## Decision Gates

Autonomous runs may proceed without asking for:

- Small bug fixes with clear issue/code evidence.
- Regression tests, docs fixes, typo fixes, and localized compatibility improvements.
- Review-requested changes that are narrow and consistent with the PR's original scope.
- CI fixes clearly caused by the PR.

Pause and ask the user before:

- Opening more active PRs than the configured limit.
- Taking on broad refactors, architecture changes, controversial product behavior, or dependency upgrades.
- Publicly discussing security-sensitive findings.
- Responding to hostile, legal, governance, or identity-sensitive comments.
- Closing, deleting, force-pushing over unrelated work, or changing repository settings.

## Reporting

For one-shot mode, final output should include selected issues, branches, commits, tests, PR URLs, and caveats.

For continuous mode, every scheduled run should end with a concise report:

- New upstream signals found.
- Backlog changes and top next candidates.
- PR comments/reviews processed and replies posted.
- Code changes, commits, pushes, and tests run.
- CI/merge status.
- Items requiring user decision.

## Quality Bar

- Keep PRs independent unless the user explicitly requests a stacked series.
- Prefer issue-backed, tested changes over speculative improvements.
- Use exact branch names, commit hashes, PR URLs, and test commands in handoff summaries.
- Treat `gh` auth and tokens carefully: never echo secrets, store them in logs, commit them, or include them in automation prompts.
- In continuous mode, optimize for maintainership trust: fewer better PRs, fast review follow-up, no spam, and clear rationale.
- Before finalizing or ending a scheduled run, verify:
  - State files were updated.
  - Active PR count is within limit.
  - Every processed comment/review is marked seen.
  - Every code change has tests/lint run or a documented blocker.
  - Every public reply was necessary, specific, and non-sensitive.
