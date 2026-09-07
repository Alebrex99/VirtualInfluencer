# Setup — Google Cloud Express Mode, API key ed esecuzione delle pipeline

Guida per riprodurre da zero l'ambiente necessario a eseguire le pipeline di generazione degli
stimoli (`main-generating-v5London.py`, `second-generating-{female,male}-London.py`).

> 🇮🇹 **Prima parte: italiano.** 🇬🇧 **Second part: [English version](#english-version).**

---

## Livelli di affidabilità delle informazioni

Questa guida distingue tre tipi di contenuto, perché non hanno lo stesso grado di certezza:

| Marca | Significato |
|---|---|
| ✅ **Verificato nel codice** | Ricavato dal codice del progetto o dal sorgente dell'SDK `google-genai` 1.74.0 installato in `.venv/`. È vero per *questa* repo, ora. |
| 📄 **Verificato in documentazione** | Confermato sulla documentazione ufficiale Google Cloud (settembre 2026). I termini commerciali possono cambiare: ricontrolla le cifre prima di farci affidamento. |
| ⚠️ **Da confermare** | Procedura di console ricavata dagli appunti dell'autore, non verificabile automaticamente. **Verifica sulla documentazione ufficiale prima di seguirla alla lettera.** I link canonici sono in §9. |

---

## 1. Come si autentica la pipeline ✅

Prima di scegliere un percorso di setup conviene capire cosa chiede il codice, perché determina
tutto il resto. Tutti e tre gli script inizializzano il client così:

```python
client = genai.Client(vertexai=True, api_key=api_key)
```

L'SDK `google-genai` decide come autenticarsi in base a quali argomenti riceve. Nel sorgente
(`google/genai/_api_client.py`) la logica è esplicita, e il commento è di Google:

```python
# Handle when to use Vertex AI in express mode (api key).
```

e più avanti, al momento della richiesta HTTP:

```python
if self.vertexai and (self.project or self.location):
    http_request.headers['Authorization'] = f'Bearer {self._access_token()}'   # → ADC
else:
    ...                                                                        # → API key
```

Se ne ricavano due modalità operative:

| Modalità | Argomenti al `Client` | Autenticazione | Serve billing? |
|---|---|---|---|
| **Express mode** | `vertexai=True`, `api_key=...`, **senza** `project`/`location` | Chiave API | No, finché dura il periodo gratuito |
| **Vertex AI completo** | `vertexai=True`, `project=...`, `location=...` | ADC (token Bearer) | Sì |

**Le pipeline in questa repo usano Express mode.** Non passano né `project` né `location`, quindi
il ramo ADC non viene mai preso.

### Variabili d'ambiente lette dall'SDK ✅

Oltre a quelle lette dagli script, l'SDK stesso consulta l'ambiente:

`GOOGLE_API_KEY`, `GEMINI_API_KEY`, `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`,
`GOOGLE_GENAI_USE_VERTEXAI`.

Due conseguenze pratiche:

- Se sono impostate **sia** `GOOGLE_API_KEY` sia `GEMINI_API_KEY`, l'SDK usa `GOOGLE_API_KEY` e
  registra un avviso. Tieni impostata solo `GEMINI_API_KEY`.
- Se nell'ambiente esistono `GOOGLE_CLOUD_PROJECT` o `GOOGLE_CLOUD_LOCATION` — capita spesso dopo
  aver usato `gcloud` — **non interferiscono**: quando `api_key` è passata esplicitamente al
  costruttore, come fanno questi script, l'SDK imposta `project` e `location` a `None` e resta in
  Express mode. Il comportamento è codificato nel costruttore, non accidentale.

---

## 2. Prerequisiti

- **Python 3.11+** con `venv`
- Un account Google **nuovo**, non ancora associato a fatturazione (vedi §3)
- I dataset sorgente in `Images/LondonDataset/ExperimentalDataset/` (16 file, 1350 × 1350 px)

---

## 3. Percorso A — Account Express (gratuito)

L'ordine delle operazioni è la parte più importante di questa sezione: **l'errore da evitare è
partire da Google AI Studio.**

### 3.1 Condizioni del livello gratuito 📄

Fatti confermati sulla documentazione ufficiale:

| Condizione | Valore |
|---|---|
| Durata del livello gratuito | **90 giorni**, entro quote definite |
| Chi è idoneo | **Solo utenti nuovi di Google Cloud** |
| Serve un account di fatturazione? | **No**, per iscriversi al livello gratuito |
| Se attivi la fatturazione | Il livello gratuito di 90 giorni **viene rimosso** e passi al livello a pagamento |
| Se sei già utente Google Cloud | Non hai diritto ai 90 giorni: puoi usare Express solo sul livello a pagamento, con la tua fatturazione esistente |

Express mode semplifica la gestione di organizzazione, fatturazione e progetto rispetto al percorso
Vertex AI completo, e offre un **sottoinsieme** delle funzionalità di generative AI: solo alcuni
modelli Gemini sono supportati (questo progetto ha funzionato con `gemini-3-pro-image-preview` e
`gemini-3.1-flash-image-preview`), e le quote sono limitate.

### 3.2 Perché non partire da AI Studio 📄

Poiché l'attivazione della fatturazione **rimuove** il periodo gratuito, e poiché il periodo
gratuito spetta **solo a chi è nuovo su Google Cloud**, la sequenza è a senso unico: se crei prima
la chiave in Google AI Studio e poi associ un metodo di pagamento — che AI Studio richiede — perdi
la possibilità di attivare i 90 giorni su quell'account.

La sequenza corretta è l'inversa: **prima l'account Express, poi la chiave.**

### 3.3 La chiave Express non è una chiave AI Studio 📄

Questo è il punto più frainteso, e vale la pena essere precisi perché determina se la pipeline
funziona o no.

- **Vertex AI standard non accetta chiavi API.** Richiede OAuth2 / ADC / service account, e
  respinge le chiavi con l'errore `API keys are not supported by this API`.
- **Le chiavi API in senso classico appartengono alla Gemini Developer API** di AI Studio
  (`generativelanguage.googleapis.com`), che è una superficie diversa.
- **Express mode è l'eccezione**: consente l'autenticazione a chiave API al posto di OAuth, ma con
  chiavi **specifiche per quella modalità**, non con chiavi AI Studio.

Che poi la chiave Express compaia anche nell'interfaccia di AI Studio non la rende una chiave AI
Studio: è una chiave del progetto Cloud, e la sua capacità di raggiungere il backend Vertex deriva
dall'abilitazione di Express sul progetto.

### 3.4 Creazione dell'account

1. Crea un **account Google nuovo**, mai usato per Google Cloud (altrimenti niente 90 giorni).
2. Vai su Google Cloud e attiva la **modalità Express** seguendo la guida ufficiale (§9). Non
   associare una fatturazione.
3. Crea o lascia creare il progetto (es. `VirtualInfluencer`).

> **Usa un progetto dedicato**, non quello già impiegato con AI Studio: le due superfici hanno
> percorsi di autenticazione distinti e il riuso non è garantito.

### 3.5 Ostacolo: organizzazione e policy sulle chiavi API ⚠️

Se durante la creazione dell'account viene creata anche un'**organizzazione**, il progetto ne
eredita le policy — e per impostazione predefinita la creazione di chiavi API può risultare
disabilitata. Il sintomo è che la voce per creare la chiave è assente o restituisce un errore di
permessi.

**Prestare attenzione alla schermata iniziale di creazione dell'account**, che è il momento in cui
l'organizzazione viene creata: evitarla, dove possibile, semplifica tutto il resto.

Rimedio — concedere il ruolo necessario sull'organizzazione. I comandi sono questi 📄:

```powershell
# a livello di organizzazione
gcloud organizations add-iam-policy-binding RESOURCE_ID `
    --member=PRINCIPAL --role=ROLE_NAME --condition=CONDITION

# a livello di progetto
gcloud projects add-iam-policy-binding RESOURCE_ID `
    --member=PRINCIPAL --role=ROLE_NAME --condition=CONDITION
```

dove `RESOURCE_ID` è l'ID dell'organizzazione o del progetto, `PRINCIPAL` ha forma
`TIPO:IDENTIFICATIVO` (es. `user:tuo.indirizzo@gmail.com`), `ROLE_NAME` è il ruolo da concedere
(es. `roles/resourcemanager.projectCreator`) e `CONDITION` vale `None` se non servono condizioni.
In alternativa, dalla console: **IAM → seleziona l'organizzazione → Concedi accesso**.

> Le modifiche ai criteri IAM diventano effettive **entro circa 2 minuti**. 📄

### 3.6 Creazione della chiave API

1. Abilita le API necessarie sul progetto, se l'attivazione di Express non lo ha già fatto.
2. Crea la chiave API.

> ⚠️ **Trappola da evitare: non restringere la chiave alla sola "Gemini API".**
> Se applichi alla chiave la restrizione obbligatoria sull'API "Gemini API", **la generazione di
> immagini smette di funzionare.** La ragione è verificabile nel codice: il client è creato con
> `vertexai=True`, quindi le richieste passano dal backend **Vertex AI**, non dalla Gemini Developer
> API. Una chiave ristretta alla sola Gemini API non ha titolo su quell'endpoint. Lascia la chiave
> senza restrizioni di API, oppure includi esplicitamente l'API di Vertex AI. ✅ *(il motivo è
> verificato dal codice; la restrizione in sé è dagli appunti)*

