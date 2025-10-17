# KI-Scanner (AI-Scanner)

Kleine Desktop-Anwendung (Tkinter) zur Erkennung wahrscheinlich KI-generierter Texte in PDFs mithilfe der Google Gemini API.

Kurz (was diese Repo enthält)
- `start.py` — Launcher: prüft Python-Version, benötigte Packages und Projektdateien, startet die GUI.
- `main.py` — Tkinter GUI, Datei‑Upload, API‑Key Eingabe, Analyse-Button, Exportfunktion.
- `pdf_processor.py` — PDF‑Text‑Extraktion, Erkennung unsichtbarer Unicode‑Zeichen, Reinigung und Text‑Metriken.
- `gemini_analyzer.py` — Chunking/Overlap, Prompt‑Erzeugung, robuste API‑Aufrufe, Antwort‑Parsing, Aggregation.

Schnellstart (lokal, zsh/Linux)
1. Virtuelle Umgebung erstellen und aktivieren
```bash
python3 -m venv venv
source venv/bin/activate
```
2. Abhängigkeiten installieren
```bash
pip install -r requirements.txt
```
3. Launcher ausführen (prüft Abhängigkeiten und Dateien)
```bash
python start.py
```
4. In der GUI: API Key eintragen → "Verbindung testen" → PDF auswählen → "ANALYSE STARTEN" → Ergebnis exportieren

Wichtige Design‑Konventionen & Hinweise für Entwickler
- Chunking: `GeminiAnalyzer.chunk_size` = 8000, `chunk_overlap` = 200. Änderungen beeinflussen Kosten/Leistung und Aggregation.
- JSON‑Contract: Die API‑Antwort muss ein JSON‑Objekt enthalten. Pflichtfelder, die das System extrahiert:
  - `confidence_score`, `is_ai_generated`, `ai_probability`, `human_probability`, `reasoning`, `specific_indicators`, `suspicious_phrases`, `text_metrics`.
- Invisible/Unicode: `PDFProcessor.invisible_chars` listet Zeichen (z. B. Zero‑Width Space U+200B). Schwellen wie >20 ZWSP oder invisibility_ratio >0.001 gelten als verdächtig.
- Networking: Verwende `_make_robust_api_call` (exponential backoff + retries) für alle externen Aufrufe.
- UI/Threading: Lang laufende Arbeit in Hintergrund‑Threads; GUI‑Updates nur über `root.after(0, ...)` oder `progress_callback`.

Fehlende/zu beachtende Punkte
- Es gibt keine automatisierten Tests im Repo (Prototyp‑Status). Empfohlene Tests sind im `.github/copilot-instructions.md` dokumentiert.
- Für echte API‑Analysen wird ein Google Gemini API‑Key benötigt.
- Die GUI setzt eine Desktop‑Umgebung voraus (kein Headless‑Server).

Troubleshooting
- Fehlende Dependencies erkennt `start.py` und gibt `pip install ...` Anweisungen aus.
- Logs: `ki_scanner.log` wird im Arbeitsverzeichnis geschrieben.

Weiteres
- Für kleine Änderungen am Analyzer (z. B. zusätzliche Textmetriken) aktualisiere sowohl `_parse_api_response` als auch `_aggregate_chunk_results` in `gemini_analyzer.py`.
- Wenn du ein CI möchtest, kann ich eine minimale GitHub Actions Workflow-Datei hinzufügen, die `pip install -r requirements.txt` und einen Smoke‑Run des Launchers ausführt.

Wenn du willst, kann ich jetzt den Launcher lokal ausführen (zeigt fehlende Pakete / Probleme) oder ein kurzes Beispiel‑JSON in die Doku einfügen. Welche Aktion ausführen? 
# AI-Scanner
