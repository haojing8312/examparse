import json
from pathlib import Path

import fastjsonschema

from sidecar.events import SidecarEvent


def load_schema() -> dict:
    schema_path = Path(__file__).resolve().parents[1] / "sidecar" / "event_schema.json"
    return json.loads(schema_path.read_text())


def test_event_json_matches_schema():
    schema = load_schema()
    validate = fastjsonschema.compile(schema)

    e = SidecarEvent(type="progress", stage="split", fileId="fid-1", percent=0.3)
    payload = json.loads(e.to_json())

    validate(payload)

    # 越界 percent 应报错
    bad = payload.copy()
    bad["percent"] = 2.0
    try:
        validate(bad)
        assert False, "schema 应当拒绝 percent>1 的值"
    except fastjsonschema.JsonSchemaException:
        pass


