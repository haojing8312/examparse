import json
import subprocess
import sys
from pathlib import Path


def run_sidecar_mock(tmp_path: Path):
    """运行 sidecar 的 mock 模式，返回其逐行 JSON 事件。"""
    # 创建一个临时输入文件以通过 sidecar 的输入校验
    input_file = tmp_path / "in.pdf"
    input_file.write_bytes(b"%PDF-1.4\n% mock content")
    proc = subprocess.run(
        [sys.executable, "-m", "sidecar.main", "--mock", "--input", str(input_file), "--output", str(tmp_path / "out.xlsx")],
        check=True,
        capture_output=True,
        text=True,
    )
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    return [json.loads(ln) for ln in lines]


def test_sidecar_mock_events_schema(tmp_path):
    events = run_sidecar_mock(tmp_path)
    # 期望包含至少一个 progress 和一个 completed 事件
    assert any(e.get("type") == "progress" for e in events)
    assert any(e.get("type") == "completed" for e in events)
    # 校验字段存在
    for e in events:
        assert "ts" in e
        assert "stage" in e
        assert "fileId" in e


def test_percent_is_in_range(tmp_path):
    # 运行 mock 并确保 percent 在 [0,1]
    events = run_sidecar_mock(tmp_path)
    percents = [e["percent"] for e in events if e.get("type") == "progress"]
    assert percents, "应当产生进度事件"
    assert all(0.0 <= p <= 1.0 for p in percents if p is not None)


