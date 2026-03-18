# 首次引导（无配置时）

当检测到项目或用户目录下不存在约定配置文件（如 `.aws-article/config.yaml` 或 `EXTEND.md`）时，由 **aws-wechat-article-main** 或当前被调用的子 skill 触发首次引导。

## 流程

1. 询问用户：配置保存在项目（仅当前项目）还是用户目录（所有项目）。  
2. 按 [config-schema.md](config-schema.md) 中的首期必选项，逐项或分组询问（可合并为一次 AskUserQuestion）：  
   - 账号类型、目标读者、调性、更新频率、默认作者  
   - 选题方向/禁区、标题风格、摘要长度、禁用标题套路  
   - 文章风格、段落偏好、小标题密度、文末引导模板、禁用词  
   - 默认排版预设（若有）、封面比例与风格、素材根目录、头尾图路径  
   - 审稿必检项、审稿输出格式  
   - 文章/草稿/已发稿根目录  
3. 将用户选择写入约定路径的配置文件（YAML 或 EXTEND.md 格式）。  
4. 确认「配置已保存到 [路径]」，并继续执行用户原本请求的 skill。

## 路径约定

- 项目级：`.aws-article/config.yaml` 或 `.aws-article/EXTEND.md`  
- 用户级：`~/.aws-article/config.yaml` 或 `~/.aws-article/EXTEND.md`  

实现时二选一或同时支持；若同时存在，优先级为项目 > 用户。
