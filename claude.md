# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ExamParse is a tool for converting PDF/Word exam question files into structured Excel format. It uses AI (OpenAI/Gemini) to standardize and parse different question types (single choice, multiple choice, judgment, short answer, essay, case analysis).

## Architecture

### Core Components
- **Standardizers**: Individual processors for each question type (`*_standardizer.py`) that extend `QuestionStandardizerBase`
- **Utils**: Common utilities in `utils/standardization_utils.py` for file processing, AI calls, and Excel generation
- **Sidecar**: Event-driven processing system for desktop integration (`sidecar/`)
- **Desktop App**: Tauri + React GUI in `apps/desktop/`

### Processing Flow
1. **Text Extraction**: Extract text from PDF/Word files
2. **Question Type Classification**: Identify and separate different question types
3. **Chunking**: Split content into manageable chunks for AI processing
4. **Standardization**: Use AI to convert raw text into structured format
5. **Export**: Generate Excel files with standardized question data

## Development Commands

### Environment Setup
```bash
# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

### Testing
```bash
# Run all tests
uv run pytest tests -q

# Run specific test file
uv run pytest tests/test_text_splitting.py -v

# Run specific test pattern
uv run pytest tests/test_sidecar* -v
```

### Question Standardization
```bash
# Process all question types
uv run python main.py --type all

# Process specific question type
uv run python main.py --type single --base-dir "question_processing_*/question_types"

# Run individual standardizers directly
uv run python single_choice_standardizer.py
uv run python judgment_standardizer.py
uv run python multiple_choice_standardizer.py
uv run python short_answer_standardizer.py
uv run python essay_standardizer.py
uv run python case_analysis_standardizer.py
```

### Desktop Application
```bash
# Install desktop dependencies
cd apps/desktop/ui && npm i
cd .. && npm i

# Start development mode
npm run dev

# Build desktop app
npm run build
```

## Configuration

### Environment Variables
Create `.env` file from `env.example`:
```
OPENAI_API_KEY=sk-xxxx
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL_NAME=gpt-4o
```

### API Configuration
- OpenAI config in `config.py` with automatic `.env` loading
- Gemini support available as alternative
- Retry logic and error handling built into `utils/standardization_utils.py`

## Key Files and Patterns

### Standardizer Base Class
All question type standardizers inherit from `QuestionStandardizerBase` in `question_standardizer_base.py`:
- Implements chunking, AI calling, and result parsing
- Standardizers must implement abstract methods: `get_question_type_name()`, `get_standard_format()`, etc.

### Common Utilities
`utils/standardization_utils.py` provides:
- File chunking with configurable overlap
- OpenAI API calls with retry logic
- Markdown content extraction
- Excel generation with auto-formatting
- Question text splitting and parsing

### Event System
Sidecar uses JSON event streaming (`sidecar/EVENTS.md`):
- Event types: stage, progress, warning, error, metric, completed
- Schema validation in `sidecar/event_schema.json`
- Desktop app consumes events for UI updates

## File Structure Patterns

### Generated Output Structure
```
question_processing_[PDF_NAME]/
├── question_types/              # Question type markdown files
│   ├── single_choice.md
│   ├── multiple_choice.md
│   └── ...
├── [TYPE]_questions/           # Split questions per type
│   ├── question_0001.md
│   └── split_stats.md
└── split_summary.md
```

### Standardization Output
```
[TYPE]_standardized/
├── original_backup.md
├── standardized_chunk_001.md
├── original_chunk_001.md
├── standardization_report.md
└── quality_stats.json
```

## Development Guidelines

### Adding New Question Types
1. Create new standardizer class extending `QuestionStandardizerBase`
2. Implement required abstract methods
3. Add prompt templates and parsing logic
4. Update `main.py` to include new type
5. Add corresponding tests in `tests/`

### Working with AI Responses
- Use consistent separators: `=== 题目分隔符 ===`
- Implement fallback parsing for different response formats
- Handle API failures gracefully with retry logic
- Validate and clean extracted content

### Testing Strategy
- Unit tests for text processing in `tests/test_text_splitting.py`
- Integration tests for sidecar events
- Excel output validation
- API mocking for reliable CI/CD

## Common Issues

### Import Warnings
Ensure virtual environment activation: `source .venv/bin/activate && uv sync`

### File Processing
- Generated directories auto-created in corresponding question type folders
- Check `split_stats.md` files for processing statistics
- Review `standardization_report.md` for quality metrics

### Desktop App Dependencies
- Windows: Visual Studio Build Tools + WebView2 Runtime
- Linux: gtk3-dev, webkit2gtk-dev, pkg-config
- Ensure Python environment accessible from Tauri context