import json

with open("archive/history_faq_nis_aggiornamento_delle_informazioni.json", "r") as f:
    history = json.load(f)

latest = history[0]

with open("status.json", "r") as f:
    status = json.load(f)

for page in status["pages"]:
    if page["id"] == "faq_nis_aggiornamento_delle_informazioni":
        page["additions"] = latest.get("additions", [])
        page["removals"] = latest.get("removals", [])
        page["ai_summary"] = latest.get("ai_summary", "")
        page["summary"] = f"+{len(page['additions'])} aggiunte, -{len(page['removals'])} rimozioni"
        page["last_change_date"] = latest.get("date_formatted", "15/05/2026 10:12")
        print("Sincronizzato")
        break

with open("status.json", "w") as f:
    json.dump(status, f, indent=2)
