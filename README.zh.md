# annotools

[English](README.md)

一个 MCP 服务与 Python 库，帮助 agent 在 MLLM 的 token 预算内查看多模态数据（图片、视频、音频），并附带用于在
SQLite 上构建 agentic 数据标注管道的 skills 与示例。

## 为什么

把全分辨率媒体直接喂给多模态模型既昂贵又不精确。annotools 为 coding agent 提供便宜且有针对性的视图：缩小预览、
局部放大、网格辅助线，以及 BBox、关键点、多边形、分割掩码的叠加层，让 agent 在写入前能检查自己的标注结果。
同一批函数也以库的形式提供，供你用 Claude Agent SDK 或 Codex SDK 构建的执行 agent 使用。

## 状态

建设中——里程碑 P4（skills）完成；接下来是示例项目。规划中的 MCP 工具已全部可用。进度见
[tracking issue](https://github.com/hoshiori-dev/annotools/issues/1)。

## 安装

```bash
uv add annotools            # 库 + MCP 服务（PyPI 尚未启用发布；请从 git 安装）
uv add "annotools[media]"   # 增加 PyAV，用于视频与音频工具
```

容器：`docker run --rm -i ghcr.io/hoshiori-dev/annotools`（stdio），或加上 `--http --host 0.0.0.0` 与
`-p 8000:8000`。

## 作为 MCP 服务使用

在你的 agent 框架中注册 `uv run annotools`（stdio）。本仓库自身的配置展示了三种写法：`.mcp.json`（Claude Code）、
`.codex/config.toml`（Codex）、`opencode.json`（OpenCode）。`annotools --http --port 8000` 提供 Streamable HTTP，
用于共享或远程访问。

## 工具（规划中）

| 工具 | 用途 |
|---|---|
| `preview_image` | 裁剪 + 缩小到 768×768 以内（可配置） |
| `preview_image_grid` | 叠加半透明 10×10 网格的预览 |
| `preview_image_bboxes` / `_keypoints` / `_polygons` | 基于归一化坐标的叠加层，可带标签 |
| `preview_image_segmentation` | ID 掩码叠加，标签或图例模式 |
| `color_from_text` | 由任意文本得到稳定颜色 |
| `rotated_bbox_to_polygon` | (cx, cy, w, h, θ) → DOTA 8 数角点 |
| `preview_video` / `preview_video_grid` | 按 N fps 抽帧 → 预览 |
| `clip_audio` | 音频切片与重采样 |

规范文档位于 `docs/spec/`（共享约定：`docs/spec/mcp-overview.md`）。

## Skills 与示例

`skills/` 提供可安装的 skills（`npx skills add hoshiori-dev/annotools`）。七个 skill 全部可用：`annotation-project-interview`
（设计树访谈 + 工作区脚手架）、`sqlite-annotation-store`（库表、工具契约、导出）、`mllm-multimodal-input`
（各模型 token 成本、坐标约定、缓存布局）、`localization-annotation-guide`（网格 → 提议 → 校验 → 修正 → 入库循环）、
`agent-vision-tools`（基于库层为 Claude Agent SDK / Codex SDK 执行 agent 构建的工具）、`task-image-captioning` 与
`task-object-detection`（含提示词与管道骨架的任务脚手架）。`examples/` 将提供两种 SDK 的完整示例项目（图片 caption、
物体检测），并记录实际用量。

## 开发

```bash
uv sync --all-extras
just check          # lint、格式、类型、label 一致性、README 同步、单元测试
just docker-build && just test-container
```

参见 `CONTRIBUTING.md`；agent 从 `AGENTS.md` 开始。

## 许可证

Apache-2.0
