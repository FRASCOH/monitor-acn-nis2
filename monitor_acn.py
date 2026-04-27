import requests
import hashlib
import json
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import difflib
import re
from urllib.parse import urljoin

# Configurazione monitoraggio
PAGES_TO_MONITOR = [
    {
        "name": "ACN Atti Generali",
        "url": "https://www.acn.gov.it/portale/atti-generali",
        "id": "atti_generali"
    },
    {
        "name": "FAQ NIS (Parent)",
        "url": "https://www.acn.gov.it/portale/faq/nis",
        "id": "faq_nis_parent",
        "discover_subpages": True,
        "subpage_pattern": r'/portale/faq/nis/[\w-]+'
    },
    {
        "name": "NIS Home",
        "url": "https://www.acn.gov.it/portale/nis",
        "id": "nis_home",
        "discover_subpages": True,
        "subpage_pattern": r'/portale/nis/[\w-]+'
    }
]

# File di stato (ora gestiti per ID)
def get_state_paths(page_id):
    return {
        "hash": f"page_hash_{page_id}.json",
        "content": f"page_content_{page_id}.txt"
    }

def get_page_content(url):
    """Scarica il contenuto della pagina"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=30, headers=headers)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Errore scaricando {url}: {e}")
        return None

def clean_html(html):
    """Estrae il testo visibile dalla pagina HTML"""
    # Rimuovi script e style
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    # Rimuovi commenti HTML
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    # Rimuovi tag HTML ma mantieni il contenuto
    html = re.sub(r'<[^>]+>', '\n', html)
    # Decodifica entità HTML comuni
    html = html.replace('&nbsp;', ' ')
    html = html.replace('&amp;', '&')
    html = html.replace('&lt;', '<')
    html = html.replace('&gt;', '>')
    # Rimuovi linee vuote multiple
    html = re.sub(r'\n\s*\n', '\n', html)
    # Rimuovi spazi multipli
    html = re.sub(r' +', ' ', html)
    return html.strip()

def discover_links(html, base_url, pattern):
    """Trova link che corrispondono a un pattern"""
    links = re.findall(f'href="({pattern})"', html)
    # Rendi i link assoluti e rimuovi duplicati
    absolute_links = set()
    for link in links:
        absolute_links.add(urljoin(base_url, link))
    return list(absolute_links)

def load_state(paths):
    """Carica hash e contenuto precedente"""
    old_hash, last_check = None, None
    old_content = None
    
    if os.path.exists(paths["hash"]):
        try:
            with open(paths["hash"], 'r') as f:
                data = json.load(f)
                old_hash = data.get('hash')
                last_check = data.get('last_check')
        except: pass
        
    if os.path.exists(paths["content"]):
        try:
            with open(paths["content"], 'r', encoding='utf-8') as f:
                old_content = f.read()
        except: pass
        
    return old_hash, old_content, last_check

def save_state(paths, content_hash, content):
    """Salva hash e contenuto attuale"""
    with open(paths["hash"], 'w') as f:
        json.dump({
            'hash': content_hash,
            'last_check': datetime.now().isoformat()
        }, f, indent=2)
    
    with open(paths["content"], 'w', encoding='utf-8') as f:
        f.write(content)

def generate_detailed_diff(old_content, new_content):
    """Genera un diff dettagliato tra vecchio e nuovo contenuto"""
    old_lines = [line.strip() for line in old_content.split('\n') if line.strip()]
    new_lines = [line.strip() for line in new_content.split('\n') if line.strip()]
    
    diff = list(difflib.unified_diff(old_lines, new_lines, lineterm='', n=0))
    
    additions = []
    removals = []
    
    for line in diff:
        if line.startswith('+++') or line.startswith('---') or line.startswith('@@'):
            continue
        if line.startswith('+'):
            additions.append(line[1:].strip())
        elif line.startswith('-'):
            removals.append(line[1:].strip())
    
    return additions, removals

def generate_html_report(page_name, additions, removals, url):
    """Genera il report HTML delle modifiche"""
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }}
            h2 {{ color: #2c3e50; }}
            .summary {{ background: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .section {{ margin: 20px 0; }}
            .addition {{ background: #d4edda; border-left: 4px solid #28a745; padding: 10px; margin: 5px 0; }}
            .removal {{ background: #f8d7da; border-left: 4px solid #dc3545; padding: 10px; margin: 5px 0; }}
            .no-changes {{ background: #d1ecf1; border-left: 4px solid #17a2b8; padding: 15px; margin: 20px 0; }}
            .timestamp {{ color: #666; font-size: 0.9em; }}
            a {{ color: #3498db; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <h2>🔔 Report Modifiche - {page_name}</h2>
        <p><strong>Pagina monitorata:</strong> <a href="{url}">{url}</a></p>
        <p class="timestamp">Report generato il {datetime.now().strftime('%d/%m/%Y alle %H:%M')}</p>
    """
    
    total_changes = len(additions) + len(removals)
    
    if total_changes == 0:
        html += """
        <div class="no-changes">
            <strong>✅ Nessuna modifica rilevata</strong>
            <p>La pagina non ha subito modifiche dall'ultimo controllo.</p>
        </div>
        """
    else:
        html += f"""
        <div class="summary">
            <strong>📊 Riepilogo modifiche:</strong>
            <ul>
                <li><strong>{len(additions)}</strong> aggiunte/modifiche</li>
                <li><strong>{len(removals)}</strong> rimozioni</li>
                <li><strong>Totale: {total_changes}</strong> modifiche rilevate</li>
            </ul>
        </div>
        """
        
        if additions:
            html += """<div class="section"><h3>✅ Contenuti Aggiunti o Modificati</h3>"""
            for item in additions[:50]:
                html += f'<div class="addition">{item}</div>\n'
            if len(additions) > 50:
                html += f'<p><em>... e altre {len(additions) - 50} aggiunte</em></p>'
            html += "</div>"
        
        if removals:
            html += """<div class="section"><h3>❌ Contenuti Rimossi</h3>"""
            for item in removals[:50]:
                html += f'<div class="removal">{item}</div>\n'
            if len(removals) > 50:
                html += f'<p><em>... e altre {len(removals) - 50} rimozioni</em></p>'
            html += "</div>"
    
    html += f"""
        <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
        <p class="timestamp">Sistema di monitoraggio automatico ACN - {page_name}</p>
    </body>
    </html>
    """
    return html

