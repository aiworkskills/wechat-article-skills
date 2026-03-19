# Cloud Agent Starter — 代码库运行与测试指南

> **用途**：Cloud agent 首次接触本仓库时的速查手册。涵盖环境准备、各模块验证流程和常见坑点。

---

## 1. 环境准备

### 1.1 依赖

| 依赖 | 必需？ | 检查 |
|------|--------|------|
| Python 3.10+ | ✅ | `python3 --version` |
| PyYAML | ✅ | `python3 -c "import yaml"` |
| Bash | ✅ | `bash --version` |
| Pillow | 可选 | `python3 -c "from PIL import Image"` |

不需要 Node.js、npm、Docker 或任何包管理器。

### 1.2 安装 Skills

```bash
bash scripts/install-skills.sh
```

将 `skills/` 下所有 skill + shared 资源复制到 `.cursor/skills/`。  
**幂等**——可重复执行；每次先 `rm -rf` 再 `cp -R`。

### 1.3 创建配置（可选）

```bash
cp .aws-article/config.example.yaml .aws-article/config.yaml
```

`config.yaml` 已在 `.gitignore` 中，不会被提交。大部分验证不需要它——只有 `write.py`、`image-gen.py`、`publish.py` 的实际 API 调用才需要真实凭证。

---

## 2. 验证矩阵（无外部依赖即可运行）

以下所有检查均可在没有 API key 或网络的环境中执行：

```bash
# Bash 语法
bash -n scripts/install-skills.sh

# YAML 配置格式
python3 -c "import yaml; yaml.safe_load(open('.aws-article/config.example.yaml'))"

# 安装后一致性
bash scripts/install-skills.sh
diff -rq skills/aws-wechat-article-main .cursor/skills/aws-wechat-article-main
# 对每个 skill 目录重复

# Python 脚本语法
python3 -m py_compile skills/aws-wechat-article-formatting/scripts/format.py
python3 -m py_compile skills/aws-wechat-article-writing/scripts/write.py
python3 -m py_compile skills/shared/scripts/image-gen.py
python3 -m py_compile skills/shared/scripts/publish.py

# 发布环境检查（不需要真实凭证）
python3 skills/shared/scripts/publish.py check
```

---

## 3. 按模块测试

### 3.1 安装脚本 (`scripts/install-skills.sh`)

**改了什么要测**：install-skills.sh 本身、skills/ 目录结构。

```bash
# 语法检查
bash -n scripts/install-skills.sh

# 执行并验证输出
bash scripts/install-skills.sh

# 验证一致性（所有 skill 目录）
for d in skills/aws-wechat-article-* skills/aws-wechat-sticker skills/shared skills/cloud-agent-starter; do
  [ -d "$d" ] || continue
  name=$(basename "$d")
  diff -rq "$d" ".cursor/skills/$name" || echo "MISMATCH: $name"
done
```

### 3.2 排版 (`format.py`)

**改了什么要测**：format.py、主题 YAML、SKILL.md 中排版相关内容。

```bash
# 列出可用主题
python3 skills/aws-wechat-article-formatting/scripts/format.py --list-themes

# 用各主题转换测试文件
echo '# 测试标题\n\n## 小节\n\n正文内容，**加粗**和普通文字。\n\n> 引用块' > /tmp/test.md
for theme in default grace modern simple; do
  python3 skills/aws-wechat-article-formatting/scripts/format.py /tmp/test.md \
    --theme "$theme" -o "/tmp/test-${theme}.html"
done

# 验证输出文件非空且包含 HTML
grep -q '<section' /tmp/test-default.html && echo "OK: HTML output"
```

**主题查找优先级**：
1. `.aws-article/presets/formatting/<name>.yaml`（用户自定义）
2. `skills/aws-wechat-article-formatting/references/presets/themes/<name>.yaml`（内置）

### 3.3 写作 (`write.py`)

**改了什么要测**：write.py、writing SKILL.md。

```bash
# 语法检查（无 API key 即可）
python3 -m py_compile skills/aws-wechat-article-writing/scripts/write.py

# 查看帮助
python3 skills/aws-wechat-article-writing/scripts/write.py --help
```

需要 `writing_model` 配置才能实际调用 LLM。无凭证时验证到语法检查即可。

### 3.4 图片生成 (`image-gen.py`)

**改了什么要测**：image-gen.py、images SKILL.md。

```bash
python3 -m py_compile skills/shared/scripts/image-gen.py
python3 skills/shared/scripts/image-gen.py --help

# 模型连通性测试（需要 image_model 配置）
python3 skills/shared/scripts/image-gen.py test
```

