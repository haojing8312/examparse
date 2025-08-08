#!/usr/bin/env python3
"""
测试Gemini案例分析处理 - 小样本测试
"""

from config import Config
from case_analysis_standardizer import CaseAnalysisStandardizer
import tempfile
import os

def test_small_case_analysis():
    """测试小样本案例分析处理"""
    print("=== 测试Gemini案例分析处理（小样本）===\n")
    
    # 获取配置
    config = Config.get_gemini_config()
    if not config['api_key']:
        print("❌ 错误：未配置GEMINI_API_KEY")
        return False
    
    # 创建测试文件
    test_content = """# 案例分析题 (2题)

## 提取时间
2025-08-07 10:00:00

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
        print(f"📝 创建测试文件: {temp_file}")
        
        # 创建标准化器
        standardizer = CaseAnalysisStandardizer(
            api_key=config['api_key'],
            api_base=config['api_base'],
            model=config['model']
        )
        
        # 设置较小的chunk大小以便测试
        standardizer.config["lines_per_chunk"] = 20
        standardizer.config["max_retries"] = 2
        
        print("🚀 开始标准化处理...")
        
        # 执行标准化
        result = standardizer.standardize_file(temp_file)
        
        print(f"✅ 处理完成！")
        print(f"📊 结果统计: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ 处理出错: {e}")
        return False
        
    finally:
        # 清理临时文件
        if os.path.exists(temp_file):
            os.unlink(temp_file)

def main():
    """主函数"""
    success = test_small_case_analysis()
    
    if success:
        print("\n🎉 小样本测试成功！Gemini可以处理案例分析题")
        return 0
    else:
        print("\n❌ 小样本测试失败")
        return 1

if __name__ == "__main__":
    exit(main())