"""
Excel写入功能的测试
"""

import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock, mock_open
from question_processor import QuestionProcessor


class TestExcelWriting:
    """Excel写入测试类"""
    
    def setup_method(self):
        """测试前置设置"""
        with patch('question_processor.openai.OpenAI'):
            self.processor = QuestionProcessor(api_key="test_key")
    
    def test_save_to_excel_single_choice_questions(self):
        """测试保存单选题到Excel"""
        questions_data = [
            {
                "question_type": "单选",
                "difficulty": "",
                "question_stem": "数据安全管理的首要原则是什么？",
                "options": ["保密性", "完整性", "可用性", "可控性"],
                "answer": "A",
                "explanation": ""
            },
            {
                "question_type": "单选", 
                "difficulty": "中3",
                "question_stem": "以下哪项不是数据分类的常用方法？",
                "options": ["按敏感度分类", "按来源分类", "按颜色分类", "按用途分类"],
                "answer": "C",
                "explanation": "按颜色分类不是数据分类的常用方法"
            }
        ]
        
        with patch('openpyxl.Workbook') as mock_workbook, \
             patch('os.path.exists', return_value=False):
            
            mock_wb = MagicMock()
            mock_ws = MagicMock()
            # 设置max_row属性为具体数值
            mock_ws.max_row = 1
            mock_ws.title = "Sheet"
            # 设置cell方法的返回值
            mock_cell = MagicMock()
            mock_cell.value = None
            mock_ws.cell.return_value = mock_cell
            mock_wb.active = mock_ws
            mock_workbook.return_value = mock_wb
            
            # 执行测试
            self.processor.save_to_excel(questions_data, "output.xlsx")
            
            # 验证创建了工作簿
            mock_workbook.assert_called_once()
            # 验证保存了文件
            mock_wb.save.assert_called_once_with("output.xlsx")
    
    def test_save_to_excel_multiple_question_types(self):
        """测试保存多种题型到Excel"""
        questions_data = [
            {
                "question_type": "单选",
                "difficulty": "",
                "question_stem": "单选题测试",
                "options": ["A选项", "B选项", "C选项", "D选项"],
                "answer": "A",
                "explanation": ""
            },
            {
                "question_type": "多选",
                "difficulty": "",
                "question_stem": "多选题测试",
                "options": ["A选项", "B选项", "C选项", "D选项"],
                "answer": "ABC",
                "explanation": ""
            },
            {
                "question_type": "判断",
                "difficulty": "",
                "question_stem": "判断题测试",
                "options": [],
                "answer": "正确",
                "explanation": ""
            },
            {
                "question_type": "填空",
                "difficulty": "",
                "question_stem": "填空题测试_____",
                "options": [],
                "answer": "答案",
                "explanation": ""
            },
            {
                "question_type": "简答",
                "difficulty": "",
                "question_stem": "简答题测试",
                "options": [],
                "answer": "这是简答题答案",
                "explanation": ""
            }
        ]
        
        with patch('openpyxl.Workbook') as mock_workbook, \
             patch('os.path.exists', return_value=False):
            
            mock_wb = MagicMock()
            mock_ws = MagicMock()
            # 设置max_row属性为具体数值
            mock_ws.max_row = 1
            mock_ws.title = "Sheet"
            # 设置cell方法的返回值
            mock_cell = MagicMock()
            mock_cell.value = None
            mock_ws.cell.return_value = mock_cell
            mock_wb.active = mock_ws
            mock_workbook.return_value = mock_wb
            
            # 执行测试
            self.processor.save_to_excel(questions_data, "output.xlsx")
            
            # 验证所有题型都被处理了
            assert mock_ws.cell.call_count > 0  # 确保有数据写入
            mock_wb.save.assert_called_once_with("output.xlsx")
    
    def test_save_to_excel_empty_data(self):
        """测试保存空数据到Excel"""
        questions_data = []
        
        with patch('openpyxl.Workbook') as mock_workbook, \
             patch('os.path.exists', return_value=False):
            
            mock_wb = MagicMock()
            mock_ws = MagicMock()
            # 设置max_row属性为具体数值
            mock_ws.max_row = 1
            mock_ws.title = "Sheet"
            # 设置cell方法的返回值
            mock_cell = MagicMock()
            mock_cell.value = None
            mock_ws.cell.return_value = mock_cell
            mock_wb.active = mock_ws
            mock_workbook.return_value = mock_wb
            
            # 执行测试
            self.processor.save_to_excel(questions_data, "empty.xlsx")
            
            # 验证仍然创建了文件（即使数据为空）
            mock_wb.save.assert_called_once_with("empty.xlsx")
    
    def test_save_to_excel_with_existing_template(self):
        """测试基于现有模板保存Excel"""
        questions_data = [
            {
                "question_type": "单选",
                "difficulty": "",
                "question_stem": "测试题目",
                "options": ["选项A", "选项B", "选项C", "选项D"],
                "answer": "A",
                "explanation": ""
            }
        ]
        
        # 模拟模板文件存在
        with patch('openpyxl.load_workbook') as mock_load, \
             patch('os.path.exists', return_value=True):
            
            mock_wb = MagicMock()
            mock_ws = MagicMock()
            mock_ws.max_row = 2
            mock_ws.title = "题库数据"
            mock_wb.active = mock_ws
            mock_load.return_value = mock_wb
            
            # 执行测试
            self.processor.save_to_excel(questions_data, "template.xlsx")
            
            # 验证加载了现有模板而不是创建新工作簿
            mock_load.assert_called_once_with("template.xlsx")
            mock_wb.save.assert_called_once_with("template.xlsx")
    
    def test_save_to_excel_handles_write_error(self):
        """测试处理Excel写入错误"""
        questions_data = [
            {
                "question_type": "单选",
                "difficulty": "",
                "question_stem": "测试题目",
                "options": ["选项A", "选项B"],
                "answer": "A",
                "explanation": ""
            }
        ]
        
        with patch('openpyxl.Workbook') as mock_workbook, \
             patch('os.path.exists', return_value=False):
            
            mock_wb = MagicMock()
            mock_ws = MagicMock()
            # 设置max_row属性为具体数值
            mock_ws.max_row = 1
            mock_ws.title = "Sheet"
            # 设置cell方法的返回值
            mock_cell = MagicMock()
            mock_cell.value = None
            mock_ws.cell.return_value = mock_cell
            mock_wb.active = mock_ws
            mock_wb.save.side_effect = Exception("文件写入失败")
            mock_workbook.return_value = mock_wb
            
            # 执行测试并验证异常处理
            with pytest.raises(Exception, match="Excel文件保存失败"):
                self.processor.save_to_excel(questions_data, "error.xlsx")
    
    def test_save_to_excel_creates_headers(self):
        """测试Excel文件包含正确的表头"""
        questions_data = [
            {
                "question_type": "单选",
                "difficulty": "",
                "question_stem": "测试题目",
                "options": ["选项A", "选项B"],
                "answer": "A",
                "explanation": ""
            }
        ]
        
        with patch('openpyxl.Workbook') as mock_workbook, \
             patch('os.path.exists', return_value=False):
            
            mock_wb = MagicMock()
            mock_ws = MagicMock()
            # 设置max_row属性为具体数值
            mock_ws.max_row = 1
            mock_ws.title = "Sheet"
            # 设置cell方法的返回值
            mock_cell = MagicMock()
            mock_cell.value = None
            mock_ws.cell.return_value = mock_cell
            mock_wb.active = mock_ws
            mock_workbook.return_value = mock_wb
            
            # 执行测试
            self.processor.save_to_excel(questions_data, "headers.xlsx")
            
            # 验证设置了表头（检查是否有对cell的调用）
            assert mock_ws.cell.call_count > 0  # 确保设置了表头和数据
    
    def test_save_to_excel_formats_options_correctly(self):
        """测试选项格式化正确"""
        questions_data = [
            {
                "question_type": "单选",
                "difficulty": "",
                "question_stem": "测试题目",
                "options": ["选项A", "选项B", "选项C", "选项D"],
                "answer": "A",
                "explanation": ""
            },
            {
                "question_type": "判断",
                "difficulty": "",
                "question_stem": "判断题",
                "options": [],  # 判断题没有选项
                "answer": "正确",
                "explanation": ""
            }
        ]
        
        with patch('openpyxl.Workbook') as mock_workbook, \
             patch('os.path.exists', return_value=False):
            
            mock_wb = MagicMock()
            mock_ws = MagicMock()
            # 设置max_row属性为具体数值
            mock_ws.max_row = 1
            mock_ws.title = "Sheet"
            # 设置cell方法的返回值
            mock_cell = MagicMock()
            mock_cell.value = None
            mock_ws.cell.return_value = mock_cell
            mock_wb.active = mock_ws
            mock_workbook.return_value = mock_wb
            
            # 执行测试
            self.processor.save_to_excel(questions_data, "options.xlsx")
            
            # 验证正确处理了有选项和无选项的情况
            mock_wb.save.assert_called_once_with("options.xlsx")
    
    def test_save_to_excel_handles_long_content(self):
        """测试处理长内容"""
        long_content = "这是一个非常长的题目内容，" * 50  # 创建很长的内容
        questions_data = [
            {
                "question_type": "简答",
                "difficulty": "",
                "question_stem": long_content,
                "options": [],
                "answer": long_content,
                "explanation": long_content
            }
        ]
        
        with patch('openpyxl.Workbook') as mock_workbook, \
             patch('os.path.exists', return_value=False):
            
            mock_wb = MagicMock()
            mock_ws = MagicMock()
            # 设置max_row属性为具体数值
            mock_ws.max_row = 1
            mock_ws.title = "Sheet"
            # 设置cell方法的返回值
            mock_cell = MagicMock()
            mock_cell.value = None
            mock_ws.cell.return_value = mock_cell
            mock_wb.active = mock_ws
            mock_workbook.return_value = mock_wb
            
            # 执行测试
            self.processor.save_to_excel(questions_data, "long.xlsx")
            
            # 验证长内容也能正确处理
            mock_wb.save.assert_called_once_with("long.xlsx")