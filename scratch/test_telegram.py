import os
import sys
import requests
import re
from datetime import datetime

# Aggiungiamo la root directory al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from monitor_acn import to_telegram_html, send_telegram_notification
    print("✅ Importazione di monitor_acn riuscita!")
except ImportError as e:
    print(f"❌ Errore durante l'importazione di monitor_acn: {e}")
    sys.exit(1)

# Definiamo dei dati fittizi
mock_changes = [
    {
        "id": "atti_generali",
        "name": "ACN Atti Generali (Test)",
        "url": "https://www.acn.gov.it/portale/atti-generali",
        "status": "Modificato",
        "summary": "+1 aggiunta, -0 rimozioni",
        "ai_summary": "Test di notifica: Inserito un documento di prova per la verifica del bot Telegram."
    }
]

mock_ai_summary = """
*Test di notifica*: Questa è una notifica di test inviata per verificare la corretta configurazione del bot Telegram.
Tutto sembra funzionare correttamente!
"""

def run_test():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("❌ Variabili d'ambiente TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID mancanti.")
        print("Esegui lo script definendo le variabili d'ambiente nel terminale.")
        return
        
    print(f"\n🚀 Invio notifica di test su Telegram...")
    print(f"Bot Token: {token[:6]}...{token[-6:] if len(token) > 12 else ''}")
    print(f"Chat ID: {chat_id}")
    
    send_telegram_notification(mock_changes, mock_ai_summary)

if __name__ == "__main__":
    run_test()
