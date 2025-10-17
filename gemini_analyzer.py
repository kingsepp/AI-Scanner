import json
import time
import logging
import math
from typing import Dict, Any, List, Optional
from google import genai

class GeminiAnalyzer:
    """
    Erweiterte Gemini API Integration für KI-Texterkennung
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = None
        self.logger = logging.getLogger(__name__)
        
        # Konfiguration
        self.chunk_size = 8000      # Zeichen pro Chunk
        self.chunk_overlap = 200    # Overlap zwischen Chunks
        self.max_retries = 3
        self.retry_delay_base = 2
        self.model_name = "gemini-2.0-flash"
        
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialisiert Gemini API Client"""
        try:
            self.client = genai.Client(api_key=self.api_key)
            self.logger.info("✅ Gemini API Client initialisiert")
        except Exception as e:
            error_msg = f"Gemini Client Initialisierung fehlgeschlagen: {str(e)}"
            self.logger.error("❌ %s", error_msg)
            raise ValueError(error_msg)
    
    def test_connection(self) -> Dict[str, Any]:
        """Testet die API-Verbindung"""
        try:
            test_text = "Dies ist ein Test-Text zur Überprüfung der API-Verbindung."
            
            start_time = time.time()
            result = self._analyze_single_chunk(test_text)
            end_time = time.time()
            
            if result.get('success'):
                return {
                    'success': True,
                    'message': '✅ API-Verbindung erfolgreich',
                    'response_time': round(end_time - start_time, 2),
                    'test_classification': result.get('is_ai_generated', 'unknown')
                }
            else:
                return {
                    'success': False,
                    'message': f"❌ API-Test fehlgeschlagen: {result.get('error', 'Unbekannter Fehler')}",
                    'response_time': None
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f"❌ Verbindungstest fehlgeschlagen: {str(e)}",
                'response_time': None
            }
    
    def analyze_document(self, text: str, unicode_analysis: Dict = None, progress_callback=None) -> Dict[str, Any]:
        """
        Analysiert komplettes Dokument mit Chunk-basierter Verarbeitung
        
        Args:
            text: Zu analysierender Text
            unicode_analysis: Ergebnisse der Unicode-Analyse
            progress_callback: Callback für Progress-Updates
            
        Returns:
            Kombinierte Analyse-Ergebnisse
        """
        try:
            self.logger.info("🔍 Starte Dokument-Analyse (%d Zeichen)", len(text))
            
            if len(text) <= self.chunk_size:
                # Kurzer Text - direkte Analyse
                if progress_callback:
                    progress_callback("Analysiere Dokument...")
                
                result = self._analyze_single_chunk(text, unicode_analysis)
                result['analysis_method'] = 'single_chunk'
                return result
            
            else:
                # Langer Text - Chunk-basierte Analyse
                return self._analyze_with_chunks(text, unicode_analysis, progress_callback)
                
        except Exception as e:
            error_msg = f"Dokument-Analyse fehlgeschlagen: {str(e)}"
            self.logger.error("❌ %s", error_msg)
            return {
                'success': False,
                'error': error_msg,
                'confidence_score': 0.0,
                'is_ai_generated': False
            }
    
    def _analyze_with_chunks(self, text: str, unicode_analysis: Dict = None, progress_callback=None) -> Dict[str, Any]:
        """Chunk-basierte Analyse mit Overlap"""
        
        # Erstelle überlappende Chunks
        chunks = self._create_overlapping_chunks(text)
        total_chunks = len(chunks)
        
        self.logger.info("📄 Text in %d überlappende Chunks aufgeteilt", total_chunks)
        
        chunk_results = []
        
        for i, chunk in enumerate(chunks):
            if progress_callback:
                progress_callback(f"Analysiere Chunk {i+1}/{total_chunks}...")
            
            self.logger.info("🔍 Analysiere Chunk %d/%d", i+1, total_chunks)
            
            try:
                # Nur für ersten Chunk Unicode-Info übergeben
                chunk_unicode_info = unicode_analysis if i == 0 else None
                result = self._analyze_single_chunk(chunk, chunk_unicode_info)
                
                if result.get('success'):
                    chunk_results.append(result)
                else:
                    self.logger.warning("⚠️ Chunk %d Analyse fehlgeschlagen: %s", 
                                      i+1, result.get('error', 'Unbekannt'))
                    
            except Exception as e:
                self.logger.warning("⚠️ Chunk %d Fehler: %s", i+1, str(e))
                continue
        
        if not chunk_results:
            return {
                'success': False,
                'error': 'Keine erfolgreichen Chunk-Analysen',
                'confidence_score': 0.0,
                'is_ai_generated': False
            }
        
        # Aggregiere Ergebnisse
        if progress_callback:
            progress_callback("Ergebnisse werden zusammengeführt...")
        
        return self._aggregate_chunk_results(chunk_results, text)
    
    def _create_overlapping_chunks(self, text: str) -> List[str]:
        """Erstellt überlappende Text-Chunks"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunk = text[start:end]
            chunks.append(chunk)
            
            if end >= len(text):
                break
            
            # Nächster Chunk beginnt mit Overlap
            start = end - self.chunk_overlap
        
        return chunks
    
    def _analyze_single_chunk(self, text: str, unicode_analysis: Dict = None) -> Dict[str, Any]:
        """Analysiert einzelnen Text-Chunk"""
        try:
            # Erstelle optimierten Prompt
            prompt = self._create_analysis_prompt(text, unicode_analysis)
            
            # API-Call mit Retry-Logic
            response = self._make_robust_api_call(prompt)
            
            # Parse und validiere Response
            result = self._parse_api_response(response.text)
            
            # Füge Metadaten hinzu
            result.update({
                'success': True,
                'text_length': len(text),
                'analysis_timestamp': time.time(),
                'model_used': self.model_name
            })
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'confidence_score': 0.0,
                'is_ai_generated': False
            }
    
    def _create_analysis_prompt(self, text: str, unicode_analysis: Dict = None) -> str:
        """Erstellt optimierten Analyse-Prompt"""
        
        prompt = f"""Du bist ein spezialisierter KI-Detektor für akademische Texte mit Expertise in der Erkennung maschinell generierter vs. menschlich verfasster wissenschaftlicher Arbeiten.