---

## 4. Configurazione del file `.env` ✅

Crea un file `.env` nella radice del progetto:

```dotenv
GEMINI_API_KEY=<la_tua_chiave>
GEMINI_MODEL=gemini-3-pro-image-preview
```

Solo queste due variabili sono lette dagli script (`load_config()` in tutti e tre i file).

**Note verificate:**

- `GEMINI_MODEL` **deve** essere impostata. Se manca, `load_config()` ricade su
  `DEFAULT_MODEL = "gemini-2.5-flash-image-preview"` definito in `constants.py`: non solleva un
  errore, **declassa il modello in silenzio** e i risultati non saranno riproducibili.
- `IMAGEN_MODEL` compare nel `.env` esistente e in `CLAUDE.md`, ma **non è letta da nessuno degli
  script London**. È residuo: puoi ometterla.
- `.env` è in `.gitignore`. Non committarlo.

### Modelli usati nella produzione ✅

| Modello | Uso |
|---|---|
| `gemini-3-pro-image-preview` | Modello di produzione per tutte le chiamate |
| `gemini-3.1-flash-image-preview` | Solo per quattro stimoli (`FT1_HEM`, `MC1_HE`, `MC1_HEM`, `FC3_MHEM`), rigenerati cambiando `GEMINI_MODEL` nel `.env` |

