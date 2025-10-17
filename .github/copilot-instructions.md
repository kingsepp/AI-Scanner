## Quick project context

This repository contains a local desktop app (Tkinter) that detects AI-generated text in PDFs using Google Gemini.
Key modules:
- `start.py` — launcher + dependency checks and entry point.
- `pdf_processor.py` — PDF extraction, invisible-Unicode detection (`invisible_chars`) and cleaning.
- `gemini_analyzer.py` — Gemini integration, chunking, prompt engineering, response parsing.
- `main.py` — Tkinter GUI, threading, progress callbacks, export (`JSON`) of results.

## What an AI coding agent should know first

- The app uses chunked analysis with overlap: `GeminiAnalyzer.chunk_size` (default 8000) and `chunk_overlap` (200). Changes to those values affect memory and API cost.
- Prompts must request JSON-only responses. See `_create_analysis_prompt(...)` and `_parse_api_response(...)` — the code expects a valid JSON object inside the response text and will extract the first `{...}` block.
- Unicode/watermark signals are enumerated in `PDFProcessor.invisible_chars`. High counts (>20 zero-width spaces) are treated as strong indicators.
- GUI updates are thread-safe via `root.after(0, ...)`; long-running work runs in a background thread and reports via `progress_callback(message)`.

## Patterns and conventions to follow

- Keep API calls robust: `_make_robust_api_call` uses exponential backoff and retries — preserve or extend that pattern when changing network logic.
- Maintain the JSON response contract from the model: fields `confidence_score`, `is_ai_generated`, `ai_probability`, `human_probability`, `reasoning`, `specific_indicators`, `suspicious_phrases`, `text_metrics`.
- Chunk aggregation uses weighted averages by `confidence_score`. When adding new per-chunk metrics, ensure `_aggregate_chunk_results` and `_aggregate_text_metrics` are updated.
- UI changes must not block the main thread. Use `threading.Thread(..., daemon=True)` for background tasks and `root.after` to update widgets.

## Quick dev workflow & commands (zsh/Linux)

1. Create and activate venv:
   - `python3 -m venv venv`
   - `source venv/bin/activate`
2. Install deps:
   - `pip install -r requirements.txt`
3. Start the app (launcher performs checks):
   - `python start.py`

Use `Gemini API Key` in the GUI to run `Verbindung testen` (calls `GeminiAnalyzer.test_connection`).

## Files to inspect when modifying behavior

- `pdf_processor.py` — text extraction, `process_pdf`, `_analyze_unicode_characters`, `_clean_text`
- `gemini_analyzer.py` — prompt format, `_create_overlapping_chunks`, `_make_robust_api_call`, `_parse_api_response`, `_aggregate_chunk_results`
- `main.py` — thread lifecycle, `progress_callback` usage, GUI export logic (`_export_results` saves JSON with `ensure_ascii=False`)
- `start.py` — environment and dependency checks; tests expected packages by import name (e.g. `google.genai`).

## Testing guidance for agents

- Unit tests are not present; add small, focused tests around:
  - `_create_overlapping_chunks` (boundary: short text, exact multiple of chunk_size)
  - `_parse_api_response` (valid JSON, trailing text, invalid JSON)
  - `PDFProcessor._analyze_unicode_characters` (texts with various invisible chars)
- Manual test: run `python start.py`, provide API key, load a small PDF and verify GUI progress and JSON export.

If anything here is unclear or you want the instructions expanded (e.g., sample unit tests or CI steps), tell me which parts to expand.
