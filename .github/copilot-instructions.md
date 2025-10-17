## Quick project context

This is a small local desktop app (Tkinter) that detects likely AI-generated text inside PDFs using the Google Gemini API.

Key modules (read all when making cross-cutting changes):
- `start.py` — launcher, environment/dependency checks and entry point used by developers to run the app.
- `pdf_processor.py` — PDF text extraction, invisible/unicode watermark detection (`invisible_chars`), cleaning and per-file text metrics.
- `gemini_analyzer.py` — chunking logic, prompt construction, robust API calls with retries/backoff, response parsing and result aggregation.
- `main.py` — Tkinter GUI, background thread orchestration, progress callbacks, and JSON export (`_export_results` uses ensure_ascii=False).

Important repo-specific rules (do not change without updating related code):
- Chunking: `GeminiAnalyzer.chunk_size` defaults to 8000 and `chunk_overlap` to 200. Changing these affects memory, latency and API cost — update tests and aggregation logic if you alter chunk behavior.
- JSON contract: the model is asked to return a JSON object and code extracts the first `{...}` block. Preserve these fields: `confidence_score`, `is_ai_generated`, `ai_probability`, `human_probability`, `reasoning`, `specific_indicators`, `suspicious_phrases`, `text_metrics`. If you add fields, update `_aggregate_chunk_results` and `_parse_api_response`.
- Invisible/unicode signals: check `PDFProcessor.invisible_chars` for enumerated markers (zero-width spaces, soft-hyphens, etc.). The code treats high counts (e.g. >20 zero-width spaces) as strong indicators — keep thresholds consistent across UI and export.
- Networking: use `_make_robust_api_call` in `gemini_analyzer.py` for all external calls. It implements exponential backoff and retries — extend the pattern if adding new endpoints.
- UI threading: long-running work runs in background threads (`threading.Thread(..., daemon=True)`) and reports to the UI using `root.after(0, ...)` and `progress_callback(message)`. Never perform blocking I/O on the main thread.

Developer workflow (quick):
1. Create virtualenv and activate (zsh):
   python3 -m venv venv
   source venv/bin/activate
2. Install dependencies:
   pip install -r requirements.txt
3. Run launcher (performs runtime dependency checks):
   python start.py
4. Use the GUI to enter `Gemini API Key` and click "Verbindung testen" (calls `GeminiAnalyzer.test_connection`).

Places to inspect when changing behavior:
- `pdf_processor.py`: `process_pdf`, `_analyze_unicode_characters`, `_clean_text`.
- `gemini_analyzer.py`: `_create_overlapping_chunks`, `_create_analysis_prompt`, `_make_robust_api_call`, `_parse_api_response`, `_aggregate_chunk_results`, `_aggregate_text_metrics`.
- `main.py`: background thread lifecycle, `progress_callback`, `_export_results` (writes JSON with ensure_ascii=False).
- `start.py`: environment checks — it detects required imports (e.g. `google.genai`) and fails early if missing.

Testing and quick verification:
- There are no unit tests by default. Useful focused tests to add:
  - `test_chunking.py`: `_create_overlapping_chunks` (cases: shorter than chunk_size, exactly multiple, and off-by-one overlaps).
  - `test_parse_response.py`: `_parse_api_response` handling valid JSON, JSON with trailing text, and invalid responses.
  - `test_unicode_analysis.py`: `PDFProcessor._analyze_unicode_characters` with strings that include multiple invisible chars.
- Manual smoke: run `python start.py`, supply API key, open a small PDF and confirm progress messages and exported JSON contains the required JSON contract fields.

Editing guidelines for AI agents:
- Preserve the JSON response contract and aggregation logic when modifying model prompts or post-processing.
- Use the existing exponential-backoff wrapper for any network call; avoid adding new raw requests without the same robustness.
- Keep GUI updates on the main thread via `root.after` and do background work in daemon threads.
- When adding per-chunk metrics, update both `_aggregate_chunk_results` and `_aggregate_text_metrics` to include weighted aggregation by `confidence_score`.

If anything is missing or unclear, tell me which function or behavior you want expanded and I will iterate.
  - `PDFProcessor._analyze_unicode_characters` (texts with various invisible chars)
