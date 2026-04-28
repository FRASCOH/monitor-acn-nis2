# Monitor ACN NIS2

Un sistema automatizzato in Python per il monitoraggio continuo degli aggiornamenti pubblicati dall'Agenzia per la Cybersicurezza Nazionale (ACN) in materia di NIS2 e Atti Generali.

Questo progetto è progettato per inviare notifiche email istantanee non appena viene rilevata una modifica sui siti istituzionali monitorati e offre una dashboard visiva dello stato di controllo, basata su GitHub Pages.

## Funzionalità Principali

*   **Monitoraggio Multi-Pagina**: Controlla contemporaneamente la sezione Atti Generali e tutto l'albero delle pagine relative alla NIS2 (FAQ comprese).
*   **Discovery Automatica**: Identifica e aggiunge automaticamente al monitoraggio nuove sotto-pagine pubblicate all'interno delle sezioni principali (es. nuove sezioni FAQ).
*   **Notifiche Email in Tempo Reale**: Invia una mail dettagliata con le differenze (aggiunte e rimozioni nel testo) non appena viene rilevata una modifica. Supporta l'invio a destinatari multipli.
*   **Esecuzione Automatica su Cloud**: Utilizza GitHub Actions per eseguire lo script di controllo ogni 5 minuti in modo totalmente gratuito e senza necessità di un server dedicato.
*   **Dashboard di Stato Integrata**: Include un'interfaccia web moderna (Glassmorphism, Dark Mode) ospitata su GitHub Pages che mostra lo stato in tempo reale di tutte le pagine monitorate (Modificato, Nessuna modifica, Errore).

## Struttura del Progetto

*   `monitor_acn.py`: Lo script Python principale che si occupa di scaricare le pagine, calcolarne l'hash, confrontare le versioni e inviare le mail.
*   `.github/workflows/monitor_acn.yml`: Il file di configurazione per GitHub Actions che schedula l'esecuzione dello script.
*   `index.html`: La dashboard web per la visualizzazione dello stato.
*   `status.json`: File generato automaticamente dallo script che alimenta i dati della dashboard.
*   `page_content_*.txt` / `page_hash_*.json`: File di stato generati automaticamente per tenere traccia dell'ultima versione nota di ogni pagina.

## Come Installare e Configurare

1.  **Clona o crea un fork di questo repository**.
2.  **Configura i GitHub Secrets**:
    Vai su *Settings > Secrets and variables > Actions* e aggiungi:
    *   `EMAIL_SENDER`: Il tuo indirizzo Gmail da cui inviare le notifiche.
    *   `EMAIL_PASSWORD`: La "Password per le app" di Google (non la tua password standard).
    *   `EMAIL_RECEIVER`: Gli indirizzi email a cui inviare le notifiche (separati da virgola, es. `mario@email.it, luigi@email.it`).
3.  **Abilita i permessi di scrittura per GitHub Actions**:
    Vai su *Settings > Actions > General*, scorri fino a *Workflow permissions* e seleziona **Read and write permissions**. Questo è fondamentale affinché lo script possa aggiornare i file di stato (`status.json` e storici).
4.  **Attiva la Dashboard (GitHub Pages)**:
    Vai su *Settings > Pages*, imposta il *Source* su *Deploy from a branch*, scegli il branch `main` e la cartella `/(root)`, poi salva.

## Come Funziona il Discovery delle Pagine

Lo script analizza il codice HTML delle pagine genitore (come la home NIS e la home delle FAQ NIS) alla ricerca di URL che corrispondono a determinati pattern (es. `/portale/faq/nis/[\w-]+`). 
Ogni nuovo link trovato che rientra in questa categoria viene automaticamente accodato per il monitoraggio. Questo garantisce che se l'ACN aggiunge nuove categorie di FAQ, il sistema le includerà senza alcun intervento manuale sul codice.

## Tecnologie Utilizzate

*   **Python 3.10**: Logica di scraping e hashing.
*   **Requests**: Per il download delle pagine web.
*   **smtplib / email**: Per la gestione e l'invio delle email HTML.
*   **GitHub Actions**: Per l'orchestrazione CI/CD e l'esecuzione schedulata (cron jobs).
*   **HTML/CSS/JS (Vanilla)**: Per la dashboard.