Il cambio di modello **non è codificato negli script**: è una sostituzione a livello di ambiente.
Per riprodurre quei quattro stimoli occorre cancellarli dall'output (altrimenti il controllo
skip-if-exists li preserva) e rilanciare con il modello alternativo nel `.env`.

---

## 5. Installazione dell'ambiente Python

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install google-genai pillow python-dotenv
```

Versione dell'SDK con cui il progetto è stato eseguito e verificato: **`google-genai` 1.74.0**. ✅

---

## 6. Esecuzione delle pipeline ✅

L'ordine è vincolante e **fra le due pipeline c'è uno stadio manuale**.

### 6.1 Prima pipeline

```powershell
python main-generating-v5London.py
```

Legge `Images/LondonDataset/ExperimentalDataset/` (16 soggetti), scrive 48 file in
`Output_images/` — `_H`, `_MH`, `_M` per soggetto — e archivia gli input standardizzati a
1024 × 1024 in `Images/StandardizedImages/`.

### 6.2 Stadio manuale di curation

Non è automatizzato e **non può essere saltato**, perché la seconda pipeline non legge
`Output_images/` ma le cartelle popolate a mano:

1. Copia i 48 render in `Output_images/ReadyToEdit/`.
2. Ispeziona ogni render contro la sorgente e correggi eventuali derive di esposizione o tinta.
3. Copia i soli `_H` e `_MH` in `Output_images/ReadyToEnhance/Female/` (soggetti `FC*`, `FT*`) e
   `Output_images/ReadyToEnhance/Male/` (soggetti `MC*`, `MT*`) — 16 file per cartella.

I `_M` non vengono trattati dalla seconda pipeline.

### 6.3 Seconda pipeline

Due esecuzioni separate, perché il prompt di beautification è differenziato per genere:

```powershell
python second-generating-female-London.py
python second-generating-male-London.py
```

Ciascuna produce 32 file in `Output_images/Enhanced/` (`_HE`, `_MHE`, `_HEM`, `_MHEM`), 64 in
totale.

### 6.4 Risultato atteso

| Cartella | File | Risoluzione |
|---|---|---|
| `Images/StandardizedImages/` | 16 | 1024 × 1024 |
| `Output_images/` | 48 | 1024 × 1024 |
| `Output_images/Enhanced/` | 64 | 1024 × 1024 |
| **Totale set sperimentale** | **128** | **1024 × 1024** |

### 6.5 Costi e ripartenza ✅

Entrambe le pipeline sono **idempotenti**: prima di ogni chiamata verificano se il file di output
esiste già e, in tal caso, la saltano senza spendere. Un'esecuzione interrotta riparte senza
ripagare il lavoro fatto. Una rigenerazione completa da zero richiede un minimo di **112 chiamate
API** (48 + 64), escluse ritentativi e scarti.

> Il costo di riferimento di ~$0.039 per immagine vale per output fino a 1024 × 1024 (1290 token).
> Le immagini richieste con `image_size = "2K"` costano di più.

---

## 7. Percorso B — Alla scadenza del periodo gratuito ⚠️✅

Quando il periodo Express termina, l'autenticazione a sola chiave API non basta più: occorre
passare a **Vertex AI completo con ADC** (Application Default Credentials).

1. Installa Google Cloud CLI e autenticati:

   ```powershell
   gcloud auth application-default login
   ```

2. Modifica l'inizializzazione del client negli script:

   ```python
   import os
   PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
   LOCATION   = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")
   client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
   ```

Passando `project` e `location`, l'SDK prende il ramo ADC verificato in §1 e autentica con token
Bearer invece che con la chiave. ✅ *(il meccanismo è verificato dal sorgente SDK; la necessità di
migrare alla scadenza è dagli appunti)*

> ⚠️ Nota sul nome della variabile: lo snippet usa `GOOGLE_CLOUD_REGION`, ma **l'SDK legge
> autonomamente `GOOGLE_CLOUD_LOCATION`**, non `GOOGLE_CLOUD_REGION`. Poiché qui `location` è
> passata esplicitamente al costruttore la cosa non crea problemi, ma se preferisci affidarti alla
> risoluzione automatica dell'SDK usa `GOOGLE_CLOUD_LOCATION`.

---

## 8. Errori comuni

| Sintomo | Causa probabile |
|---|---|
| Generazione immagini fallisce con chiave valida | Chiave ristretta alla sola "Gemini API": il client usa il backend Vertex AI (§3.4) |
| Voce di creazione chiave assente o errore di permessi | Policy dell'organizzazione che disabilita le chiavi API (§3.3) |
| Risultati diversi dall'atteso, nessun errore | `GEMINI_MODEL` mancante nel `.env` → fallback silenzioso a `gemini-2.5-flash-image-preview` (§4) |
| Impossibile attivare Express sull'account | Account già associato a fatturazione, tipicamente creando prima la chiave in AI Studio (§3.1) |
| La seconda pipeline non trova nulla da fare | `ReadyToEnhance/{Female,Male}/` non popolate: manca lo stadio manuale (§6.2) |
| Warning su chiave API doppia | `GOOGLE_API_KEY` e `GEMINI_API_KEY` entrambe impostate; l'SDK usa la prima (§1) |

---

## 9. Riferimenti ufficiali

**Stato della verifica (settembre 2026).** Le pagine di documentazione Google Cloud sono
renderizzate lato client: il recupero diretto restituisce solo la struttura di navigazione per la
maggior parte di esse. I contenuti marcati 📄 in questa guida sono stati confermati per due vie —
la pagina IAM è risultata leggibile direttamente, mentre i termini di Express mode provengono dalla
pagina di panoramica ufficiale recuperata via ricerca. **Consulta comunque le pagine prima di
seguire le procedure di console, e ricontrolla le cifre commerciali: cambiano.**

- Express mode — panoramica:
  `https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/start/express-mode/overview`
- Express mode — tutorial API:
  `https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/start/express-mode/vertex-ai-express-mode-api-quickstart`
- Ottenere una chiave API:
  `https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/start/api-keys`
- Configurare le Application Default Credentials:
  `https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/start/gcp-auth`
- Migrazione da Google AI Studio:
  `https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/migrate/migrate-google-ai`
- Concessione e modifica degli accessi IAM:
  `https://docs.cloud.google.com/iam/docs/granting-changing-revoking-access`
