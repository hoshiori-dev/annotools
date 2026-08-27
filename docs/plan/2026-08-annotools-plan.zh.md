# annotools 总体计划（已批准，2026-08-27）

> 语言约定：本计划与后续 Issue/PR 草案先用中文供你审查；确认后以英文发布。代码、注释、文档、commit、Issue、PR 一律英文；README 提供 `README.md` / `README.zh.md` 镜像。

## 1. 背景与目标

仓库 `hoshiori-dev/annotools`（公开、组织所有、默认分支 `main`）目前只有初始提交 + 未跟踪的脚手架（`pyproject.toml`、meta- 系技能、zensical 文档骨架、`src/annotools/__init__.py` 占位）。没有 AGENTS.md、没有 CI、没有测试。

目标：交付一个 **MCP + Skill 组合**，帮助 agent 创建多模态数据集：

1. **MCP 服务（fastmcp）**：与数据集、agent 框架无关的"看数据"工具——缩图、局部放大、网格辅助线、BBox/关键点/多边形/分割叠加、视频抽帧、音频切片——降低 MLLM token 消耗、提高标注精度。主要给 **开发项目的 coding agent** 用。
2. **可安装的 Python 库层**：MCP 只是薄包装；同一批函数以库 API 暴露，供 coding agent 按 skill 指导，为 **执行管道的 agent**（Claude Agent SDK / Codex SDK）构建自定义看图工具。
3. **对外发布的 Skills**（`skills/`）：以 SQLite 为默认数据引擎的标注方法论、即插即用的数据结构与库表模板、各模型多模态输入/缓存策略、需求访谈（design tree）流程、每类任务的脚手架 skill。
4. **示例**（`examples/`）：图片 caption、物体检测两个任务，各含 Claude Agent SDK 与 Codex SDK 两套管道，README 附运行用量。
5. **Harness**：对 Codex / Claude Code / OpenCode 无强假设的 agent 工程化层（AGENTS.md、架构文件、知识库、开发技能、GitHub Workflow CI、lint/format 自动化、Issue-first + 规范驱动 + TDD 流程）。

## 2. 已核实事实（无需你回答）

| 事实 | 证据 |
|---|---|
| 组织仓库、PUBLIC、issues 开、merge/squash/rebase 均允许 | `gh repo view` |
| 组织所有 → 可用 rulesets、issue types、CODEOWNERS 强制 | owner type = Organization |
| Python ≥3.12，uv + uv_build，ruff（120 列）、ty、pytest 已在 dev 依赖 | `pyproject.toml` |
| pre-commit 已含 ruff/ty/uv-lock/gitleaks(PII 规则)，但 ruff 钩子版本 (0.11.9) 落后于依赖 (≥0.16.4) | `.pre-commit-config.yaml` |
| 仅有 `docs.yml`（zensical → Pages），无 lint/test CI | `.github/workflows/` |
| `.claude/skills -> ../.agents/skills` 软链已存在；三框架均已注册 `fastmcp-docs` MCP | `.mcp.json` / `opencode.json` / `.codex/config.toml` |
| FastMCP 3.x：工具直接返回 `Image(data=bytes, format="png")` / `Audio` / `list[Image | str]` 即转成 MCP content block | fastmcp docs `servers/tools#media-helper-classes` |
| 容器内无 `ffmpeg`、无 `just`；系统 python 3.10（项目由 uv 装 3.12） | `which` |

## 3. 模块划分

```
┌──────────────────────────────────────────────────────────────┐
│ skills/ (对外发布，方法论+脚手架)     examples/ (示范 SDK 管道) │
├──────────────────────────────────────────────────────────────┤
│ src/annotools/server + tools/   ← MCP 薄包装（fastmcp）        │
├──────────────────────────────────────────────────────────────┤
│ src/annotools/{image,video,audio,geometry,color,io}  ← 纯库层 │
│   PIL / numpy / fsspec / (PyAV 可选)                           │
└──────────────────────────────────────────────────────────────┘
   harness: AGENTS.md · ARCHITECTURE.md · .agents/{knowledge,skills} · CI
```

