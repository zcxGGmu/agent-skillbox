---
name: oss-contribution-scout
description: Scout open-source contribution opportunities for a specified repository or local fork by collecting upstream GitHub issues, reading maintainer contribution signals, scanning code for defects and feature gaps, and producing a categorized ranked report with priority, difficulty, confidence, evidence, and next PR recommendations. Use when asked to find OSS/open-source contribution targets, triage upstream issues, explore codebase bugs, identify feature contribution points, or build a contribution roadmap.
---

# OSS Contribution Scout

## Overview

Use this skill to turn an upstream open-source repository into an actionable contribution map. The output must combine maintainer-visible issue demand with local codebase exploration, then rank opportunities by contribution value, implementation difficulty, and confidence.

## Required Inputs

Resolve these before collecting data:

- **Target repository**: GitHub `owner/repo`, URL, or local checkout.
- **Upstream**: Prefer the canonical upstream, not the user's fork. For a local checkout, inspect `git remote -v`; prefer `upstream` when present, otherwise identify whether `origin` is a fork parent with `gh repo view --json parent`.
- **Scope**: Default to open issues plus fast static code exploration. Ask only if the target repo or upstream is ambiguous.
- **Output path**: Default to a Markdown report in the current workspace, not inside the target repository, unless the user asks otherwise.

## Workflow

1. **Read contribution rules**
   - Inspect `AGENTS.md`, `CONTRIBUTING*`, `CODE_OF_CONDUCT*`, `SECURITY*`, issue templates, PR template, README contribution sections, labels, CI workflows, and release/roadmap docs.
   - Record constraints such as CLA/DCO, sign-off, coding style, supported languages, test commands, maintainer review expectations, and security disclosure policy.

2. **Collect upstream issue inventory**
   - Use `scripts/collect_github_issues.py` when the upstream is on GitHub:
     ```bash
     python3 /path/to/oss-contribution-scout/scripts/collect_github_issues.py owner/repo --limit 200 --output-dir ./contribution-scout-owner-repo
     ```
   - Prefer authenticated `gh` data when available. If `gh` is unavailable, the script falls back to GitHub REST with `GITHUB_TOKEN` when set.
   - Supplement the script with focused `gh issue view`, label inspection, discussions, release notes, or maintainer comments for promising candidates.

3. **Explore the codebase for contribution points**
   - Build a quick module map from package manifests, top-level directories, docs, test layout, and main entrypoints.
   - Use targeted searches for defects and maintainability gaps:
     - `TODO|FIXME|HACK|XXX|BUG|DEPRECATED`
     - skipped/flaky tests: `skip|xfail|todo|pending|only`
     - suspicious error handling: `panic|unwrap|expect|TODO error|catch \\(|except:|eslint-disable|ts-ignore`
     - dependency/tooling gaps: CI failures, stale workflows, missing test coverage around touched modules.
   - Treat code-derived findings as candidates only when there is concrete evidence: file paths, line references, failing/absent tests, user-facing impact, or a clear maintainer signal.

4. **Classify candidates**
   - Load `references/scoring.md` before assigning final priority and difficulty.
   - Classify every candidate by source and contribution type:
     - `Issue-backed`: upstream issue, label, milestone, maintainer comment, or repeated user report.
     - `Code-derived`: defect, flaky test, missing edge case, docs gap, tooling gap, or small feature gap found in code.
     - `Hybrid`: a code finding that directly supports or explains an upstream issue.
   - Assign: priority (`P0`-`P3`), difficulty (`XS`-`XL`), confidence (`High`/`Medium`/`Low`), and contribution fit (`Good first PR`, `Focused PR`, `Needs maintainer confirmation`, `Avoid for now`).

5. **Rank and recommend**
   - Favor small, reviewable, evidence-backed PRs over broad rewrites.
   - Surface the top 3 near-term PR opportunities, then a larger categorized backlog.
   - Mark candidates that need maintainer confirmation before implementation.
   - Separate private/security-sensitive findings from public issue/PR suggestions.

6. **Verify before finalizing**
   - Confirm every ranked candidate has a source URL or file reference.
   - Confirm difficulty is grounded in touched modules, test scope, and domain complexity.
   - Confirm priority is grounded in user impact, maintainer signal, or project leverage.
   - Run link checks or API checks for referenced GitHub issues when feasible.
   - If a report file is created, scan it for placeholders (`TODO`, `TBD`, empty tables) before finishing.

## Parallel Scouting

When the platform supports subagents and the repository is non-trivial, split read-only exploration into independent passes:

- **Issue scout**: collect and cluster upstream issues, labels, maintainer comments, stale/high-signal issues.
- **Code scout**: scan source/tests/docs for localized defects, skipped tests, and small feature gaps.
- **Contribution policy scout**: summarize contribution rules, CI expectations, CLA/DCO, security policy, and maintainer preferences.
- **Synthesis pass**: merge evidence, deduplicate candidates, assign scores, and produce the final ranked report.

Keep subagents read-only unless the user explicitly asks for implementation.

## Report Structure

Use this structure by default:

```markdown
# Contribution Scout Report: owner/repo

Generated: YYYY-MM-DD
Upstream: https://github.com/owner/repo
Local checkout: /absolute/path or N/A

## Executive Summary
- Top recommendation:
- Best first PR:
- Highest-impact candidate:
- Main caveat:

## Top 3 PR Opportunities
| Rank | Candidate | Type | Priority | Difficulty | Confidence | Why now | Next step |
|---:|---|---|---|---|---|---|---|

## Ranked Backlog
| Priority | Difficulty | Confidence | Fit | Type | Candidate | Evidence | Suggested patch |
|---|---|---|---|---|---|---|---|

## Issue-Backed Opportunities
[Clustered by label/theme with issue URLs and maintainer signals.]

## Code-Derived Opportunities
[File/line evidence, suspected impact, validation path, and why it is small enough for OSS review.]

## Contribution Rules and CI
[How to submit, tests to run, branch/PR conventions, security disclosure notes.]

## Avoid / Defer
[Vague, stale, politically risky, huge, unmaintained, or low-confidence items.]
```

## Evidence Rules

- Do not invent upstream intent. A candidate needs issue evidence, code evidence, or an explicit assumption labeled as such.
- Do not rank "rewrite", "modernize everything", or "add comprehensive tests" as top opportunities unless maintainers asked for it.
- Do not publicly describe exploitable security details beyond the project's security policy; mark those as private disclosure candidates.
- Do not treat stale TODO comments as contribution opportunities without nearby impact evidence or maintainer interest.
- Prefer PRs that can be reviewed independently and validated with one or two focused test commands.

## Stop Conditions

Stop and ask the user only when:

- The upstream repository cannot be determined from the URL, local remotes, or GitHub metadata.
- The repository is not publicly accessible and required credentials are unavailable.
- The user requests implementation but the candidate touches security-sensitive or high-risk production behavior without enough project-specific guidance.

