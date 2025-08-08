from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Callable

from .events import SidecarEvent


@contextmanager
def _temp_chdir(target: Path):
    original = Path.cwd()
    try:
        os.chdir(target)
        yield
    finally:
        os.chdir(original)


def run_split_and_split_questions(
    pdf_path: Path,
    work_dir_parent: Path,
    emit: Callable[[SidecarEvent], None],
    file_id: str,
) -> Path:
    """
    运行真实核心：先执行 split，再执行 split-questions。

    返回工作目录路径（question_processing_{base}）。
    """
    # 延迟导入避免 UI 端 import 时拉入重依赖
    from question_processor import QuestionProcessor

    work_dir_parent.mkdir(parents=True, exist_ok=True)

    with _temp_chdir(work_dir_parent):
        base_name = pdf_path.stem
        work_dir = Path(f"question_processing_{base_name}")

        emit(SidecarEvent(type="stage", stage="split", fileId=file_id, message="start split"))
        # 进度预热
        emit(SidecarEvent(type="progress", stage="split", fileId=file_id, percent=0.05))

        processor = QuestionProcessor()
        # 步骤1：split（提取文本并按题型拆分）
        processor.process_questions(str(pdf_path), output_path=str(work_dir / "dummy.xlsx"), step="split")
        emit(SidecarEvent(type="progress", stage="split", fileId=file_id, percent=0.5))
        emit(SidecarEvent(type="progress", stage="split", fileId=file_id, percent=1.0))

        # 步骤2：split-questions（将题型文件拆为题目）
        emit(SidecarEvent(type="stage", stage="split-questions", fileId=file_id, message="start split-questions"))
        emit(SidecarEvent(type="progress", stage="split-questions", fileId=file_id, percent=0.1))
        processor.process_questions(str(pdf_path), output_path=str(work_dir / "dummy.xlsx"), step="split-questions")
        emit(SidecarEvent(type="progress", stage="split-questions", fileId=file_id, percent=1.0))

        # 完成事件，返回工作目录
        emit(SidecarEvent(type="completed", stage="done", fileId=file_id, message=str(work_dir.resolve())))

        return work_dir.resolve()


