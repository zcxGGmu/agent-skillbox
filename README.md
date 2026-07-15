# Agent Skillbox

A personal collection of reusable Codex and AI agent skills for automating recurring development, research, debugging, and open-source contribution workflows.

## What This Repository Is For

This repository stores skills that are useful often enough to keep versioned, portable, and easy to install across agent environments. Each skill is kept as a self-contained folder with a `SKILL.md` entrypoint and optional resources such as scripts, references, or UI metadata.

Use this repository to:

- Keep frequently used agent workflows under Git version control.
- Share reusable skills across machines or Codex workspaces.
- Preserve helper scripts and reference material next to the workflow instructions that use them.
- Review, validate, and evolve skills without editing live runtime copies directly.

## Skills

| Skill | Purpose | Key files |
|---|---|---|
| [`oss-contribution-scout`](./oss-contribution-scout/SKILL.md) | Finds and ranks open-source contribution opportunities by combining upstream issue triage with local codebase exploration. | [`references/scoring.md`](./oss-contribution-scout/references/scoring.md), [`scripts/collect_github_issues.py`](./oss-contribution-scout/scripts/collect_github_issues.py) |

## Repository Layout

```text
agent-skillbox/
+-- README.md
`-- oss-contribution-scout/
    |-- SKILL.md
    |-- agents/
    |   `-- openai.yaml
    |-- references/
    |   `-- scoring.md
    `-- scripts/
        `-- collect_github_issues.py
```

## Install A Skill

Codex discovers user skills from `~/.codex/skills`. To install a skill from this repository, copy or symlink the skill folder into that directory.

Copy:

```bash
mkdir -p ~/.codex/skills
cp -R oss-contribution-scout ~/.codex/skills/
```

Symlink:

```bash
mkdir -p ~/.codex/skills
ln -sfn "$PWD/oss-contribution-scout" ~/.codex/skills/oss-contribution-scout
```

Use a symlink when you want edits in this repository to be reflected immediately in your local Codex skill directory.

## Validate Skills

Run the Codex skill validator against each skill before committing changes:

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py oss-contribution-scout
```

For skills with scripts, also run a syntax or smoke check:

```bash
python3 -m py_compile oss-contribution-scout/scripts/collect_github_issues.py
python3 oss-contribution-scout/scripts/collect_github_issues.py --help
```

Remove generated cache files before committing:

```bash
find . -name "__pycache__" -type d -prune -exec rm -rf {} +
find . -name "*.pyc" -delete
```

## Add Or Update A Skill

1. Create or copy a skill folder at the repository root using kebab-case naming.
2. Keep `SKILL.md` concise and executable: clear trigger, ordered workflow, evidence requirements, and stop conditions.
3. Put detailed reusable guidance in `references/`, deterministic helpers in `scripts/`, and UI-facing metadata in `agents/openai.yaml`.
4. Validate the skill and run representative script smoke tests.
5. Commit only source files. Do not commit local caches, generated reports, secrets, or temporary artifacts.

## Conventions

- Skill folder names must match the `name` field in `SKILL.md`.
- `SKILL.md` frontmatter should include only the fields required by the skill format unless there is a specific reason to add more.
- Prefer portable scripts with no unnecessary third-party dependencies.
- Keep examples realistic, but avoid embedding private paths, tokens, or machine-specific state.
- Treat security-sensitive workflows carefully: include disclosure guidance, but do not publish exploit details in public reports.
