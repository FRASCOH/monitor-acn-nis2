import json
import os
import glob

# 1. Clean status.json
if os.path.exists('status.json'):
    with open('status.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for page in data['pages']:
        page['status'] = "Nessuna modifica"
        page['has_changes'] = False
        page['has_history'] = False
        page['summary'] = ""
        page['additions'] = []
        page['removals'] = []
        if 'last_change_date' in page:
            del page['last_change_date']
            
    with open('status.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("status.json cleaned.")

# 2. Clean all page_hash_*.json files
for hash_file in glob.glob('page_hash_*.json'):
    with open(hash_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    data['last_change_date'] = None
    data['last_additions'] = []
    data['last_removals'] = []
    
    with open(hash_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
print("Page hash files cleaned.")
