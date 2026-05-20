import json

status_path = "status.json"
with open(status_path, 'r', encoding='utf-8') as f:
    status = json.load(f)

for page in status.get("pages", []):
    if page.get("id") == "global_header":
        page["has_changes"] = True
        page["status"] = "Modificato"
        page["additions"] = ["Relazioni Internazionali e Affari Europei"]
        page["removals"] = []
        page["summary"] = "+1 aggiunte, -0 rimozioni"
        page["ai_summary"] = "La voce di menu è stata aggiornata in 'Relazioni Internazionali e Affari Europei'."
        page["last_change_date"] = "20/05/2026 15:16"
        print("global_header aggiornato in status.json")

with open(status_path, 'w', encoding='utf-8') as f:
    json.dump(status, f, indent=2)
print("Fatto.")