- Avvio Vertex AI generative AI:
  `https://docs.cloud.google.com/vertex-ai/generative-ai/docs/start`

---
---

# English version

Guide to reproducing, from scratch, the environment needed to run the stimulus-generation
pipelines (`main-generating-v5London.py`, `second-generating-{female,male}-London.py`).

## Confidence levels

| Mark | Meaning |
|---|---|
| ✅ **Verified in code** | Derived from this project's code or from the source of the `google-genai` 1.74.0 SDK installed in `.venv/`. True for *this* repository, now. |
| 📄 **Verified in documentation** | Confirmed against official Google Cloud documentation (September 2026). Commercial terms can change: re-check the figures before relying on them. |
| ⚠️ **To confirm** | Console procedure taken from the author's notes, not automatically verifiable. **Check the official documentation before following it literally.** Canonical links are in §9. |

---

## 1. How the pipeline authenticates ✅

Understanding what the code asks for determines every other choice. All three scripts initialise
the client as:

```python
client = genai.Client(vertexai=True, api_key=api_key)
```

The `google-genai` SDK selects its authentication path from the arguments it receives. In the
source (`google/genai/_api_client.py`) the logic is explicit, and the comment is Google's own:

```python
# Handle when to use Vertex AI in express mode (api key).
```

and later, when the HTTP request is made:

