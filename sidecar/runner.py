from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Callable
import time

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

        processor = QuestionProcessor()

        # 全量缓存：若 split_summary.md 已存在，直接跳过两步
        summary = work_dir / "split_summary.md"
        if summary.exists():
            emit(SidecarEvent(type="stage", stage="split", fileId=file_id, message="skip split (cache)"))
            emit(SidecarEvent(type="progress", stage="split", fileId=file_id, percent=1.0))
            emit(SidecarEvent(type="stage", stage="split-questions", fileId=file_id, message="skip split-questions (cache)"))
            emit(SidecarEvent(type="progress", stage="split-questions", fileId=file_id, percent=1.0))
        else:
            # 缓存判断：若 question_types 已存在，则跳过 split
            question_types_dir = work_dir / "question_types"
            if question_types_dir.exists():
                emit(SidecarEvent(type="stage", stage="split", fileId=file_id, message="skip split (cache)"))
                emit(SidecarEvent(type="progress", stage="split", fileId=file_id, percent=1.0))
            else:
                emit(SidecarEvent(type="stage", stage="split", fileId=file_id, message="start split"))
                emit(SidecarEvent(type="progress", stage="split", fileId=file_id, percent=0.05))
                _run_with_retry(lambda: processor.process_questions(str(pdf_path), output_path=str(work_dir / "dummy.xlsx"), step="split"), emit, file_id, "split")
                emit(SidecarEvent(type="progress", stage="split", fileId=file_id, percent=0.5))
                emit(SidecarEvent(type="progress", stage="split", fileId=file_id, percent=1.0))

            # 步骤2：split-questions（将题型文件拆为题目）
            emit(SidecarEvent(type="stage", stage="split-questions", fileId=file_id, message="start split-questions"))
            emit(SidecarEvent(type="progress", stage="split-questions", fileId=file_id, percent=0.1))
            _run_with_retry(lambda: processor.process_questions(str(pdf_path), output_path=str(work_dir / "dummy.xlsx"), step="split-questions"), emit, file_id, "split-questions")
            emit(SidecarEvent(type="progress", stage="split-questions", fileId=file_id, percent=1.0))

        # 完成事件，返回工作目录
        emit(SidecarEvent(type="completed", stage="done", fileId=file_id, message=str(work_dir.resolve())))

        return work_dir.resolve()


def _run_with_retry(fn: Callable[[], None], emit: Callable[[SidecarEvent], None], file_id: str, stage: str, max_attempts: int = 2, backoff_base: float = 0.1):
    attempt = 0
    last_exc: Exception | None = None
    while attempt < max_attempts:
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            emit(SidecarEvent(type="error", stage=stage, fileId=file_id, message=str(exc)))
            attempt += 1
            if attempt < max_attempts:
                delay = backoff_base * (2 ** (attempt - 1))
                emit(SidecarEvent(type="warning", stage=stage, fileId=file_id, message=f"retrying in {delay:.2f}s (attempt {attempt+1}/{max_attempts})"))
                time.sleep(delay)
            else:
                break
    # 重试失败，抛出最后异常
    assert last_exc is not None
    raise last_exc


