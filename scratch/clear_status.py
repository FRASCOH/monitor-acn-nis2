import json

status_path = "status.json"
with open(status_path, 'r', encoding='utf-8') as f:
    status = json.load(f)

for page in status.get("pages", []):
    name = page.get("name")
    if name not in ["FAQ NIS: Aggiornamento Delle Informazioni", "Header Globale ACN", "Footer Globale ACN"]:
        page["has_changes"] = False
        page["status"] = "Nessuna modifica"
        page["additions"] = []
        page["removals"] = []
        page["summary"] = "Nessuna modifica"
        page.pop("ai_summary", None)

with open(status_path, 'w', encoding='utf-8') as f:
    json.dump(status, f, indent=2)
print("status.json pulito dai falsi positivi.")
