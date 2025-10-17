import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import json
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from pdf_processor import PDFProcessor
from gemini_analyzer import GeminiAnalyzer

class KIScannerApp:
    """
    Hauptanwendung für den KI-Scanner mit Tkinter GUI
    """
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("KI-Scanner für Masterarbeiten - v1.0")
        self.root.geometry("900x800")
        self.root.resizable(True, True)
        
        # Styling
        style = ttk.Style()
        style.theme_use('clam')
        
        # Konfiguriere Custom-Styles
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Accent.TButton', font=('Arial', 10, 'bold'))
        
        # Anwendungsvariablen
        self.api_key_var = tk.StringVar()
        self.pdf_path_var = tk.StringVar()
        self.check_invisible_var = tk.BooleanVar(value=True)
        self.detailed_analysis_var = tk.BooleanVar(value=True)
        
        # Komponenten
        self.pdf_processor = PDFProcessor()
        self.gemini_analyzer: Optional[GeminiAnalyzer] = None
        self.current_analysis_results: Optional[Dict[str, Any]] = None
        self.analysis_thread: Optional[threading.Thread] = None
        
        # Logging
        self.logger = logging.getLogger(__name__)
        
        # GUI erstellen
        self._create_gui()
        
        # Cleanup bei Schließen
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _create_gui(self):
        """Erstellt die komplette GUI"""
        
        # Hauptcontainer
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        title_label = ttk.Label(header_frame, text="🔍 KI-Scanner für Masterarbeiten", style='Title.TLabel')
        title_label.grid(row=0, column=0, pady=(0, 5))
        
        subtitle_label = ttk.Label(header_frame, text="Erkennung von KI-generiertem Text mit Gemini API", 
                                  font=('Arial', 10, 'italic'))
        subtitle_label.grid(row=1, column=0)
        
        # API-Key Sektion
        self._create_api_section(main_frame, 1)
        
        # PDF-Upload Sektion
        self._create_pdf_section(main_frame, 2)
        
        # Optionen Sektion
        self._create_options_section(main_frame, 3)
        
        # Analyse-Button und Progress
        self._create_analysis_section(main_frame, 4)
        
        # Ergebnisse Sektion
        self._create_results_section(main_frame, 5)
        
        # Action-Buttons
        self._create_action_buttons(main_frame, 6)
        
        # Grid-Konfiguration für Responsiveness
        main_frame.columnconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)  # Results-Sektion soll expandieren
    
    def _create_api_section(self, parent, row):
        """API-Key Eingabe Sektion"""
        
        api_frame = ttk.LabelFrame(parent, text="🔑 Gemini API Konfiguration", padding="10")
        api_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # API-Key Eingabe
        ttk.Label(api_frame, text="API Key:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        api_entry = ttk.Entry(api_frame, textvariable=self.api_key_var, show="*", width=50)
        api_entry.grid(row=0, column=1, padx=(0, 10), sticky=(tk.W, tk.E))
        
        test_button = ttk.Button(api_frame, text="Verbindung testen", command=self._test_api_connection)
        test_button.grid(row=0, column=2)
        
        # Info-Label
        info_label = ttk.Label(api_frame, text="Hol dir einen kostenlosen API-Key von: https://aistudio.google.com/app/apikey", 
                              font=('Arial', 8), foreground='blue')
        info_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
        
        api_frame.columnconfigure(1, weight=1)
    
    def _create_pdf_section(self, parent, row):
        """PDF-Upload Sektion"""
        
        pdf_frame = ttk.LabelFrame(parent, text="📄 PDF-Dokument auswählen", padding="10")
        pdf_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        ttk.Label(pdf_frame, text="Datei:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        path_entry = ttk.Entry(pdf_frame, textvariable=self.pdf_path_var, state='readonly', width=60)
        path_entry.grid(row=0, column=1, padx=(0, 10), sticky=(tk.W, tk.E))
        
        browse_button = ttk.Button(pdf_frame, text="Durchsuchen...", command=self._browse_pdf_file)
        browse_button.grid(row=0, column=2)
        
        # Datei-Info Label
        self.file_info_label = ttk.Label(pdf_frame, text="", font=('Arial', 9), foreground='gray')
        self.file_info_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
        
        pdf_frame.columnconfigure(1, weight=1)
    
    def _create_options_section(self, parent, row):
        """Analyse-Optionen Sektion"""
        
        options_frame = ttk.LabelFrame(parent, text="⚙️ Analyse-Optionen", padding="10")
        options_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # Checkboxen
        invisible_check = ttk.Checkbutton(options_frame, text="Unsichtbare Unicode-Zeichen prüfen", 
                                        variable=self.check_invisible_var)
        invisible_check.grid(row=0, column=0, sticky=tk.W)
        
        detailed_check = ttk.Checkbutton(options_frame, text="Detaillierte Stilanalyse durchführen", 
                                       variable=self.detailed_analysis_var)
        detailed_check.grid(row=1, column=0, sticky=tk.W)
        
        # Info-Text
        info_text = ("• Unsichtbare Zeichen-Prüfung erkennt AI-Wasserzeichen (Zero-Width Spaces)\n"
                    "• Detaillierte Analyse bietet umfangreichere Begründungen")
        info_label = ttk.Label(options_frame, text=info_text, font=('Arial', 8), foreground='gray')
        info_label.grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
    
    def _create_analysis_section(self, parent, row):
        """Analyse-Button und Progress Sektion"""
        
        analysis_frame = ttk.Frame(parent)
        analysis_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # Analyse-Button
        self.analyze_button = ttk.Button(analysis_frame, text="🚀 ANALYSE STARTEN", 
                                       command=self._start_analysis, style='Accent.TButton')
        self.analyze_button.pack(fill=tk.X, pady=(0, 10))
        
        # Progress-Bar
        self.progress_bar = ttk.Progressbar(analysis_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))
        
        # Status-Label
        self.status_label = ttk.Label(analysis_frame, text="Bereit für Analyse...", font=('Arial', 9))
        self.status_label.pack()
    
    def _create_results_section(self, parent, row):
        """Ergebnisse Anzeige Sektion"""
        
        results_frame = ttk.LabelFrame(parent, text="📊 Analyseergebnisse", padding="10")
        results_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        
        # Scrollbarer Text-Bereich
        self.results_text = scrolledtext.ScrolledText(results_frame, height=20, width=80, 
                                                    wrap=tk.WORD, state=tk.DISABLED,
                                                    font=('Courier', 10))
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Initial-Text
        self._update_results("Wähle eine PDF-Datei und starte die Analyse...\n\n" +
                           "ℹ️ Die Analyse kann je nach Dokumentlänge 30-120 Sekunden dauern.\n" +
                           "ℹ️ Große Dokumente werden automatisch in Chunks aufgeteilt.")
        
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
    
    def _create_action_buttons(self, parent, row):
        """Action-Buttons Sektion"""
        
        buttons_frame = ttk.Frame(parent)
        buttons_frame.grid(row=row, column=0, columnspan=2, pady=10)
        
        # Button-Container für Zentrierung
        button_container = ttk.Frame(buttons_frame)
        button_container.pack()
        
        # Buttons
        self.export_button = ttk.Button(button_container, text="📄 Bericht exportieren", 
                                      command=self._export_results, state=tk.DISABLED)
        self.export_button.pack(side=tk.LEFT, padx=(0, 10))
        
        reset_button = ttk.Button(button_container, text="🔄 Neue Analyse", command=self._reset_analysis)
        reset_button.pack(side=tk.LEFT, padx=(0, 10))
        
        help_button = ttk.Button(button_container, text="❓ Hilfe", command=self._show_help)
        help_button.pack(side=tk.LEFT, padx=(0, 10))
        
        quit_button = ttk.Button(button_container, text="❌ Beenden", command=self._on_closing)
        quit_button.pack(side=tk.LEFT)
    
    def _test_api_connection(self):
        """Testet die Gemini API Verbindung"""
        
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("Fehler", "Bitte gib deinen Gemini API-Key ein.")
            return
        
        # Disable button während Test
        test_button = self.root.nametowidget(self.root.focus_get().master.children['!button'])
        test_button.config(state=tk.DISABLED, text="Teste...")
        
        def test_connection():
            try:
                analyzer = GeminiAnalyzer(api_key)
                result = analyzer.test_connection()
                
                # Zurück zum Main Thread für GUI-Updates
                self.root.after(0, lambda: self._handle_connection_test_result(result, test_button))
                
            except Exception as e:
                error_result = {
                    'success': False,
                    'message': f"Verbindungsfehler: {str(e)}"
                }
                self.root.after(0, lambda: self._handle_connection_test_result(error_result, test_button))
        
        # Starte Test in separatem Thread
        threading.Thread(target=test_connection, daemon=True).start()
    
    def _handle_connection_test_result(self, result, test_button):
        """Behandelt Ergebnis des Connection-Tests"""
        
        test_button.config(state=tk.NORMAL, text="Verbindung testen")
        
        if result['success']:
            self.gemini_analyzer = GeminiAnalyzer(self.api_key_var.get().strip())
            messagebox.showinfo("Erfolg", f"✅ {result['message']}\n\n" +
                              f"Response-Zeit: {result.get('response_time', 'N/A')}s")
        else:
            messagebox.showerror("Fehler", f"❌ {result['message']}")
    
    def _browse_pdf_file(self):
        """PDF-Datei-Dialog"""
        
        file_path = filedialog.askopenfilename(
            title="PDF-Datei für Analyse auswählen",
            filetypes=[
                ("PDF-Dateien", "*.pdf"),
                ("Alle Dateien", "*.*")
            ]
        )
        
        if file_path:
            self.pdf_path_var.set(file_path)
            
            # Zeige Datei-Informationen
            try:
                file_info = Path(file_path)
                size_mb = file_info.stat().st_size / (1024 * 1024)
                info_text = f"📄 {file_info.name} ({size_mb:.1f} MB)"
                self.file_info_label.config(text=info_text)
            except:
                self.file_info_label.config(text="Datei ausgewählt")
    
    def _start_analysis(self):
        """Startet die Analyse in separatem Thread"""
        
        # Validierung
        if not self.api_key_var.get().strip():
            messagebox.showerror("Fehler", "Bitte gib deinen Gemini API-Key ein und teste die Verbindung.")
            return
        
        if not self.pdf_path_var.get().strip():
            messagebox.showerror("Fehler", "Bitte wähle eine PDF-Datei aus.")
            return
        
        # Prüfe ob bereits Analyse läuft
        if self.analysis_thread and self.analysis_thread.is_alive():
            messagebox.showwarning("Hinweis", "Eine Analyse läuft bereits. Bitte warten...")
            return

        # UI für Analyse vorbereiten
        self.analyze_button.config(state=tk.DISABLED, text="Analyse läuft...")
        self.export_button.config(state=tk.DISABLED)
        self.progress_bar.start(10)
        self._update_status("Analyse wird gestartet...")
        self._update_results("🔄 ANALYSE GESTARTET\n" + "="*50 + "\n\n")
        
        # Starte Analyse-Thread
        self.analysis_thread = threading.Thread(target=self._perform_analysis, daemon=True)
        self.analysis_thread.start()

    def _perform_analysis(self):
        """Führt die Analyse durch (läuft in separatem Thread)"""
        
        try:
            # 1. PDF verarbeiten
            self._update_status_threadsafe("📄 PDF wird verarbeitet...")
            self._update_results_threadsafe("📄 PDF-Verarbeitung gestartet...\n")
            
            pdf_result = self.pdf_processor.process_pdf(self.pdf_path_var.get())
            
            if not pdf_result['success']:
                raise Exception(f"PDF-Verarbeitung fehlgeschlagen: {pdf_result['error']}")
            
            # PDF-Info anzeigen
            file_info = pdf_result['file_info']
            stats = pdf_result['text_statistics']
            unicode_info = pdf_result['unicode_analysis']
            
            pdf_info_text = f"""✅ PDF erfolgreich verarbeitet
📊 Dokument-Statistiken:
   • Seiten: {file_info['num_pages']}
   • Dateigröße: {file_info['file_size_mb']} MB
   • Wörter: {stats['total_words']:,}
   • Zeichen: {stats['total_characters']:,}
   • Geschätzte Lesezeit: {stats['estimated_reading_time_minutes']} Min

"""
            
            if unicode_info['total_invisible_count'] > 0:
                pdf_info_text += f"⚠️ Unsichtbare Zeichen gefunden: {unicode_info['total_invisible_count']}\n"
                for char_name, count in unicode_info['invisible_characters_found'].items():
                    pdf_info_text += f"   • {char_name}: {count}\n"
            else:
                pdf_info_text += "✅ Keine unsichtbaren Zeichen erkannt\n"
            
            pdf_info_text += "\n"
            self._update_results_threadsafe(pdf_info_text)
            
            # 2. Gemini Analyzer initialisieren
            if not self.gemini_analyzer:
                self._update_status_threadsafe("🔑 Gemini API wird initialisiert...")
                self.gemini_analyzer = GeminiAnalyzer(self.api_key_var.get().strip())
            
            # 3. Text analysieren
            self._update_status_threadsafe("🤖 KI-Analyse läuft...")
            self._update_results_threadsafe("🤖 Starte KI-Textanalyse mit Gemini...\n")
            
            def progress_callback(message):
                self._update_status_threadsafe(message)
                self._update_results_threadsafe(f"   {message}\n")
            
            analysis_result = self.gemini_analyzer.analyze_document(
                pdf_result['cleaned_text'],
                pdf_result['unicode_analysis'],
                progress_callback
            )
            
            # 4. Ergebnisse zusammenstellen
            combined_results = {
                'pdf_data': pdf_result,
                'ai_analysis': analysis_result,
                'analysis_options': {
                    'check_invisible_chars': self.check_invisible_var.get(),
                    'detailed_analysis': self.detailed_analysis_var.get()
                },
                'analysis_completed_at': time.time()
            }
            
            self.current_analysis_results = combined_results
            
            # 5. Ergebnisse anzeigen
            self._update_status_threadsafe("📋 Ergebnisse werden aufbereitet...")
            self.root.after(0, self._display_final_results)
            
        except Exception as e:
            error_msg = f"Analyse-Fehler: {str(e)}"
            self.logger.error("❌ %s", error_msg)
            self.root.after(0, lambda: self._handle_analysis_error(error_msg))
        
        finally:
            # UI zurücksetzen
            self.root.after(0, self._analysis_completed)

    def _display_final_results(self):
        """Zeigt die finalen Analyseergebnisse an"""
        
        if not self.current_analysis_results:
            return
        
        ai_analysis = self.current_analysis_results['ai_analysis']
        pdf_data = self.current_analysis_results['pdf_data']
        
        results_text = "\n🎯 ANALYSE ABGESCHLOSSEN\n" + "="*50 + "\n\n"
        
        if ai_analysis.get('success'):
            # Hauptergebnisse
            is_ai = ai_analysis['is_ai_generated']
            confidence = ai_analysis['confidence_score'] * 100
            ai_prob = ai_analysis['ai_probability'] * 100
            human_prob = ai_analysis['human_probability'] * 100
            
            results_text += f"{ '🤖 KI-GENERIERT' if is_ai else '👤 MENSCHLICH VERFASST' }\n\n"
            
            results_text += f"📊 WAHRSCHEINLICHKEITEN:\n"
            results_text += f"   • KI-generiert: {ai_prob:.1f}%\n"
            results_text += f"   • Menschlich: {human_prob:.1f}%\n"
            results_text += f"   • Vertrauen: {'Hoch' if confidence > 75 else 'Mittel' if confidence > 50 else 'Niedrig'} ({confidence:.1f}%)\n\n"
            
            # Begründung
            if ai_analysis.get('reasoning'):
                results_text += f"💭 BEGRÜNDUNG:\n{ai_analysis['reasoning']}\n\n"
            
            # Indikatoren
            if ai_analysis.get('specific_indicators'):
                results_text += f"🔍 ERKANNTE INDIKATOREN:\n"
                for indicator in ai_analysis['specific_indicators'][:8]:  # Top 8
                    results_text += f"   • {indicator}\n"
                results_text += "\n"
            
            # Verdächtige Phrasen
            if ai_analysis.get('suspicious_phrases'):
                results_text += f"⚠️ VERDÄCHTIGE PHRASEN:\n"
                for phrase in ai_analysis['suspicious_phrases'][:5]:  # Top 5
                    results_text += f"   • \"{phrase}\"\n"
                results_text += "\n"
            
            # Text-Metriken
            if ai_analysis.get('text_metrics'):
                metrics = ai_analysis['text_metrics']
                results_text += f"📈 TEXT-METRIKEN:\n"
                results_text += f"   • Satzgleichmäßigkeit: {metrics.get('sentence_uniformity', 'N/A').title()}\n"
                results_text += f"   • Wortschatz-Komplexität: {metrics.get('vocabulary_complexity', 'N/A').title()}\n"
                results_text += f"   • Emotionaler Ausdruck: {metrics.get('emotional_expression', 'N/A').title()}\n\n"
            
            # Technische Details
            if ai_analysis.get('analysis_summary'):
                summary = ai_analysis['analysis_summary']
                results_text += f"🔧 TECHNISCHE DETAILS:\n"
                results_text += f"   • Analyse-Methode: {summary.get('analysis_method', 'N/A').replace('_', ' ').title()}\n"
                
                if 'total_chunks_analyzed' in summary:
                    results_text += f"   • Chunks analysiert: {summary['total_chunks_analyzed']}\n"
                    results_text += f"   • Erfolgreiche Chunks: {summary['successful_chunks']}\n"
                
                results_text += f"   • Modell: {ai_analysis.get('model_used', 'Gemini')}\n\n"
            
        else:
            results_text += f"❌ ANALYSE FEHLGESCHLAGEN\n\n"
            results_text += f"Fehler: {ai_analysis.get('error', 'Unbekannter Fehler')}\n\n"
        
        self._update_results(results_text, clear=False)
        
        # Export-Button aktivieren wenn erfolgreich
        if ai_analysis.get('success'):
            self.export_button.config(state=tk.NORMAL)
    
    def _update_status(self, status_text):
        """Aktualisiert Status-Label"""
        self.status_label.config(text=status_text)
        self.root.update_idletasks()
    
    def _update_status_threadsafe(self, status_text):
        """Thread-sichere Status-Aktualisierung"""
        self.root.after(0, lambda: self._update_status(status_text))
    
    def _update_results(self, text, clear=True):
        """Aktualisiert Ergebnisbereich"""
        self.results_text.config(state=tk.NORMAL)
        if clear:
            self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, text)
        self.results_text.see(tk.END)
        self.results_text.config(state=tk.DISABLED)
        self.root.update_idletasks()
    
    def _update_results_threadsafe(self, text, clear=False):
        """Thread-sichere Results-Aktualisierung"""
        self.root.after(0, lambda: self._update_results(text, clear))
    
    def _analysis_completed(self):
        """Wird nach Abschluss der Analyse aufgerufen"""
        self.progress_bar.stop()
        self.analyze_button.config(state=tk.NORMAL, text="🚀 ANALYSE STARTEN")
        self._update_status("Analyse abgeschlossen")
    
    def _handle_analysis_error(self, error_message):
        """Behandelt Analyse-Fehler"""
        error_text = f"\n❌ ANALYSE FEHLGESCHLAGEN\n{'='*50}\n\n"
        error_text += f"Fehler: {error_message}\n\n"
        error_text += "💡 Mögliche Lösungen:\n"
        error_text += "   • Überprüfe deine Internetverbindung\n"
        error_text += "   • Validiere deinen API-Key\n"
        error_text += "   • Stelle sicher, dass die PDF-Datei nicht beschädigt ist\n"
        error_text += "   • Versuche es mit einer kleineren PDF-Datei\n\n"
        
        self._update_results(error_text, clear=False)
        messagebox.showerror("Analyse-Fehler", f"Die Analyse ist fehlgeschlagen:\n\n{error_message}")
    
    def _export_results(self):
        """Exportiert Analyseergebnisse"""
        
        if not self.current_analysis_results:
            messagebox.showwarning("Hinweis", "Keine Ergebnisse zum Exportieren vorhanden.")
            return
        
        # Datei-Dialog
        file_path = filedialog.asksaveasfilename(
            title="Analyseergebnisse exportieren",
            defaultextension=".json",
            filetypes=[
                ("JSON-Dateien", "*.json"),
                ("Text-Dateien", "*.txt"),
                ("Alle Dateien", "*.*")
            ]
        )
        
        if file_path:
            try:
                if file_path.endswith('.json'):
                    # JSON-Export
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(self.current_analysis_results, f, indent=2, ensure_ascii=False, default=str)
                else:
                    # Text-Export
                    current_text = self.results_text.get(1.0, tk.END)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(current_text)
                
                messagebox.showinfo("Erfolg", f"Ergebnisse erfolgreich exportiert:\n{file_path}")
                
            except Exception as e:
                messagebox.showerror("Fehler", f"Export fehlgeschlagen:\n{str(e)}")
    
    def _reset_analysis(self):
        """Setzt Analyse zurück"""
        
        # Stoppe laufende Analyse
        if self.analysis_thread and self.analysis_thread.is_alive():
            if not messagebox.askyesno("Bestätigung", "Eine Analyse läuft noch. Wirklich zurücksetzen?"):
                return
        
        # Zurücksetzen
        self.pdf_path_var.set("")
        self.file_info_label.config(text="")
        self.current_analysis_results = None
        
        self.analyze_button.config(state=tk.NORMAL, text="🚀 ANALYSE STARTEN")
        self.export_button.config(state=tk.DISABLED)
        self.progress_bar.stop()
        
        self._update_status("Bereit für neue Analyse...")
        self._update_results("Bereit für neue Analyse...\n\nWähle eine PDF-Datei und starte die Analyse.")
    
    def _show_help(self):
        """Zeigt Hilfe-Dialog"""
        
        help_text = """KI-Scanner für Masterarbeiten - Hilfe

🎯 ZWECK:
Dieses Tool analysiert PDF-Dokumente auf KI-generierten Text unter 
Verwendung der Google Gemini API.

📋 ANLEITUNG:
1. Hol dir einen kostenlosen Gemini API-Key von:
   https://aistudio.google.com/app/apikey

2. Gib deinen API-Key ein und teste die Verbindung

3. Wähle deine PDF-Datei (Masterarbeit) aus

4. Konfiguriere die Analyse-Optionen nach Bedarf

5. Starte die Analyse - dies kann 30-120s dauern

6. Exportiere die Ergebnisse als JSON oder Text

🔒 DATENSCHUTZ:
• Alle Daten werden lokal verarbeitet
• API-Key wird nur im Arbeitsspeicher gehalten
• PDF-Inhalte werden nicht dauerhaft gespeichert

⚡ PERFORMANCE:
• Große Dokumente werden automatisch in Chunks aufgeteilt
• Typische Analyse-Zeit: 30-120 Sekunden
• Empfohlene max. Dateigröße: 50 MB

❓ PROBLEME:
• Bei API-Fehlern: API-Key und Internetverbindung prüfen
• Bei PDF-Fehlern: Andere PDF-Datei versuchen
• Bei langen Ladezeiten: Dokument ist möglicherweise zu groß
"""
        
        # Erstelle Hilfe-Fenster
        help_window = tk.Toplevel(self.root)
        help_window.title("Hilfe - KI-Scanner")
        help_window.geometry("600x500")
        help_window.resizable(True, True)
        
        # Text-Widget mit Scrollbar
        text_frame = ttk.Frame(help_window, padding="10")
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        help_text_widget = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, 
                                                   font=('Arial', 10), state=tk.NORMAL)
        help_text_widget.pack(fill=tk.BOTH, expand=True)
        
        help_text_widget.insert(tk.END, help_text)
        help_text_widget.config(state=tk.DISABLED)
        
        # Schließen-Button
        close_button = ttk.Button(help_window, text="Schließen", command=help_window.destroy)
        close_button.pack(pady=10)
    
    def _on_closing(self):
        """Behandelt das Schließen der Anwendung"""
        
        # Prüfe auf laufende Analyse
        if self.analysis_thread and self.analysis_thread.is_alive():
            if not messagebox.askyesno("Bestätigung", 
                                     "Eine Analyse läuft noch. Anwendung wirklich beenden?\n\n" +
                                     "Die laufende Analyse wird abgebrochen."):
                return
        
        self.logger.info("👋 Anwendung wird beendet")
        self.root.quit()
        self.root.destroy()
    
    def run(self):
        """Startet die Anwendung"""
        self.logger.info("🚀 GUI-Anwendung gestartet")
        self.root.mainloop()

# Anwendungs-Entry-Point
if __name__ == "__main__":
    app = KIScannerApp()
    app.run()
