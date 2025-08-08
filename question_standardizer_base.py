"""
题目标准化基础框架
所有题型标准化器的基类
"""

import os
import json
import google.generativeai as genai
from typing import List, Tuple, Dict, Optional
from datetime import datetime
from abc import ABC, abstractmethod


class QuestionStandardizerBase(ABC):
    """题目标准化器基类"""
    
    def __init__(self, api_key: str, api_base: str = "https://generativelanguage.googleapis.com/v1beta", model: str = "gemini-2.5-pro"):
        """
        初始化标准化器
        
        Args:
            api_key: Gemini API密钥
            api_base: API基础地址
            model: 使用的模型名称
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        self.model_name = model
        self.config = self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "lines_per_chunk": 100,     # 每块行数
            "overlap_lines": 10,        # 重叠行数
            "max_retries": 3,           # API调用重试次数
            "preserve_original": True,  # 是否保留原文件
            "output_format": "markdown" # 输出格式
        }
    
    @abstractmethod
    def get_question_type_name(self) -> str:
        """获取题型名称"""
        pass
    
    @abstractmethod  
    def get_standard_format(self) -> str:
        """获取标准格式模板"""
        pass
    
    @abstractmethod
    def get_format_description(self) -> str:
        """获取格式说明"""
        pass
    
    @abstractmethod
    def create_standardization_prompt(self, chunk1: List[str], chunk2: Optional[List[str]] = None) -> str:
        """创建标准化prompt"""
        pass
    
    def chunk_file(self, file_path: str) -> List[Tuple[List[str], Optional[List[str]]]]:
        """
        将文件按行数切分
        
        Args:
            file_path: 文件路径
            
        Returns:
            List[(chunk1_lines, chunk2_lines), ...] 每个元组包含当前块和下一块
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
        
        # 提取原始文本部分（去掉markdown头部）
        content_start = -1
        for i, line in enumerate(all_lines):
            if line.strip() == "```" and i > 0:  # 找到第一个```（内容开始）
                content_start = i + 1
                break
        
        if content_start == -1:
            raise ValueError("无法找到markdown文本内容")
        
        # 提取到最后一个```之前的内容
        content_end = len(all_lines)
        for i in range(len(all_lines) - 1, 0, -1):
            if all_lines[i].strip() == "```":
                content_end = i
                break
        
        content_lines = all_lines[content_start:content_end]
        
        chunks = []
        lines_per_chunk = self.config["lines_per_chunk"]
        overlap_lines = self.config["overlap_lines"]
        
        for i in range(0, len(content_lines), lines_per_chunk):
            chunk1_start = i
            chunk1_end = min(i + lines_per_chunk, len(content_lines))
            chunk1 = content_lines[chunk1_start:chunk1_end]
            
            # 获取下一块的开始部分作为参考（防止题目被截断）
            chunk2 = None
            if chunk1_end < len(content_lines):
                chunk2_end = min(chunk1_end + lines_per_chunk, len(content_lines))
                chunk2 = content_lines[chunk1_end:chunk2_end]
            
            chunks.append((chunk1, chunk2))
        
        return chunks
    
    def call_ai_standardization(self, prompt: str) -> Optional[str]:
        """
        调用AI进行标准化
        
        Args:
            prompt: 标准化prompt
            
        Returns:
            标准化结果或None（如果失败）
        """
        for attempt in range(self.config["max_retries"]):
            try:
                response = self.model.generate_content(prompt)
                
                # 更详细的响应处理
                content = None
                if hasattr(response, 'text') and response.text:
                    content = response.text
                elif hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    
                    # 检查finish_reason
                    if hasattr(candidate, 'finish_reason'):
                        finish_reason = candidate.finish_reason
                        print(f"📊 API响应状态: finish_reason={finish_reason}")
                        
                        if finish_reason == 3:  # SAFETY
                            print(f"⚠️ 内容被安全过滤器阻止，尝试修改prompt")
                            # 如果是安全问题，尝试修改prompt重试
                            modified_prompt = f"Please help with the following task in a professional manner:\n{prompt}"
                            try:
                                retry_response = self.model.generate_content(modified_prompt)
                                if hasattr(retry_response, 'text') and retry_response.text:
                                    content = retry_response.text
                            except:
                                pass
                        elif finish_reason == 4:  # RECITATION
                            print(f"⚠️ 内容被认为是训练数据重复，尝试重新表述")
                        elif finish_reason == 1:  # STOP
                            if hasattr(candidate, 'content') and candidate.content and candidate.content.parts:
                                content = candidate.content.parts[0].text
                            else:
                                print(f"⚠️ 模型停止但无内容输出，可能prompt过于简单或触发了限制")
                
                if content and content.strip():
                    return content
                else:
                    print(f"❌ 第{attempt + 1}次尝试：未获取到有效响应")
                
            except Exception as e:
                print(f"API调用失败 (尝试 {attempt + 1}/{self.config['max_retries']}): {e}")
                if attempt == self.config["max_retries"] - 1:
                    return None
        
        return None
    
    def parse_standardized_result(self, ai_response: str) -> List[str]:
        """
        解析AI返回的标准化结果
        
        Args:
            ai_response: AI返回的文本
            
        Returns:
            标准化后的题目列表
        """
        if not ai_response:
            return []
        
        # 按分隔符分割题目
        separator = "=== 题目分隔符 ==="
        questions = ai_response.split(separator)
        
        # 清理和过滤
        cleaned_questions = []
        for q in questions:
            q = q.strip()
            if q and len(q) > 50:  # 过滤过短的内容
                cleaned_questions.append(q)
        
        return cleaned_questions
    
    def save_original_chunk(self, chunk_index: int, chunk1: List[str], chunk2: Optional[List[str]], output_dir: str):
        """
        保存原始分块文件（用于对比）
        
        Args:
            chunk_index: chunk索引
            chunk1: 第一个chunk的内容（主要处理内容）
            chunk2: 第二个chunk的内容（仅用于防截断，不保存到原始文件中）
            output_dir: 输出目录
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 保存原始chunk文件（只保存对应分块的内容）
        chunk_file = os.path.join(output_dir, f"original_chunk_{chunk_index:03d}.md")
        with open(chunk_file, 'w', encoding='utf-8') as f:
            f.write(f"# 原始 Chunk {chunk_index}\n\n")
            f.write(f"## 生成时间\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## 分块内容\n\n")
            f.write(''.join(chunk1))
        
        print(f"💾 原始 Chunk {chunk_index} 已保存到: {chunk_file}")

    def save_chunk_results(self, chunk_index: int, questions: List[str], output_dir: str):
        """
        保存单个chunk的标准化结果
        
        Args:
            chunk_index: chunk索引
            questions: 标准化后的题目列表
            output_dir: 输出目录
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 保存为markdown文件
        chunk_file = os.path.join(output_dir, f"standardized_chunk_{chunk_index:03d}.md")
        
        with open(chunk_file, 'w', encoding='utf-8') as f:
            f.write(f"# {self.get_question_type_name()} - Chunk {chunk_index}\n\n")
            f.write(f"## 标准化时间\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## 题目数量\n{len(questions)}\n\n")
            f.write(f"## 标准化题目\n\n")
            
            for i, question in enumerate(questions, 1):
                f.write(f"### 题目 {i}\n\n")
                f.write(f"```\n{question}\n```\n\n")
        
        print(f"✅ Chunk {chunk_index}: 保存 {len(questions)} 道题目到 {chunk_file}")
    
    def generate_summary_report(self, total_chunks: int, total_questions: int, output_dir: str):
        """
        生成汇总报告
        
        Args:
            total_chunks: 总chunk数
            total_questions: 总题目数
            output_dir: 输出目录
        """
        report_file = os.path.join(output_dir, "standardization_report.md")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"# {self.get_question_type_name()} 标准化报告\n\n")
            f.write(f"## 处理概况\n")
            f.write(f"- 处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- 题目类型: {self.get_question_type_name()}\n")
            f.write(f"- 总chunk数: {total_chunks}\n")
            f.write(f"- 标准化题目总数: {total_questions}\n")
            f.write(f"- 平均每chunk题目数: {total_questions/total_chunks if total_chunks > 0 else 0:.1f}\n\n")
            
            f.write(f"## 标准格式\n")
            f.write(f"```\n{self.get_standard_format()}\n```\n\n")
            
            f.write(f"## 格式说明\n")
            f.write(f"{self.get_format_description()}\n\n")
            
            f.write(f"## 文件结构\n")
            f.write(f"```\n")
            f.write(f"{os.path.basename(output_dir)}/\n")
            f.write(f"├── original_backup.md           # 原文件备份\n")
            f.write(f"├── standardization_report.md   # 本报告\n")
            for i in range(total_chunks):
                f.write(f"├── original_chunk_{i+1:03d}.md      # 第{i+1}个chunk的原始内容（用于对比）\n")
            for i in range(total_chunks):
                f.write(f"├── standardized_chunk_{i+1:03d}.md  # 第{i+1}个chunk的标准化结果\n")
            f.write(f"└── quality_stats.json          # 质量统计数据\n")
            f.write(f"```\n")
        
        print(f"📊 汇总报告已保存到: {report_file}")
    
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
        
        # 生成汇总报告
        self.generate_summary_report(len(chunks), total_questions, output_dir)
        
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