```python
if self.vertexai and (self.project or self.location):
    http_request.headers['Authorization'] = f'Bearer {self._access_token()}'   # → ADC
else:
    ...                                                                        # → API key
```

Two operating modes follow:

| Mode | `Client` arguments | Authentication | Billing required? |
|---|---|---|---|
| **Express mode** | `vertexai=True`, `api_key=...`, **no** `project`/`location` | API key | No, while the free period lasts |
| **Full Vertex AI** | `vertexai=True`, `project=...`, `location=...` | ADC (Bearer token) | Yes |

**The pipelines in this repository use Express mode.** They pass neither `project` nor `location`,
so the ADC branch is never taken.

### Environment variables the SDK reads ✅

Besides those the scripts read, the SDK itself consults the environment:

`GOOGLE_API_KEY`, `GEMINI_API_KEY`, `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`,
`GOOGLE_GENAI_USE_VERTEXAI`.

Two practical consequences:

- If **both** `GOOGLE_API_KEY` and `GEMINI_API_KEY` are set, the SDK uses `GOOGLE_API_KEY` and logs
  a warning. Set only `GEMINI_API_KEY`.
- If `GOOGLE_CLOUD_PROJECT` or `GOOGLE_CLOUD_LOCATION` are present in the environment — common
  after using `gcloud` — they **do not interfere**: when `api_key` is passed explicitly to the
  constructor, as these scripts do, the SDK sets `project` and `location` to `None` and stays in
  Express mode. This precedence is coded in the constructor, not accidental.

