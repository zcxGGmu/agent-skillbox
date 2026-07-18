---
name: oss-pr-lifecycle
description: End-to-end open-source contribution workflow for finding upstream issues, ranking opportunities, implementing fixes one-by-one on separate branches, pushing PRs with GitHub CLI, and scheduling/performing PR feedback monitoring and replies. Use when the user asks Codex to scout OSS issues, solve multiple upstream issues by priority, submit PRs to an upstream repository, or monitor/respond to community feedback on PRs.
---

# OSS PR Lifecycle

## Overview

Use this skill to run a complete OSS contribution loop: scout upstream work, rank it, implement prioritized fixes, open PRs, and monitor/respond to review feedback. Keep each PR small, evidence-backed, independently reviewable, and validated before moving to the next one.

## Inputs And Defaults

- Resolve the target repository from the user's URL or current checkout. If only a local checkout is provided, inspect `git remote -v`; prefer `upstream` as canonical, otherwise infer the fork parent with `gh repo view --json parent` when available.
- Default scope: open upstream issues plus fast local code exploration. Favor issue-backed work over broad code-derived refactors.
- Default branch prefix: `codex/`.
- Default PR base: upstream default branch, usually `main`.
- Default output: create real branches, commits, pushes, PRs, and a monitoring automation when the user asks for the whole lifecycle.
- Ask only when the upstream is ambiguous, credentials are unavailable, or the requested work is security-sensitive or too broad to execute safely.

## Phase 1: Scout And Rank

1. Read contribution rules first: `AGENTS.md`, `CONTRIBUTING*`, `CODE_OF_CONDUCT*`, `SECURITY*`, issue/PR templates, CI workflows, and README contribution notes.
2. If `$oss-contribution-scout` is available, read and apply it for upstream issue collection and scoring. Otherwise, recreate its essentials:
   - Collect open issues with `gh issue list --repo OWNER/REPO --state open --limit 200 --json number,title,labels,comments,updatedAt,url`.
   - Inspect promising issues with `gh issue view`.
   - Scan code with `rg` for localized defects, TODO/FIXME/HACK, skipped tests, known failures, and small feature gaps.
3. Rank candidates by:
   - Priority: user impact, maintainer signal, recurrence, CI/project leverage.
   - Difficulty: touched modules, test scope, review complexity.
   - Confidence: issue clarity, reproduction path, code evidence, maintainer guidance.
4. Pick a short ordered queue. Prefer small, independent PRs that can be reviewed separately. Defer vague, stale, policy-sensitive, security-sensitive, or rewrite-sized work.

## Phase 2: Implement Sequentially

For each selected issue, finish the current PR before starting the next:

1. Start clean:
   - `git status --short --branch`
   - Fetch upstream/main and branch from a clean base unless the user asks for stacked PRs.
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
   - Mention the behavior, not the implementation mechanics.
   - Remove generated lockfiles/caches unless the repo tracks them.

## Phase 3: Push And Open PRs

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
   - Note known caveats such as external API rate limits or flaky unrelated tests.
4. Verify creation:
   - `gh pr list --repo OWNER/REPO --author @me --state open --json number,title,headRefName,url,baseRefName`
   - Capture PR URLs for the final response and later monitoring.

## Phase 4: Monitor And Reply

When the user asks to monitor PR feedback, create a recurring automation if the environment supports it. Otherwise, perform a one-shot check and explain that scheduling is unavailable.

1. Discover and use the scheduler tool when available. Create a cron-style monitor scoped only to the target PR URLs.
2. Store durable state in the workspace, usually `.codex/pr-monitor-state.json`, so repeated runs do not reply twice to the same comment or review thread.
3. Each run checks:
   - Issue comments: `gh api repos/OWNER/REPO/issues/<number>/comments`
   - Reviews: `gh api repos/OWNER/REPO/pulls/<number>/reviews`
   - Review comments: `gh api repos/OWNER/REPO/pulls/<number>/comments`
   - PR metadata and mergeability: `gh pr view <number> --repo OWNER/REPO --json state,mergeable,reviewDecision,comments,latestReviews,statusCheckRollup`
   - CI status: `gh pr checks <number> --repo OWNER/REPO`
4. Reply only when useful:
   - Post concise acknowledgements, answers, or status updates for clear maintainer/community feedback.
   - Do not post generic "checking" comments.
   - Do not reply defensively or repeatedly.
   - Do not expose tokens, logs with secrets, private local paths, or security-sensitive details.
5. If feedback requests a code change:
   - Switch to that PR branch.
   - Confirm the worktree is clean or contains only monitor-owned changes.
   - Implement the smallest appropriate fix.
   - Run targeted tests/lint, commit, push.
   - Reply with what changed and what was tested.
6. If feedback is ambiguous, conflicting, asks for a broad redesign, or involves security/policy concerns:
   - Do not guess.
   - Avoid a public reply unless a safe acknowledgement is clearly helpful.
   - Summarize the blocker in the monitor output for the user.

## Quality Bar

- Keep PRs independent unless the user explicitly requests a stacked series.
- Prefer issue-backed, tested changes over speculative improvements.
- Use exact branch names, commit hashes, PR URLs, and test commands in handoff summaries.
- Treat `gh` auth and tokens carefully: never echo secrets, store them in logs, commit them, or include them in automation prompts.
- Before finalizing, verify:
  - All selected issues have either a branch/PR or a clear deferred reason.
  - Every branch has tests/lint run or a documented blocker.
  - Every PR URL is captured.
  - Monitoring is scoped to the created PRs and has duplicate-reply protection.
