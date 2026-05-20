import json

history_path = "archive/history_faq_nis_aggiornamento_delle_informazioni.json"
ai_summary = "Sono stati corretti refusi testuali minori sui criteri di rilevanza dei fornitori e sono state aggiunte nuove FAQ (dalla FRN.5 alla FRN.10) per chiarire la gestione di fornitori esteri, subforniture e l'inserimento di codici CPV multipli."

with open(history_path, 'r', encoding='utf-8') as f:
    history = json.load(f)

if history:
    history[0]["ai_summary"] = ai_summary
    with open(history_path, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2)
    print("Storico aggiornato!")
