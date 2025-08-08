#!/usr/bin/env python3
"""
测试OpenAI版本的案例分析标准化器
"""

import tempfile
import os
from case_analysis_standardizer import CaseAnalysisStandardizer
from config import Config

def test_openai_case_analysis():
    """测试OpenAI案例分析处理"""
    print("=== 测试OpenAI案例分析标准化器 ===\n")
    
    # 检查配置
    try:
        config = Config.get_openai_config()
        if not config['api_key']:
            print("❌ 错误：未配置OPENAI_API_KEY")
            print("请设置环境变量：export OPENAI_API_KEY='您的API密钥'")
            return False
        
        print(f"✅ OpenAI配置检查通过")
        print(f"  API Base: {config['api_base']}")
        print(f"  Model: {config['model']}")
        
    except Exception as e:
        print(f"❌ 配置错误: {e}")
        return False
    
    # 创建测试用例
    test_content = """# 案例分析题 (2题)

## 提取时间
2025-08-07 12:00:00

## 预期题数
2

## 原始文本

```
七、案例分析题：（2 题） 
1. 案例分析：员工私自使用公司数据牟利 
请分析张某的行为违反了哪些职业道德原则，并阐述公司应如何加强职业道德建设以防范此类事件再次发生。 
参考答案要点: 
• 违反职业道德原则：诚实守信、忠于职守、保守秘密、爱岗敬业、遵纪守法 
• 公司防范措施：加强职业道德和法律法规培训、健全数据安全管理制度、强化技术防护措施、完善奖惩机制、建立举报和监督机制 

2. 案例分析：数据安全团队内部协作问题 
某公司数据安全团队接到一项紧急任务，需要在48小时内完成系统安全评估。然而，团队成员A认为时间太紧，草率完成了部分工作；成员B过分追求细节，影响了整体进度；成员C缺乏主动性，只做分配的基本任务。
请分析该团队在此次任务中存在哪些职业守则方面的不足，并提出改进建议。 
参考答案要点: 
• 不足：缺乏团结协作、认真负责不足、忠于职守体现不足、缺乏精益求精 
• 改进建议：强化团队协作意识、倡导认真负责精神、加强领导引导、营造积极团队文化
```
"""
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(test_content)
        temp_file = f.name
    
    try:
        print(f"\n📝 创建测试文件: {temp_file}")
        
        # 创建标准化器
        standardizer = CaseAnalysisStandardizer()
        
        # 设置较小的chunk大小以便测试
        standardizer.config["lines_per_chunk"] = 30
        standardizer.config["max_retries"] = 3
        
        print("🚀 开始标准化处理...")
        
        # 执行标准化
        result = standardizer.standardize_file(temp_file)
        
        print(f"\n✅ 处理完成！")
        print(f"📊 结果统计: {result}")
        
        if result['total_questions'] > 0:
            print(f"\n🎉 成功！OpenAI标准化器正常工作，处理了 {result['total_questions']} 道题目")
            return True
        else:
            print(f"\n⚠️ 警告：未处理任何题目，可能存在问题")
            return False
        
    except Exception as e:
        print(f"❌ 处理出错: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 清理临时文件
        if os.path.exists(temp_file):
            os.unlink(temp_file)

def main():
    """主函数"""
    success = test_openai_case_analysis()
    
    if success:
        print("\n🎉 OpenAI案例分析标准化器测试成功！")
        print("\n💡 下一步:")
        print("1. 可以处理完整的案例分析文件")
        print("2. 可以继续处理其他文件类型")
        return 0
    else:
        print("\n❌ OpenAI案例分析标准化器测试失败")
        return 1

if __name__ == "__main__":
    exit(main())