AUFGABE: Analysiere den folgenden Textabschnitt und klassifiziere ihn als KI-generiert oder menschlich verfasst.

ANALYSIERE FOLGENDE INDIKATOREN:
1. Satzlängenverteilung: Uniforme Längen (KI-typisch) vs. natürliche Variation (menschlich)
2. Transition Words: Übermäßiger Gebrauch von "darüber hinaus", "zusammenfassend", "furthermore", "however"
3. Strukturierung: Formelhafte Organisation vs. natürlicher Gedankenfluss
4. Fehlerpattern: Fehlen typischer menschlicher Inkonsistenzen oder Schreibfehler
5. Argumentation: Perfekte Konsistenz (KI) vs. menschliche Gedankensprünge
6. AI-Phrasen: Typische Konstruktionen wie "es ist wichtig zu beachten", "in diesem Zusammenhang"
7. Emotionalität: Neutrale Sachlichkeit (KI) vs. persönlicher Ausdruck (menschlich)
"""
        
        # Füge Unicode-Analyse hinzu wenn verfügbar
        if unicode_analysis and unicode_analysis.get('total_invisible_count', 0) > 0:
            prompt += f"""
ZUSÄTZLICHE INFORMATION - UNSICHTBARE ZEICHEN ERKANNT:
Der Text enthält {unicode_analysis['total_invisible_count']} unsichtbare Unicode-Zeichen:
{json.dumps(unicode_analysis.get('invisible_characters_found', {}), indent=2, ensure_ascii=False)}

Dies ist ein STARKER Indikator für KI-Generierung (Wasserzeichen-System).
Gewichte diese Information hoch in deiner Analyse.
"""
        
        prompt += f"""
ANTWORTE AUSSCHLIESSLICH im folgenden JSON-Format (keine zusätzlichen Kommentare):
{
    "confidence_score": 0.0-1.0,
    "is_ai_generated": true/false,
    "ai_probability": 0.0-1.0,
    "human_probability": 0.0-1.0,
    "reasoning": "Detaillierte Begründung der Klassifikation in 2-3 Sätzen",
    "specific_indicators": ["Liste der erkannten Indikatoren"],
    "suspicious_phrases": ["Verdächtige Phrasen falls gefunden"],
    "text_metrics": {
        "sentence_uniformity": "low/medium/high",
        "vocabulary_complexity": "low/medium/high",
        "emotional_expression": "low/medium/high"
    }
}

