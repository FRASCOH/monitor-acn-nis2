import json

status_path = "status.json"
with open(status_path, 'r', encoding='utf-8') as f:
    status = json.load(f)

ai_summary = "Sono stati corretti refusi testuali minori sui criteri di rilevanza dei fornitori e sono state aggiunte nuove FAQ (dalla FRN.5 alla FRN.10) per chiarire la gestione di fornitori esteri, subforniture e l'inserimento di codici CPV multipli."

for page in status.get("pages", []):
    if page.get("name") == "FAQ NIS: Aggiornamento Delle Informazioni":
        page["ai_summary"] = ai_summary
        page["has_changes"] = True # Set it to true just so the button appears for testing
        print("Pagina aggiornata in status.json")

with open(status_path, 'w', encoding='utf-8') as f:
    json.dump(status, f, indent=2)
print("status.json salvato.")
