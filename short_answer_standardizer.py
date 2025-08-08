"""
简答题标准化处理器 - 使用OpenAI API
专门处理简答题的格式标准化，严格按照prompt.md要求进行绝对保真处理
并提供标准化结果的解析与Excel导出能力。
"""

import os
import json
import re
import openai
from typing import List, Optional, Dict
from datetime import datetime
from config import Config
from utils.standardization_utils import (
    chunk_file_by_lines,
    call_openai_with_retries,
    split_questions_by_separator,
    save_markdown_chunk_result,
    save_original_chunk_file,
    list_standardized_chunk_files,
    extract_codeblocks_from_markdown,
    write_excel,
)


class ShortAnswerStandardizer:
    """简答题标准化器 - 使用OpenAI API，绝对保真处理"""

    def __init__(self, api_key: str = None, api_base: str = None, model: str = None):
        # 如果没有提供参数，从配置读取
        if not api_key:
            config = Config.get_openai_config()
            api_key = config.get('api_key')
            api_base = api_base or config.get('api_base', 'https://api.openai.com/v1')
            model = model or config.get('model', 'gpt-4o')

        self.client = openai.OpenAI(api_key=api_key, base_url=api_base)
        self.model = model
        self.config = self.get_default_config()

    def get_default_config(self) -> Dict:
        return {
            "lines_per_chunk": 120,
            "overlap_lines": 10,
            "max_retries": 3,
            "preserve_original": True,
            "output_format": "markdown",
        }

    def get_question_type_name(self) -> str:
        return "简答题"

    def get_standard_format(self) -> str:
        return """#### 题型
简答I

#### 难度
{难度}

#### 题干
{题干内容}

#### 选择项
无

#### 答案
{答案}"""

    def chunk_file(self, file_path: str) -> List[tuple]:
        """将文件按行数切分"""
        return chunk_file_by_lines(file_path, self.config["lines_per_chunk"])

    def create_standardization_prompt(self, chunk1: List[str], chunk2: Optional[List[str]] = None) -> str:
        current_slice = ''.join(chunk1)
        next_slice = ''.join(chunk2) if chunk2 else ""

        prompt = f"""**角色**: 你是一个高精度的文本流处理引擎，核心任务是在分块数据流中，以**绝对保真**的方式，识别、重组和格式化文本单元。你的任何操作都不能改变原文的措辞和结构。

**背景**: 我正在处理一个超长的Markdown源文件，已将其按行数分割为多个连续的文本"切片"（slice）。由于分割是机械的，一个完整的"试题"可能会被分割到两个相邻的切片中。你的任务是逐个处理这些切片，并以最高的保真度还原试题。

**核心任务**: 给我两个文本切片：`[current_slice]`（当前处理的切片）和 `[next_slice]`（紧随其后的切片），请你严格按照以下逻辑识别并格式化`[current_slice]`中的所有试题。

**输入**:

1. `[current_slice]`: 当前需要处理的主要文本块。
2. `[next_slice]`: 下一个文本块，仅用作"前瞻缓冲区"来补全`[current_slice]`末尾的断裂试题。

        **处理逻辑与规则**:

        1. **识别起点 (忽略已处理的头部)**:
           * 在`[current_slice]`的开头，判断其内容是否是一个完整试题的开始。一个试题的明确开始标志包括：
             1) **以数字开头的行**（如 `1. `、`2．`、`3（难度...）`等）；
             2) **不以数字开头**但本行或下一行包含难度标识（如`(难度: x)`、`（难度x）`、`（难度：x）`等）的完整问句；
             3) 一个完整问句后，**紧随其后**出现 `参考答案`/`参考答案要点`/`【参考答案】` 提示。
           * 如果`[current_slice]`的开头明显属于上一题的**答案中间部分**（如以项目符号`•`/`-`开头的答案要点等），你**必须忽略**这些内容，直到找到上述任一**明确的试题开始标志**为止。

2. **顺序处理与识别**:
   * 从你找到的第一个试题开始标志起，顺序向下解析`[current_slice]`中的每一道试题。

        3. **处理末尾的断裂试题 (前瞻拼接)**:
   * 当你解析到`[current_slice]`中的**最后一个试题**时，检查它是否在`[current_slice]`的末尾被截断。
   * 如果被截断，你**必须**查看`[next_slice]`的开头部分，并从中**逐字复制**内容，直到将这道被截断的试题补充完整为止。
           * **拼接界限**：从`[next_slice]`中复制内容的终点是这道题的结尾。一旦遇到下一个**明确的试题开始标志**（参见上文三类开始标志，而不仅是以数字开头），就应立即停止。

        4. **严格限定处理范围 (防止越界)**:
   * 你对`[next_slice]`的使用**仅限于**补全`[current_slice]`末尾的那一道断裂试题。
           * **绝对不能**处理任何在`[next_slice]`中完整开始的新试题（无论是否以数字开头，只要满足上述开始标志，都视为新试题，应留待下一轮处理）。

5. **输出与编号**:
   * 仅输出你在本轮（即在`[current_slice]`中识别并完成的）所有试题。
   * 对输出的试题进行**连续编号**，从`### 试题 1`开始。

**字段提取与格式化标准 (【高保真】核心指令)**:

* **题型**: 此字段内容固定为 `简答I`。

* **难度**:
  * 可从题干中提取难度信息，如 `(难度: 4)` 或 `(难度5)`；若无则输出 `未提供`。

* **题干**:
  * **【最高优先级指令】**: 你必须对题干进行**完全逐字（verbatim）的复制**。禁止总结、改写或润色。
  * 允许的唯一修改：从中移除难度标识（如 ` (难度: 4) `）。

* **选择项**: 固定输出 `无`。

* **答案**:
  * **【最高优先级指令】**: 对`参考答案:` 或 `答案:`之后的内容**完全逐字复制**，保留原文的所有符号、换行与缩进。

**输出格式**:
每个试题使用以下格式：

```
### 试题 X

#### 题型
简答I

#### 难度
[难度信息]

#### 题干
[完全保真的题干内容]

#### 选择项
无

#### 答案
[完全保真的答案内容]

=== 题目分隔符 ===
```

**当前处理的文本块 [current_slice]**:
```
{current_slice}
```

**下一个文本块 [next_slice]** (仅用于补全断裂试题):
```
{next_slice}
```

请开始处理，严格按照上述规则进行绝对保真的试题识别和格式化。"""

        return prompt

    def call_ai_standardization(self, prompt: str) -> Optional[str]:
        return call_openai_with_retries(
            client=self.client,
            model=self.model,
            prompt=prompt,
            max_retries=self.config["max_retries"],
            temperature=0.1,
        )

    def parse_standardized_result(self, ai_response: str) -> List[str]:
        return split_questions_by_separator(ai_response)

    def save_chunk_results(self, chunk_index: int, questions: List[str], output_dir: str):
        save_markdown_chunk_result(
            chunk_index=chunk_index,
            questions=questions,
            output_dir=output_dir,
            question_type_name=self.get_question_type_name(),
        )

    def save_original_chunk(self, chunk_index: int, chunk1: List[str], chunk2: Optional[List[str]], output_dir: str):
        save_original_chunk_file(
            chunk_index=chunk_index,
            chunk1=chunk1,
            output_dir=output_dir,
        )

    def standardize_file(self, input_file: str, output_dir: str = None) -> Dict:
        if output_dir is None:
            base_dir = os.path.dirname(input_file)
            output_dir = os.path.join(base_dir, f"{self.get_question_type_name()}_standardized")

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        print(f"🚀 开始标准化 {self.get_question_type_name()}")
        print(f"📁 输入文件: {input_file}")
        print(f"📁 输出目录: {output_dir}")

        if self.config["preserve_original"]:
            backup_file = os.path.join(output_dir, "original_backup.md")
            os.system(f'cp "{input_file}" "{backup_file}"')
            print(f"💾 原文件已备份到: {backup_file}")

        print(f"🔪 正在切分文件...")
        chunks = self.chunk_file(input_file)
        print(f"📝 文件已切分为 {len(chunks)} 个块")

        if self.config["preserve_original"]:
            print(f"💾 正在保存原始分块文件...")
            for i, (chunk1, chunk2) in enumerate(chunks, 1):
                self.save_original_chunk(i, chunk1, chunk2, output_dir)

        total_questions = 0
        for i, (chunk1, chunk2) in enumerate(chunks, 1):
            print(f"\n🔄 处理 Chunk {i}/{len(chunks)}")
            prompt = self.create_standardization_prompt(chunk1, chunk2)
            ai_response = self.call_ai_standardization(prompt)
            if ai_response is None:
                print(f"❌ Chunk {i} AI调用失败，跳过")
                continue
            questions = self.parse_standardized_result(ai_response)
            self.save_chunk_results(i, questions, output_dir)
            total_questions += len(questions)

        quality_stats = {
            "question_type": self.get_question_type_name(),
            "total_chunks": len(chunks),
            "total_questions": total_questions,
            "processing_time": datetime.now().isoformat(),
            "config": self.config,
        }

        stats_file = os.path.join(output_dir, "quality_stats.json")
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(quality_stats, f, ensure_ascii=False, indent=2)

        print(f"\n🎉 {self.get_question_type_name()} 标准化完成！")
        print(f"📊 总计处理: {len(chunks)} 个块, {total_questions} 道题目")
        print(f"📁 结果保存在: {output_dir}")

        return quality_stats

    def extract_questions_from_standardized_files(self, standardized_dir: str) -> List[Dict]:
        questions: List[Dict] = []
        chunk_files = list_standardized_chunk_files(standardized_dir)
        print(f"🔍 找到 {len(chunk_files)} 个标准化文件")

        for chunk_file in chunk_files:
            print(f"📖 正在处理: {os.path.basename(chunk_file)}")
            with open(chunk_file, 'r', encoding='utf-8') as f:
                content = f.read()

            blocks = extract_codeblocks_from_markdown(content)
            for block in blocks:
                question_data = self.parse_question_block(block)
                if question_data:
                    questions.append(question_data)

        print(f"✅ 总共提取 {len(questions)} 道题目")
        return questions

    def parse_question_block(self, block: str) -> Optional[Dict]:
        try:
            patterns = {
                'question_number': r'### 试题 (\d+)',
                'question_type': r'#### 题型\n(.*?)(?=\n|$)',
                'difficulty': r'#### 难度\n(.*?)(?=\n|$)',
                'question_stem': r'#### 题干\n(.*?)(?=#### 选择项)',
                'options': r'#### 选择项\n(.*?)(?=#### 答案)',
                'answer': r'#### 答案\n(.*?)(?=\n=== 题目分隔符 ===|$)'
            }

            extracted: Dict[str, str] = {}
            for field, pattern in patterns.items():
                match = re.search(pattern, block, re.DOTALL)
                extracted[field] = match.group(1).strip() if match else ""

            if not extracted.get('question_stem') or not extracted.get('answer'):
                print(f"⚠️  跳过不完整的题目: {extracted.get('question_number', '未知')}")
                return None

            return {
                'code': '',
                'question_type': extracted['question_type'] or '简答I',
                'difficulty': extracted['difficulty'] or '未提供',
                'question_stem': extracted['question_stem'],
                'option_A': '',
                'option_B': '',
                'option_C': '',
                'option_D': '',
                'option_E': '',
                'answer': extracted['answer'],
                'score': '',
                'consistency': '',
            }
        except Exception as exc:
            print(f"❌ 解析题目块时出错: {exc}")
            return None

    def create_excel_file(self, questions: List[Dict], output_path: str):
        headers = [
            '代码', '题型', '难度', '题干',
            '选择项A', '选择项B', '选择项C', '选择项D', '选择项E',
            '答案', '分数', '题目一致性'
        ]

        rows: List[List[str]] = []
        for q in questions:
            rows.append([
                q.get('code', ''),
                q.get('question_type', ''),
                q.get('difficulty', ''),
                q.get('question_stem', ''),
                q.get('option_A', ''),
                q.get('option_B', ''),
                q.get('option_C', ''),
                q.get('option_D', ''),
                q.get('option_E', ''),
                q.get('answer', ''),
                q.get('score', ''),
                q.get('consistency', ''),
            ])

        write_excel(headers=headers, rows=rows, sheet_title="简答题", output_path=output_path)

    def process_standardized_to_excel(self, standardized_dir: str, output_dir: str = None) -> Optional[str]:
        if output_dir is None:
            output_dir = standardized_dir

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        print("🚀 开始处理标准化文件生成Excel")
        print(f"📁 标准化文件目录: {standardized_dir}")
        print(f"📁 输出目录: {output_dir}")

        questions = self.extract_questions_from_standardized_files(standardized_dir)
        if not questions:
            print("❌ 未找到有效题目，跳过Excel生成")
            return None

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        excel_filename = f"简答题_{timestamp}.xlsx"
        excel_path = os.path.join(output_dir, excel_filename)

        self.create_excel_file(questions, excel_path)

        stats = {
            "question_type": self.get_question_type_name(),
            "total_questions": len(questions),
            "excel_file": excel_path,
            "processing_time": datetime.now().isoformat(),
        }
        stats_file = os.path.join(output_dir, f"excel_generation_stats_{timestamp}.json")
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        print("🎉 Excel生成完成！")
        print(f"📊 处理统计: {stats}")
        return excel_path


