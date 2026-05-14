import requests
import hashlib
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

def get_now():
    return datetime.now(ZoneInfo("Europe/Rome"))

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import difflib
import re
from urllib.parse import urljoin
import io
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

# Configurazione e Stato
os.makedirs("archive", exist_ok=True)
STATE_FILE = "status.json"
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
    },
    {
        "name": "Linee Guida ACN",
        "url": "https://www.acn.gov.it/portale/linee-guida",
        "id": "linee_guida"
    },
    {
        "name": "Avvisi ACN",
        "url": "https://www.acn.gov.it/portale/avvisi",
        "id": "avvisi"
    },
    {
        "name": "PNRR Cybersecurity",
        "url": "https://www.acn.gov.it/portale/pnrr",
        "id": "pnrr"
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
    """Estrae il testo visibile dalla pagina HTML distinguendo header e footer"""
    
    # Rilevamento sezioni
    header_part = ""
    footer_part = ""
    main_part = html
    
    # Estrai header
    header_match = re.search(r'<header[^>]*>(.*?)</header>', html, re.DOTALL | re.IGNORECASE)
    if header_match:
        header_part = header_match.group(1)
        main_part = main_part.replace(header_match.group(0), "")
        
    # Estrai footer
    footer_match = re.search(r'<footer[^>]*>(.*?)</footer>', html, re.DOTALL | re.IGNORECASE)
    if footer_match:
        footer_part = footer_match.group(1)
        main_part = main_part.replace(footer_match.group(0), "")

    def process_text(text, prefix=""):
        if not text: return ""
        # Rimuovi script e style
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        # Rimuovi commenti HTML
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
        # Rimuovi tag HTML ma mantieni il contenuto
        text = re.sub(r'<[^>]+>', '\n', text)
        # Decodifica entità HTML comuni
        text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            if line:
                lines.append(f"{prefix}{line}")
        return "\n".join(lines)

    cleaned_header = process_text(header_part, "[HEADER] ")
    cleaned_footer = process_text(footer_part, "[FOOTER] ")
    cleaned_main = process_text(main_part, "")
    
    result = []
    if cleaned_header: result.append(cleaned_header)
    if cleaned_main: result.append(cleaned_main)
    if cleaned_footer: result.append(cleaned_footer)
    
    return "\n".join(result).strip()

def extract_document_list(html_content):
    """Estrae l'elenco dei documenti con metadati (tipo, data, anno)"""
    docs = []
    matches = re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html_content, re.IGNORECASE | re.DOTALL)
    
    # Mappa mesi italiani
    mesi = {
        "gennaio": "01", "febbraio": "02", "marzo": "03", "aprile": "04", "maggio": "05", "giugno": "06",
        "luglio": "07", "agosto": "08", "settembre": "09", "ottobre": "10", "novembre": "11", "dicembre": "12"
    }
    
    types_keywords = ["determina", "decreto", "circolare", "regolamento", "direttiva", "linee guida", "avviso", "nomina", "disciplina", "allegato", "modello", "modulo"]
    processed_urls = set()
    last_found_date = ""
    last_found_year = ""
    last_found_month = ""
    
    for m in matches:
        url = m.group(1).strip()
        name = clean_html(m.group(2))
        
        if url in processed_urls: continue
        
        lower_name = name.lower()
        doc_type = "Altro"
        for tk in types_keywords:
            if tk in lower_name:
                doc_type = tk.capitalize()
                break
        
        if doc_type != "Altro" or any(kw in lower_name for kw in ["attuazione", "piano"]) and len(name) > 10:
            # Cerchiamo la data nel testo: es. "18 gennaio 2022"
            date_str = ""
            year_str = ""
            month_str = ""
            
            # Regex per data: giorno (1-2 cifre) mese (testo) anno (4 cifre)
            date_match = re.search(r'(\d{1,2})\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+(\d{4})', lower_name)
            
            if date_match:
                giorno = date_match.group(1).zfill(2)
                mese_testo = date_match.group(2)
                anno = date_match.group(3)
                mese_num = mesi.get(mese_testo, "01")
                date_str = f"{giorno}/{mese_num}/{anno}"
                year_str = anno
                month_str = mese_num
                # Aggiorniamo la "memoria" per i successivi allegati
                last_found_date = date_str
                last_found_year = year_str
                last_found_month = month_str
            else:
                # Prova solo anno se data completa manca
                year_match = re.search(r'\b(202\d)\b', name)
                if year_match:
                    year_str = year_match.group(1)
                
                # Se è un allegato/modello e non ha data, usa l'ultima trovata
                if not date_str and not year_str and last_found_date:
                    date_str = last_found_date
                    year_str = last_found_year
                    month_str = last_found_month
                
                # Se abbiamo l'anno ma non il mese, e non abbiamo memoria, 
                # lasciamo month_str come "" (verrà gestito dal frontend)

            clean_name = name.replace('\n', ' ').replace('\r', ' ').strip()
            clean_name = re.sub(r'\s+', ' ', clean_name)
            
            if url.startswith('/'):
                url = "https://www.acn.gov.it" + url
                
            docs.append({
                "name": clean_name, 
                "url": url,
                "type": doc_type,
                "date": date_str,
                "year": year_str,
                "month": month_str
            })
            processed_urls.add(url)
            
    return docs

