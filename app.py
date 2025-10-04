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

# 환경 변수 로드
load_dotenv()

st.set_page_config(page_title="논문 요약 AI", layout="wide")

# 세션 스테이트 초기화
if 'docs' not in st.session_state:
    st.session_state.docs = None
if 'summaries' not in st.session_state:
    st.session_state.summaries = {}

# 프롬프트 설정
PROMPTS = {
    "3줄 요약": """You are an expert in summarizing academic papers into exactly 3 concise sentences.

# GuideLines
- Just output 3 standalone summary sentences.
- Each sentence should be clear, informative, and straight to the point.
- Please answer in Korean except proper nouns and technical terms.

# Format
- Do not include any greetings, introductions, or explanations.
- Use an ordered list (1, 2, 3) format.
- Your response must begin with "1." and follow an ordered list format (1., 2., 3.).
- You may begin each sentence with an emoji.

Text to summarize:
{text}

SUMMARY:""",

    "상세 요약": """Please write a summary of this paper.

# GuideLines
- Describe the paper in depth, detail, and specificity.
- Explain the core methodology in more detail and technical terms.
- Please answer in Korean except proper nouns and technical terms.

# Format
- Do not include any other words except the summary.
- Formulas should be written in LaTeX format.

Text to summarize:
{text}

SUMMARY:""",

    "키워드 설명": """List of keywords in the paper.

# Guidelines
- List keywords that are essential to understanding this paper or that occur in this paper and explain each one.
- Explain it like a dictionary. Explain in detail based on the content of the paper.
- Explain each keyword in user's language (Korean).

# Format
- At the start of the answer, write the paper's keywords without explanation. No square brackets.
- A sentence consists of one keyword and a explanation of that keyword. Only the keyword should be enclosed in square brackets.

=== Example ===
Keyword1, Keyword2, Keyword3, ...

[Keyword1 in paper's language] very detailed explanation of the keyword in user's language
[Keyword2 in paper's language] very detailed explanation of the keyword in user's language
[Keyword3 in paper's language] very detailed explanation of the keyword in user's language
...
=== End of Example ===

Text to summarize:
{text}

KEYWORDS:"""
}

def generate_summary(summary_type, docs):
    """단일 요약 생성"""
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
        return f"요약 생성 실패: {str(e)}"

def generate_all_summaries(docs):
    """3가지 요약을 병렬로 생성"""
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
    """URL에서 문서를 로드 (여러 방법 시도)"""
    errors = []

    # 1. WebBaseLoader 시도 (가장 간단)
    try:
        loader = WebBaseLoader(url)
        docs = loader.load()
        if docs and len(docs) > 0 and docs[0].page_content.strip():
            return docs, None
    except Exception as e:
        errors.append(f"WebBaseLoader: {str(e)}")

    # 2. requests + BeautifulSoup 시도
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # script, style 태그 제거
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

    # 모든 방법 실패
    return None, "\n".join(errors)

# 사이드바 - 문서 로드
with st.sidebar:
    st.header("📁 문서 로드")

    input_method = st.radio("입력 방식:", ["URL 입력", "PDF 업로드"])

    if input_method == "URL 입력":
        url = st.text_input("논문 URL:")
        load_button = st.button("문서 로드 및 요약 생성", key="url_load")

        if load_button and url:
            with st.spinner("문서를 로드하는 중..."):
                docs, error = load_url_document(url)
                if docs:
                    st.session_state.docs = docs
                    st.success(f"문서 로드 완료! ({len(st.session_state.docs)} 페이지)")
                else:
                    st.error(f"문서 로드 실패:\n{error}")
                    st.info("💡 JavaScript로 렌더링되는 페이지는 PDF로 다운로드 후 업로드해주세요.")
                    st.session_state.docs = None

            # 문서 로드 성공 시 요약 생성
            if st.session_state.docs:
                if not os.getenv("OPENAI_API_KEY"):
                    st.error("OPENAI_API_KEY가 설정되지 않았습니다.")
                else:
                    with st.spinner("3가지 요약을 생성하는 중..."):
                        st.session_state.summaries = generate_all_summaries(st.session_state.docs)
                    st.success("모든 요약 생성 완료!")

    else:  # PDF 업로드
        uploaded_file = st.file_uploader("PDF 파일:", type=['pdf'])
        load_button = st.button("문서 로드 및 요약 생성", key="pdf_load")

        if load_button and uploaded_file is not None:
            with st.spinner("PDF 파일을 로드하는 중..."):
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                        tmp_file.write(uploaded_file.read())
                        tmp_path = tmp_file.name

                    loader = PyPDFLoader(tmp_path)
                    st.session_state.docs = loader.load()
                    st.success(f"문서 로드 완료! ({len(st.session_state.docs)} 페이지)")

                    os.unlink(tmp_path)
                except Exception as e:
                    st.error(f"문서 로드 실패: {str(e)}")
                    st.session_state.docs = None

            # 문서 로드 성공 시 요약 생성
            if st.session_state.docs:
                if not os.getenv("OPENAI_API_KEY"):
                    st.error("OPENAI_API_KEY가 설정되지 않았습니다.")
                else:
                    with st.spinner("3가지 요약을 생성하는 중..."):
                        st.session_state.summaries = generate_all_summaries(st.session_state.docs)
                    st.success("모든 요약 생성 완료!")

# 메인 영역 - 요약 결과 표시
st.title("📄 논문 요약 결과")

if st.session_state.summaries:
    tab1, tab2, tab3 = st.tabs(["📌 3줄 요약", "📝 상세 요약", "🔑 키워드 설명"])

    with tab1:
        st.markdown("### 3줄 요약")
        st.markdown(st.session_state.summaries.get("3줄 요약", "생성 중..."))

    with tab2:
        st.markdown("### 상세 요약")
        st.markdown(st.session_state.summaries.get("상세 요약", "생성 중..."))

    with tab3:
        st.markdown("### 키워드 설명")
        st.markdown(st.session_state.summaries.get("키워드 설명", "생성 중..."))
else:
    st.info("좌측 사이드바에서 문서를 로드하고 요약을 생성하세요.")