def send_email(html_content, page_name, has_changes):
    """Invia email con il report"""
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = os.environ.get("EMAIL_SENDER")
    sender_password = os.environ.get("EMAIL_PASSWORD")
    receiver_emails = os.environ.get("EMAIL_RECEIVER")
    
    if not all([sender_email, sender_password, receiver_emails]):
        print(f"[{page_name}] Variabili d'ambiente email non configurate")
        return
    
    # Gestisci destinatari multipli (separati da virgola)
    dest_list = [email.strip() for email in receiver_emails.split(',')]
    
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = ", ".join(dest_list)
    
    status = "MODIFICHE RILEVATE" if has_changes else "Nessuna modifica"
    message["Subject"] = f"🔔 {status} - {page_name} - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    
    message.attach(MIMEText(html_content, "html"))
    
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(message)
        print(f"[{page_name}] Email inviata a {receiver_email}")
    except Exception as e:
        print(f"[{page_name}] Errore invio email: {e}")

def monitor_page(page_config):
    name = page_config["name"]
    url = page_config["url"]
    page_id = page_config["id"]
    
    print(f"\n--- Monitoraggio: {name} ---")
    print(f"URL: {url}")
    
    raw_content = get_page_content(url)
    if not raw_content:
        return [] # Nessun nuovo link scoperto se il download fallisce

    # Scoperta sub-pagine (se abilitata)
    discovered_urls = []
    if page_config.get("discover_subpages") and page_config.get("subpage_pattern"):
        discovered_urls = discover_links(raw_content, url, page_config["subpage_pattern"])
        print(f"Trovate {len(discovered_urls)} sub-pagine potenziali.")

    current_text = clean_html(raw_content)
    current_hash = hashlib.sha256(current_text.encode('utf-8')).hexdigest()
    
    paths = get_state_paths(page_id)
    old_hash, old_text, last_check = load_state(paths)
    
    has_changes = False
    additions, removals = [], []
    
    if old_hash and old_text:
        if current_hash != old_hash:
            print(f"⚠️ MODIFICHE RILEVATE per {name}!")
            has_changes = True
            additions, removals = generate_detailed_diff(old_text, current_text)
        else:
            print(f"✅ Nessuna modifica per {name}")
    else:
        print(f"📝 Prima esecuzione per {name} - salvataggio stato")
        save_state(paths, current_hash, current_text)
        return discovered_urls

    if has_changes:
        html_report = generate_html_report(name, additions, removals, url)
        send_email(html_report, name, has_changes)
        save_state(paths, current_hash, current_text)
    
    return discovered_urls

def main():
    print(f"=== Inizio sessione monitoraggio: {datetime.now()} ===")
    
    processed_urls = set()
    queue = PAGES_TO_MONITOR.copy()
    
    while queue:
        page = queue.pop(0)
        url = page["url"]
        
        if url in processed_urls:
            continue
        
        discovered = monitor_page(page)
        processed_urls.add(url)
        
        # Aggiungi sub-pagine scoperte alla coda se non ancora processate
        for d_url in discovered:
            if d_url not in processed_urls:
                # Crea un config dinamico per la sub-pagina
                # Determina il prefisso basato sull'URL
                prefix = "NIS" if "/portale/nis/" in d_url else "FAQ NIS"
                url_slug = d_url.strip('/').split('/')[-1]
                queue.append({
                    "name": f"{prefix}: {url_slug.replace('-', ' ').title()}",
                    "url": d_url,
                    "id": f"{prefix.lower().replace(' ', '_')}_{url_slug.replace('-', '_')}"
                })
    
    print(f"\n=== Fine sessione: {datetime.now()} ===")

if __name__ == "__main__":
    main()