| 模块 | 职责 | 依赖 |
|---|---|---|
| `annotools.config` | 默认参数（768/768/边框 2/点径 3/网格 10×10/透明度 0.5），可由环境变量 `ANNOTOOLS_*` 覆盖 | — |
| `annotools.io` | `open_bytes(uri)`：fsspec/本地统一读取；图片解码为 PIL | fsspec, Pillow |
| `annotools.geometry` | 归一化坐标 ↔ 像素、裁剪区域换算、旋转框→4 角点、`is_rectangle(points, tol)` | numpy |
| `annotools.color` | 文本哈希→颜色（sha256 → HSL 高饱和）、颜色名/hex 解析、反色计算 | — |
| `annotools.image.preview` | 裁剪 + 等比缩放（默认仅缩小） | Pillow |
| `annotools.image.grid` | 半透明网格叠加（比例/固定模式、白/黑/反色） | Pillow |
| `annotools.image.overlay` | bbox / keypoint / polygon 叠加，标签与点编号 | Pillow |
| `annotools.image.segmentation` | ID 掩码着色叠加，标签/图例两种模式 | numpy, Pillow |
| `annotools.video` | 按 FPS 抽帧 → 复用 image 管线 | PyAV（extra） |
| `annotools.audio` | 切片 + 重采样 → WAV | PyAV（extra）或 soundfile |
| `annotools.tools.*` | pydantic 参数模型 + `@mcp.tool` 包装；返回 `[Image, meta_text]` | fastmcp |
| `annotools.server` | `FastMCP("annotools")`，`annotools` 控制台入口（stdio；`--http` 可选） | fastmcp |

设计原则：库层函数**不依赖 fastmcp**，纯输入 → `PIL.Image`/bytes，便于执行 agent 的工具直接复用；MCP 层只做参数校验与编码。

## 4. 文件结构

