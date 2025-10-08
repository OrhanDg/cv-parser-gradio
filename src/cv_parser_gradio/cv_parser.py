# cv_parser.py
import os
import json
import importlib
from pathlib import Path
from typing import Dict

# Third-party libs required at runtime:
# - PDF: pymupdf (fitz) or PyPDF2
# - DOCX/DOC: python-docx (and optionally textract for .doc)

# --------- HELPERS ----------
def _import_or_raise(module: str, install_hint: str):
    if importlib.util.find_spec(module) is None:
        raise ImportError(install_hint)
    return importlib.import_module(module)

# --------- TEXT EXTRACTION ----------
def extract_text(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        # Try PyMuPDF first
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            text = "".join(page.get_text() for page in doc)
            doc.close()
            return text
        except ImportError:
            pass
        # Fallback: PyPDF2
        try:
            from PyPDF2 import PdfReader
            with open(file_path, "rb") as f:
                reader = PdfReader(f)
                return "".join(p.extract_text() or "" for p in reader.pages)
        except ImportError:
            raise ImportError("Install a PDF library: pip install pymupdf or pip install PyPDF2")
    elif ext == ".docx":
        docx_module = _import_or_raise("docx", "Install: pip install python-docx to parse DOCX files.")
        Document = docx_module.Document
        doc = Document(file_path)
        text = "\n".join(p.text for p in doc.paragraphs)
        for table in doc.tables:
            for row in table.rows:
                text += "\n" + "\t".join(cell.text for cell in row.cells)
        return text
    elif ext == ".doc":
        textract = _import_or_raise("textract", "Install: pip install textract to parse legacy .doc files.")
        return textract.process(file_path).decode("utf-8", errors="ignore")
    elif ext == ".txt":
        # Try common encodings
        for enc in ("utf-8", "latin-1", "cp1252", "iso-8859-1", "utf-16"):
            try:
                with open(file_path, "r", encoding=enc) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        with open(file_path, "rb") as f:
            return f.read().decode("utf-8", errors="ignore")
    else:
        raise ValueError(f"Unsupported file type: {ext} (supported: .pdf, .docx, .doc, .txt)")

# --------- LLM STRUCTURED OUTPUT ----------
# Move OpenAI import to top-level by your rule; fail gracefully if missing.
try:
    from openai import OpenAI
except Exception as _e:
    OpenAI = None  # Will error at call time if used without package installed

def llm_extract_resume(resume_text: str) -> Dict:
    if OpenAI is None:
        raise ImportError("openai package not installed. Run: pip install openai")
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set in environment.")
    client = OpenAI(api_key=api_key)

    schema = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "name": {"type": "string"},
        "email": {"type": ["string", "null"]},
        "phone": {"type": ["string", "null"]},
        "linkedin": {"type": ["string", "null"]},
        "summary": {"type": ["string", "null"]},
        "skills": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 0
        },
        "experience": {
            "type": "array",
            "minItems": 0,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "position": {"type": "string"},
                    "company": {"type": ["string", "null"]},
                    "duration": {"type": ["string", "null"]},
                    "description": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 0
                    }
                },
                "required": ["position", "company", "duration", "description"]
            }
        },
        "education": {
            "type": "array",
            "minItems": 0,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "degree": {"type": ["string", "null"]},
                    "institution": {"type": ["string", "null"]},
                    "year": {"type": ["string", "null"]},
                    "field": {"type": ["string", "null"]}
                },
                "required": ["degree", "institution", "year", "field"]
            }
        },
        "certificates": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 0
        },
        "languages": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 0
        },
        "detected_language": {"type": "string"}
    },
    "required": [
        "name",
        "email",
        "phone",
        "linkedin",
        "summary",
        "skills",
        "experience",
        "education",
        "certificates",
        "languages",
        "detected_language"
    ]
}



    system = "Extract the resume into a single JSON object that matches the schema exactly; output only valid JSON."
    user = f"""
Resume:
\"\"\"{resume_text}\"\"\"

Rules:
- Detect primary language as ISO-2 (e.g., 'en', 'de', 'tr'); default to 'en' if unclear.
- Normalize LinkedIn as 'linkedin.com/in/<handle>' when present.
- Use null for missing fields.
- Return ONLY valid JSON conforming to the provided schema.
"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "ResumeSchema", "schema": schema, "strict": True},
        },
        temperature=0
    )
    return json.loads(resp.choices[0].message.content)

# --------- DRIVER: ANY UPLOAD → JSON ----------
def parse_any_resume_to_json(upload_path: str, out_json: str = "parsed_cv.json") -> str:
    text = extract_text(upload_path)
    if not text or not text.strip():
        raise ValueError("No text extracted (consider OCR for scanned PDFs).")
    data = llm_extract_resume(text)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return out_json

if __name__ == "__main__":
    # Optional: direct run for quick manual test
    sample = "/path/to/resume.pdf"  # or .docx/.txt
    if os.path.exists(sample):
        out = parse_any_resume_to_json(sample, "parsed_cv.json")
        print("Saved structured JSON to:", out)
    else:
        print("Update 'sample' path to test direct run.")
