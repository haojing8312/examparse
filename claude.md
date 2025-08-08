项目测试说明（面向AI协作）

1. 单元测试组织
   - 所有单元测试统一放置在 `tests/` 目录
   - 运行全部用例：
     ```bash
     uv run pytest tests -q
     ```
   - 运行单个用例：
     ```bash
     uv run pytest tests/test_text_splitting.py -v
     ```

2. 临时脚本清理
   - 为保持仓库整洁，临时调试脚本已移除（例如 `simple_test.py`、`debug_gemini.py`）
   - 如需调试，请新增临时分支或在 `tests/` 内编写隔离的用例

3. 标准化器入口
   - 各题型标准化器的 `main()` 默认执行：标准化 → 解析标准化结果 → 生成 Excel
   - 例如：
     ```bash
     uv run python single_choice_standardizer.py
     uv run python judgment_standardizer.py
     uv run python multiple_choice_standardizer.py
     uv run python short_answer_standardizer.py
     uv run python essay_standardizer.py
     ```

4. 公共工具复用
   - `utils/standardization_utils.py` 提供：
     - 文件分块、OpenAI重试调用
     - 标准化文本分割、分块结果与原始内容保存
     - 标准化目录遍历、Markdown代码块提取
     - Excel写入（含表头渲染与列宽自动调整）

5. 常见问题
   - `openai` import 警告：请确保在虚拟环境中安装依赖并通过 `uv sync` 同步
   - 生成的标准化目录与 Excel 路径：均在对应题型目录内自动创建