def discover_links(html, base_url, pattern):
    """Trova link che corrispondono a un pattern"""
    links = re.findall(f'href="({pattern})"', html)
    # Rendi i link assoluti e rimuovi duplicati
    absolute_links = set()
    for link in links:
        absolute_links.add(urljoin(base_url, link))
    return list(absolute_links)

def extract_pdf_text(url):
    """Scarica un PDF ed estrae il testo"""
    if not PyPDF2:
        return None, "PyPDF2 non installato"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/pdf,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        response = requests.get(url, timeout=30, headers=headers, stream=True, verify=False) # verify=False per bypassare eventuali problemi SSL
        response.raise_for_status()
        
        # Verifica che il server abbia effettivamente restituito un PDF
        content_type = response.headers.get('Content-Type', '').lower()
        if 'application/pdf' not in content_type:
            return None, f"Il link non restituisce un PDF (Content-Type: {content_type}). Potrebbe essere una pagina di errore o di login."
        
        with io.BytesIO(response.content) as f:
            # strict=False permette di leggere PDF malformati o senza marker EOF
            try:
                reader = PyPDF2.PdfReader(f, strict=False)
            except Exception as pdf_err:
                return None, f"Impossibile leggere il file PDF: {str(pdf_err)}"
                
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            
            if not text.strip():
                return None, "PDF senza testo estraibile (immagine/scansione)"
                
            return text.strip(), None
    except requests.exceptions.HTTPError as e:
        return None, f"Errore HTTP: {e.response.status_code}"
    except Exception as e:
        print(f"Errore estrazione PDF {url}: {e}")
        return None, str(e)

def load_state(paths):
    """Carica hash, contenuto e dati ultima modifica"""
    state = {
        "hash": None,
        "content": None,
        "last_check": None,
        "last_change_date": None,
        "last_additions": [],
        "last_removals": []
    }
    
    if os.path.exists(paths["hash"]):
        try:
            with open(paths["hash"], 'r') as f:
                data = json.load(f)
                state["hash"] = data.get('hash')
                state["last_check"] = data.get('last_check')
                state["last_change_date"] = data.get('last_change_date')
                state["last_additions"] = data.get('last_additions', [])
                state["last_removals"] = data.get('last_removals', [])
        except: pass
        
    if os.path.exists(paths["content"]):
        try:
            with open(paths["content"], 'r', encoding='utf-8') as f:
                state["content"] = f.read()
        except: pass
        
    return state

