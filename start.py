#!/usr/bin/env python3
import sys
import os
import logging
from pathlib import Path

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ki_scanner.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def check_python_version():
    """Überprüft Python-Version (mindestens 3.8 erforderlich)"""
    if sys.version_info < (3, 8):
        logger.error("❌ Python 3.8+ erforderlich. Aktuelle Version: %s", sys.version)
        return False
    logger.info("✅ Python-Version: %s", sys.version.split()[0])
    return True

def check_dependencies():
    """Überprüft alle erforderlichen Dependencies"""
    required_packages = [
        ('google.genai', 'google-genai'),
        ('pypdf', 'pypdf'),
        ('requests', 'requests')
    ]
    
    missing_packages = []
    
    for import_name, package_name in required_packages:
        try:
            __import__(import_name)
            logger.info("✅ %s verfügbar", package_name)
        except ImportError:
            missing_packages.append(package_name)
            logger.error("❌ %s fehlt", package_name)
    
    # Prüfe Standard-Bibliotheken
    standard_libs = ['tkinter', 'threading', 'json', 'logging', 'pathlib']
    for lib in standard_libs:
        try:
            __import__(lib)
        except ImportError:
            logger.error("❌ Standard-Bibliothek '%s' nicht verfügbar", lib)
            return False
    
    if missing_packages:
        logger.error("Installiere fehlende Packages mit:")
        logger.error("pip install %s", " ".join(missing_packages))
        return False
    
    return True

def check_project_files():
    """Überprüft, ob alle Projektdateien vorhanden sind"""
    required_files = [
        'main.py',
        'pdf_processor.py', 
        'gemini_analyzer.py'
    ]
    
    missing_files = []
    for file_name in required_files:
        if not Path(file_name).exists():
            missing_files.append(file_name)
            logger.error("❌ Datei '%s' nicht gefunden", file_name)
        else:
            logger.info("✅ %s vorhanden", file_name)
    
    if missing_files:
        logger.error("Fehlende Dateien müssen erstellt werden: %s", missing_files)
        return False
    
    return True

def main():
    """Hauptfunktion des Launchers"""
    logger.info("🚀 KI-Scanner wird gestartet...")
    
    # Systemprüfungen
    if not check_python_version():
        input("Drücke Enter zum Beenden...")
        sys.exit(1)
    
    if not check_dependencies():
        input("Drücke Enter zum Beenden...")
        sys.exit(1)
    
    if not check_project_files():
        input("Drücke Enter zum Beenden...")
        sys.exit(1)
    
    try:
        # Importiere und starte Hauptanwendung
        logger.info("✅ Alle Prüfungen erfolgreich - starte GUI...")
        from main import KIScannerApp
        
        app = KIScannerApp()
        logger.info("🎯 GUI initialisiert - Anwendung läuft")
        app.run()
        
    except Exception as e:
        logger.error("❌ Kritischer Fehler beim Start: %s", str(e))
        logger.exception("Vollständiger Error-Stack:")
        input("Drücke Enter zum Beenden...")
        sys.exit(1)
    
    logger.info("👋 KI-Scanner wurde beendet")

if __name__ == "__main__":
    main()
