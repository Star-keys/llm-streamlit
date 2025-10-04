# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Streamlit-based academic paper summarization application using LangChain and OpenAI GPT-4o-mini. It generates three types of summaries in parallel: 3-line summary, detailed summary, and keyword explanations.

## Environment Setup

- **Virtual Environment**: Always work within a Python virtual environment
- **Environment Variables**: Create a `.env` file based on `.env.example` with `OPENAI_API_KEY`

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

## Architecture

### Document Loading (app.py:117-157)
- Dual-strategy URL loading: tries `WebBaseLoader` first, falls back to `requests + BeautifulSoup`
- PDF loading via `PyPDFLoader` with temporary file handling
- Session state management for loaded documents

### Summary Generation (app.py:86-115)
- Three summary types with distinct prompts (PROMPTS dict at app.py:25-84)
  - "3줄 요약": 3-sentence Korean summary with emoji bullets
  - "상세 요약": Detailed technical explanation with LaTeX formulas
  - "키워드 설명": Dictionary-style keyword explanations
- Parallel processing using `ThreadPoolExecutor` (3 workers)
- Uses LangChain's `load_summarize_chain` with "stuff" chain type

### UI Structure
- Sidebar: Document input (URL or PDF upload)
- Main area: Tabbed display of three summary types
- Session state tracks `docs` and `summaries`

## Project Checklist

All development work must be tracked in `checklist.md`:
- Update checklist **before** starting work
- Update checklist **after** completing work
