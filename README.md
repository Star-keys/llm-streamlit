# 논문 요약 AI

Streamlit 기반 학술 논문 자동 요약 애플리케이션입니다. LangChain과 OpenAI GPT-4o-mini를 활용하여 논문을 3가지 방식으로 요약합니다.

## 주요 기능

- **문서 입력**: URL 입력 또는 PDF 파일 업로드
- **3가지 요약 자동 생성** (병렬 처리):
  - 📌 3줄 요약: 핵심 내용을 3문장으로 간결하게
  - 📝 상세 요약: 방법론과 기술적 세부사항 포함
  - 🔑 키워드 설명: 주요 키워드의 사전식 해설
- **다중 URL 로더**: WebBaseLoader 실패 시 requests + BeautifulSoup으로 자동 대체

## 설치 및 실행

### 1. 가상환경 설정

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.env` 파일을 생성하고 OpenAI API 키를 설정하세요:

```bash
cp .env.example .env
# .env 파일을 열어서 OPENAI_API_KEY 값 입력
```

### 4. 애플리케이션 실행

```bash
streamlit run app.py
```

## 사용 방법

1. 좌측 사이드바에서 **URL 입력** 또는 **PDF 업로드** 선택
2. 논문 URL을 입력하거나 PDF 파일을 업로드
3. **문서 로드 및 요약 생성** 버튼 클릭
4. 메인 화면의 3개 탭에서 요약 결과 확인

## 제한사항

- JavaScript로 동적 렌더링되는 웹페이지는 URL 로딩이 불가능할 수 있습니다
- 이 경우 PDF로 다운로드 후 업로드하여 사용하세요

## 기술 스택

- **프론트엔드**: Streamlit
- **LLM**: OpenAI GPT-4o-mini
- **프레임워크**: LangChain
- **문서 처리**: PyPDF, BeautifulSoup4
