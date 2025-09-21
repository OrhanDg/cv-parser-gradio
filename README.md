# CV Parser (LLM + Gradio)

Parse resumes (PDF/DOCX/DOC/TXT) into strict, schema-aligned JSON using an LLM. Includes a Gradio UI for upload, preview, and download of the parsed JSON.

- Upload → Extract text → Structured LLM output (JSON Mode / tool-calling style)
- UTF‑8 JSON suitable for ATS/RAG pipelines
- Works locally with uv or pip; easy to host on Hugging Face Spaces

## Repo Layout

-project-root/ gradio_app.py    
-Gradio entrypoint (UI) cv_parser.py      
-Extraction + LLM structured outputs pyproject.toml    
-uv/PEP 621 deps (pinned)


## Prerequisites

- Python 3.10+
- OpenAI API key
- uv (recommended for fast installs)
  - macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - Windows (PowerShell): `irm https://astral.sh/uv/install.ps1 | iex`

## Setup (uv)

1) Clone and enter

git clone https://github.com/OrhanDg/cv-parser-gradio.git
cd cv-parser-gradio


2) Install dependencies

uv lock
uv synv

3) Configure Secrets

Create '.env' file in the same folder with the app
After that copy your 'Open AI API Key' as follows OPENAI_API_KEY=sk-…your_key in the '.env' file

4) Run the app

uv run python gradio_app.py

After running the you should copy the https//127.XXX.XXX into your browser



So that's it !! Congratulations 
