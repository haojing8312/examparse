import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


def test_runner_emits_stages_and_creates_workdir(tmp_path: Path, monkeypatch):
    # 构造一个假的 PDF 文件路径
    pdf = tmp_path / "fake.pdf"
    pdf.write_text("%PDF-1.4\n")

    # 替换 QuestionProcessor.process_questions，避免真实 PDF 解析依赖
    from sidecar import runner

    calls = []

    def fake_process_questions(self, pdf_path, output_path, step):
        # 记录调用参数，模拟成功
        calls.append((Path(pdf_path).name, step))
        # 按 step 创建最小目录结构，满足后续断言
        base_name = Path(pdf_path).stem
        work_dir = tmp_path / f"question_processing_{base_name}"
        work_dir.mkdir(exist_ok=True)
        (work_dir / "question_types").mkdir(exist_ok=True)

    with patch("question_processor.QuestionProcessor.process_questions", new=fake_process_questions):
        events = []

        def capture(e):
            events.append(json.loads(e.to_json()))

        workdir = runner.run_split_and_split_questions(
            pdf_path=pdf,
            work_dir_parent=tmp_path,
            emit=capture,
            file_id="fid-1",
        )

    # 断言阶段与进度事件
    types = [e["type"] for e in events]
    assert types.count("stage") >= 2
    assert types.count("progress") >= 3
    assert types.count("completed") == 1
    assert Path(workdir).exists()
    # 断言 QuestionProcessor 被按顺序调用
    assert ("fake.pdf", "split") in calls
    assert ("fake.pdf", "split-questions") in calls


