## ExamParse 桌面应用开发 TODO 列表

维护约定：
- 使用复选框标记进度；完成后勾选 [x]，必要时补充产出链接或说明。
- 遵循 TDD：先写用例再实现；所有变更需保持测试绿。
- 模块化/组件化：UI 与 Sidecar 与核心算法解耦，可替换可扩展。

### 已完成（可复查）
- [x] 创建 `sidecar/` 包，提供可执行入口 `-m sidecar.main`（mock 管线）
- [x] 事件模型：`sidecar/events.py`（Pydantic，`type|stage|ts|fileId|message|percent`，`percent∈[0,1]` 校验）
- [x] CLI 参数：`--mock`、`--input/--inputs`、`--output/--output-dir`
- [x] 输入校验：不存在文件即输出 `error: validate` 并退出非零
- [x] 多文件支持：为每个输入生成独立 `fileId` 并顺序输出事件
- [x] 测试：`tests/test_sidecar_events.py`、`tests/test_sidecar_config.py` 全绿
- [x] 依赖与环境：新增 `pydantic`，安装 dev 依赖（pytest、pytest-mock），本地虚拟环境可运行

### 进行中（当前迭代）
- [x] Sidecar 真实桥接（第一步仅打通 split/split-questions）
  - [x] 新增 `sidecar/runner.py`：封装阶段化调用，向 stdout 推送 JSON 事件
  - [x] 用例：monkeypatch `QuestionProcessor.process_questions`（间接替代 `extract_text_from_pdf` 依赖），模拟轻量路径，断言阶段事件序列与产物结构
  - [x] 从 mock 切换到真实桥接的最小闭环（单/多输入 → 阶段事件 → 产物）
- [x] 事件契约文档化（JSON Schema + 阶段名表 + 示例）
- [x] 中间产物缓存与恢复策略（阶段一：缓存跳过逻辑）
  - [ ] 阶段二：断点续跑与中间产物恢复（按阶段恢复点）
- [x] 错误分类与重试策略（指数退避、最大重试次数、可恢复/不可恢复区分）

#### 新增（本轮）
- [x] Tauri Rust 侧命令：`start_jobs`（支持单/多 PDF、可选输出目录、自动定位仓库根与 `.venv`）
- [x] 修复构建：新增 `build.rs` 与 `tauri-build`，引入 `tauri::Emitter`
- [x] Windows 图标：生成 `src-tauri/icons/icon.ico`（占位），消除构建失败
- [x] 前端事件订阅：改用 `@tauri-apps/api/event` 的 `listen` 订阅 `sidecar-event`
- [x] 前端最小界面：标题、按钮（开始 Mock、选择 PDF、选择输出目录、开始处理）、事件列表渲染

### 下一步：UI 外壳（Tauri + React）
- 设计系统 & 视觉
  - [ ] 设计 Tokens（色板、半径、阴影、动效参数）、暗色默认主题、AI 渐变/毛玻璃风格
  - [ ] 组件基座：Radix/Headless + Tailwind + Framer Motion
  - [ ] 基础组件封装：Button、Card、Progress、Toast、Dialog、DataTable（分页/筛选）
- Tauri 项目初始化
  - [x] 新建 `apps/desktop/`（Tauri 外壳 + React UI）
  - [x] Dev 启动链路（`tauri.conf.json` 指向 `ui/`，Rust 命令 `start_mock`）
  - [x] 事件桥接命令：`start_jobs`（真实 sidecar）
  - [ ] 打包目标配置（win/mac/linux）与 sidecar 嵌入
  - [ ] 定义完整 IPC：任务派发接口、密钥存储（Keychain）
- 页面与流程
  - [ ] 欢迎/设置（首次启动引导、API Key/模型/OCR 开关，系统钥匙串存储）
  - [ ] 主工作台（拖拽区 + 文件列表：名称/类型/大小/状态）
  - [ ] 任务队列（并发上限、暂停/继续/取消、失败重试）
  - [ ] 进度与日志（阶段进度、事件时间线、错误弹窗、复制日志）
  - [ ] 结果预览（表格分页、筛选题型/质量、告警提示）
  - [ ] 导出完成（打开文件夹、复制路径、再次处理）
- 功能联动
  - [x] 与 sidecar 事件流对接（最小事件列表展示）
  - [ ] 文件类型检测与去重（PDF/Word/TXT，预留 OCR）
  - [ ] 导出 Excel、一键打开所在目录
  - [ ] i18n 基础（中文优先，预留英文资源）

### 后端桥接扩展（核心流程可视化）
- [ ] `QuestionProcessor.process_questions` 分阶段映射 → 事件输出
- [ ] 与 `main.py` 标准化流程的 Hook（逐题型/全量）
- [ ] 参数化步骤选择（split/split-questions/process/export/full）
- [ ] 指标 Metric 事件（时长、速率、错误率、内存峰值）

### 测试（TDD 优先级顺序）
- 单元测试
  - [ ] `sidecar/runner.py` 行为测试（阶段顺序、异常路径、重试）
  - [ ] 事件 Schema 测试（fastjsonschema/pydantic 校验）
- 集成/E2E
  - [ ] 端到端（假数据）：触发 → 事件 → 产物校验
  - [ ] Tauri UI E2E（Playwright）：拖拽上传、进度展示、导出完成
  - [ ] 可达性测试（键盘导航、对比度）
- 性能与稳定性
  - [ ] 基准：1k 题 PDF ≤ 目标时长；记录内存峰值
  - [ ] 连续任务稳定运行（N 小时）

### 打包与发布
- [ ] Sidecar：PyInstaller/Nuitka 单文件可执行
- [ ] Tauri：Windows（NSIS/MSI）、macOS（.dmg）、Linux（AppImage/Deb）
- [ ] CI/CD（GitHub Actions）：三平台并行构建、签名/公证（可分阶段）、发布 Release
- [ ] 版本策略与变更日志（语义化版本）

### 文档
- [ ] 事件契约文档（字段、阶段、示例）
- [ ] 使用指南（首次启动、配置、拖拽、预览、导出）
- [ ] 常见问题（API、权限、性能、日志）
- [ ] 贡献指南更新（目录结构、运行与测试、代码规范）

### 验收标准（MVP）
- [ ] 单文件输入 → 可视进度 → 结果预览 → 一键导出 Excel，全流程无崩溃
- [ ] 多文件批处理：失败重试、任务可取消
- [ ] API Key 安全存储（系统钥匙串），不落盘明文
- [ ] Windows 与 Linux 至少两平台产物可运行

### 维护说明
- 每次任务完成即在本文件勾选，并在 PR/提交信息中引用该条目
- 若任务拆分过大，请细化为可在 0.5～1 天内完成的子任务


