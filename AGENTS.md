# AGENTS.md

## Cursor Cloud specific instructions

This repository is a **Cursor IDE Skills collection** for WeChat Official Account (微信公众号) content automation. It contains no compiled code, no runtime services, no package managers, and no build tooling.

### Repository structure

- `skills/` — source for 8 sub-skills + 1 Cloud agent starter skill (Markdown `SKILL.md` files + references)
- `scripts/install-skills.sh` — copies skills into `.cursor/skills/` for Cursor to load
- `.aws-article/config.example.yaml` — example YAML config (copy to `config.yaml` for use)

### "Build" / install

```bash
bash scripts/install-skills.sh
```

This is the only setup step. It copies all skill directories from `skills/` into `.cursor/skills/`.

### Lint / test / build

There is no linter, test framework, or build system. Validation is limited to:

- **Bash syntax check**: `bash -n scripts/install-skills.sh`
- **YAML validation**: `python3 -c "import yaml; yaml.safe_load(open('.aws-article/config.example.yaml'))"`
- **Diff check after install**: verify `skills/aws-wechat-article-*` matches `.cursor/skills/aws-wechat-article-*`

### Configuration

Copy `.aws-article/config.example.yaml` to `.aws-article/config.yaml` and edit as needed. The `config.yaml` file is git-ignored.

### Gotchas

- `.cursor/` is git-ignored — installed skills are local-only and must be reinstalled after a fresh clone.
- The install script uses `rm -rf` before `cp -R` so it's idempotent.
