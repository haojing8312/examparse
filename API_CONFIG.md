# API 配置说明（OpenAI）

## 环境变量配置

推荐使用 `.env` 文件管理 OpenAI 配置：

1. 复制 `env.example` 为 `.env`
2. 填写以下变量：

```
OPENAI_API_KEY=sk-xxxx
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL_NAME=gpt-4o
```

`config.py` 会在运行时自动加载 `.env`，并由各标准化器读取使用。

## 配置验证

```bash
python -c "from config import Config; print('配置有效' if Config.validate_openai_config() else '请设置OPENAI_API_KEY')"
```