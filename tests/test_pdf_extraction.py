"""
PDF文本提取功能的测试
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from question_processor import QuestionProcessor


class TestPDFTextExtraction:
    """PDF文本提取测试类"""
    
    def setup_method(self):
        """测试前置设置"""
        self.processor = QuestionProcessor()
    
    def test_extract_text_from_existing_pdf(self):
        """测试从存在的PDF文件中提取文本"""
        # 准备测试数据
        expected_text = "这是测试文本\n包含多行内容\n\n"  # 加上额外的换行符因为实现中每页后面加了\n
        
        # Mock PyMuPDF和文件存在检查
        with patch('fitz.open') as mock_open, \
             patch('os.path.exists', return_value=True):
            
            mock_doc = MagicMock()
            mock_page = MagicMock()
            mock_page.get_text.return_value = "这是测试文本\n包含多行内容\n"
            mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
            mock_doc.close = Mock()
            mock_open.return_value = mock_doc
            
            # 执行测试
            result = self.processor.extract_text_from_pdf("test.pdf")
            
            # 验证结果
            assert result == expected_text
            mock_open.assert_called_once_with("test.pdf")
            mock_doc.close.assert_called_once()
    
    def test_extract_text_from_nonexistent_pdf(self):
        """测试从不存在的PDF文件中提取文本应该抛出异常"""
        with pytest.raises(FileNotFoundError):
            self.processor.extract_text_from_pdf("nonexistent.pdf")
    
    def test_extract_text_from_multiple_pages(self):
        """测试从多页PDF中提取文本"""
        # Mock多页PDF
        with patch('fitz.open') as mock_open, \
             patch('os.path.exists', return_value=True):
            
            mock_doc = MagicMock()
            
            # 创建多个页面
            page1 = MagicMock()
            page1.get_text.return_value = "第一页内容\n"
            page2 = MagicMock()
            page2.get_text.return_value = "第二页内容\n"
            
            mock_doc.__iter__ = Mock(return_value=iter([page1, page2]))
            mock_doc.close = Mock()
            mock_open.return_value = mock_doc
            
            # 执行测试
            result = self.processor.extract_text_from_pdf("multipage.pdf")
            
            # 验证结果包含所有页面内容
            expected = "第一页内容\n\n第二页内容\n\n"
            assert result == expected
    
    def test_extract_text_from_empty_pdf(self):
        """测试从空PDF中提取文本"""
        with patch('fitz.open') as mock_open, \
             patch('os.path.exists', return_value=True):
            
            mock_doc = MagicMock()
            mock_doc.__iter__ = Mock(return_value=iter([]))
            mock_doc.close = Mock()
            mock_open.return_value = mock_doc
            
            # 执行测试
            result = self.processor.extract_text_from_pdf("empty.pdf")
            
            # 验证结果为空字符串
            assert result == ""
    
    def test_extract_text_handles_pdf_processing_error(self):
        """测试PDF处理错误的处理"""
        with patch('fitz.open') as mock_open, \
             patch('os.path.exists', return_value=True):
            
            mock_open.side_effect = Exception("PDF处理错误")
            
            # 执行测试并验证异常
            with pytest.raises(Exception, match="PDF处理错误"):
                self.processor.extract_text_from_pdf("error.pdf")