import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from pypdf import PdfReader
import unicodedata

class PDFProcessor:
    """
    Verarbeitet PDF-Dateien und extrahiert Text mit Unicode-Analyse
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Unsichtbare Unicode-Zeichen für Erkennung
        self.invisible_chars = {
            '\u200B': 'Zero-Width Space',
            '\u200C': 'Zero-Width Non-Joiner',
            '\u200D': 'Zero-Width Joiner',
            '\u2060': 'Word Joiner',
            '\u00AD': 'Soft Hyphen',
            '\u200E': 'Left-to-Right Mark',
            '\u200F': 'Right-to-Left Mark',
            '\u2028': 'Line Separator',
            '\u2029': 'Paragraph Separator',
            '\uFEFF': 'Byte Order Mark'
        }
    
    def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Hauptmethode zur PDF-Verarbeitung
        
        Args:
            pdf_path: Pfad zur PDF-Datei
            
        Returns:
            Dict mit Textinhalt, Metadaten und Analyse-Ergebnissen
        """
        try:
            self.logger.info("📄 Starte PDF-Verarbeitung: %s", pdf_path)
            
            # Validiere Dateipfad
            pdf_file = Path(pdf_path)
            if not pdf_file.exists():
                raise FileNotFoundError(f"PDF-Datei nicht gefunden: {pdf_path}")
            
            if not pdf_file.suffix.lower() == '.pdf':
                raise ValueError(f"Datei ist keine PDF: {pdf_path}")
            
            # PDF lesen und Text extrahieren
            reader = PdfReader(pdf_path)
            extraction_result = self._extract_text_from_pdf(reader, pdf_file)
            
            if not extraction_result['success']:
                return extraction_result
            
            # Unicode-Analyse durchführen
            unicode_analysis = self._analyze_unicode_characters(extraction_result['full_text'])
            
            # Text bereinigen für weitere Verarbeitung
            cleaned_text = self._clean_text(extraction_result['full_text'])
            
            # Finale Ergebnisse zusammenstellen
            result = {
                'success': True,
                'file_info': extraction_result['file_info'],
                'pdf_metadata': extraction_result['pdf_metadata'],
                'full_text': extraction_result['full_text'],
                'cleaned_text': cleaned_text,
                'page_texts': extraction_result['page_texts'],
                'unicode_analysis': unicode_analysis,
                'text_statistics': self._calculate_text_statistics(cleaned_text),
                'processing_timestamp': extraction_result['processing_timestamp']
            }
            
            self.logger.info("✅ PDF-Verarbeitung erfolgreich abgeschlossen")
            return result
            
        except Exception as e:
            error_msg = f"Fehler bei PDF-Verarbeitung: {str(e)}"
            self.logger.error("❌ %s", error_msg)
            return {
                'success': False,
                'error': error_msg,
                'full_text': None,
                'cleaned_text': None
            }
    
    def _extract_text_from_pdf(self, reader: PdfReader, pdf_file: Path) -> Dict[str, Any]:
        """Extrahiert Text aus PDF"""
        import time
        
        try:
            # Datei-Informationen sammeln
            file_info = {
                'filename': pdf_file.name,
                'file_size_bytes': pdf_file.stat().st_size,
                'file_size_mb': round(pdf_file.stat().st_size / (1024*1024), 2),
                'num_pages': len(reader.pages)
            }
            
            # PDF-Metadaten extrahieren
            metadata = reader.metadata or {}
            pdf_metadata = {
                'title': getattr(metadata, 'title', None),
                'author': getattr(metadata, 'author', None),
                'creator': getattr(metadata, 'creator', None),
                'producer': getattr(metadata, 'producer', None),
                'creation_date': str(getattr(metadata, 'creation_date', None)),
                'modification_date': str(getattr(metadata, 'modification_date', None))
            }
            
            # Text von allen Seiten extrahieren
            full_text = ""
            page_texts = []
            
            for page_num, page in enumerate(reader.pages, 1):
                self.logger.debug("Verarbeite Seite %d/%d", page_num, len(reader.pages))
                
                try:
                    page_text = page.extract_text()
                    page_info = {
                        'page_number': page_num,
                        'text': page_text,
                        'char_count': len(page_text),
                        'word_count': len(page_text.split()) if page_text else 0,
                        'line_count': page_text.count('\n') if page_text else 0
                    }
                    page_texts.append(page_info)
                    full_text += page_text + "\n\n"  # Seitentrenner
                    
                except Exception as e:
                    self.logger.warning("⚠️ Fehler bei Seite %d: %s", page_num, str(e))
                    page_texts.append({
                        'page_number': page_num,
                        'text': "",
                        'char_count': 0,
                        'word_count': 0,
                        'line_count': 0,
                        'error': str(e)
                    })
            
            return {
                'success': True,
                'file_info': file_info,
                'pdf_metadata': pdf_metadata,
                'full_text': full_text,
                'page_texts': page_texts,
                'processing_timestamp': time.time()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Text-Extraktion fehlgeschlagen: {str(e)}"
            }
    
    def _analyze_unicode_characters(self, text: str) -> Dict[str, Any]:
        """Analysiert unsichtbare und verdächtige Unicode-Zeichen"""
        
        analysis_result = {
            'invisible_characters_found': {},
            'character_positions': {},
            'total_invisible_count': 0,
            'private_use_area_count': 0,
            'suspicious_patterns': [],
            'text_length': len(text),
            'invisibility_ratio': 0.0
        }
        
        if not text:
            return analysis_result
        
        # Analysiere bekannte unsichtbare Zeichen
        for char, name in self.invisible_chars.items():
            count = text.count(char)
            if count > 0:
                analysis_result['invisible_characters_found'][name] = count
                # Speichere erste 10 Positionen für Debugging
                positions = [i for i, c in enumerate(text) if c == char]
                analysis_result['character_positions'][name] = positions[:10]
        
        # Prüfe auf Private Use Area Zeichen (U+E000-U+F8FF)
        private_use_count = 0
        for char in text:
            code_point = ord(char)
            if 0xE000 <= code_point <= 0xF8FF:
                private_use_count += 1
        
        if private_use_count > 0:
            analysis_result['private_use_area_count'] = private_use_count
            analysis_result['invisible_characters_found']['Private Use Area Characters'] = private_use_count
        
        # Berechne Gesamtzahlen
        total_invisible = sum(analysis_result['invisible_characters_found'].values())
        analysis_result['total_invisible_count'] = total_invisible
        
        if len(text) > 0:
            analysis_result['invisibility_ratio'] = total_invisible / len(text)
        
        # Erkennung verdächtiger Muster
        if total_invisible > 50:
            analysis_result['suspicious_patterns'].append("Sehr hohe Anzahl unsichtbarer Zeichen")
        
        if analysis_result['invisibility_ratio'] > 0.001:  # >0.1%
            analysis_result['suspicious_patterns'].append("Hohe Dichte unsichtbarer Zeichen")
        
        if 'Zero-Width Space' in analysis_result['invisible_characters_found']:
            if analysis_result['invisible_characters_found']['Zero-Width Space'] > 20:
                analysis_result['suspicious_patterns'].append("Verdacht auf AI-Wasserzeichen (Zero-Width Spaces)")
        
        return analysis_result
    
    def _clean_text(self, text: str) -> str:
        """Bereinigt Text von unsichtbaren Zeichen für die Analyse"""
        if not text:
            return ""
        
        cleaned_text = text
        
        # Entferne bekannte unsichtbare Zeichen
        for char in self.invisible_chars.keys():
            cleaned_text = cleaned_text.replace(char, '')
        
        # Entferne Private Use Area Zeichen
        cleaned_text = ''.join(char for char in cleaned_text 
                              if not (0xE000 <= ord(char) <= 0xF8FF))
        
        # Normalisiere Whitespace
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # Multiple Spaces → Single Space
        cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text)  # Multiple Newlines → Double Newline
        
        return cleaned_text.strip()
    
    def _calculate_text_statistics(self, text: str) -> Dict[str, Any]:
        """Berechnet grundlegende Textstatistiken"""
        if not text:
            return {
                'total_characters': 0,
                'total_words': 0,
                'total_sentences': 0,
                'average_word_length': 0.0,
                'average_sentence_length': 0.0,
                'estimated_reading_time_minutes': 0
            }
        
        # Grundlegende Zählung
        total_chars = len(text)
        words = text.split()
        total_words = len(words)
        
        # Sätze zählen (vereinfacht)
        sentence_endings = re.findall(r'[.!?]+', text)
        total_sentences = len(sentence_endings)
        
        # Durchschnittswerte berechnen
        avg_word_length = sum(len(word.strip('.,!?;:')) for word in words) / total_words if total_words > 0 else 0
        avg_sentence_length = total_words / total_sentences if total_sentences > 0 else 0
        
        # Geschätzte Lesezeit (200 Wörter/Minute)
        reading_time = total_words / 200 if total_words > 0 else 0
        
        return {
            'total_characters': total_chars,
            'total_words': total_words, 
            'total_sentences': total_sentences,
            'average_word_length': round(avg_word_length, 2),
            'average_sentence_length': round(avg_sentence_length, 1),
            'estimated_reading_time_minutes': round(reading_time, 1)
        }
    
    def get_text_sample(self, text: str, max_length: int = 500) -> str:
        """Gibt einen Textausschnitt für Vorschau zurück"""
        if not text:
            return ""
        
        if len(text) <= max_length:
            return text
        
        # Schneide am Wortende ab
        truncated = text[:max_length]
        last_space = truncated.rfind(' ')
        if last_space > max_length * 0.8:  # Nur wenn nicht zu viel verloren geht
            truncated = truncated[:last_space]
        
        return truncated + "..."
