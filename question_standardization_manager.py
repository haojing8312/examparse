"""
题目标准化管理器
统一管理所有题型的标准化处理
"""

import os
from typing import Dict, List
from config import Config

# 导入所有标准化器
from single_choice_standardizer import SingleChoiceStandardizer
from multiple_choice_standardizer import MultipleChoiceStandardizer  
from judgment_standardizer import JudgmentStandardizer
from case_analysis_standardizer import CaseAnalysisStandardizer


class QuestionStandardizationManager:
    """题目标准化管理器"""
    
    def __init__(self, api_key: str = None, api_base: str = None, model: str = None):
        """
        初始化标准化管理器
        
        Args:
            api_key: Gemini API密钥，如果不提供则从配置读取
            api_base: API基础地址
            model: 使用的模型名称
        """
        # 获取配置
        if api_key is None:
            config = Config.get_gemini_config()
            api_key = config['api_key']
            api_base = api_base or config.get('api_base', 'https://generativelanguage.googleapis.com/v1beta')
            model = model or config.get('model', 'gemini-2.5-pro')
        
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        
        # 题型文件映射
        self.type_mapping = {
            "single_choice.md": {
                "name": "单选题",
                "standardizer": SingleChoiceStandardizer,
                "expected_count": 476
            },
            "multiple_choice.md": {
                "name": "多选题", 
                "standardizer": MultipleChoiceStandardizer,
                "expected_count": 124
            },
            "judgment.md": {
                "name": "判断题",
                "standardizer": JudgmentStandardizer,
                "expected_count": 318
            },
            "case_analysis.md": {
                "name": "案例分析题",
                "standardizer": CaseAnalysisStandardizer,
                "expected_count": 22
            },
            "short_answer.md": {
                "name": "简答题",
                "standardizer": None,  # 待实现
                "expected_count": 45
            },
            "essay.md": {
                "name": "论述题",
                "standardizer": None,  # 待实现
                "expected_count": 23
            }
        }
    
    def get_available_types(self) -> List[str]:
        """获取可用的题型列表"""
        available = []
        for filename, info in self.type_mapping.items():
            if info["standardizer"] is not None:
                available.append(info["name"])
        return available
    
    def standardize_single_type(self, type_file: str, custom_config: Dict = None) -> Dict:
        """
        标准化单个题型文件
        
        Args:
            type_file: 题型文件路径
            custom_config: 自定义配置
            
        Returns:
            处理结果统计
        """
        if not os.path.exists(type_file):
            raise FileNotFoundError(f"题型文件不存在: {type_file}")
        
        filename = os.path.basename(type_file)
        
        if filename not in self.type_mapping:
            raise ValueError(f"不支持的题型文件: {filename}")
        
        type_info = self.type_mapping[filename]
        
        if type_info["standardizer"] is None:
            raise NotImplementedError(f"{type_info['name']}标准化器尚未实现")
        
        # 创建标准化器实例
        standardizer = type_info["standardizer"](
            api_key=self.api_key,
            api_base=self.api_base,
            model=self.model
        )
        
        # 应用自定义配置
        if custom_config:
            standardizer.config.update(custom_config)
        
        # 执行标准化
        print(f"🚀 开始标准化 {type_info['name']} (预期: {type_info['expected_count']} 题)")
        result = standardizer.standardize_file(type_file)
        
        # 添加预期数量信息
        result["expected_count"] = type_info["expected_count"]
        result["extraction_rate"] = (result["total_questions"] / type_info["expected_count"] * 100) if type_info["expected_count"] > 0 else 0
        
        return result
    
    def standardize_all_types(self, base_dir: str, custom_configs: Dict[str, Dict] = None) -> Dict:
        """
        标准化所有支持的题型
        
        Args:
            base_dir: 包含题型文件的目录
            custom_configs: 各题型的自定义配置 {filename: config}
            
        Returns:
            总体处理结果统计
        """
        if not os.path.exists(base_dir):
            raise FileNotFoundError(f"目录不存在: {base_dir}")
        
        results = {}
        total_expected = 0
        total_processed = 0
        total_chunks = 0
        
        print(f"🎯 开始批量标准化所有题型")
        print(f"📁 工作目录: {base_dir}")
        print(f"📋 支持的题型: {', '.join(self.get_available_types())}")
        
        for filename, type_info in self.type_mapping.items():
            if type_info["standardizer"] is None:
                print(f"⏭️ 跳过 {type_info['name']} (标准化器未实现)")
                continue
            
            type_file = os.path.join(base_dir, filename)
            
            if not os.path.exists(type_file):
                print(f"⚠️ 题型文件不存在: {type_file}")
                continue
            
            try:
                # 获取该题型的自定义配置
                custom_config = custom_configs.get(filename) if custom_configs else None
                
                # 标准化该题型
                result = self.standardize_single_type(type_file, custom_config)
                results[type_info["name"]] = result
                
                # 统计总计数据
                total_expected += result["expected_count"]
                total_processed += result["total_questions"] 
                total_chunks += result["total_chunks"]
                
                print(f"✅ {type_info['name']} 完成: {result['total_questions']}/{result['expected_count']} 题 ({result['extraction_rate']:.1f}%)")
                
            except Exception as e:
                print(f"❌ {type_info['name']} 处理失败: {e}")
                results[type_info["name"]] = {"error": str(e)}
        
        # 生成总体报告
        overall_stats = {
            "total_types_processed": len([r for r in results.values() if "error" not in r]),
            "total_expected": total_expected,
            "total_processed": total_processed,
            "overall_extraction_rate": (total_processed / total_expected * 100) if total_expected > 0 else 0,
            "total_chunks": total_chunks,
            "type_results": results
        }
        
        print(f"\n🎉 批量标准化完成！")
        print(f"📊 总体统计:")
        print(f"  • 处理题型: {overall_stats['total_types_processed']} 个")
        print(f"  • 题目提取: {total_processed}/{total_expected} ({overall_stats['overall_extraction_rate']:.1f}%)")
        print(f"  • 处理块数: {total_chunks} 个")
        
        return overall_stats
    
    def interactive_standardization(self):
        """交互式标准化处理"""
        print("=== 题目标准化交互式处理 ===\n")
        
        while True:
            print("请选择操作:")
            print("1. 标准化单个题型文件")
            print("2. 批量标准化所有题型")
            print("3. 查看支持的题型")
            print("4. 退出")
            
            choice = input("\n请输入选择 (1-4): ").strip()
            
            if choice == '1':
                file_path = input("请输入题型文件路径: ").strip()
                try:
                    result = self.standardize_single_type(file_path)
                    print(f"✅ 处理完成: {result}")
                except Exception as e:
                    print(f"❌ 处理失败: {e}")
            
            elif choice == '2':
                base_dir = input("请输入题型文件目录: ").strip()
                try:
                    result = self.standardize_all_types(base_dir)
                    print(f"✅ 批量处理完成!")
                except Exception as e:
                    print(f"❌ 批量处理失败: {e}")
            
            elif choice == '3':
                available_types = self.get_available_types()
                print(f"支持的题型: {', '.join(available_types)}")
                
                not_implemented = [info["name"] for info in self.type_mapping.values() if info["standardizer"] is None]
                if not_implemented:
                    print(f"待实现的题型: {', '.join(not_implemented)}")
            
            elif choice == '4':
                print("👋 再见!")
                break
            
            else:
                print("❌ 无效选择，请重新输入")
            
            print("\n" + "-"*50 + "\n")


def main():
    """主函数"""
    manager = QuestionStandardizationManager()
    
    # 可以直接调用批量处理，或者启动交互式模式
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        manager.interactive_standardization()
    else:
        # 默认处理当前目录下的题型文件
        base_dir = "question_processing_《数据安全管理员题库》（客观题）-20250713（提交版）/question_types"
        if os.path.exists(base_dir):
            # 设置一些自定义配置
            custom_configs = {
                "single_choice.md": {"lines_per_chunk": 80},  # 单选题用稍大的chunk
                "case_analysis.md": {"lines_per_chunk": 200}, # 案例分析题用更大的chunk
                "judgment.md": {"lines_per_chunk": 100}       # 判断题用中等的chunk
            }
            
            result = manager.standardize_all_types(base_dir, custom_configs)
        else:
            print(f"❌ 目录不存在: {base_dir}")
            print("请先运行题目拆分步骤，或使用 --interactive 选项进入交互式模式")


if __name__ == "__main__":
    main()