```
annotools/
├── AGENTS.md                      # 入口地图（≈100 行）；CLAUDE.md 内容为 "@AGENTS.md"
├── CLAUDE.md
├── ARCHITECTURE.md                # 专门架构文件：分层、数据流、约束、扩展点
├── README.md / README.zh.md       # 双语镜像
├── CONTRIBUTING.md  SECURITY.md  LICENSE
├── justfile                       # lint / format / typecheck / test / docs / mcp-dev
├── Dockerfile                     # MCP 服务镜像（ghcr.io/hoshiori-dev/annotools）
├── pyproject.toml                 # 补：pytest/coverage 配置、extras [media]、元数据
├── .pre-commit-config.yaml        # 升 ruff 版本；去掉无用的 uv-export
├── .github/
│   ├── workflows/ci.yml           # 见 §8.1：每 push 跑 lint/format/type；main 与 PR 最新 commit 跑单元+容器测试
│   ├── workflows/secret-scan.yml  # 见 §8.2：TruffleHog 机密扫描（main push + PR）
│   ├── workflows/release.yml      # 见 §8.3：release 发布 → 测试 → 构建冒烟 → GHCR（PyPI 占位）
│   ├── workflows/docs.yml         # 现有，改为 uv 安装
│   ├── ISSUE_TEMPLATE/feature-spec.yml   # 规范驱动：目标/范围/接口/验收标准
│   ├── ISSUE_TEMPLATE/bug.yml, task.yml, config.yml
│   ├── PULL_REQUEST_TEMPLATE.md   # 关联 Issue、规范链接、测试、README 双语同步勾选、经验沉淀候选
│   ├── dependabot.yml  release.yml  CODEOWNERS
├── .agents/
│   ├── knowledge/                 # 开发知识库（英文）
│   │   ├── conventions.md         # Python 约定（Google docstring、pytest 教义、ruff/ty）
│   │   ├── spec-format.md         # 规范文档模板与验收标准写法
│   │   ├── mllm-token-budget.md   # 768 tile 依据、各模型输入方式速查
│   │   └── examples-context.md    # 修改 examples 前必须先读其 CONTEXT.md 的规则来源
│   └── skills/                    # 开发用技能（meta-* 建完后由 meta-disposal 删除）
│       ├── github-project-workflow/   # Issue → 规范 → 分支 → PR → 发布流程与发布前审查
│       ├── spec-driven-feature/       # 开 Issue、写 docs/spec、先写测试、再实现
│       ├── retrospective-to-skill/    # PR 前总结经验，候选沉淀为 skill
│       └── readme-bilingual-sync/     # README.md ↔ README.zh.md 同步检查
├── .claude/skills -> ../.agents/skills（已有）；.claude/settings.json（注册 annotools MCP）
├── .codex/config.toml  .mcp.json  opencode.json  # 三框架均注册 `uv run annotools`
├── docs/                          # zensical 站点
│   ├── index.md  getting-started.md
│   ├── spec/                      # 规范文档（每个 MCP 工具一份：目标、参数、返回、验收标准）
│   │   ├── mcp-overview.md  preview-image.md  preview-image-grid.md  … clip-audio.md
│   └── guides/                    # 面向使用者：接入三框架、为执行 agent 建工具
├── src/annotools/                 # 见 §3
├── skills/                        # 对外发布 skills（`npx skills add hoshiori-dev/annotools`）
│   ├── annotation-project-interview/   # design-tree 访谈流程 + 示例项目结构脚手架
│   ├── sqlite-annotation-store/        # 预制 schema、BBox/Polygon/Keypoint/Caption 结构、写入工具设计
│   ├── mllm-multimodal-input/          # Gemini/GPT/Claude/Qwen 输入方式、tile/token、缓存前缀策略
│   ├── localization-annotation-guide/  # 归一化 xyxy、网格建议、DOTA 8 点、矩形检查代码
│   ├── agent-vision-tools/             # 用 annotools 库为执行 agent 构建看图/看结果工具
│   ├── task-image-captioning/          # 任务脚手架：需求项、提示词模板、试标 1–3 张、管道骨架
│   └── task-object-detection/          # 任务脚手架：类目标准、网格→预览→修正 ≤3 轮流程
├── examples/                      # 每个 SDK 一个独立完整项目
│   ├── image-captioning-claude/
│   │   ├── CONTEXT.md             # 示例项目的 agent 入口（不用 AGENTS.md）
│   │   ├── .agents/{skills,knowledge}/  spec/  config/  template/  skills/  justfile
│   │   ├── scripts/download_coco_cats.py
│   │   ├── src/                   # Claude Agent SDK 管道
│   │   └── workspaces/coco-cats/{data/raw,data/interim,data/dataset.db,output/}
│   ├── image-captioning-codex/    # 同结构，Codex SDK 管道
│   ├── object-detection-claude/   # 类目：black_cat / white_cat / other_cat
│   └── object-detection-codex/
└── tests/                         # pytest；fixtures 用程序生成的小图，不入库二进制大文件
```

## 5. MCP 接口设计（请确认）

约定：
- 所有坐标为 **0.0–1.0 归一化**（相对裁剪前原图）；颜色接受名称（`blue`）或 `#RRGGBB`；默认 `blue`。
- 每个预览类工具返回 `[Image, text]`：图 + 一行 JSON 元数据（原图尺寸、输出尺寸、缩放比、实际裁剪区域、网格步长），便于 agent 换算。
- 参数以 pydantic 模型分组复用（`PreviewOptions` → `GridOptions` → 叠加物体）。

### 5.1 公共参数组