ZU ANALYSIERENDER TEXT:
{text[:self.chunk_size]}
"""
        
        return prompt
    
    def _make_robust_api_call(self, prompt: str) -> Any:
        """Robuster API-Call mit exponential backoff"""
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                
                if response and response.text:
                    return response
                else:
                    raise ValueError("Leere API-Response")
                    
            except Exception as e:
                wait_time = self.retry_delay_base ** attempt
                self.logger.warning("⚠️ API-Call Versuch %d/%d fehlgeschlagen: %s", 
                                  attempt + 1, self.max_retries, str(e))
                
                if attempt < self.max_retries - 1:
                    self.logger.info("⏳ Warte %ds vor erneutem Versuch...", wait_time)
                    time.sleep(wait_time)
                else:
                    raise Exception(f"API-Call nach {self.max_retries} Versuchen fehlgeschlagen: {str(e)}")
    
    def _parse_api_response(self, response_text: str) -> Dict[str, Any]:
        """Parst und validiert API-Response"""
        try:
            # Extrahiere JSON aus Response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end <= json_start:
                raise ValueError("Keine gültige JSON-Struktur gefunden")
            
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
            
            # Validiere Pflichtfelder
            required_fields = ['confidence_score', 'is_ai_generated', 'ai_probability']
            missing_fields = [field for field in required_fields if field not in result]
            
            if missing_fields:
                raise ValueError(f"Fehlende Pflichtfelder: {missing_fields}")
            
            # Normalisiere numerische Werte
            result['confidence_score'] = max(0.0, min(1.0, float(result.get('confidence_score', 0.5))))
            result['ai_probability'] = max(0.0, min(1.0, float(result.get('ai_probability', 0.5))))
            result['human_probability'] = max(0.0, min(1.0, float(result.get('human_probability', 1 - result['ai_probability']))))
            
            # Stelle sicher, dass Wahrscheinlichkeiten sich zu 1.0 addieren
            total_prob = result['ai_probability'] + result['human_probability']
            if abs(total_prob - 1.0) > 0.01:
                result['human_probability'] = 1.0 - result['ai_probability']
            
            return result
            
        except json.JSONDecodeError as e:
            self.logger.error("❌ JSON-Parsing Fehler: %s", str(e))
            self.logger.debug("Response-Text: %s", response_text[:500])
            raise ValueError(f"Ungültige JSON in API-Response: {str(e)}")
            
        except Exception as e:
            self.logger.error("❌ Response-Parsing Fehler: %s", str(e))
            raise ValueError(f"Response-Validierung fehlgeschlagen: {str(e)}")
    
    def _aggregate_chunk_results(self, chunk_results: List[Dict], original_text: str) -> Dict[str, Any]:
        """Aggregiert Chunk-Ergebnisse mit gewichtetem Durchschnitt"""
        
        if not chunk_results:
            return {'success': False, 'error': 'Keine Chunk-Ergebnisse zum Aggregieren'}
        
        # Extrahiere Werte
        confidences = [r.get('confidence_score', 0.0) for r in chunk_results]
        ai_probs = [r.get('ai_probability', 0.5) for r in chunk_results]
        
        # Gewichteter Durchschnitt basierend auf Confidence
        total_weight = sum(confidences)
        if total_weight > 0:
            weighted_ai_prob = sum(ai_prob * conf for ai_prob, conf in zip(ai_probs, confidences)) / total_weight
            avg_confidence = sum(confidences) / len(confidences)
        else:
            weighted_ai_prob = sum(ai_probs) / len(ai_probs)
            avg_confidence = 0.5
        
        # Sammle alle Indikatoren
        all_indicators = []
        all_suspicious_phrases = []
        
        for result in chunk_results:
            indicators = result.get('specific_indicators', [])
            if isinstance(indicators, list):
                all_indicators.extend(indicators)
            
            phrases = result.get('suspicious_phrases', [])
            if isinstance(phrases, list):
                all_suspicious_phrases.extend(phrases)
        
        # Entferne Duplikate und behalte häufigste
        unique_indicators = list(dict.fromkeys(all_indicators))[:10]
        unique_suspicious = list(dict.fromkeys(all_suspicious_phrases))[:5]
        
        # Kombiniere Reasoning
        reasoning_parts = [r.get('reasoning', '') for r in chunk_results if r.get('reasoning')]
        combined_reasoning = f"Kombinierte Analyse von {len(chunk_results)} Textabschnitten zeigt konsistente Muster. {reasoning_parts[0] if reasoning_parts else 'Weitere Details in den Indikatoren.'}"
        
        return {
            'success': True,
            'confidence_score': avg_confidence,
            'is_ai_generated': weighted_ai_prob > 0.5,
            'ai_probability': weighted_ai_prob,
            'human_probability': 1.0 - weighted_ai_prob,
            'reasoning': combined_reasoning,
            'specific_indicators': unique_indicators,
            'suspicious_phrases': unique_suspicious,
            'text_metrics': self._aggregate_text_metrics(chunk_results),
            'analysis_summary': {
                'total_chunks_analyzed': len(chunk_results),
                'successful_chunks': len([r for r in chunk_results if r.get('success')]),
                'text_length': len(original_text),
                'analysis_method': 'chunked_with_overlap',
                'average_chunk_confidence': avg_confidence
            },
            'analysis_timestamp': time.time(),
            'model_used': self.model_name
        }
    
    def _aggregate_text_metrics(self, chunk_results: List[Dict]) -> Dict[str, str]:
        """Aggregiert Text-Metriken aus Chunks"""
        
        metrics = {
            'sentence_uniformity': [],
            'vocabulary_complexity': [],
            'emotional_expression': []
        }
        
        # Sammle alle Metrik-Werte
        for result in chunk_results:
            text_metrics = result.get('text_metrics', {})
            for metric_name in metrics.keys():
                value = text_metrics.get(metric_name, 'medium')
                if value in ['low', 'medium', 'high']:
                    metrics[metric_name].append(value)
        
        # Bestimme häufigste Werte
        aggregated = {}
        for metric_name, values in metrics.items():
            if values:
                # Zähle Vorkommen
                counts = {'low': 0, 'medium': 0, 'high': 0}
                for value in values:
                    counts[value] += 1
                
                # Häufigster Wert
                aggregated[metric_name] = max(counts, key=counts.get)
            else:
                aggregated[metric_name] = 'medium'
        
        return aggregated