---

## 2. Prerequisites

- **Python 3.11+** with `venv`
- A **fresh** Google account, not yet linked to billing (see §3)
- Source images in `Images/LondonDataset/ExperimentalDataset/` (16 files, 1350 × 1350 px)

---

## 3. Path A — Express account (free)

The order of operations is the most important part of this section: **the mistake to avoid is
starting from Google AI Studio.**

### 3.1 Free-tier terms 📄

Confirmed against the official documentation:

| Condition | Value |
|---|---|
| Free-tier duration | **90 days**, within defined quotas |
| Who is eligible | **New Google Cloud users only** |
| Billing account required? | **No**, to sign up for the free tier |
| If you enable billing | The 90-day free tier is **removed** and you move to the paid tier |
| If you are an existing Google Cloud user | Not eligible for the 90 days: you can use Express only on the paid tier, with your existing billing account |

Express mode simplifies organisation, billing and project management compared with the full Vertex
AI path, and offers a **subset** of the generative AI features: only some Gemini models are
supported (this project worked with `gemini-3-pro-image-preview` and
`gemini-3.1-flash-image-preview`), and quotas are limited.

### 3.2 Why not to start from AI Studio 📄

Because enabling billing **removes** the free period, and because the free period is available
**only to users new to Google Cloud**, the sequence is one-way: if you create the key in Google AI
Studio first and then attach a payment method — which AI Studio requires — you lose the ability to
activate the 90 days on that account.

The correct sequence is the reverse: **Express account first, key second.**

### 3.3 An Express key is not an AI Studio key 📄

This is the most misunderstood point, and worth being precise about, because it determines whether
the pipeline works at all.

- **Standard Vertex AI does not accept API keys.** It requires OAuth2 / ADC / service account, and
  rejects keys with the error `API keys are not supported by this API`.
- **API keys in the classic sense belong to AI Studio's Gemini Developer API**
  (`generativelanguage.googleapis.com`), which is a different surface.
- **Express mode is the exception**: it allows API-key authentication in place of OAuth, but with
  keys **specific to that mode**, not with AI Studio keys.

That the Express key subsequently appears in the AI Studio interface does not make it an AI Studio
key: it is a Cloud project key, and its ability to reach the Vertex backend comes from Express
being enabled on the project.

### 3.4 Creating the account

1. Create a **new Google account**, never used for Google Cloud (otherwise no 90 days).
2. Go to Google Cloud and enable **Express mode** following the official guide (§9). Do not attach
   billing.
3. Create, or let it create, the project (e.g. `VirtualInfluencer`).

> **Use a dedicated project**, not one already used with AI Studio: the two surfaces have distinct
> authentication paths and reuse is not guaranteed to work.

### 3.5 Obstacle: organisation policy on API keys ⚠️

If an **organisation** is also created while setting up the account, the project inherits its
policies — and by default API-key creation may be disabled. The symptom is that the option to
create a key is missing, or returns a permissions error.

**Pay attention to the initial account-creation screen**, which is where the organisation gets
created: avoiding it, where possible, simplifies everything downstream.

Remedy — grant the necessary role on the organisation. The commands are 📄:

```powershell
# at organisation level
gcloud organizations add-iam-policy-binding RESOURCE_ID `
    --member=PRINCIPAL --role=ROLE_NAME --condition=CONDITION

# at project level
gcloud projects add-iam-policy-binding RESOURCE_ID `
    --member=PRINCIPAL --role=ROLE_NAME --condition=CONDITION
```

