"""
文本分割功能的测试
"""

import pytest
from question_processor import QuestionProcessor


class TestTextSplitting:
    """文本分割测试类"""
    
    def setup_method(self):
        """测试前置设置"""
        self.processor = QuestionProcessor()
    
    def test_split_simple_questions(self):
        """测试分割简单的题目文本"""
        text = """
        1. （单选）这是第一道题？
        A. 选项A
        B. 选项B
        参考答案: A
        
        2. （多选）这是第二道题？
        A. 选项A
        B. 选项B
        C. 选项C
        参考答案: AB
        """
        
        result = self.processor.split_text_into_questions(text)
        
        # 验证分割结果
        assert len(result) >= 2
        # 检查第一道题包含必要内容
        assert "这是第一道题" in result[0] or "这是第一道题" in result[1]
        assert "这是第二道题" in result[0] or "这是第二道题" in result[1]
    
    def test_split_questions_with_different_numbering(self):
        """测试不同编号格式的题目分割"""
        text = """
        1、（判断）这是判断题
        参考答案: 正确
        
        2．（填空）这是填空题_____。
        参考答案: 答案
        
        3. (难度：中3) 这是有难度标记的题目
        A. 选项A
        B. 选项B
        参考答案: A
        """
        
        result = self.processor.split_text_into_questions(text)
        
        # 验证分割结果包含所有题目
        assert len(result) >= 3
    
    def test_split_questions_with_chapters(self):
        """测试包含章节标题的文本分割"""
        text = """
        一、基础知识题
        
        1. （单选）第一道基础题？
        A. 选项A
        B. 选项B
        参考答案: A
        
        二、应用题
        
        2. （多选）第一道应用题？
        A. 选项A
        B. 选项B
        参考答案: AB
        """
        
        result = self.processor.split_text_into_questions(text)
        
        # 验证分割后包含题目而非只有章节标题
        valid_questions = [q for q in result if len(q) > 50]  # 过滤掉太短的分块
        assert len(valid_questions) >= 2
    
    def test_split_empty_text(self):
        """测试空文本分割"""
        result = self.processor.split_text_into_questions("")
        assert result == []
    
    def test_split_text_without_questions(self):
        """测试不包含题目的文本分割"""
        text = "这只是一段普通的文本，没有题目格式。"
        result = self.processor.split_text_into_questions(text)
        
        # 应该返回原文本或空列表，取决于实现
        assert isinstance(result, list)
    
    def test_split_questions_filters_short_chunks(self):
        """测试过滤掉过短的文本块"""
        text = """
        标题
        
        1. （单选）这是一道完整的题目，包含足够的内容用于测试过滤功能？
        A. 选项A
        B. 选项B
        C. 选项C
        D. 选项D
        参考答案: A
        
        短
        
        2. （多选）这是另一道完整的题目？
        A. 选项A
        B. 选项B
        参考答案: AB
        """
        
        result = self.processor.split_text_into_questions(text)
        
        # 验证过滤掉了过短的块（如"标题"和"短"）
        for question in result:
            assert len(question) > 20  # 应该过滤掉长度小于20的块
    
    def test_split_questions_preserves_complete_content(self):
        """测试分割保持题目内容完整"""
        text = """
        1. （单选）这是一道包含多行内容的题目，
        题干可能跨越多行，
        需要保持完整？
        A. 这是选项A，也可能很长
        B. 这是选项B
        C. 选项C
        参考答案: A
        解析: 这是详细解析
        
        2. （简答）简答题通常没有选项
        参考答案: 这是简答题的答案，可能包含多个要点：
        1) 要点一
        2) 要点二
        """
        
        result = self.processor.split_text_into_questions(text)
        
        # 验证每个题目块包含完整内容
        assert len(result) >= 2
        # 第一道题应该包含题干、选项和答案
        first_question = next((q for q in result if "这是一道包含多行内容的题目" in q), None)
        assert first_question is not None
        assert "选项A" in first_question
        assert "参考答案" in first_question