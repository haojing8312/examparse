## ExamParse Desktop (Tauri + React)

本目录为桌面应用外壳（Tauri + React）。当前目标：提供基础 UI 骨架与 Tauri 命令，调用仓库根目录的 Python sidecar，并将事件转发到前端。

### 运行前置
- Node.js 18+
- Rust（稳定版）
- Tauri 构建依赖（参见官方文档）
- 根目录已完成 Python 依赖安装：`. .venv/bin/activate && uv sync`

### 开发启动（仅前端）
```bash
cd apps/desktop/ui
pnpm i # 或 npm i / yarn
pnpm dev # 或 npm run dev / yarn dev
```

### 桌面应用（Tauri）启动
```bash
# 终端 1：确保 Python venv 激活，便于 sidecar 可用
cd /home/easegen/liwenyao/ExamParse
source .venv/bin/activate

# 终端 2：启动 Tauri（会调用根目录 sidecar）
cd apps/desktop/ui
pnpm i
pnpm tauri dev
```

### 打包
```bash
cd apps/desktop/ui
pnpm tauri build
```

### 说明
- Tauri 后端通过命令 `start_jobs` 与 `start_mock` 调用 `python -m sidecar.main`，以管道读取 JSON 行事件并通过 `sidecar-event` 事件名推送到前端。
- 默认工作目录设为仓库根目录，并设置 `PYTHONPATH` 指向根目录，保证 `sidecar` 包可导入。


