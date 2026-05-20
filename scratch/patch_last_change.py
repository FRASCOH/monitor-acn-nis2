import json

status_path = "status.json"
with open(status_path, 'r', encoding='utf-8') as f:
    status = json.load(f)

for page in status.get("pages", []):
    if not page.get("has_changes") and page.get("status") == "Nessuna modifica":
        page["last_change_date"] = None
        print(f"Azzerato last_change_date per {page['name']}")

with open(status_path, 'w', encoding='utf-8') as f:
    json.dump(status, f, indent=2)

print("Patch completato.")
