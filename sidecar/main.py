from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .events import SidecarEvent
from .config import RunConfig


def emit(event: SidecarEvent):
    print(event.to_json())
    sys.stdout.flush()


def mock_pipeline(input_path: Path, output_path: Path, file_id: str):
    stages = [
        ("split", 0.15),
        ("split-questions", 0.45),
        ("process", 0.8),
        ("export", 1.0),
    ]
    for stage, final_p in stages:
        emit(SidecarEvent(type="stage", stage=stage, fileId=file_id, message=f"start {stage}"))
        for p in range(0, 101, 20):
            time.sleep(0.02)
            emit(SidecarEvent(type="progress", stage=stage, fileId=file_id, percent=min(final_p, p / 100.0)))
    # 产物声明
    emit(SidecarEvent(type="completed", stage="done", fileId=file_id, message=str(output_path)))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ExamParse sidecar")
    parser.add_argument("--input", type=str, required=False, help="单个输入文件")
    parser.add_argument("--inputs", nargs="*", help="多个输入文件")
    parser.add_argument("--output", type=str, required=False, help="单个输出文件")
    parser.add_argument("--output-dir", type=str, required=False, help="输出目录（多输入时使用）")
    parser.add_argument("--mock", action="store_true", help="运行模拟流水线")
    args = parser.parse_args(argv)

    cfg = RunConfig.from_args(args.inputs, args.input, args.output, args.output_dir, args.mock)

    # 校验输入
    if not cfg.inputs:
        emit(SidecarEvent(type="error", stage="validate", fileId="startup", message="no input provided"))
        return 2
    for p in cfg.inputs:
        if not p.exists():
            emit(SidecarEvent(type="error", stage="validate", fileId=p.name, message=f"input not found: {p}"))
            return 2

    if args.mock:
        if len(cfg.inputs) == 1:
            file_id = uuid.uuid4().hex
            input_path = cfg.inputs[0]
            output_path = cfg.output or Path("/tmp/result.xlsx")
            mock_pipeline(input_path, output_path, file_id)
        else:
            out_dir = cfg.output_dir or Path("/tmp")
            for ip in cfg.inputs:
                file_id = uuid.uuid4().hex
                output_path = out_dir / f"{ip.stem}.xlsx"
                mock_pipeline(ip, output_path, file_id)
        return 0

    # 真实路径：调用现有 main.py / 标准化脚本，逐阶段输出 JSON 事件
    emit(SidecarEvent(type="error", stage="startup", fileId="startup", message="real pipeline not wired yet"))
    return 2


if __name__ == "__main__":
    sys.exit(main())