```python
class PreviewOptions:  # 所有预览工具共用
    source: str  # 图片地址：本地路径或 fsspec URL (s3://, gs://, http(s)://…)
    crop: tuple[float, float, float, float] | None = None  # (x_min,y_min,x_max,y_max) 归一化，局部放大
    target_pixels: int | None = None  # 目标像素总数（与 max_* 取更小者）
    max_width: int = 768
    max_height: int = 768
    allow_upscale: bool = False  # 默认仅缩小
    output_format: Literal["jpeg", "png", "webp"] = "jpeg"  # JPEG 质量 90
    save_to: str | None = None  # 可选：同时把结果写到路径（供执行 agent 复用/调试）


class GridOptions:  # 网格叠加；预览工具通过 grid: GridOptions | None 使用
    columns: int = 10  # 9 条竖线
    rows: int = 10  # 9 条横线
    mode: Literal["ratio", "fixed"] = "ratio"
    column_width: int | None = None  # mode=fixed 时的列宽（输出像素）
    row_width: int | None = None
    color: Literal["white", "black", "invert"] = "white"
    opacity: float = 0.5
    line_width: int = 1
```

### 5.2 图片工具

| 工具 | 参数 | 返回 |
|---|---|---|
| `preview_image` | `PreviewOptions` | `[Image, meta]` |
| `preview_image_grid` | `PreviewOptions` + `GridOptions` | `[Image, meta]` |
| `preview_image_bboxes` | `PreviewOptions`, `grid: GridOptions\|None`, `objects: list[BBoxObject]`, `line_width: int = 2` | `[Image, meta]` |
| `preview_image_keypoints` | `PreviewOptions`, `grid`, `objects: list[KeypointObject]`, `point_diameter: int = 3` | `[Image, meta]` |
| `preview_image_polygons` | `PreviewOptions`, `grid`, `objects: list[PolygonObject]`, `line_width=2`, `point_diameter=3`, `show_point_index: bool = True` | `[Image, meta]` |
| `preview_image_segmentation` | `PreviewOptions`, `grid`, `mask_source: str`, `annotation: Literal["label","legend"]="label"`, `id_names: dict[int,str]\|None`, `alpha: float=0.5`, `line_width=2` | `[Image, meta]` |

```python
class BBoxObject:
    bbox: tuple[float, float, float, float]
    label: str | None
    color: str = "blue"


class KeypointObject:
    point: tuple[float, float]
    label: str | None
    color: str = "blue"


class PolygonObject:
    points: list[float]  # [x1,y1,x2,y2,…] 偶数个、≥6; label; color
```

分割掩码约定：单通道 PNG/TIFF（uint8/uint16），像素值 = 实例/类别 ID，0 = 背景；缩放到原图尺寸（最近邻）后按 ID 用 `color_from_text(str(id))` 着色；`legend` 模式先在图下方拼接图例再整体缩放到限制内。

### 5.3 几何 / 颜色工具

| 工具 | 参数 | 返回 |
|---|---|---|
| `color_from_text` | `text: str` | `{"hex": "#1f77b4", "rgb": [31,119,180]}` |
| `rotated_bbox_to_polygon` | `boxes: list[RotatedBox]`（`cx,cy,w,h,theta`，归一化；`angle_unit: "degrees"\|"radians" = "degrees"`） | `list[list[float]]` 每项 8 个数 `[x1,y1,…,x4,y4]`（DOTA 4 角点顺时针） |

> 已确认：8 个数 = 4 个角点（DOTA 格式）。

库层另提供 `geometry.is_rectangle(points, angle_tol_deg=2.0)`，在 skill 中给出检查代码示例（不作为 MCP 工具）。

### 5.4 视频工具

| 工具 | 参数 | 返回 |
|---|---|---|
| `preview_video` | `PreviewOptions`, `fps: float = 1.0`, `start: float\|None`, `end: float\|None`, `max_frames: int = 32` | `[Image…, meta]` 帧序列 + 时间戳 |
| `preview_video_grid` | 同上 + `GridOptions` | 同上 |

超过 `max_frames` 时按等间隔降采样并在 meta 中说明，避免一次调用撑爆上下文。

### 5.5 音频工具

| 工具 | 参数 | 返回 |
|---|---|---|
| `clip_audio` | `source: str`, `start: float\|None`, `end: float\|None`, `sample_rate: int\|None`, `save_to: str\|None` | `Audio`(wav) + meta |

