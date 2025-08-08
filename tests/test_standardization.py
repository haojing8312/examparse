"""
测试题目标准化功能
简化版本，用于验证切分和格式逻辑
"""

import os
from typing import List, Tuple

def chunk_file(file_path: str, lines_per_chunk: int = 100) -> List[Tuple[List[str], List[str]]]:
    """
    将文件按行数切分，返回 [(chunk1_lines, chunk2_lines), ...] 
    每个元组包含当前块和下一块的内容
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    chunks = []
    for i in range(0, len(lines), lines_per_chunk):
        chunk1 = lines[i:i + lines_per_chunk]
        chunk2 = lines[i + lines_per_chunk:i + 2 * lines_per_chunk] if i + lines_per_chunk < len(lines) else []
        chunks.append((chunk1, chunk2))
    
    return chunks

def save_chunks(chunks: List[Tuple[List[str], List[str]]], output_dir: str, base_name: str):
    """保存切分后的文件块"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for i, (chunk1, chunk2) in enumerate(chunks):
        # 保存第一个块
        chunk1_file = os.path.join(output_dir, f"{base_name}_chunk_{i+1:03d}_part1.md")
        with open(chunk1_file, 'w', encoding='utf-8') as f:
            f.write(f"# 文件块 {i+1} - 第一部分\n\n")
            f.write(f"行数范围: {i*100 + 1} - {i*100 + len(chunk1)}\n\n")
            f.write("```\n")
            f.writelines(chunk1)
            f.write("```\n")
        
        # 保存第二个块（参考块）
        if chunk2:
            chunk2_file = os.path.join(output_dir, f"{base_name}_chunk_{i+1:03d}_part2.md")
            with open(chunk2_file, 'w', encoding='utf-8') as f:
                f.write(f"# 文件块 {i+1} - 第二部分（参考）\n\n")
                f.write(f"行数范围: {i*100 + len(chunk1) + 1} - {i*100 + len(chunk1) + len(chunk2)}\n\n")
                f.write("```\n")
                f.writelines(chunk2)
                f.write("```\n")
        
        print(f"✅ 保存文件块 {i+1}: {chunk1_file}")
        if chunk2:
            print(f"✅ 保存参考块 {i+1}: {chunk2_file}")

def main():
    """主测试函数"""
    print("=== 题目标准化测试 ===\n")
    
    # 测试文件路径
    test_file = "question_processing_《数据安全管理员题库》（客观题）-20250713（提交版）/question_types/case_analysis.md"
    
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        return
    
    print(f"📄 测试文件: {test_file}")
    
    # 获取文件大小
    file_size = os.path.getsize(test_file)
    print(f"📊 文件大小: {file_size:,} 字节")
    
    # 切分文件
    print("\n🔪 开始切分文件...")
    chunks = chunk_file(test_file, lines_per_chunk=100)
    print(f"📦 切分完成，共 {len(chunks)} 个文件块")
    
    # 保存切分结果
    output_dir = "standardization_test_output"
    base_name = "case_analysis"
    save_chunks(chunks, output_dir, base_name)
    
    # 生成统计报告
    stats_file = os.path.join(output_dir, "chunking_stats.md")
    with open(stats_file, 'w', encoding='utf-8') as f:
        f.write("# 文件切分统计报告\n\n")
        f.write(f"## 基本信息\n")
        f.write(f"- 原始文件: {test_file}\n")
        f.write(f"- 文件大小: {file_size:,} 字节\n")
        f.write(f"- 切分块数: {len(chunks)} 个\n")
        f.write(f"- 每块行数: 100 行\n")
        f.write(f"- 输出目录: {output_dir}\n\n")
        
        f.write("## 文件块详情\n")
        for i, (chunk1, chunk2) in enumerate(chunks):
            f.write(f"### 文件块 {i+1}\n")
            f.write(f"- 第一部分: {len(chunk1)} 行\n")
            f.write(f"- 第二部分: {len(chunk2)} 行（参考）\n")
            f.write(f"- 总行数: {len(chunk1) + len(chunk2)} 行\n\n")
    
    print(f"\n📊 统计报告已保存到: {stats_file}")
    print(f"📁 切分结果保存在: {output_dir}")
    
    # 显示前几个文件块的内容预览
    print("\n🔍 文件块内容预览:")
    for i, (chunk1, chunk2) in enumerate(chunks[:3]):  # 只显示前3个
        print(f"\n--- 文件块 {i+1} ---")
        print(f"第一部分前5行:")
        for j, line in enumerate(chunk1[:5]):
            print(f"  {j+1}: {line.strip()}")
        
        if chunk2:
            print(f"第二部分前3行:")
            for j, line in enumerate(chunk2[:3]):
                print(f"  {j+1}: {line.strip()}")

if __name__ == "__main__":
    main() 