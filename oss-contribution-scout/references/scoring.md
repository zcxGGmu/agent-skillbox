# Contribution Opportunity Scoring

Use this reference when assigning priority, difficulty, confidence, and fit in OSS contribution reports.

## Priority

| Score | Meaning | Typical evidence |
|---|---|---|
| `P0` | Private or urgent maintainer-sensitive item. Do not recommend public PR/issue without checking policy. | Security vulnerability, data loss, supply-chain risk, active breakage in latest release. |
| `P1` | High-value public contribution. Prioritize for near-term PR. | Maintainer-labeled bug/help-wanted, regression, repeated user reports, failing CI/test, widely used path, release blocker. |
| `P2` | Useful focused contribution. Good backlog item. | Docs gap with clear user impact, test coverage gap, small feature request with maintainer interest, localized cleanup that reduces bugs. |
| `P3` | Low urgency or weak evidence. Keep only if easy and aligned. | Stale issue with no maintainer signal, speculative enhancement, isolated TODO, broad refactor with unclear payoff. |

Raise priority when:

- A maintainer commented recently or applied labels like `help wanted`, `good first issue`, `bug`, `regression`, `priority`, or milestone.
- Multiple users reproduce the problem.
- The issue blocks installation, onboarding, common workflows, tests, or release readiness.
- The fix is small but unblocks many downstream changes.

Lower priority when:

- The issue is stale and maintainers have not engaged.
- The request conflicts with roadmap/docs.
- The change requires broad redesign for marginal benefit.
- The evidence is only a TODO comment or stylistic preference.

## Difficulty

| Score | Meaning | Typical scope |
|---|---|---|
| `XS` | Trivial or docs-only. | Typo, broken link, doc clarification, tiny test fixture, config label, one-file change. |
| `S` | Small focused PR. | Localized bug fix, one module plus tests, reproducer is clear, low API risk. |
| `M` | Moderate contribution. | Requires reading adjacent modules, adding tests, behavior changes, compatibility concerns. |
| `L` | Large or domain-heavy. | Cross-package behavior, migration, public API changes, performance work, complex concurrency/state. |
| `XL` | Avoid as first contribution unless requested. | Architecture rewrite, multi-maintainer coordination, ambiguous product direction, deep security or release risk. |

Increase difficulty for:

- Cross-language or cross-package changes.
- Weak tests or hard-to-reproduce behavior.
- Public API, storage format, protocol, or compatibility changes.
- Domain-specific code requiring maintainer review (cryptography, kernel, database engine, compiler, auth, billing).

Decrease difficulty for:

- Existing failing test or minimal repro.
- Clear maintainer guidance.
- Good test harness and local validation path.
- Narrow files with established patterns nearby.

## Confidence

| Score | Meaning |
|---|---|
| `High` | Evidence is current, direct, and independently checkable. The candidate has issue or file/line references and a plausible validation command. |
| `Medium` | Evidence is plausible but incomplete. The next step should confirm scope, reproduce behavior, or ask maintainers. |
| `Low` | Candidate is speculative. Keep it out of top recommendations unless the user asked for exploratory ideas. |

## Contribution Fit

| Fit | Use when |
|---|---|
| `Good first PR` | Small, low-risk, clear validation, maintainers welcome similar changes. |
| `Focused PR` | Valuable and bounded, but needs more codebase familiarity. |
| `Needs maintainer confirmation` | Product direction, API behavior, security, or broad design is uncertain. |
| `Avoid for now` | Too broad, stale, politically risky, low evidence, or likely to be rejected. |

## Candidate Card Fields

Each candidate should include:

- Title.
- Source: issue URL, discussion URL, file path with line number, CI failure, or doc reference.
- Type: issue-backed, code-derived, or hybrid.
- Category: bug, docs, tests, tooling, feature, performance, compatibility, security/private, cleanup.
- Priority, difficulty, confidence, and fit.
- User/project impact.
- Suggested first patch.
- Validation command or manual verification path.
- Risks or maintainer questions.

