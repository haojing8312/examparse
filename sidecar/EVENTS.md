## Sidecar 事件契约

字段说明：
- type: 事件类型（stage|progress|warning|error|metric|completed）
- stage: 阶段名（split|split-questions|process|export|done|startup|validate|runtime）
- ts: ISO 8601 时间戳（UTC）
- fileId: 文件维度的唯一 ID（每个输入文件不同）
- message: 附加信息（可为路径、描述、错误原因）
- percent: 进度（0~1，可空，仅 progress 事件有意义）

示例：
```json
{"type":"stage","stage":"split","ts":"2025-01-01T00:00:00Z","fileId":"abc","message":"start split","percent":null}
{"type":"progress","stage":"split","ts":"2025-01-01T00:00:01Z","fileId":"abc","message":null,"percent":0.5}
{"type":"completed","stage":"done","ts":"2025-01-01T00:00:10Z","fileId":"abc","message":"/path/to/workdir","percent":null}
```

Schema：见 `sidecar/event_schema.json`。


