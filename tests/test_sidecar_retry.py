import json
from pathlib import Path
from unittest.mock import patch

import pytest

from sidecar import runner


def test_retry_success_on_second_try_for_split(tmp_path: Path, monkeypatch):
    pdf = tmp_path / "r.pdf"
    pdf.write_text("%PDF-1.4\n")

    calls = {"split": 0, "split-questions": 0}

    def flaky_process(self, pdf_path, output_path, step):
        calls[step] += 1
        # 首次 split 抛错，第二次成功；split-questions 一次过
        if step == "split" and calls[step] == 1:
            raise RuntimeError("transient failure")
        # 成功时创建必要目录，避免后续逻辑依赖
        base_name = Path(pdf_path).stem
        workdir = tmp_path / f"question_processing_{base_name}"
        workdir.mkdir(exist_ok=True)
        (workdir / "question_types").mkdir(exist_ok=True)
        # 当 split-questions 调用时，生成 summary
        if step == "split-questions":
            (workdir / "split_summary.md").write_text("ok")

    events = []

    def capture(e):
        events.append(json.loads(e.to_json()))

    with patch("question_processor.QuestionProcessor.process_questions", new=flaky_process), \
         patch("time.sleep", lambda *_: None):
        workdir = runner.run_split_and_split_questions(
            pdf_path=pdf,
            work_dir_parent=tmp_path,
            emit=capture,
            file_id="fid-r1",
        )

    # 确认 split 经历了失败与重试，最终 completed
    assert calls["split"] == 2
    assert any(e["type"] == "error" and e["stage"] == "split" for e in events)
    assert any(e["type"] == "warning" and e["stage"] == "split" for e in events)
    assert any(e["type"] == "completed" for e in events)
    assert Path(workdir).exists()


def test_retry_exhausts_and_raises(tmp_path: Path):
    pdf = tmp_path / "fail.pdf"
    pdf.write_text("%PDF-1.4\n")

    def always_fail(self, pdf_path, output_path, step):
        raise RuntimeError("hard failure")

    events = []

    def capture(e):
        events.append(json.loads(e.to_json()))

    with patch("question_processor.QuestionProcessor.process_questions", new=always_fail), \
         patch("time.sleep", lambda *_: None):
        with pytest.raises(RuntimeError):
            runner.run_split_and_split_questions(
                pdf_path=pdf,
                work_dir_parent=tmp_path,
                emit=capture,
                file_id="fid-r2",
            )

    # 应有多条 error 与 warning，且无 completed
    assert any(e["type"] == "error" and e["stage"] in {"split", "split-questions"} for e in events)
    assert any(e["type"] == "warning" for e in events)
    assert not any(e["type"] == "completed" for e in events)


