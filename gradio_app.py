# gradio_app.py
import os
import json
import shutil
from pathlib import Path
from dotenv import load_dotenv  
load_dotenv()  

import gradio as gr

from cv_parser_gradio import extract_text, llm_extract_resume, parse_any_resume_to_json

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

def parse_upload(file_obj) -> tuple[str, dict | list | str, str | None]:
    """
    - file_obj: Gradio File object; has attributes .name (temp path) and .orig_name (original name)
    Returns:
      - status string
      - JSON content (dict) for display
      - path to JSON file for download (or None)
    """
    if file_obj is None:
        return ("No file uploaded.", {}, None)

    # Gradio provides a tempfile; copy to a stable path with original name for logging/debug (optional)
    temp_path = Path(file_obj.name)
    orig_name = getattr(file_obj, "orig_name", temp_path.name)
    stable_path = OUTPUT_DIR / orig_name
    try:
        shutil.copyfile(temp_path, stable_path)
    except Exception:
        # If copy fails (name collisions, permissions), just use temp path
        stable_path = temp_path

    # Build output JSON filename
    out_json = OUTPUT_DIR / (Path(orig_name).stem + "_parsed.json")

    try:
        # Use your existing pipeline: any of pdf/docx/doc/txt
        saved_path = parse_any_resume_to_json(str(stable_path), str(out_json))

        # Load the JSON for on-screen display
        with open(saved_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return ("✅ Parsed successfully.", data, str(saved_path))
    except Exception as e:
        return (f"❌ Error: {e}", {}, None)

with gr.Blocks(title="LLM CV Parser") as demo:
    gr.Markdown("# LLM CV Parser\nUpload a CV (PDF/DOCX/DOC/TXT) to extract a structured JSON.")

    with gr.Row():
        file_in = gr.File(label="Upload CV", file_count="single", file_types=[".pdf", ".docx", ".doc", ".txt"])
        parse_btn = gr.Button("Parse")

    with gr.Row():
        status = gr.Textbox(label="Status", interactive=False)
    with gr.Row():
        json_view = gr.JSON(label="Parsed JSON")
    with gr.Row():
        download = gr.DownloadButton(label="Download JSON", visible=False)

    # Wire up: when Parse clicked, run parse_upload
    # We need to toggle visibility of download button depending on whether a file was created
    def run_parse(file_obj):
        s, data, path = parse_upload(file_obj)
        # Gradio DownloadButton takes a file path; show it only when we have one
        if path:
            return s, data, gr.update(visible=True, value=path, label=f"Download {Path(path).name}")
        else:
            return s, data, gr.update(visible=False, value=None)

    parse_btn.click(
        fn=run_parse,
        inputs=[file_in],
        outputs=[status, json_view, download]
    )

if __name__ == "__main__":
    # share=True gives a public link like https://xxx.gradio.live for quick testing
    demo.launch(share=True)
