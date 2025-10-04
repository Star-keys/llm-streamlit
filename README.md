# Academic Paper Summarization AI

A Streamlit-based academic paper automatic summarization application. It leverages LangChain and OpenAI GPT-4o-mini to generate three types of summaries in parallel.

## Key Features

- **Document Input**: URL input or PDF file upload
- **Three Types of Auto-Generated Summaries** (parallel processing):
  - 📌 3-Line Summary: Concise 3-sentence overview of key points
  - 📝 Detailed Summary: In-depth explanation with methodology and technical details
  - 🔑 Keyword Explanations: Dictionary-style descriptions of key terms
- **Multi-Strategy URL Loader**: Automatic fallback to requests + BeautifulSoup when WebBaseLoader fails

## Installation & Setup

### 1. Virtual Environment Setup

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Variables

Create a `.env` file and configure your OpenAI API key:

```bash
cp .env.example .env
# Edit .env file and add your OPENAI_API_KEY
```

### 4. Run the Application

```bash
streamlit run app.py
```

## Usage

1. Select **URL Input** or **PDF Upload** from the left sidebar
2. Enter a paper URL or upload a PDF file
3. Click **Load Document & Generate Summary**
4. View summaries in the three tabs on the main screen

## Limitations

- JavaScript-rendered dynamic web pages may fail to load via URL
- In such cases, download the paper as PDF and upload it instead

## Tech Stack

- **Frontend**: Streamlit
- **LLM**: OpenAI GPT-4o-mini
- **Framework**: LangChain
- **Document Processing**: PyPDF, BeautifulSoup4
