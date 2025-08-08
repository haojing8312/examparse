"""
案例分析题标准化处理器 - 使用OpenAI API
专门处理案例分析题的格式标准化，严格按照prompt.md要求进行绝对保真处理
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


class CaseAnalysisStandardizer:
    """案例分析题标准化器 - 使用OpenAI API，绝对保真处理"""
    
    def __init__(self, api_key: str = None, api_base: str = None, model: str = None):
        """
        初始化标准化器
        
        Args:
            api_key: OpenAI API密钥
            api_base: API基础地址
            model: 使用的模型名称
        """
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
        """获取默认配置"""
        return {
            "lines_per_chunk": 150,     # 每块行数
            "overlap_lines": 10,        # 重叠行数（用于防止题目被截断）
            "max_retries": 3,           # API调用重试次数
            "preserve_original": True,  # 是否保留原文件
            "output_format": "markdown" # 输出格式
        }
    
    def get_question_type_name(self) -> str:
        """获取题型名称"""
        return "案例分析题"
    
    def get_standard_format(self) -> str:
        """获取案例分析题的标准格式模板"""
        return """#### 题型
案例分析I

#### 难度
{难度}

#### 题干
{题干内容}

#### 选择项
无

#### 答案
{答案}"""
    
    def chunk_file(self, file_path: str) -> List[tuple]:
        """
        将文件按行数切分
        
        Args:
            file_path: 文件路径
            
        Returns:
            List[(chunk1_lines, chunk2_lines), ...] 每个元组包含当前块和下一块
        """
        return chunk_file_by_lines(file_path, self.config["lines_per_chunk"])
    
    def create_standardization_prompt(self, chunk1: List[str], chunk2: Optional[List[str]] = None) -> str:
        """创建高保真案例分析题标准化prompt，严格按照prompt.md要求"""
        
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
             3) 一个完整问句后，**紧随其后**出现 `参考答案要点`/`【参考答案】`/`参考答案` 提示。
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

* **题型**: 此字段内容固定为 `案例分析I`。

* **难度**:
  * 从题干中提取难度信息，如 `(难度: 4)` 或 `(难度5)`。提取后，仅保留数字，输出为 `较难4` 或 `难5` 等标准格式。
  * 如果题目中没有明确的难度标识，此字段内容应为 `未提供`。

* **题干**:
  * **【最高优先级指令】**: 你必须对题干（案例背景和问题）进行**完全逐字（verbatim）的复制**。**禁止进行任何形式的总结、归纳、改写或文本润色**。必须完整保留原文的所有文字、标点、换行和空格。
  * 唯一允许的修改是：在复制完成后，从中移除难度标识，例如 `  (难度: 4) `。

* **选择项**:
  * 此字段内容固定为 `无`。

* **答案**:
  * **【最高优先级指令】**: 你必须对`参考答案要点:` 或 `【参考答案】：`之后的所有内容进行**完全逐字（verbatim）的复制**。**禁止进行任何形式的总结、归纳、改写或文本润色**。必须完整保留原文的所有文字、标点、换行、缩进和列表格式，确保输出与原文在视觉和内容上**完全一致**。

**输出格式**:
每个试题使用以下格式：

```
### 试题 X

#### 题型
案例分析I

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
        """
        调用OpenAI进行标准化
        
        Args:
            prompt: 标准化prompt
            
        Returns:
            标准化结果或None（如果失败）
        """
        return call_openai_with_retries(
            client=self.client,
            model=self.model,
            prompt=prompt,
            max_retries=self.config["max_retries"],
            temperature=0.1,
        )
    
    def parse_standardized_result(self, ai_response: str) -> List[str]:
        """
        解析AI返回的标准化结果
        
        Args:
            ai_response: AI返回的文本
            
        Returns:
            标准化后的题目列表
        """
        return split_questions_by_separator(ai_response)
    
    def save_chunk_results(self, chunk_index: int, questions: List[str], output_dir: str):
        """
        保存单个chunk的标准化结果
        
        Args:
            chunk_index: chunk索引
            questions: 标准化后的题目列表
            output_dir: 输出目录
        """
        save_markdown_chunk_result(
            chunk_index=chunk_index,
            questions=questions,
            output_dir=output_dir,
            question_type_name=self.get_question_type_name(),
        )
    
    def save_original_chunk(self, chunk_index: int, chunk1: List[str], chunk2: Optional[List[str]], output_dir: str):
        """
        保存原始分块文件（用于对比）
        
        Args:
            chunk_index: chunk索引
            chunk1: 第一个chunk的内容（主要处理内容）
            chunk2: 第二个chunk的内容（仅用于防截断，不保存到原始文件中）
            output_dir: 输出目录
        """
        save_original_chunk_file(
            chunk_index=chunk_index,
            chunk1=chunk1,
            output_dir=output_dir,
        )
    
    def standardize_file(self, input_file: str, output_dir: str = None) -> Dict:
        """
        标准化单个题型文件的主要方法
        
        Args:
            input_file: 输入文件路径
            output_dir: 输出目录，如果不指定则自动生成
            
        Returns:
            处理结果统计
        """
        if output_dir is None:
            base_dir = os.path.dirname(input_file)
            output_dir = os.path.join(base_dir, f"{self.get_question_type_name()}_standardized")
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        print(f"🚀 开始标准化 {self.get_question_type_name()}")
        print(f"📁 输入文件: {input_file}")
        print(f"📁 输出目录: {output_dir}")
        
        # 备份原文件
        if self.config["preserve_original"]:
            backup_file = os.path.join(output_dir, "original_backup.md")
            os.system(f'cp "{input_file}" "{backup_file}"')
            print(f"💾 原文件已备份到: {backup_file}")
        
        # 切分文件
        print(f"🔪 正在切分文件...")
        chunks = self.chunk_file(input_file)
        print(f"📝 文件已切分为 {len(chunks)} 个块")
        
        # 保存原始分块文件（用于对比）
        if self.config["preserve_original"]:
            print(f"💾 正在保存原始分块文件...")
            for i, (chunk1, chunk2) in enumerate(chunks, 1):
                self.save_original_chunk(i, chunk1, chunk2, output_dir)
        
        # 标准化每个chunk
        total_questions = 0
        for i, (chunk1, chunk2) in enumerate(chunks, 1):
            print(f"\n🔄 处理 Chunk {i}/{len(chunks)}")
            
            # 创建标准化prompt
            prompt = self.create_standardization_prompt(chunk1, chunk2)
            
            # 调用AI标准化
            ai_response = self.call_ai_standardization(prompt)
            if ai_response is None:
                print(f"❌ Chunk {i} AI调用失败，跳过")
                continue
            
            # 解析结果
            questions = self.parse_standardized_result(ai_response)
            
            # 保存结果
            self.save_chunk_results(i, questions, output_dir)
            total_questions += len(questions)
        
        # 保存质量统计
        quality_stats = {
            "question_type": self.get_question_type_name(),
            "total_chunks": len(chunks),
            "total_questions": total_questions,
            "processing_time": datetime.now().isoformat(),
            "config": self.config
        }
        
        stats_file = os.path.join(output_dir, "quality_stats.json")
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(quality_stats, f, ensure_ascii=False, indent=2)
        
        print(f"\n🎉 {self.get_question_type_name()} 标准化完成！")
        print(f"📊 总计处理: {len(chunks)} 个块, {total_questions} 道题目")
        print(f"📁 结果保存在: {output_dir}")
        
        return quality_stats
    
    def extract_questions_from_standardized_files(self, standardized_dir: str) -> List[Dict]:
        """
        从标准化文件中使用正则表达式提取试题信息
        
        Args:
            standardized_dir: 标准化文件目录
            
        Returns:
            提取的试题信息列表
        """
        questions = []
        
        # 获取所有标准化chunk文件
        chunk_files = list_standardized_chunk_files(standardized_dir)
        
        print(f"🔍 找到 {len(chunk_files)} 个标准化文件")
        
        for chunk_file in chunk_files:
            chunk_path = chunk_file
            print(f"📖 正在处理: {os.path.basename(chunk_file)}")

            with open(chunk_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取每个试题块（从```到```之间的内容）
            question_blocks = extract_codeblocks_from_markdown(content)
            
            for block in question_blocks:
                question_data = self.parse_question_block(block)
                if question_data:
                    questions.append(question_data)
        
        print(f"✅ 总共提取 {len(questions)} 道题目")
        return questions
    
    def parse_question_block(self, block: str) -> Optional[Dict]:
        """
        解析单个题目块，提取各个字段
        
        Args:
            block: 题目文本块
            
        Returns:
            题目信息字典或None
        """
        try:
            # 使用正则表达式提取各个字段
            patterns = {
                'question_number': r'### 试题 (\d+)',
                'question_type': r'#### 题型\n(.*?)(?=\n|$)',
                'difficulty': r'#### 难度\n(.*?)(?=\n|$)',
                'question_stem': r'#### 题干\n(.*?)(?=#### 选择项)',
                'options': r'#### 选择项\n(.*?)(?=#### 答案)',
                'answer': r'#### 答案\n(.*?)(?=\n=== 题目分隔符 ===|$)'
            }
            
            extracted_data = {}
            for field, pattern in patterns.items():
                match = re.search(pattern, block, re.DOTALL)
                if match:
                    extracted_data[field] = match.group(1).strip()
                else:
                    extracted_data[field] = ""
            
            # 验证必要字段
            if not extracted_data.get('question_stem') or not extracted_data.get('answer'):
                print(f"⚠️  跳过不完整的题目: {extracted_data.get('question_number', '未知')}")
                return None
            
            return {
                'code': '',  # 代码列留空
                'question_type': extracted_data['question_type'] or '案例分析I',
                'difficulty': extracted_data['difficulty'] or '未提供',
                'question_stem': extracted_data['question_stem'],
                'option_A': '',  # 案例分析题无选择项
                'option_B': '',
                'option_C': '',
                'option_D': '',
                'option_E': '',
                'answer': extracted_data['answer'],
                'score': '',  # 分数列留空
                'consistency': ''  # 题目一致性列留空
            }
            
        except Exception as e:
            print(f"❌ 解析题目块时出错: {e}")
            return None
    
    def create_excel_file(self, questions: List[Dict], output_path: str):
        """
        创建Excel文件，按照模板格式写入题目
        
        Args:
            questions: 题目数据列表
            output_path: 输出Excel文件路径
        """
        # 表头与行数据
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

        write_excel(headers=headers, rows=rows, sheet_title="案例分析题", output_path=output_path)
    
    def process_standardized_to_excel(self, standardized_dir: str, output_dir: str = None) -> str:
        """
        处理标准化文件并生成Excel
        
        Args:
            standardized_dir: 标准化文件目录
            output_dir: 输出目录，如果不指定则使用standardized_dir
            
        Returns:
            生成的Excel文件路径
        """
        if output_dir is None:
            output_dir = standardized_dir
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        print(f"🚀 开始处理标准化文件生成Excel")
        print(f"📁 标准化文件目录: {standardized_dir}")
        print(f"📁 输出目录: {output_dir}")
        
        # 提取题目
        questions = self.extract_questions_from_standardized_files(standardized_dir)
        
        if not questions:
            print("❌ 未找到有效题目，跳过Excel生成")
            return None
        
        # 生成Excel文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        excel_filename = f"案例分析题_{timestamp}.xlsx"
        excel_path = os.path.join(output_dir, excel_filename)
        
        self.create_excel_file(questions, excel_path)
        
        # 保存处理统计
        stats = {
            "question_type": self.get_question_type_name(),
            "total_questions": len(questions),
            "excel_file": excel_path,
            "processing_time": datetime.now().isoformat()
        }
        
        stats_file = os.path.join(output_dir, f"excel_generation_stats_{timestamp}.json")
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        print(f"🎉 Excel生成完成！")
        print(f"📊 处理统计: {stats}")
        
        return excel_path


def main():
    """测试函数"""
    import os
    from config import Config
    
    # 获取配置 - 使用OpenAI配置
    config = Config.get_openai_config()
    api_key = config['api_key']
    api_base = config.get('api_base', 'https://api.openai.com/v1')
    model = config.get('model', 'gpt-4o')
    
    # 创建标准化器
    standardizer = CaseAnalysisStandardizer(
        api_key=api_key,
        api_base=api_base,
        model=model
    )
    
    # 设置配置参数
    standardizer.config["lines_per_chunk"] = 150  # 测试用较小的chunk
    
    # 处理案例分析题文件
    input_file = "question_processing_《数据安全管理员题库》（客观题）-20250713（提交版）/question_types/case_analysis.md"
    
    if os.path.exists(input_file):
        # 第一步：标准化处理
        result = standardizer.standardize_file(input_file)
        print(f"\n🎉 标准化完成！")
        print(f"📊 处理结果: {result}")
        
        # 第二步：生成Excel文件
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


def generate_excel_only():
    """仅生成Excel文件的函数（当标准化已完成时使用）"""
    standardizer = CaseAnalysisStandardizer()
    
    standardized_dir = "question_processing_《数据安全管理员题库》（客观题）-20250713（提交版）/question_types/案例分析题_standardized"
    
    if os.path.exists(standardized_dir):
        excel_path = standardizer.process_standardized_to_excel(standardized_dir)
        if excel_path:
            print(f"\n✅ Excel文件生成完成: {excel_path}")
        else:
            print(f"\n❌ Excel文件生成失败")
    else:
        print(f"❌ 标准化目录不存在: {standardized_dir}")


if __name__ == "__main__":
    # 由于标准化已经完成，直接生成Excel
    generate_excel_only()