## 6. Skills 内容纲要（`skills/`，英文）

- **annotation-project-interview**：design-tree 访谈（前沿轮次、编号+推荐答案、事实自查不问用户）；产出 `spec/`（目标、输出格式、质量标准）与工作区目录；强制约定：`data/raw` 只读、DB 不存二进制、指针用 fsspec/本地路径。
- **sqlite-annotation-store**：预制表（`items`, `annotations`, `bboxes`, `polygons`, `keypoints`, `captions`, `runs`），JSON 数据结构定义（归一化 xyxy 等），"记录/更新标注"工具的接口模板，导出 jsonl/csv/parquet/webdataset 的脚本骨架。
- **mllm-multimodal-input**：Gemini/GPT/Claude/Qwen 默认与最省 token 的图片/视频/音频输入方式、768 tile 依据、前缀缓存策略（静态提示词在前，逐条 metadata 与数据在最后；调查各框架缓存最小长度），推理长度档位选择。
- **localization-annotation-guide**：归一化 xyxy 优于绝对坐标、10×10 网格依据、旋转框用 DOTA 8 点 + `is_rectangle` 检查代码、检测流程（网格预览 → 带编号 BBox 预览 → 修正 ≤3 轮 → 入库）。
- **agent-vision-tools**：用 `annotools` 库为 Claude Agent SDK / Codex SDK 的执行 agent 定义看图、看结果、写库工具，限制其只能访问工作区。
- **task-image-captioning / task-object-detection**：任务脚手架（需求清单、提示词模板、试标 1–3 张回传用户确认、管道骨架、导出）。

## 7. 示例项目

- **image-captioning**：COCO 2017 val 含猫图片（`instances_val2017.json` 过滤 cat 类，下载脚本只拉需要的图）；先生成长 caption，再逐级缩写为中、短，tag 单独生成；SQLite → `output/captions.jsonl`。
- **object-detection**：同一数据源；类目 `black_cat` / `white_cat` / `other_cat`；网格预览 → 自评预览 → ≤3 轮修正 → 入库 → `output/detections.jsonl`。
- 每个示例：`CONTEXT.md`（示例入口）、`spec/`、Claude Agent SDK 与 Codex SDK 两套 `src/`，README 记录运行用量（token/费用/时间）。根 `AGENTS.md` 规定：修改 `examples/*` 前必须先读该目录 `CONTEXT.md`。

## 8. 工作流程与阶段（Issue-first、规范驱动、TDD）

每个阶段：开 Issue（含目标 + 验收标准，中文草案 → 你确认 → 英文发布）→ `docs/spec/` 写规范 → 先写测试 → 实现 → PR 前跑 `retrospective-to-skill` 列出经验候选 → PR。

| 阶段 | 内容 | 产物 |
|---|---|---|
| P0 Harness | AGENTS/CLAUDE/ARCHITECTURE、知识库、开发 skills、CI、Issue/PR 模板、labels、justfile、pyproject 补全、README 双语、三框架 MCP 注册；完成后 `meta-disposal` 清理 meta-* | 一个 tracking issue + 若干子 issue |
| P1 核心库 + 图片 MCP | io/geometry/color/preview/grid/overlay + 6 个图片工具规范与测试 | `annotools` 可 `uv run annotools` 启动 |
| P2 分割 + 几何工具 | segmentation、color_from_text、rotated_bbox_to_polygon | |
| P3 视频 + 音频 | PyAV extra、抽帧、切片 | |
| P4 对外 Skills | `skills/` 7 个技能 | 可 `npx skills add` |
| P5 示例 captioning | 下载脚本、两套 SDK 管道、试标回传流程、用量记录 | |
| P6 示例 detection | 同上 | |

### 8.1 CI 设计（`.github/workflows/ci.yml`）

