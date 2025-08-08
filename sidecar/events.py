from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator


EventType = Literal["stage", "progress", "warning", "error", "metric", "completed"]


class SidecarEvent(BaseModel):
    type: EventType
    stage: str
    ts: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    fileId: str
    message: str | None = None
    percent: float | None = None

    @field_validator("percent")
    @classmethod
    def validate_percent(cls, v: float | None):
        if v is None:
            return v
        if v < 0 or v > 1:
            raise ValueError("percent must be within [0, 1]")
        return v

    def to_json(self) -> str:
        return self.model_dump_json()


