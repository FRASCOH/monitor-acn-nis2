import json
import glob
import os

# Pulizia status.json
with open("status.json", "r", encoding="utf-8") as f:
    status = json.load(f)

for page in status.get("pages", []):
    name = page.get("name")
    if name == "Footer Globale ACN":
        page["has_changes"] = False
        page["status"] = "Nessuna modifica"
        page["additions"] = []
        page["removals"] = []
        page["summary"] = "Nessuna modifica"
        page.pop("ai_summary", None)
        page["last_change_date"] = None

with open("status.json", "w", encoding="utf-8") as f:
    json.dump(status, f, indent=2)

# Pulizia page_hash_*.json
files = glob.glob("page_hash_*.json")
for file_path in files:
    if "faq_nis_aggiornamento_delle_informazioni" in file_path or "global_header" in file_path:
        continue
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    data["last_change_date"] = None
    data["last_additions"] = []
    data["last_removals"] = []
    data["ai_summary"] = ""
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

print("Pulizia profonda completata.")
