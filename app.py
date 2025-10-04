import streamlit as st
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain_openai import ChatOpenAI
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
import tempfile
from concurrent.futures import ThreadPoolExecutor
import requests
from bs4 import BeautifulSoup

# Load environment variables
load_dotenv()

st.set_page_config(page_title="Academic Paper Summarization AI", layout="wide")

# Initialize session state
if 'docs' not in st.session_state:
    st.session_state.docs = None
if 'summaries' not in st.session_state:
    st.session_state.summaries = {}

# Prompt configuration
PROMPTS = {
    "3-Line Summary": """You are an expert in summarizing academic papers into exactly 3 concise sentences.

# GuideLines
- Just output 3 standalone summary sentences.
- Each sentence should be clear, informative, and straight to the point.
- Please answer in English.

# Format
- Do not include any greetings, introductions, or explanations.
- Use an ordered list (1, 2, 3) format.
- Your response must begin with "1." and follow an ordered list format (1., 2., 3.).
- You may begin each sentence with an emoji.

Text to summarize:
{text}

SUMMARY:""",

    "Detailed Summary": """Please write a summary of this paper.

# GuideLines
- Describe the paper in depth, detail, and specificity.
- Explain the core methodology in more detail and technical terms.
- Please answer in English.

# Format
- Do not include any other words except the summary.
- Formulas should be written in LaTeX format.

Text to summarize:
{text}

SUMMARY:""",

    "Keyword Explanations": """List of keywords in the paper.

# Guidelines
- List keywords that are essential to understanding this paper or that occur in this paper and explain each one.
- Explain it like a dictionary. Explain in detail based on the content of the paper.
- Explain each keyword in English.

# Format
- At the start of the answer, write the paper's keywords without explanation. No square brackets.
- A sentence consists of one keyword and a explanation of that keyword. Only the keyword should be enclosed in square brackets.

=== Example ===
Keyword1, Keyword2, Keyword3, ...

[Keyword1 in paper's language] very detailed explanation of the keyword in English
[Keyword2 in paper's language] very detailed explanation of the keyword in English
[Keyword3 in paper's language] very detailed explanation of the keyword in English
...
=== End of Example ===

Text to summarize:
{text}

KEYWORDS:"""
}

def generate_summary(summary_type, docs):
    """Generate a single summary"""
    try:
        llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini")
        prompt = PromptTemplate(
            template=PROMPTS[summary_type],
            input_variables=["text"]
        )
        chain = load_summarize_chain(
            llm=llm,
            chain_type="stuff",
            prompt=prompt
        )
        summary = chain.invoke(docs)
        return summary['output_text']
    except Exception as e:
        return f"Summary generation failed: {str(e)}"

def generate_all_summaries(docs):
    """Generate all three summaries in parallel"""
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            summary_type: executor.submit(generate_summary, summary_type, docs)
            for summary_type in PROMPTS.keys()
        }
        results = {
            summary_type: future.result()
            for summary_type, future in futures.items()
        }
    return results

def load_url_document(url):
    """Load document from URL (try multiple methods)"""
    errors = []

    # 1. Try WebBaseLoader (simplest method)
    try:
        loader = WebBaseLoader(url)
        docs = loader.load()
        if docs and len(docs) > 0 and docs[0].page_content.strip():
            return docs, None
    except Exception as e:
        errors.append(f"WebBaseLoader: {str(e)}")

    # 2. Try requests + BeautifulSoup
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove script and style tags
        for script in soup(["script", "style"]):
            script.decompose()

        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        if text.strip():
            from langchain.docstore.document import Document
            docs = [Document(page_content=text, metadata={"source": url})]
            return docs, None
    except Exception as e:
        errors.append(f"requests+BeautifulSoup: {str(e)}")

    # All methods failed
    return None, "\n".join(errors)

# Sidebar - Document loading
with st.sidebar:
    st.header("📁 Load Document")

    input_method = st.radio("Input Method:", ["URL Input", "PDF Upload"])

    if input_method == "URL Input":
        url = st.text_input("Paper URL:")
        load_button = st.button("Load Document & Generate Summary", key="url_load")

        if load_button and url:
            with st.spinner("Loading document..."):
                docs, error = load_url_document(url)
                if docs:
                    st.session_state.docs = docs
                    st.success(f"Document loaded successfully! ({len(st.session_state.docs)} pages)")
                else:
                    st.error(f"Failed to load document:\n{error}")
                    st.info("💡 For JavaScript-rendered pages, please download as PDF and upload.")
                    st.session_state.docs = None

            # Generate summaries if document loaded successfully
            if st.session_state.docs:
                if not os.getenv("OPENAI_API_KEY"):
                    st.error("OPENAI_API_KEY is not configured.")
                else:
                    with st.spinner("Generating three summaries..."):
                        st.session_state.summaries = generate_all_summaries(st.session_state.docs)
                    st.success("All summaries generated successfully!")

    else:  # PDF Upload
        uploaded_file = st.file_uploader("PDF File:", type=['pdf'])
        load_button = st.button("Load Document & Generate Summary", key="pdf_load")

        if load_button and uploaded_file is not None:
            with st.spinner("Loading PDF file..."):
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                        tmp_file.write(uploaded_file.read())
                        tmp_path = tmp_file.name

                    loader = PyPDFLoader(tmp_path)
                    st.session_state.docs = loader.load()
                    st.success(f"Document loaded successfully! ({len(st.session_state.docs)} pages)")

                    os.unlink(tmp_path)
                except Exception as e:
                    st.error(f"Failed to load document: {str(e)}")
                    st.session_state.docs = None

            # Generate summaries if document loaded successfully
            if st.session_state.docs:
                if not os.getenv("OPENAI_API_KEY"):
                    st.error("OPENAI_API_KEY is not configured.")
                else:
                    with st.spinner("Generating three summaries..."):
                        st.session_state.summaries = generate_all_summaries(st.session_state.docs)
                    st.success("All summaries generated successfully!")

# Main area - Display summary results
st.title("📄 Paper Summary Results")

if st.session_state.summaries:
    tab1, tab2, tab3 = st.tabs(["📌 3-Line Summary", "📝 Detailed Summary", "🔑 Keyword Explanations"])

    with tab1:
        st.markdown("### 3-Line Summary")
        st.markdown(st.session_state.summaries.get("3-Line Summary", "Generating..."))

    with tab2:
        st.markdown("### Detailed Summary")
        st.markdown(st.session_state.summaries.get("Detailed Summary", "Generating..."))

    with tab3:
        st.markdown("### Keyword Explanations")
        st.markdown(st.session_state.summaries.get("Keyword Explanations", "Generating..."))
else:
    st.info("Please load a document from the left sidebar and generate summaries.")
