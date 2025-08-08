import json
import subprocess
import sys
from pathlib import Path


def run_sidecar(args: list[str]):
    proc = subprocess.run(
        [sys.executable, "-m", "sidecar.main", *args],
        check=False,
        capture_output=True,
        text=True,
    )
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    return proc.returncode, [json.loads(ln) for ln in lines]


def test_invalid_input_path_emits_error(tmp_path):
    code, events = run_sidecar(["--mock", "--input", str(tmp_path / "not-exists.pdf"), "--output", str(tmp_path / "out.xlsx")])
    # mock 模式也做输入校验，若文件不存在，应先发 error 事件并退出非零
    assert code != 0
    assert events, "应当产生至少一个事件"
    assert events[0]["type"] == "error"
    assert events[0]["stage"] == "validate"


def test_multiple_inputs_emit_distinct_file_ids(tmp_path):
    # 创建两个空文件模拟输入
    f1 = tmp_path / "a.pdf"
    f2 = tmp_path / "b.pdf"
    f1.write_text("a")
    f2.write_text("b")
    code, events = run_sidecar([
        "--mock",
        "--inputs", str(f1), str(f2),
        "--output-dir", str(tmp_path),
    ])
    assert code == 0
    file_ids = {e["fileId"] for e in events if e.get("type") in {"stage", "progress", "completed"}}
    assert len(file_ids) == 2