def append_to_history(page_id, name, url, additions, removals):
    """Aggiunge una nuova voce allo storico delle modifiche"""
    archive_dir = "archive"
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)
        
    history_file = os.path.join(archive_dir, f"history_{page_id}.json")
    history = []
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except:
            pass
            
    entry = {
        "timestamp": get_now().isoformat(),
        "date_formatted": get_now().strftime('%d/%m/%Y %H:%M'),
        "additions": additions,
        "removals": removals
    }
    
    history.insert(0, entry) # Inserisci in cima (più recente prima)
    
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2)

def save_state(paths, content_hash, content, last_change_date=None, additions=None, removals=None):
    """Salva hash, contenuto e metadati modifica"""
    # Carichiamo lo stato esistente per non perdere i dati se non stiamo salvando una nuova modifica
    existing_state = load_state(paths)
    
    state_data = {
        'hash': content_hash,
        'last_check': get_now().isoformat(),
        'last_change_date': last_change_date or existing_state.get('last_change_date'),
        'last_additions': additions if additions is not None else existing_state.get('last_additions', []),
        'last_removals': removals if removals is not None else existing_state.get('last_removals', [])
    }
    
    with open(paths["hash"], 'w') as f:
        json.dump(state_data, f, indent=2)
    
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
        <p class="timestamp">Report generato il {get_now().strftime('%d/%m/%Y alle %H:%M')}</p>
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

def send_email(html_content, subject):
    """Invia email con il report consolidato"""
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = os.environ.get("EMAIL_SENDER")
    sender_password = os.environ.get("EMAIL_PASSWORD")
    receiver_emails = os.environ.get("EMAIL_RECEIVER")
    
    if not all([sender_email, sender_password, receiver_emails]):
        print("Variabili d'ambiente email non configurate")
        return
    
    dest_list = [email.strip() for email in receiver_emails.split(',')]
    
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = ", ".join(dest_list)
    message["Subject"] = subject
    
    message.attach(MIMEText(html_content, "html"))
    
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(message)
        print(f"Email inviata correttamente a {len(dest_list)} destinatari")
    except Exception as e:
        print(f"Errore invio email: {e}")

def get_ai_summary(results_with_changes):
    """Genera un riassunto delle modifiche usando Google Gemini"""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not genai or not api_key:
        return None
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Prepara il testo completo per l'AI
        all_text = ""
        for res in results_with_changes:
            all_text += f"\n--- PAGINA: {res['name']} ---\n"
            if res['additions']:
                all_text += "AGGIUNTE:\n" + "\n".join(res['additions'][:15]) + "\n"
            if res['removals']:
                all_text += "RIMOZIONI:\n" + "\n".join(res['removals'][:15]) + "\n"

        prompt = f"""
        Sei un esperto di cybersecurity e normativa NIS2. 
        Analizza le seguenti modifiche rilevate sul sito dell'Agenzia per la Cybersicurezza Nazionale (ACN).
        Fornisci un breve riassunto esecutivo (max 150 parole) spiegando in modo semplice:
        1. Qual è la natura principale dei cambiamenti.
        2. Se ci sono impatti diretti per i soggetti obbligati NIS2 (es. nuove scadenze, requisiti tecnici).
        3. Un consiglio rapido su come procedere.
        
        Usa un tono professionale ma accessibile. Rispondi in Italiano.
        Usa grassetti per evidenziare i punti chiave.
        
        MODIFICHE RILEVATE:
        {all_text}
        """
        
        response = model.generate_content(prompt)
        return response.text.replace("\n", "<br>")
    except Exception as e:
        print(f"Errore durante la generazione del riassunto AI: {e}")
        return None

