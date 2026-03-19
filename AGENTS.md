# AGENTS.md

## Cursor Cloud specific instructions

This repository is a **Cursor IDE Skills collection** for WeChat Official Account (微信公众号) content automation. It contains no compiled code, no runtime services, no package managers, and no build tooling.

### Repository structure

- `skills/` — source for 8 sub-skills (Markdown `SKILL.md` files + references)
- `scripts/install-skills.sh` — multi-platform installer (Cursor / Claude Code / Codex / OpenClaw)
- `.aws-article/config.example.yaml` — example YAML config (copy to `config.yaml` for use)
- `CLAUDE.md` — Claude Code project instructions
- `AGENTS.md` — Codex / Cursor Cloud agent instructions

### "Build" / install

```bash
bash scripts/install-skills.sh
```

Installs skills for all supported platforms:

| Target | Directory | Action |
|--------|-----------|--------|
| Cursor | `.cursor/skills/` | Copy full skill directories |
| Claude Code | `.claude/rules/` | Generate rule files from SKILL.md |
| Codex | `AGENTS.md` | Already tracked in repo |
| OpenClaw | `skills/` | Native — no copy needed |

Install for a single target: `bash scripts/install-skills.sh cursor`

### Lint / test / build

There is no linter, test framework, or build system. Validation is limited to:

- **Bash syntax check**: `bash -n scripts/install-skills.sh`
- **YAML validation**: `python3 -c "import yaml; yaml.safe_load(open('.aws-article/config.example.yaml'))"`
- **Diff check after install**: verify `skills/aws-wechat-article-*` matches `.cursor/skills/aws-wechat-article-*`

### Configuration

Copy `.aws-article/config.example.yaml` to `.aws-article/config.yaml` and edit as needed. The `config.yaml` file is git-ignored.

### Gotchas

- `.cursor/` and `.claude/` are git-ignored — installed skills are local-only and must be reinstalled after a fresh clone.
- The install script uses `rm -rf` before `cp -R` so it's idempotent.
- OpenClaw reads `skills/` directly — no installation needed.
