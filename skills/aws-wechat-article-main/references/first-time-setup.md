# 首次引导 ⛔ BLOCKING

当项目和用户目录下均不存在 `config.yaml` 时，**必须完成首次引导后才能执行任何操作**。

## 检测方法

```bash
test -f .aws-article/config.yaml && echo "project" || echo "无"
test -f "$HOME/.aws-article/config.yaml" && echo "user" || echo "无"
```

## 阻断规则

⛔ **如果两个路径都不存在 config.yaml**：
- 立即进入首次引导流程
- **禁止**执行任何子 skill 的功能
- **禁止**跳过引导直接回答用户问题
- 引导完成并写入配置后，才继续执行用户原本的请求

## 引导流程

### 第1步：确定保存位置

询问用户：
- **项目级**（`.aws-article/config.yaml`）：仅当前项目生效
- **用户级**（`~/.aws-article/config.yaml`）：所有项目通用

### 第2步：收集配置（必填项）

以下为**必须填写**的项，不能跳过：

**账号定位**（必填）：
- 账号类型/领域（如科技、职场、情感）
- 目标读者（如「一线互联网人」「大学生」）
- 语气调性（正式/轻松/专业/幽默/犀利）

**内容偏好**（必填）：
- 文章风格（口语化/书面/故事型/方法论/清单体）
- 标题风格偏好（悬念/干货/数字/反问/故事）

### 第3步：收集配置（选填项）

以下可以跳过，后续在 config.yaml 中补充：

**内容细节**：
- 选题方向或禁区
- 更新频率
- 默认作者名
- 文末固定引导语

**排版与图片**：
- 默认排版主题
- 封面比例与风格
- 配图密度

**模型与发布**：
- 写作模型配置（base_url、api_key、model）
- 图片生成模型配置
- 公众号 AppID 和 AppSecret

### 第4步：写入配置

将用户回答写入 `config.yaml`，未回答的选填项使用默认值。

同时创建目录结构：

```bash
mkdir -p .aws-article/presets/formatting
mkdir -p .aws-article/presets/image-styles
mkdir -p .aws-article/presets/title-styles
mkdir -p .aws-article/assets/brand
mkdir -p .aws-article/assets/covers
mkdir -p .aws-article/assets/stock
mkdir -p .aws-article/templates
```

### 第5步：确认并继续

输出确认信息：

```
✅ 配置已保存到 [路径]

已配置：
- 账号类型：[值]
- 目标读者：[值]
- 调性：[值]
- 文章风格：[值]
- 标题风格：[值]

后续可编辑 config.yaml 修改配置。
写作规范：复制 writing-spec.example.md → writing-spec.md
自定义预设：放到 .aws-article/presets/ 下

现在继续您的请求……
```

然后继续执行用户原本的请求。
