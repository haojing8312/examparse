# 数据安全管理员题库处理工具

## 项目简介

这是一个用于处理PDF题库文件的工具，支持按题型拆分、题目提取和AI结构化处理。

## 功能特性

- 📄 PDF文本提取和题型分类
- 🔍 智能题目识别和拆分
- 🤖 AI驱动的题目结构化处理
- 📊 详细的统计报告和追溯功能
- 🎯 分步骤处理，支持验证和调试

## 安装依赖

```bash
# 安装uv包管理器
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装项目依赖
uv sync
```

## 配置API与环境变量

推荐使用 `.env` 文件集中管理环境变量：

1. 复制 `env.example` 为 `.env`
2. 填写 `OPENAI_API_KEY`、`OPENAI_API_BASE`、`OPENAI_MODEL_NAME`（或使用 Gemini 相关变量）
3. 运行时会自动从 `.env` 加载变量（见 `config.py` 的 `load_env_file`）

环境变量示例：

```
OPENAI_API_KEY=sk-xxxx
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL_NAME=gpt-4o
```

## 分步骤测试命令

### 运行主流程（基于 OpenAI 标准化）
```bash
# 先在当前项目创建虚拟环境（建议）
uv venv
source .venv/bin/activate  # Windows 使用 .venv\Scripts\activate

# 安装依赖
uv sync

# 自动发现最新的 question_processing_*/question_types 目录，按题型批量标准化与导出
uv run python main.py --type all

# 或仅处理某一个题型（示例：单选题）
uv run python main.py --type single --base-dir "question_processing_《数据安全管理员题库》（客观题）-20250713（提交版）/question_types"
```

### 第四步：运行单元测试
```bash
# 运行全部用例
uv run pytest tests -q

# 或仅运行某个用例文件
uv run pytest tests/test_text_splitting.py -v
```
- 所有单元测试已迁移至 `tests/` 目录
- 验证题目拆分算法与标准化流程的正确性
- 确保所有测试用例通过

### 第五步：测试题目提取效果
```bash
uv run python -c "
from question_processor import QuestionProcessor
processor = QuestionProcessor('your-api-key')
# 测试题目提取算法
"
```

说明：
- 已移除非AI的题目拆分与处理逻辑；当前逻辑依赖 OpenAI 对题型 markdown 进行标准化与导出
- 已移除 Gemini 支持，统一使用 `.env` 中的 OpenAI 配置

### 各题型独立标准化器（可直接运行生成 Excel）
```bash
uv run python single_choice_standardizer.py      # 单选题
uv run python multiple_choice_standardizer.py    # 多选题
uv run python judgment_standardizer.py           # 判断题
uv run python short_answer_standardizer.py       # 简答题
uv run python essay_standardizer.py              # 论述题
uv run python case_analysis_standardizer.py      # 案例分析题
```

### 第七步：指定输入输出文件
```bash
uv run python main.py --input "input.pdf" --output "result.xlsx" --step full
```

## 验证命令

```bash
# 查看生成的文件结构
ls -la question_processing_*/

# 查看拆分统计
cat question_processing_*/split_summary.md

# 查看某个题型的详细统计
cat question_processing_*/question_types/单选题_questions/split_stats.md

# 查看单个题目文件
cat question_processing_*/question_types/单选题_questions/question_0001.md
```

## 处理步骤说明

### 步骤1: 按题型拆分 (split)
- 识别PDF中的题型标题
- 将不同题型分别保存为markdown文件
- 保留原始文本和元数据信息

### 步骤2: 题目拆分 (split-questions)
- 使用正则表达式识别题目编号
- 将每个题型文件拆分为独立题目
- 生成详细的统计报告
- 支持多种编号格式识别

### 步骤3: AI处理 (process)
- 使用大语言模型结构化处理题目
- 提取题目类型、难度、选项、答案等信息
- 生成标准化的Excel输出文件

## 文件结构

```
question_processing_[PDF名称]/
├── question_types/              # 题型分类文件
│   ├── single_choice.md         # 单选题 (476题)
│   ├── multiple_choice.md       # 多选题 (124题)
│   ├── judgment.md              # 判断题 (318题)
│   ├── short_answer.md          # 简答题 (45题)
│   ├── essay.md                # 论述题 (23题)
│   └── case_analysis.md        # 案例分析题 (22题)
├── 单选题_questions/            # 拆分出的单选题
│   ├── question_0001.md
│   ├── question_0002.md
│   ├── ...
│   └── split_stats.md          # 拆分统计
├── [其他题型目录...]
└── split_summary.md            # 总体拆分统计
```

### 测试文件位置

```
tests/
├── test_text_splitting.py
├── test_pdf_extraction.py
├── test_excel_writing.py
├── test_integration.py
└── ...
```

说明：临时调试脚本已清理（如 `simple_test.py`、`debug_gemini.py`）。请使用 `pytest` 在 `tests/` 目录下运行单元测试。

## 故障排除

### 常见问题

1. **题目提取率低**
   - 检查PDF格式是否规范
   - 查看split_stats.md了解详细统计
   - 可能需要优化正则表达式

2. **API调用失败**
   - 检查config.py中的API配置
   - 确认网络连接正常
   - 验证API密钥有效性

3. **文件权限问题**
   - 确保有写入目录的权限
   - 检查磁盘空间是否充足

### 调试技巧

1. 使用 `--step split` 先验证题型拆分
2. 使用 `--type-file` 单独测试某个题型
3. 查看生成的markdown文件验证内容
4. 检查统计报告了解提取效果

## 性能优化

- 对于大型PDF文件，建议分步骤处理
- 可以单独处理特定题型进行调试
- 使用 `--type-file` 参数进行精确测试

## 贡献指南

1. 运行测试确保功能正常
2. 遵循现有的代码风格
3. 添加适当的文档和注释
4. 提交前进行充分测试

## 未来规划

- 提供跨平台客户端（桌面GUI），一键导入 Word/PDF/TXT，自动生成 Excel
- 内置模板选择与题型映射配置
- 支持批量处理与断点续跑
- 模型/速率/重试等参数可视化配置
- 生态：导出 CSV/JSON、数据库入库、API 服务化

## 许可证

本项目采用MIT许可证。