| Job | 触发 | 内容 |
|---|---|---|
| `lint` / `format` / `typecheck` | **所有分支的每次 push** + PR | `ruff check`、`ruff format --check`、`ty check`（`uv sync --frozen`） |
| `test-unit` | 仅 push 到 `main` 与 PR | `pytest --cov`，矩阵 3.12 / 3.13 |
| `test-container` | 仅 push 到 `main` 与 PR | `docker build` 本地镜像 → 启动容器 → 用 `fastmcp` Client 经 stdio/http 调用 `preview_image` 验证 MCP 可用 |
| `ci-gate` | 同上 | 聚合 job（`needs` 全部，`if: always()` 检查无 failure/cancelled），作为 `main` ruleset 的唯一必需检查 |

- PR 的 `concurrency: { group: ci-${{ github.event.pull_request.number \|\| github.ref }}, cancel-in-progress: true }` → **测试只对 PR 最新 commit 运行**，旧 commit 的测试被取消；lint/format/typecheck 因轻量，仍在每个 push 上跑。
- 触发条件：`on: push`（全部分支）+ `on: pull_request`（目标 `main`）；测试类 job 加 `if: github.event_name == 'pull_request' || github.ref == 'refs/heads/main'`。
- squash merge，PR 标题遵循 Conventional Commits（`pr-title` 校验 job 放入 gate），`.github/release.yml` 按 label 生成发布说明。

### 8.2 机密扫描（`.github/workflows/secret-scan.yml`）

按你给的参考实现，独立 workflow：

```yaml
name: Secret Scanning
on:
  push: { branches: [main] }
  pull_request:
permissions: { contents: read }
jobs:
  secret-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
        with: { fetch-depth: 0, persist-credentials: false }
      - uses: trufflesecurity/trufflehog@main
        with: { extra_args: --results=verified,unknown }
```

- `secret-scan` job 加入 `main` ruleset 必需检查（与 `ci-gate` 并列）。
- 与本地 pre-commit 的 gitleaks（PII 规则）互补：gitleaks 管邮箱/IP 等 PII，TruffleHog 管已验证/未知的凭据；两者规则不重复维护。
- 例外配置（如需）放 `.trufflehogignore`，不放进 gitleaks 配置。

### 8.3 分发与发布（`.github/workflows/release.yml`、`Dockerfile`）

分发渠道：**GHCR**（`ghcr.io/hoshiori-dev/annotools`，本期实现自动部署）与 **PyPI**（本期仅留占位 job，不自动执行）。

```
on: release: [published]
 ├─ verify   : lint/format/typecheck + test-unit + test-container（复用 ci.yml 的 reusable workflow）
 ├─ build    : uv build → sdist/wheel artifact；docker build (multi-arch amd64/arm64) → 本地 tar artifact
 ├─ smoke    : 从 wheel 全新 venv 安装 → `annotools --help` + Client 调用 preview_image；
 │            从镜像 tar 载入 → 容器内同样冒烟；两者都过才继续
 ├─ publish-ghcr : push 镜像，标签规则：
 │      pre-release → `<version>`（如 0.2.0rc1）
 │      正式 release → `<version>`、`<major>.<minor>`、`latest`
 ├─ publish-pypi  : 占位（`if: false` + 注释说明启用条件：配置 PyPI Trusted Publishing 后去掉守卫）
 │      pre-release → TestPyPI；正式 release → PyPI
 └─ 权限：contents: read, packages: write, id-token: write（为将来 trusted publishing 预留）
```

- 版本来源：`pyproject.toml` 版本与 release tag（`v<version>`）一致性在 `verify` 中校验，不一致直接失败。
- `Dockerfile`：`python:3.12-slim` 多阶段，`uv` 安装 `annotools[media]`，`ENTRYPOINT ["annotools"]`，默认 stdio；`--http` 时暴露 8000。
- 发布前测试失败则全部下游 job 不执行；GHCR 推送在 `smoke` 通过后进行。
- 需要人工完成的远端设置：GHCR 包可见性设为 public（首次推送后）、PyPI/TestPyPI Trusted Publisher（启用占位时）。

## 9. 验证方式

