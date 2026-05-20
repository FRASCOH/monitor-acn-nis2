import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
import hashlib
from monitor_acn import get_page_content, clean_html, load_state, PAGES

for page in PAGES:
    url = page["url"]
    page_id = page["id"]
    print(f"Rebasing {page_id}...")
    
    paths = {
        "hash": f"page_hash_{page_id}.json",
        "content": f"page_content_{page_id}.txt"
    }
    
    state = load_state(paths)
    if not state["hash"]: continue
    
    raw_content = get_page_content(url)
    if not raw_content: continue
    
    current_text = clean_html(raw_content)
    current_hash = hashlib.sha256(current_text.encode('utf-8')).hexdigest()
    
    # Update only the hash and content, leave the rest
    with open(paths["content"], "w", encoding='utf-8') as f:
        f.write(current_text)
        
    with open(paths["hash"], "r") as f:
        data = json.load(f)
        
    data["hash"] = current_hash
    with open(paths["hash"], "w") as f:
        json.dump(data, f, indent=2)

print("Rebase completato.")
