import json
import os
import sys

# Aggiungiamo la cartella superiore al path per importare monitor_acn
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from monitor_acn import get_page_ai_summary
except ImportError:
    import importlib.util
    spec = importlib.util.spec_from_file_location("monitor_acn", "monitor_acn.py")
    monitor_acn = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(monitor_acn)
    get_page_ai_summary = monitor_acn.get_page_ai_summary

history_path = "archive/history_faq_nis_aggiornamento_delle_informazioni.json"

with open(history_path, 'r', encoding='utf-8') as f:
    history = json.load(f)

if not history:
    print("Storico vuoto")
    sys.exit(0)

entry = history[0]
additions = entry.get("additions", [])
removals = entry.get("removals", [])
name = "FAQ NIS: Aggiornamento Delle Informazioni"

print(f"Generazione summary per {name}...")
ai_summary = get_page_ai_summary(name, additions, removals)

print("\n--- AI SUMMARY ---")
print(ai_summary)
print("------------------\n")

if ai_summary:
    entry["ai_summary"] = ai_summary
    with open(history_path, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2)
    print("File storico aggiornato con successo.")
else:
    print("Nessun summary generato.")