- `just check`（lint/format/type/test）全绿；CI 在 PR 上全绿。
- MCP：`uv run annotools` 启动后用 `fastmcp` Client 调 `preview_image` 等工具的集成测试（生成 256×256 合成图，断言尺寸 ≤768、网格线像素、bbox 位置）。
- 在 Claude Code / Codex / OpenCode 三端各调用一次 `preview_image_grid` 手动确认图片可显示。
- 示例：跑 3 张图的 dry-run，记录用量写入示例 README。

## 10. 已确认决策（访谈三轮，前沿已清空）

| # | 决策 | 结论 |
|---|---|---|
| 1 | 示例组织 | **每个 SDK 独立完整项目**：`examples/image-captioning-claude/`、`examples/image-captioning-codex/`、`examples/object-detection-claude/`、`examples/object-detection-codex/`，各自完整（CONTEXT.md、spec/、workspaces/、scripts/、src/、skills/、config/、template/、justfile） |
| 2 | 媒体后端 | PyAV 放入 extra `annotools[media]`；PyPI 名称已核实为 **`av`**（18.1.0） |
| 3 | 输出格式 | JPEG q90 默认，`png`/`webp` 可选 |
| 4 | 合并门禁 | `main` ruleset：必需 `ci-gate` 检查；squash merge；PR 标题 Conventional Commits；不强制审阅 |
| 5 | 旋转框 | 输出 8 个数 `[x1,y1,…,x4,y4]`（DOTA 4 角点）；`theta` 默认度，`angle_unit` 可切弧度 |
| 6 | 掩码格式 | 单通道 ID 图（uint8/uint16 PNG/TIFF，0=背景）；非单通道报错 |
| 7 | 网格索引 | 不加，严格按需求（§5.1 删除 `show_indices`） |
| 8 | Skills 分发 | 根目录 `skills/`，兼容 `npx skills add hoshiori-dev/annotools` |
| 9 | MCP 传输 | stdio 默认，`annotools --http` 可选 |
| 10 | Issue 组织 | 1 个 tracking issue + P0–P6 各一个 milestone + sub-issues（每工具/skill/示例一个，含规范与验收）；不用 Projects |
| 11 | meta 清理 | P0 验证后，dry-run 展示 → 再次确认 → `meta-disposal` 删除 meta-*（保留 goal-alignment） |
| 12 | 分发 | GHCR 自动部署（本期实现）+ PyPI 占位（不自动执行）；正式 release → GHCR+PyPI 并更新 `latest`；pre-release → GHCR+TestPyPI；发布前必须通过测试与构建冒烟测试 |
| 13 | CI 触发 | 所有 push 跑 lint/format/typecheck；仅 `main` push 与 PR 跑测试（单元 + 容器），PR 测试通过 concurrency 只保留最新 commit |

## 11. 假设（未再提问，按此执行；有异议随时改）

- 网格默认线宽 1 px，透明度 0.5；文本→颜色用 sha256 前 3 字节映射到 HSL（S=0.75，L=0.5）。
- 分割/网格线在 JPEG q90 下的轻微锯齿可接受。
- `theta` 顺时针为正（与 DOTA/mmrotate le90 的换算写入规范）。
- 视频 `max_frames` 默认 32；超出时等间隔降采样并在 meta 说明。
- 测试夹具用程序生成的小图/小视频，仓库不提交二进制样本。
- 示例 README 用量以实际一次完整运行记录（token、费用、时长）；示例默认模型取各 SDK 当前最新默认，写入 `config/`。
- 示例执行 agent 只挂载 `workspaces/<task>/`，工具白名单由 `src/` 内的 SDK 配置限定。

## 12. 立即执行的下一步（P0）

1. 用中文起草 tracking issue 与 P0 sub-issues（harness 各层）供你审查 → 英文发布。
2. 按 meta-harness-architecture / meta-python-defaults / meta-github-workflow 搭建 §4 中的 harness 文件、CI、模板、labels、ruleset（远端写入前逐项确认）。
3. `just check` 与 CI 全绿后，向你确认 meta-* 清理。