def generate_summary_report(results_with_changes):
    """Genera un report HTML consolidato per tutte le pagine modificate"""
    now_str = get_now().strftime('%d/%m/%Y alle %H:%M')
    
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; color: #333; }}
            h2 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            .change-group {{ background: #f9f9f9; border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin-bottom: 30px; }}
            .url-list {{ background: #fff; padding: 10px; border-radius: 4px; border-left: 4px solid #3498db; margin: 10px 0; }}
            .addition {{ color: #27ae60; background: #eafaf1; padding: 5px 10px; margin: 2px 0; border-radius: 3px; font-family: monospace; }}
            .removal {{ color: #c0392b; background: #fdedec; padding: 5px 10px; margin: 2px 0; border-radius: 3px; font-family: monospace; text-decoration: line-through; }}
            .context-header {{ color: #2980b9; font-weight: bold; font-size: 0.9em; text-transform: uppercase; }}
            .context-footer {{ color: #8e44ad; font-weight: bold; font-size: 0.9em; text-transform: uppercase; }}
            .timestamp {{ color: #7f8c8d; font-size: 0.9em; font-style: italic; }}
            .ai-summary {{ background: #eef2ff; border: 1px solid #c7d2fe; border-radius: 8px; padding: 20px; margin: 20px 0; border-left: 6px solid #6366f1; }}
            a {{ color: #3498db; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <h2>🔔 Report Consolidato Modifiche ACN</h2>
        <p class="timestamp">Sessione di monitoraggio del {now_str}</p>
        <p>Sono state rilevate modifiche in <strong>{len(results_with_changes)}</strong> risorse.</p>
    """
    
    # Ottieni il riassunto AI
    ai_summary = get_ai_summary(results_with_changes)
    if ai_summary:
        html += f"""
        <div class="ai-summary">
            <h3 style="margin-top: 0; color: #4338ca; display: flex; align-items: center; gap: 10px;">
                🤖 Analisi Intelligente (Gemini AI)
            </h3>
            <div style="line-height: 1.6;">{ai_summary}</div>
        </div>
        """

    # Raggruppa le pagine per set di modifiche identiche
    groups = {}
    for res in results_with_changes:
        # Crea una chiave basata su aggiunte e rimozioni
        key = hashlib.md5(json.dumps([res["additions"], res["removals"]]).encode()).hexdigest()
        if key not in groups:
            groups[key] = {
                "additions": res["additions"],
                "removals": res["removals"],
                "pages": []
            }
        groups[key]["pages"].append({"name": res["name"], "url": res["url"]})

    for key, group in groups.items():
        html += '<div class="change-group">'
        html += '<h3>Pagine interessate:</h3>'
        html += '<div class="url-list">'
        for p in group["pages"]:
            html += f'• <a href="{p["url"]}">{p["name"]}</a><br>'
        html += '</div>'
        
        if group["additions"]:
            html += '<h4>✅ Aggiunte o Modifiche:</h4>'
            for item in group["additions"][:30]:
                content = item
                label = ""
                if item.startswith("[HEADER]"):
                    label = '<span class="context-header">[HEADER]</span> '
                    content = item.replace("[HEADER] ", "")
                elif item.startswith("[FOOTER]"):
                    label = '<span class="context-footer">[FOOTER]</span> '
                    content = item.replace("[FOOTER] ", "")
                
                html += f'<div class="addition">{label}{content}</div>'
            if len(group["additions"]) > 30:
                html += f'<p><em>... e altre {len(group["additions"]) - 30} righe</em></p>'

        if group["removals"]:
            html += '<h4>❌ Rimozioni:</h4>'
            for item in group["removals"][:30]:
                content = item
                label = ""
                if item.startswith("[HEADER]"):
                    label = '<span class="context-header">[HEADER]</span> '
                    content = item.replace("[HEADER] ", "")
                elif item.startswith("[FOOTER]"):
                    label = '<span class="context-footer">[FOOTER]</span> '
                    content = item.replace("[FOOTER] ", "")
                
                html += f'<div class="removal">{label}{content}</div>'
            if len(group["removals"]) > 30:
                html += f'<p><em>... e altre {len(group["removals"]) - 30} righe</em></p>'
        
        html += '</div>'

    html += """
        <hr style="margin: 40px 0; border: none; border-top: 1px solid #eee;">
        <p class="timestamp">Sistema di monitoraggio automatico ACN & NIS2</p>
    </body>
    </html>
    """
    return html

def monitor_page(page_config):
    name = page_config["name"]
    url = page_config["url"]
    page_id = page_config["id"]
    is_pdf = url.lower().endswith('.pdf')
    
    print(f"\n--- Monitoraggio: {name} ---")
    print(f"URL: {url}")
    
    # Risultato per la dashboard
    result = {
        "id": page_id,
        "name": name,
        "url": url,
        "last_check": get_now().strftime('%d/%m/%Y %H:%M'),
        "status": "Inizializzato",
        "has_changes": False,
        "has_history": os.path.exists(os.path.join("archive", f"history_{page_id}.json")),
        "summary": "",
        "additions": [],
        "removals": [],
        "atti_list": [] # Elenco documenti se è la pagina Atti Generali
    }
    
    if is_pdf:
        current_text, error_msg = extract_pdf_text(url)
        raw_content = current_text # Per coerenza
        if error_msg:
            # Se è un falso PDF (pagina HTML), nascondilo dalla dashboard ignorandolo
            if "non restituisce un PDF" in error_msg:
                return [], None
            result["status"] = f"Errore: {error_msg}"
            result["summary"] = error_msg
    else:
        raw_content = get_page_content(url)
        current_text = clean_html(raw_content) if raw_content else None
        if not current_text:
            result["status"] = "Errore download/lettura"

    if not current_text:
        return [], result

    # Se è la pagina Atti Generali, estraiamo la lista documenti
    if "atti-generali" in url:
        result["atti_list"] = extract_document_list(raw_content)
        print(f"📊 Estratti {len(result['atti_list'])} documenti dalla lista atti")

    # Scoperta sub-pagine e PDF (solo per pagine HTML)
    discovered_urls = []
    if not is_pdf:
        if page_config.get("discover_subpages") and page_config.get("subpage_pattern"):
            discovered_urls = discover_links(raw_content, url, page_config["subpage_pattern"])
        
        # Trova anche i PDF nella pagina
        pdf_links = re.findall(r'href="([^"]+\.pdf)"', raw_content, re.IGNORECASE)
        for pdf in pdf_links:
            discovered_urls.append(urljoin(url, pdf))

    current_hash = hashlib.sha256(current_text.encode('utf-8')).hexdigest()
    
    paths = get_state_paths(page_id)
    old_state = load_state(paths)
    old_hash = old_state["hash"]
    old_text = old_state["content"]
    
    # Logica dei 15 giorni
    change_date_str = old_state.get("last_change_date")
    is_within_15_days = False
    if change_date_str:
        change_date = datetime.fromisoformat(change_date_str)
        days_since = (get_now().replace(tzinfo=None) - change_date.replace(tzinfo=None)).days
        if days_since <= 15:
            is_within_15_days = True
            result["last_change_date"] = change_date.strftime('%d/%m/%Y %H:%M')

    if old_hash and old_text:
        if current_hash != old_hash:
            print(f"⚠️ MODIFICHE RILEVATE per {name}!")
            additions, removals = generate_detailed_diff(old_text, current_text)
            
            # Salva nello storico permanente
            append_to_history(page_id, name, url, additions, removals)
            result["has_history"] = True
            
            now_str = get_now().isoformat()
            result["has_changes"] = True
            result["status"] = "Modificato"
            result["summary"] = f"+{len(additions)} aggiunte, -{len(removals)} rimozioni"
            result["additions"] = additions
            result["removals"] = removals
            result["last_change_date"] = get_now().strftime('%d/%m/%Y %H:%M')
            
            # Non inviamo più l'email qui, salviamo solo lo stato
            save_state(paths, current_hash, current_text, now_str, additions, removals)
        else:
            print(f"✅ Nessuna modifica per {name}")
            if is_within_15_days:
                result["has_changes"] = True
                result["status"] = "Modificato (Recente)"
                result["additions"] = old_state.get("last_additions", [])
                result["removals"] = old_state.get("last_removals", [])
                result["summary"] = f"+{len(result['additions'])} aggiunte, -{len(result['removals'])} rimozioni"
            else:
                result["status"] = "Nessuna modifica"
                result["has_changes"] = False
            
            # Aggiorniamo comunque l'ultimo check nello stato
            save_state(paths, current_hash, current_text)
    else:
        print(f"📝 Prima esecuzione per {name} - salvataggio stato")
        save_state(paths, current_hash, current_text)
        result["status"] = "Nuova risorsa aggiunta"
    
    return list(set(discovered_urls)), result

def main():
    print(f"=== Inizio sessione monitoraggio: {get_now()} ===")
    
    processed_urls = set()
    queue = PAGES_TO_MONITOR.copy()
    all_results = []
    
    while queue:
        page = queue.pop(0)
        url = page["url"]
        
        if url in processed_urls:
            continue
        
        discovered, res = monitor_page(page)
        if res is not None:
            all_results.append(res)
        processed_urls.add(url)
        
        # Aggiungi sub-pagine o PDF scoperti alla coda
        for d_url in discovered:
            if d_url not in processed_urls:
                is_pdf = d_url.lower().endswith('.pdf')
                url_slug = d_url.strip('/').split('/')[-1]
                
                if is_pdf:
                    queue.append({
                        "name": f"📄 PDF: {url_slug}",
                        "url": d_url,
                        "id": f"pdf_{hashlib.md5(d_url.encode()).hexdigest()[:10]}"
                    })
                else:
                    prefix = "NIS" if "/portale/nis/" in d_url else "FAQ NIS"
                    queue.append({
                        "name": f"{prefix}: {url_slug.replace('-', ' ').title()}",
                        "url": d_url,
                        "id": f"{prefix.lower().replace(' ', '_')}_{url_slug.replace('-', '_')}"
                    })
    
    # Gestione notifiche consolidate
    results_with_changes = [r for r in all_results if r.get("has_changes") and not r.get("status") == "Nessuna modifica" and not "Modificato (Recente)" in r.get("status")]
    
    # Includiamo anche i "Nuova risorsa aggiunta" se vogliamo notificarli
    new_resources = [r for r in all_results if r.get("status") == "Nuova risorsa aggiunta"]
    
    if results_with_changes or new_resources:
        print(f"\n📧 Preparazione invio email consolidata per {len(results_with_changes)} modifiche...")
        
        # Per le nuove risorse, creiamo dei fake "additions" per il report
        for nr in new_resources:
            nr["has_changes"] = True
            nr["additions"] = ["[NUOVA RISORSA] Contenuto inizializzato correttamente"]
            nr["removals"] = []
            results_with_changes.append(nr)

        subject = f"🔔 Monitor ACN: {len(results_with_changes)} modifiche rilevate - {get_now().strftime('%d/%m/%Y %H:%M')}"
        html_report = generate_summary_report(results_with_changes)
        send_email(html_report, subject)
    else:
        print("\n✅ Nessuna nuova modifica rilevante da notificare via email.")

    # Salva risultati per la dashboard
    try:
        with open("status.json", "w", encoding="utf-8") as f:
            json.dump({
                "last_update": get_now().strftime('%d/%m/%Y %H:%M'),
                "pages": all_results
            }, f, indent=2)
        print("\n✅ status.json aggiornato correttamente")
    except Exception as e:
        print(f"\n❌ Errore salvataggio status.json: {e}")
    
    print(f"\n=== Fine sessione: {get_now()} ===")

if __name__ == "__main__":
    main()
