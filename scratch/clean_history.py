import json
import os
import glob
from datetime import datetime

archive_dir = "archive"
files = glob.glob(os.path.join(archive_dir, "history_*.json"))

for file_path in files:
    filename = os.path.basename(file_path)
    
    # Per history_faq_nis_aggiornamento_delle_informazioni.json non toccare le cose vecchie, ma magari ha l'entry delle 15:04
    # Voglio rimuovere tutte le entry delle 15:04 e 15:16
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            history = json.load(f)
        except:
            history = []
    
    if filename == "history_global_header.json":
        # Sostituisci con l'entry personalizzata dell'utente
        history = [
            {
                "timestamp": "2026-05-20T15:16:00+02:00",
                "date_formatted": "20/05/2026 15:16",
                "additions": [
                    "Relazioni Internazionali e Affari Europei"
                ],
                "removals": [],
                "ai_summary": "La voce di menu è stata aggiornata in 'Relazioni Internazionali e Affari Europei'."
            }
        ]
    elif filename == "history_global_footer.json":
        # Per il footer, svuotiamo la history dato che è stato creato solo per refactoring
        history = []
    else:
        # Per tutti gli altri, filtriamo le esecuzioni di oggi alle 15:04 e 15:16
        filtered = []
        for entry in history:
            ts = entry.get("timestamp", "")
            if ts.startswith("2026-05-20T15:04") or ts.startswith("2026-05-20T15:16"):
                continue
            filtered.append(entry)
        history = filtered
        
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

print("Pulizia storico completata con successo.")
