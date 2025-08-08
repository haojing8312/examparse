#!/usr/bin/env python3
"""
数据安全管理员题库处理工具 - 标准化与导出

说明：
- 已移除非AI的题目拆分与处理逻辑
- 已移除 Gemini 依赖与流程
- 该脚本将直接调用各题型标准化器（基于 OpenAI），
  对 `question_types/` 下的现有题型 markdown 进行标准化并导出 Excel
"""

import os
import sys
import argparse
from config import Config
from single_choice_standardizer import SingleChoiceStandardizer
from multiple_choice_standardizer import MultipleChoiceStandardizer
from judgment_standardizer import JudgmentStandardizer
from short_answer_standardizer import ShortAnswerStandardizer
from essay_standardizer import EssayStandardizer
from case_analysis_standardizer import CaseAnalysisStandardizer


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='数据安全管理员题库处理工具（OpenAI 标准化）')
    parser.add_argument('--type', choices=['single', 'multiple', 'judgment', 'short', 'essay', 'case', 'all'], default='all',
                       help='处理题型：single/multiple/judgment/short/essay/case/all (默认: all)')
    parser.add_argument('--base-dir', default=None, help='题型markdown所在的question_types目录（默认自动检测）')
    
    args = parser.parse_args()
    
    print("=== 数据安全管理员题库处理工具（OpenAI） ===\n")
    # 加载 OpenAI 配置（各标准化器内部会自行读取 .env）
    openai_cfg = Config.get_openai_config()
    if not openai_cfg.get('api_key'):
        print('❌ 未检测到 OPENAI_API_KEY，请在 .env 中配置。')
        return 1
    
    # 定位 question_types 目录
    base_dir = args.base_dir
    if not base_dir:
        # 尝试自动推断一个以 question_processing_ 开头的工作目录
        candidates = [d for d in os.listdir('.') if d.startswith('question_processing_') and os.path.isdir(d)]
        if candidates:
            # 取最近修改的一个
            candidates.sort(key=lambda d: os.path.getmtime(d), reverse=True)
            base_dir = os.path.join(candidates[0], 'question_types')
        else:
            print('❌ 未找到 question_types 目录，请通过 --base-dir 指定。')
            return 1
    if not os.path.exists(base_dir):
        print(f'❌ 指定的 question_types 目录不存在: {base_dir}')
        return 1

    print(f'📁 题型目录: {base_dir}')

    type_to_file = {
        'single': os.path.join(base_dir, 'single_choice.md'),
        'multiple': os.path.join(base_dir, 'multiple_choice.md'),
        'judgment': os.path.join(base_dir, 'judgment.md'),
        'short': os.path.join(base_dir, 'short_answer.md'),
        'essay': os.path.join(base_dir, 'essay.md'),
        'case': os.path.join(base_dir, 'case_analysis.md'),
    }

    type_to_handler = {
        'single': SingleChoiceStandardizer(),
        'multiple': MultipleChoiceStandardizer(),
        'judgment': JudgmentStandardizer(),
        'short': ShortAnswerStandardizer(),
        'essay': EssayStandardizer(),
        'case': CaseAnalysisStandardizer(),
    }

    to_process = list(type_to_file.keys()) if args.type == 'all' else [args.type]

    for t in to_process:
        input_file = type_to_file[t]
        if not os.path.exists(input_file):
            print(f'⚠️  跳过 {t}：未找到文件 {input_file}')
            continue

        handler = type_to_handler[t]
        print(f"\n🚀 开始标准化：{t} -> {input_file}")
        try:
            result = handler.standardize_file(input_file)
            print(f"✅ 标准化完成: {result}")

            standardized_dir = os.path.join(
                os.path.dirname(input_file),
                f"{handler.get_question_type_name()}_standardized"
            )
            if os.path.exists(standardized_dir):
                excel_path = handler.process_standardized_to_excel(standardized_dir)
                if excel_path:
                    print(f"📊 Excel 已生成: {excel_path}")
        except Exception as e:
            print(f"❌ 处理 {t} 时出错: {e}")

    print("\n🎉 全部处理完成。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
