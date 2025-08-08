from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class RunConfig:
    inputs: tuple[Path, ...]
    output: Path | None = None
    output_dir: Path | None = None
    mock: bool = False

    @staticmethod
    def from_args(
        inputs: Iterable[str] | None,
        input_single: str | None,
        output: str | None,
        output_dir: str | None,
        mock: bool,
    ) -> "RunConfig":
        input_paths: list[Path] = []
        if inputs:
            input_paths.extend(Path(p) for p in inputs)
        if input_single:
            input_paths.append(Path(input_single))

        return RunConfig(
            inputs=tuple(input_paths),
            output=Path(output) if output else None,
            output_dir=Path(output_dir) if output_dir else None,
            mock=mock,
        )