where `RESOURCE_ID` is the organisation or project ID, `PRINCIPAL` has the form `TYPE:IDENTIFIER`
(e.g. `user:your.address@gmail.com`), `ROLE_NAME` is the role to grant (e.g.
`roles/resourcemanager.projectCreator`), and `CONDITION` is `None` if no conditions are needed.
Alternatively, from the console: **IAM → select the organisation → Grant access**.

> IAM policy changes take effect **within about 2 minutes**. 📄

### 3.6 Creating the API key

1. Enable the required APIs on the project, if enabling Express did not already do so.
2. Create the API key.

> ⚠️ **Trap to avoid: do not restrict the key to "Gemini API" only.**
> Applying the mandatory API restriction for "Gemini API" to the key **breaks image generation.**
> The reason is verifiable in the code: the client is built with `vertexai=True`, so requests go
> through the **Vertex AI** backend, not the Gemini Developer API. A key scoped to the Gemini API
> alone has no standing on that endpoint. Leave the key unrestricted, or explicitly include the
> Vertex AI API. ✅ *(the reason is verified from code; the restriction itself is from the notes)*

---

## 4. Configuring `.env` ✅

Create a `.env` file in the project root:

```dotenv
GEMINI_API_KEY=<your_key>
GEMINI_MODEL=gemini-3-pro-image-preview
```

Only these two variables are read by the scripts (`load_config()` in all three files).

**Verified notes:**

- `GEMINI_MODEL` **must** be set. If absent, `load_config()` falls back to
  `DEFAULT_MODEL = "gemini-2.5-flash-image-preview"` defined in `constants.py`: it does not raise,
  it **silently downgrades the model**, and results will not be reproducible.
- `IMAGEN_MODEL` appears in the existing `.env` and in `CLAUDE.md` but is **read by none of the
  London scripts**. It is a leftover; you can omit it.
- `.env` is in `.gitignore`. Do not commit it.

### Models used in production ✅

| Model | Use |
|---|---|
| `gemini-3-pro-image-preview` | Production model for all calls |
| `gemini-3.1-flash-image-preview` | Four stimuli only (`FT1_HEM`, `MC1_HE`, `MC1_HEM`, `FC3_MHEM`), regenerated by changing `GEMINI_MODEL` in `.env` |

The model switch is **not encoded in the scripts**; it is an environment-level substitution. To
reproduce those four stimuli you must delete them from the output first (otherwise the
skip-if-exists check preserves them) and re-run with the alternative model in `.env`.

---

