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

import monitor_acn
from zoneinfo import ZoneInfo

# Sovrascriviamo get_now in monitor_acn per mostrare la data specificata nel test
def mock_get_now():
    return datetime(2026, 5, 15, 10, 12, tzinfo=ZoneInfo("Europe/Rome"))
monitor_acn.get_now = mock_get_now

# Definiamo dei dati fittizi basati sulla richiesta dell'utente
mock_changes = [
    {
        "id": "faq_nis_categorizzazione",
        "name": "FAQ NIS: Categorizzazione",
        "url": "https://www.acn.gov.it/portale/faq/nis/categorizzazione",
        "status": "Modificato",
        "summary": "+29 aggiunte, -5 rimozioni",
        "ai_summary": "Sono stati corretti refusi testuali minori sui criteri di rilevanza dei fornitori e sono state aggiunte nuove FAQ (dalla FRN.5 alla FRN.10) per chiarire la gestione di fornitori esteri, subforniture e l'inserimento di codici CPV multipli."
    }
]

mock_ai_summary = """
Sono stati corretti refusi testuali minori sui criteri di rilevanza dei fornitori e sono state aggiunte nuove FAQ (dalla FRN.5 alla FRN.10) per chiarire la gestione di fornitori esteri, subforniture e l'inserimento di codici CPV multipli.
"""

def run_test():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("❌ Variabili d'ambiente TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID mancanti.")
        print("Esegui lo script definendo le variabili d'ambiente nel terminale.")
        return
        
    print(f"\n🚀 Invio notifica di test personalizzata su Telegram...")
    print(f"Bot Token: {token[:6]}...{token[-6:] if len(token) > 12 else ''}")
    print(f"Chat ID: {chat_id}")
    
    send_telegram_notification(mock_changes, mock_ai_summary)

if __name__ == "__main__":
    run_test()
