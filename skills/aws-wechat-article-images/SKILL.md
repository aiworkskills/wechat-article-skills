---
name: aws-wechat-article-images
description: Provides cover and in-article images via asset library, OpenAI image generation with prompt presets, or local HTML-to-image export. Use when the user asks for "封面", "配图", "多图推送", "贴图", "图片规格", "素材库", "生成图片", or "导出图片".
---

# 贴图与素材

配图支持**三种方式**，按场景或用户选择其一或组合使用。配置见 aws-wechat-article-main 的 references。

## 方式一：素材库

从本地或项目约定的素材库（配置：素材根目录、头尾图路径）选图。产出：封面建议、正文配图位置与图注、多图推送图序与每张配文 + 尺寸规格。贴图 = 文案 + 图序 + 规格。

## 方式二：调用 OpenAI 接口生成

根据正文/摘要/标题生成配图或封面。提供**多套提示词样式预设**，从 `references/presets/` 或配置直接读取（不现场编提示词）；用户或配置选定预设后，用该预设的 prompt 模板调用生成接口。预设可区分风格（插画/写实/简约等）、尺寸、画幅等。

## 方式三：本地生成 HTML 再导出为图片

按给定内容与版式生成 HTML，再通过本地工具（如 headless 截图或导出 API）导出为图片；适用于信息图、数据图、固定版式封面等。

## 步骤

1. **读配置**：封面比例与风格、配图密度、图注风格、多图张数、素材根目录、默认配图方式等。  
2. **确定方式**：用户指定或配置默认，可选组合（如封面用生成、正文用素材库）。  
3. **执行**：素材库选取 / 读预设后调 OpenAI / 生成 HTML 并导出。  
4. **输出**：图片文件或路径、图片规格表、配图位置与图注建议、多图推送文案与顺序。

## References

- [references/specs.md](references/specs.md)：封面/正文/多图尺寸与格式、品牌头尾图约定。  
- 方式二：`references/presets/` 下多份提示词样式预设，每份为可被直接读取的 prompt 模板或配置；列表与说明供用户/配置选择。  
- 方式三：实现时可提供 HTML 模板或导出说明（本地工具、调用方式）。