def main():
    """执行简答题标准化并导出Excel"""
    import os
    from config import Config

    config = Config.get_openai_config()
    api_key = config['api_key']
    api_base = config.get('api_base', 'https://api.openai.com/v1')
    model = config.get('model', 'gpt-4o')

    standardizer = ShortAnswerStandardizer(
        api_key=api_key,
        api_base=api_base,
        model=model,
    )

    # 可调整chunk大小
    standardizer.config["lines_per_chunk"] = 120

    input_file = "question_processing_《数据安全管理员题库》（客观题）-20250713（提交版）/question_types/short_answer.md"

    if os.path.exists(input_file):
        # 标准化
        result = standardizer.standardize_file(input_file)
        print(f"\n🎉 标准化完成！")
        print(f"📊 处理结果: {result}")

        # 导出Excel
        standardized_dir = os.path.join(
            os.path.dirname(input_file),
            f"{standardizer.get_question_type_name()}_standardized"
        )
        if os.path.exists(standardized_dir):
            excel_path = standardizer.process_standardized_to_excel(standardized_dir)
            if excel_path:
                print(f"\n✅ Excel文件生成完成: {excel_path}")
            else:
                print(f"\n❌ Excel文件生成失败")
        else:
            print(f"❌ 标准化目录不存在: {standardized_dir}")
    else:
        print(f"❌ 输入文件不存在: {input_file}")


if __name__ == "__main__":
    main()