## 5. Python environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install google-genai pillow python-dotenv
```

SDK version the project was run and verified with: **`google-genai` 1.74.0**. ✅

---

## 6. Running the pipelines ✅

The order is mandatory, and **a manual stage sits between the two pipelines**.

### 6.1 First pipeline

```powershell
python main-generating-v5London.py
```

Reads `Images/LondonDataset/ExperimentalDataset/` (16 subjects), writes 48 files to
`Output_images/` — `_H`, `_MH`, `_M` per subject — and archives the standardized 1024 × 1024
inputs in `Images/StandardizedImages/`.

### 6.2 Manual curation stage

Not automated, and **cannot be skipped**, because the second pipeline does not read
`Output_images/` but folders populated by hand:

1. Copy the 48 renders into `Output_images/ReadyToEdit/`.
2. Inspect each render against its source and correct any exposure or colour drift.
3. Copy only the `_H` and `_MH` files into `Output_images/ReadyToEnhance/Female/` (subjects `FC*`,
   `FT*`) and `Output_images/ReadyToEnhance/Male/` (subjects `MC*`, `MT*`) — 16 files per folder.

The `_M` renders are not processed by the second pipeline.

### 6.3 Second pipeline

Two separate runs, because the beautification prompt is gender-specific:

```powershell
python second-generating-female-London.py
python second-generating-male-London.py
```

Each produces 32 files in `Output_images/Enhanced/` (`_HE`, `_MHE`, `_HEM`, `_MHEM`), 64 in total.

### 6.4 Expected result

| Folder | Files | Resolution |
|---|---|---|
| `Images/StandardizedImages/` | 16 | 1024 × 1024 |
| `Output_images/` | 48 | 1024 × 1024 |
| `Output_images/Enhanced/` | 64 | 1024 × 1024 |
| **Total experimental set** | **128** | **1024 × 1024** |

### 6.5 Cost and resumption ✅

Both pipelines are **idempotent**: before each call they check whether the output file already
exists and, if so, skip it without spending. An interrupted run resumes without paying twice. A
full regeneration from scratch requires a minimum of **112 API calls** (48 + 64), excluding retries
and rejected outputs.

> The reference cost of ~$0.039 per image applies to outputs up to 1024 × 1024 (1290 tokens).
> Images requested with `image_size = "2K"` cost more.

---

## 7. Path B — When the free period expires ⚠️✅

Once the Express period ends, API-key-only authentication is no longer sufficient: you must move to
**full Vertex AI with ADC** (Application Default Credentials).

1. Install the Google Cloud CLI and authenticate:

   ```powershell
   gcloud auth application-default login
   ```

2. Change the client initialisation in the scripts:

   ```python
   import os
   PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
   LOCATION   = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")
   client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
   ```

Passing `project` and `location` makes the SDK take the ADC branch verified in §1, authenticating
with a Bearer token instead of the key. ✅ *(the mechanism is verified from the SDK source; the need
to migrate at expiry is from the notes)*

> ⚠️ Note on the variable name: the snippet uses `GOOGLE_CLOUD_REGION`, but **the SDK reads
> `GOOGLE_CLOUD_LOCATION`**, not `GOOGLE_CLOUD_REGION`, when resolving location on its own. Since
> `location` is passed explicitly to the constructor here this causes no problem, but if you prefer
> to rely on the SDK's automatic resolution, use `GOOGLE_CLOUD_LOCATION`.

---

## 8. Common errors

| Symptom | Likely cause |
|---|---|
| Image generation fails with a valid key | Key restricted to "Gemini API" only; the client uses the Vertex AI backend (§3.4) |
| Key-creation option missing, or permissions error | Organisation policy disabling API keys (§3.3) |
| Results differ from expected, no error raised | `GEMINI_MODEL` missing from `.env` → silent fallback to `gemini-2.5-flash-image-preview` (§4) |
| Cannot enable Express on the account | Account already linked to billing, typically by creating the key in AI Studio first (§3.1) |
| Second pipeline finds nothing to do | `ReadyToEnhance/{Female,Male}/` not populated: the manual stage is missing (§6.2) |
| Warning about duplicate API key | Both `GOOGLE_API_KEY` and `GEMINI_API_KEY` set; the SDK uses the former (§1) |

---

## 9. Official references

**Verification status (September 2026).** Google Cloud documentation pages are client-side
rendered: direct retrieval returns only the navigation shell for most of them. Content marked 📄 in
this guide was confirmed by two routes — the IAM page proved directly readable, while the Express
mode terms come from the official overview page retrieved via search. **Consult the pages anyway
before following console procedures, and re-check the commercial figures: they change.**

- Express mode — overview:
  `https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/start/express-mode/overview`
- Express mode — API tutorial:
  `https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/start/express-mode/vertex-ai-express-mode-api-quickstart`
- Get an API key:
  `https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/start/api-keys`
- Configure Application Default Credentials:
  `https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/start/gcp-auth`
- Migrate from Google AI Studio:
  `https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/migrate/migrate-google-ai`
- Granting, changing and revoking IAM access:
  `https://docs.cloud.google.com/iam/docs/granting-changing-revoking-access`
- Vertex AI generative AI — start:
  `https://docs.cloud.google.com/vertex-ai/generative-ai/docs/start`