### 3.5 发布 (`publish.py`)

**改了什么要测**：publish.py、publish SKILL.md。

```bash
python3 -m py_compile skills/shared/scripts/publish.py

# 环境检查（不需要真实凭证也能运行，会报告缺失项）
python3 skills/shared/scripts/publish.py check

# 查看帮助
python3 skills/shared/scripts/publish.py --help
```

**`publish.py` 子命令一览**：

| 命令 | 用途 | 需要凭证？ |
|------|------|-----------|
| `check` | 环境检查 | 否 |
| `token` | 获取 access_token | 是 |
| `upload-thumb <img>` | 上传封面 | 是 |
| `upload-content-image <img>` | 上传正文图 | 是 |
| `create-draft <yaml>` | 创建草稿 | 是 |
| `full <dir>` | 完整发布流程 | 是 |
| `accounts` | 列出配置的账号 | 否（需 config） |
| `recent-articles` | 最近文章 | 是 |

### 3.6 Skill 内容（SKILL.md / references/）

**改了什么要测**：任何 SKILL.md 或 references/ 下的 Markdown 文件。

```bash
# 重新安装确保 .cursor/skills/ 同步
bash scripts/install-skills.sh

# Diff 验证
diff -rq skills/ .cursor/skills/ 2>/dev/null | grep -v __pycache__ || echo "All synced"
```

### 3.7 配置 (`config.example.yaml`)

**改了什么要测**：config.example.yaml、config-schema.md。

```bash
python3 -c "import yaml; data = yaml.safe_load(open('.aws-article/config.example.yaml')); print(f'Fields: {len(data)}')"
```

---

## 4. 端到端流程验证

如果改动跨越多个模块，按照实际内容生产流水线顺序验证：

```
选题(topics) → 写作(writing) → 审稿(review) → 排版(formatting) → 配图(images) → 发布(publish)
```

最小端到端测试（不需要 API）：

```bash
# 1. 安装
bash scripts/install-skills.sh

# 2. 准备测试文章
mkdir -p /tmp/e2e-test
cat > /tmp/e2e-test/article.md << 'EOF'
# 端到端测试文章

## 第一节

这是一段测试内容，包含**加粗**和*斜体*。

> 引用示例

## 第二节

1. 列表项一
2. 列表项二
3. 列表项三

## 总结

测试完成。
EOF

# 3. 排版（唯一不需要 API 即可完整运行的脚本）
python3 skills/aws-wechat-article-formatting/scripts/format.py \
  /tmp/e2e-test/article.md --theme default -o /tmp/e2e-test/article.html

# 4. 验证输出
[ -s /tmp/e2e-test/article.html ] && echo "E2E OK" || echo "E2E FAIL"
```

---

## 5. 常见坑点速查

| 问题 | 原因 | 解决 |
|------|------|------|
| `ModuleNotFoundError: yaml` | PyYAML 未装 | `pip install pyyaml` |
| `skills/` 改了但 `.cursor/skills/` 没变 | 没重新安装 | `bash scripts/install-skills.sh` |
| `publish.py` 报 config 缺失 | `config.yaml` 不存在 | `cp .aws-article/config.example.yaml .aws-article/config.yaml` |
| `format.py` 找不到主题 | 主题名拼写错误 | `--list-themes` 查看可用主题 |
| `.cursor/` 下的文件没被 git 追踪 | `.cursor` 在 `.gitignore` 中 | 这是预期行为，修改 `skills/` 源文件即可 |
| Python 脚本路径报错 | CWD 不是项目根目录 | 从 `/workspace` 运行，或使用绝对路径 |

---

## 6. 维护本 Skill

发现新的测试技巧、环境坑点或 runbook 知识时，按以下步骤更新：

1. **编辑源文件** `skills/cloud-agent-starter/SKILL.md`（不要直接改 `.cursor/skills/` 下的副本）
2. **选择合适的位置**：
   - 新的验证命令 → §2 验证矩阵 或 §3 对应模块
   - 新的坑点 → §5 常见坑点速查
   - 新的依赖 → §1 环境准备
   - 跨模块流程 → §4 端到端流程验证
3. **重新安装**：`bash scripts/install-skills.sh`
4. **验证 diff**：`diff -rq skills/cloud-agent-starter .cursor/skills/cloud-agent-starter`

保持条目简短、可执行。每条应包含：**触发条件**（什么改动需要这个测试）和**具体命令**（可直接复制运行）。
