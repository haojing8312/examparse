import json
from pathlib import Path
from unittest.mock import patch

from sidecar import runner


def test_runner_skips_split_when_question_types_exists(tmp_path: Path):
    pdf = tmp_path / "a.pdf"
    pdf.write_text("%PDF-1.4\n")

    # 预创建缓存：question_types 已存在，视为 split 完成
    workdir = tmp_path / "question_processing_a"
    (workdir / "question_types").mkdir(parents=True, exist_ok=True)

    calls = []

    def fake_process_questions(self, pdf_path, output_path, step):
        calls.append(step)

    events = []

    def capture(e):
        events.append(json.loads(e.to_json()))

    with patch("question_processor.QuestionProcessor.process_questions", new=fake_process_questions):
        runner.run_split_and_split_questions(
            pdf_path=pdf,
            work_dir_parent=tmp_path,
            emit=capture,
            file_id="fid-1",
        )

    # 仅执行 split-questions，不再执行 split
    assert "split" not in calls
    assert "split-questions" in calls
    # 仍应有 completed 事件
    assert any(e.get("type") == "completed" for e in events)


def test_runner_skips_all_when_summary_exists(tmp_path: Path):
    pdf = tmp_path / "b.pdf"
    pdf.write_text("%PDF-1.4\n")

    # 预创建缓存：split_summary.md 存在，视为 split-questions 也完成
    workdir = tmp_path / "question_processing_b"
    workdir.mkdir(parents=True, exist_ok=True)
    (workdir / "split_summary.md").write_text("summary")

    calls = []

    def fake_process_questions(self, pdf_path, output_path, step):
        calls.append(step)

    events = []

    def capture(e):
        events.append(json.loads(e.to_json()))

    with patch("question_processor.QuestionProcessor.process_questions", new=fake_process_questions):
        runner.run_split_and_split_questions(
            pdf_path=pdf,
            work_dir_parent=tmp_path,
            emit=capture,
            file_id="fid-2",
        )

    # 两步均跳过
    assert calls == []
    # 仍应有 completed 事件
    assert any(e.get("type") == "completed" for e in events)


