# 🤖 Chatbot RAG locale

Chatbot con **Retrieval-Augmented Generation** che risponde a domande basandosi sui documenti (PDF, TXT, MD e file di testo senza estensione) presenti nella cartella `documents/`. Supporta tre provider LLM: **Ollama** (locale), **Anthropic Claude**, **OpenAI**.

---

## 📑 Indice

- [✨ Caratteristiche](#-caratteristiche)
- [🦙 Installazione Ollama su Linux](#-installazione-ollama-su-linux)
  - [📥 Installazione](#-installazione)
  - [👤 Creazione utente e gruppo](#-creazione-utente-e-gruppo)
  - [⚙️ Servizio systemd](#️-servizio-systemd)
  - [🔄 Aggiornamento](#-aggiornamento)
  - [📌 Installare una versione specifica](#-installare-una-versione-specifica)
  - [📜 Visualizzare i log](#-visualizzare-i-log)
  - [🗑️ Disinstallazione](#️-disinstallazione)
- [🔧 Prerequisiti](#-prerequisiti)
- [⚙️ Setup](#️-setup)
  - [🦙 Provider Ollama](#-provider-ollama)
  - [🧠 Provider Anthropic](#-provider-anthropic)
  - [🤖 Provider OpenAI](#-provider-openai)
- [🚀 Avvio rapido](#-avvio-rapido)
- [💬 Uso](#-uso)
- [✅ Cosa verificare (checklist)](#-cosa-verificare-checklist)
- [🐧 Deploy su Debian / Linux](#-deploy-su-debian--linux)
  - [1️⃣ nohup — una riga, resiste al logout](#1️⃣-nohup--una-riga-resiste-al-logout)
  - [2️⃣ tmux — sessione riattaccabile](#2️⃣-tmux--sessione-riattaccabile)
  - [3️⃣ systemd — autoavvio e riavvio automatico](#3️⃣-systemd--autoavvio-e-riavvio-automatico)
- [🐳 Deploy con Docker Compose](#-deploy-con-docker-compose)
  - [⚠️ Prima di iniziare: ferma Ollama locale](#️-prima-di-iniziare-ferma-ollama-locale)
  - [▶️ Avvio](#️-avvio)
  - [⚙️ Configurazione](#️-configurazione)
  - [🩺 Risoluzione problemi](#-risoluzione-problemi)
- [💡 Consigli per l'uso come biblioteca personale](#-consigli-per-luso-come-biblioteca-personale)
- [📝 Note](#-note)

---

## ✨ Caratteristiche

- 📚 Indicizzazione automatica di documenti PDF, TXT e MD
- 🐧 Supporto ai file di testo senza estensione (tipici di Linux, es. `Dockerfile`, `appunti`)
- 🔍 Ricerca semantica con embedding `sentence-transformers`
- 🗂️ Citazione delle fonti (esempio file e pagina per i PDF)
- 🔄 Re-indicizzazione on-demand dall'interfaccia
- 🔌 Provider LLM intercambiabile (Ollama / Anthropic / OpenAI)
- 🖥️ UI web pronta all'uso via Gradio

---

## 🦙 Installazione Ollama su Linux

> 🐧 Guida step-by-step per installare Ollama come servizio di sistema su Linux (Debian/Ubuntu e derivate).

### 📥 Installazione

Scarica ed estrai il binario ufficiale in `/usr`:

```bash
curl -fsSL https://ollama.com/download/ollama-linux-amd64.tar.zst \
    | sudo tar x --zstd -C /usr
```

Verifica l'installazione:

```bash
ollama -v
```

### 👤 Creazione utente e gruppo

Crea un utente di sistema dedicato a Ollama e aggiungi il tuo utente al gruppo:

```bash
sudo useradd -r -s /bin/false -U -m -d /usr/share/ollama ollama
sudo usermod -a -G ollama $(whoami)
```

### ⚙️ Servizio systemd

Crea il file di servizio:

```bash
sudo vim /etc/systemd/ollama.service
```

Contenuto:

```ini
[Unit]
Description=Ollama Service
After=network-online.target

[Service]
ExecStart=/usr/bin/ollama serve
User=ollama
Group=ollama
Restart=always
RestartSec=3
Environment="PATH=$PATH"

[Install]
WantedBy=multi-user.target
```

Sposta il file nella posizione corretta e abilita il servizio:

```bash
sudo mv /etc/systemd/ollama.service /etc/systemd/system/ollama.service
sudo systemctl daemon-reload
sudo systemctl enable --now ollama
```

### 🔄 Aggiornamento

Per aggiornare Ollama, riesegui lo script di installazione:

```bash
curl -fsSL https://ollama.com/download/ollama-linux-amd64.tar.zst \
    | sudo tar x --zstd -C /usr
```

### 📌 Installare una versione specifica

Usa la variabile d'ambiente `OLLAMA_VERSION` con lo script di install. I numeri di versione si trovano nella releases page.

Esempio:

```bash
curl -fsSL https://ollama.com/install.sh | OLLAMA_VERSION=0.5.7 sh
```

### 📜 Visualizzare i log

Per vedere i log del servizio Ollama in avvio:

```bash
journalctl -e -u ollama
```

### 🗑️ Disinstallazione

🛑 Ferma e rimuovi il servizio:

```bash
sudo systemctl stop ollama
sudo systemctl disable ollama
sudo rm /etc/systemd/system/ollama.service
```

📚 Rimuovi le librerie Ollama dalla directory `lib` (`/usr/local/lib`, `/usr/lib` o `/lib`):

```bash
sudo rm -r $(which ollama | tr 'bin' 'lib')
```

🔧 Rimuovi il binario Ollama dalla directory `bin` (`/usr/local/bin`, `/usr/bin` o `/bin`):

```bash
sudo rm $(which ollama)
```

🧹 Rimuovi modelli, utente e gruppo:

```bash
sudo userdel ollama
sudo groupdel ollama
sudo rm -r /usr/share/ollama
```

---

## 🔧 Prerequisiti

- 🐍 **Python 3.10+**
- 🦙 **Ollama** installato e in esecuzione se si usa il provider `ollama` (default).
- 🔑 API key valida se si usa `anthropic` o `openai`.

---

## ⚙️ Setup


📂 Metti i tuoi documenti in `documents/` (formati supportati: `.pdf`, `.txt`, `.md` e file di testo senza estensione).

> ℹ️ Un file senza estensione viene indicizzato solo se è testo UTF-8 (niente binari) e non è nascosto (es. `.bashrc` viene ignorato). I file con un'estensione diversa da quelle supportate (es. `nginx.conf`, `note.log`) restano esclusi anche se sono testo.

### 🦙 Provider Ollama

```bash
ollama pull llama3.1:8b   # o il modello che preferisci
ollama serve              # se non parte da solo
```

Nel `.env`:

```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.1:8b
```

### 🧠 Provider Anthropic

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-haiku-4-5
```

### 🤖 Provider OpenAI

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```
##### modifica .env con il provider desiderato e (se cloud) l'API key

---

## 🚀 Avvio rapido

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# (Ollama attivo con: ollama pull llama3.1:8b && ollama serve)
python3 app.py
```

🌐 L'UI si apre su **<http://localhost:7860>**.

> ℹ️ Al primo avvio viene scaricato il modello di embedding `sentence-transformers` (~500 MB): richiede qualche minuto.

---

## 💬 Uso

- ✍️ Scrivi una domanda in chat: il chatbot risponde citando le fonti (nome file e, per i PDF, numero di pagina).
- 📥 Aggiungi/modifica/rimuovi file nella cartella `documents/`, poi clicca **Re-indicizza documenti** per aggiornare l'indice.
- 🔀 Il provider e il modello attivo sono mostrati in cima alla pagina; per cambiarli modifica `.env` e riavvia.

---

## ✅ Cosa verificare (checklist)

1. 🟢 **Primo avvio** → indicizza il PDF senza errori.
2. 🔁 **Secondo avvio** → indice ricaricato dal disco.
3. 📄 **Domanda sul PDF** → risposta con fonte citata (es. `file.pdf p.1`).
4. 🚫 **Domanda fuori topic** → ammette di non sapere.
5. ➕ **Aggiungi un `.md`** in `documents/` → click **Re-indicizza** → interrogabile.
6. 🔄 **Cambia `LLM_PROVIDER`** in `.env` → riavvia → funziona con l'altro provider.

---

## 🐧 Deploy su Debian / Linux

Tre modi, dal più semplice al più robusto:

### 1️⃣ nohup — una riga, resiste al logout

```bash
cd /path/al/progetto
source .venv/bin/activate      # se usi venv
nohup python3 app.py > app.log 2>&1 & echo $! > app.pid
```

- 📄 Log in `app.log`, PID in `app.pid`.
- 🛑 Per fermarlo: `kill $(cat app.pid)`
- 👀 Log in tempo reale: `tail -f app.log`

### 2️⃣ tmux — sessione riattaccabile

```bash
sudo apt install tmux          # se non c'è
tmux new -s rag                # entri in una sessione chiamata "rag"
# dentro:
source .venv/bin/activate && python3 app.py
# stacca la sessione: Ctrl+B poi D
```

- 🔌 Riattaccarti: `tmux attach -t rag`
- 🛑 Fermare l'app: riattacchi e `Ctrl+C`
- 💀 Uccidere la sessione: `tmux kill-session -t rag`

### 3️⃣ systemd — autoavvio e riavvio automatico

> 👍 Consigliato per uso stabile: parte al boot e riparte in caso di crash.

Crea `/etc/systemd/system/chatbot-rag.service`:

```ini
[Unit]
Description=RAG Chatbot Gradio
After=network.target ollama.service

[Service]
Type=simple
User=TUO_UTENTE
WorkingDirectory=/chatbot-rag
ExecStart=/chatbot-rag/.venv/bin/python3 app.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Poi:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now chatbot-rag
sudo systemctl status chatbot-rag
journalctl -u chatbot-rag -f      # log live
```

- 🛑 Ferma: `sudo systemctl stop chatbot-ragt`
- 🔁 Riavvia: `sudo systemctl restart chatbot-rag`

---

> 💡 **Consigliato**: per test rapidi il **#1 (nohup)**, per uso continuativo il **#3 (systemd)**.

---

## 🐳 Deploy con Docker Compose

> 📦 Avvia chatbot e Ollama in due container, senza installare Python o Ollama sull'host.

### ⚠️ Prima di iniziare: ferma Ollama locale

> 🛑 **Obbligatorio.** Il container `ollama` usa la porta **11434**, la stessa di Ollama installato sull'host. Se Ollama locale è attivo, l'avvio fallisce con `failed to bind host port 0.0.0.0:11434/tcp: address already in use`.

🐧 Linux:

```bash
sudo systemctl stop ollama
sudo systemctl disable ollama   # opzionale: evita che riparta al boot
ss -ltn | grep 11434            # nessun output = porta libera
```

🪟 Windows (PowerShell): chiudi Ollama dalla system tray, oppure:

```powershell
Stop-Process -Name ollama* -Force
Get-NetTCPConnection -LocalPort 11434   # errore "nessun oggetto trovato" = porta libera
```

### ▶️ Avvio

```bash
docker compose up -d --build
docker compose exec ollama ollama pull llama3.2:latest   # solo al primo avvio
docker compose logs -f chatbot
```

- 🌐 UI su **<http://localhost:7860>**.
- 🔁 Finché il modello non è scaricato, il container `chatbot` si riavvia (il preflight non trova il modello): è normale.
- 🧠 Il modello di embedding è già incluso nell'immagine, quindi al primo avvio non viene scaricato.
- 🛑 Per fermare tutto: `docker compose down` (i volumi restano).

### ⚙️ Configurazione

Il compose legge queste variabili dal `.env` nella cartella del progetto:

| Variabile | Default | Note |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | `ollama`, `anthropic` o `openai` |
| `OLLAMA_MODEL` | `llama3.2:latest` | deve corrispondere al modello scaricato con `ollama pull` |
| `ANTHROPIC_API_KEY` | vuota | richiesta con `LLM_PROVIDER=anthropic` |
| `OPENAI_API_KEY` | vuota | richiesta con `LLM_PROVIDER=openai` |

`OLLAMA_BASE_URL` e `CHROMA_DIR` sono impostate dal compose e puntano al container `ollama` e al volume dell'indice: non vanno cambiate nel `.env`.

💾 Volumi:

- `./documents` → `/app/documents`: i tuoi documenti, modificabili dall'host.
- `chatbot_index` → `/app/index`: indice ChromaDB persistente tra i riavvii.
- `ollama_data` → `/root/.ollama`: modelli Ollama scaricati.

### 🩺 Risoluzione problemi

**🔌 `address already in use` sulla porta 11434**

Ollama locale è ancora attivo: vedi [Prima di iniziare](#️-prima-di-iniziare-ferma-ollama-locale).

**🦙 `[preflight] ERRORE: Modello Ollama '...' non trovato`**

`OLLAMA_MODEL` nel `.env` non corrisponde al modello scaricato. Allinea i due, poi ricrea il container:

```bash
docker compose exec ollama ollama list            # modelli scaricati
# correggi OLLAMA_MODEL nel .env, oppure scarica il modello richiesto:
docker compose exec ollama ollama pull <modello>
docker compose up -d
```

> ⚠️ Dopo aver modificato il `.env` usa `docker compose up -d`, non `restart`: `restart` non rilegge le variabili d'ambiente.

**🌐 `ollama pull` fallisce con `lookup registry.ollama.ai on [fe80::1%...]:53 ... invalid argument`**

Il DNS dell'host è un indirizzo IPv6 link-local (verificabile con `cat /etc/resolv.conf`), che Docker copia nei container ma che lì non funziona. Imposta DNS espliciti per Docker:

```bash
sudo cat /etc/docker/daemon.json 2>/dev/null   # se esiste, aggiungi la chiave "dns" invece di sovrascrivere
echo '{ "dns": ["1.1.1.1", "8.8.8.8"] }' | sudo tee /etc/docker/daemon.json
sudo systemctl restart docker
docker compose down && docker compose up -d
docker compose exec ollama ollama pull llama3.2:latest
```

> ℹ️ Se nella tua rete c'è un DNS interno (es. il router), puoi usarlo al posto di `1.1.1.1`.

**🔒 Fedora / RHEL: documenti non letti (`Permission denied`)**

SELinux blocca l'accesso del container alla cartella montata. Aggiungi `:z` al mount in `docker-compose.yml`:

```yaml
- ./documents:/app/documents:z
```

---

## 💡 Consigli per l'uso come biblioteca personale

Se pensi di usare il progetto per raccogliere e interrogare le tue guide/appunti nel tempo, un paio di suggerimenti pratici man mano che la collezione cresce:

- 📂 **Organizza per sottocartelle** dentro `documents/` (il loader fa `rglob("*")`, quindi `documents/linux/`, `documents/python/`, ecc. funzionano già).
- 🔽 **`TOP_K`**: se aggiungi decine di file, alza a `TOP_K=6` in `.env` per pescare più chunk rilevanti a ogni domanda.
- 🧠 **Embedding più forte**: quando avrai molti documenti, `EMBEDDING_MODEL=BAAI/bge-m3` migliora sensibilmente la precisione (più pesante ma vale la pena; l'indice verrà rigenerato in automatico).
- 💾 **Backup**: la cartella `documents/` è la tua fonte di verità; `chroma_db/` si rigenera da sola. Un `rsync` periodico dei documenti su un disco esterno o su cloud e sei al sicuro.
- 🔒 **Contenuti sensibili**: se indicizzi documenti privati/aziendali, assicurati di avere `LLM_PROVIDER=ollama` (locale), non un provider cloud.

---

## 📝 Note

- 🔧 Se cambi `EMBEDDING_MODEL`, `CHUNK_SIZE` o `CHUNK_OVERLAP` in `.env`, l'indice viene automaticamente rigenerato al prossimo avvio.
- 🖼️ I PDF scannerizzati (immagini) non sono supportati: serve OCR, fuori scope.
- 💾 Storico chat non persistito tra sessioni.
- 🛡️ **Rifiuti "di sicurezza" dell'LLM**: i modelli locali più piccoli (es. Llama 8B) hanno un allineamento piuttosto rigido e ogni tanto rifiutano di rispondere quando nel contesto compaiono parole "sensibili" (`virus`, `exploit`, `bypass`, ecc.), anche se si tratta di documentazione tecnica legittima. Se il fenomeno si presenta spesso, prova modelli con allineamento più permissivo — ad esempio `mistral:7b-instruct`, `qwen2.5:7b` o varianti quantizzate come `llama3.1:8b-instruct-q5_K_M` — oppure passa a un provider cloud (`LLM_PROVIDER=anthropic` o `openai`), che generalmente segue meglio il contesto senza autocensurarsi.

---

## 📸 Screenshot

![Screenshot Chatbot RAG](https://i.ibb.co/R4z9m3M7/Screenshot-20260928-143508.png)

![Screenshot Chatbot RAG](https://i.ibb.co/JFRJv9Bc/Screenshot-20260928-142827.png)

