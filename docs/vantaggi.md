# I vantaggi di QGIS Headless

Una guida completa all'esecuzione di QGIS senza interfaccia grafica.

---

## Introduzione

**QGIS headless** è l'esecuzione di QGIS senza finestra grafica — via riga di comando, script Python, oppure integrato in pipeline di automazione. Con una sola variabile d'ambiente (`QT_QPA_PLATFORM=offscreen`), accedi a tutta la potenza di QGIS (algoritmi, PyQGIS, rendering) senza GUI, da terminale, container, CI/CD o server.

Questo documento esplora i vantaggi concreti per sviluppatori, GIS professionali, team di automazione e gestori di infrastrutture.

---

## Vantaggi Tecnici

### Nessuna dipendenza grafica

QGIS headless non richiede X11, Wayland, WSLg o desktop remoto. Gira ovunque ci sia il kernel Linux e una riga di comando: server Linux tradizionali, container Docker, WSL2 Windows, macOS ssh, cloud VM, Raspberry Pi.

**Impatto:** stessa codebase in produzione e sviluppo, niente codice diverso per headless e GUI.

### Consumo di risorse minimale

Senza GUI (finestre, temi, rendering Qt): memoria ridotta di 40–60%, CPU libera, zero latenza di rendering iniziale. Idoneo a workload batch, server a basso costo, container isolati, ambienti ristretti (VPS budget, embedded).

**Footprint tipico:** ~5 GB per l'ambiente completo QGIS; esecuzione in ~200 MB RAM per script leggeri, fino a 1–2 GB per raster grandi.

### Isolamento dall'ambiente desktop

Né profili QGIS desktop, né plugin desktop, né impostazioni GUI interferiscono. L'ambiente `micromamba` è completamente separato — riproducibile, versionato, aggiornabile indipendentemente da QGIS Desktop su Windows/Linux.

**Caso d'uso:** testing di algoritmi senza intaccare la QGIS desktop usata dagli utenti grafici.

### Accesso completo agli algoritmi Processing

Tutti i nativi di QGIS (`native:buffer`, `native:dissolve`, …) e i plugin Processing registrati sono disponibili via `qgis_process` o PyQGIS, senza perdite di funzionalità rispetto alla GUI.

**Programmaticamente:** parametri validati prima dell'esecuzione, errori in JSON, output predicibili (layer in memoria o file).

### Rendering deterministico

Senza variabilità di tema Qt, DPI, font system (usa font integrate nella build QGIS), i PNG generati sono byte-uguali tra runhost diversi. Sfruttabile per test su CI: generi una mappa, la confronti pixel-perfect o hashsum.

**Bonus:** batch rendering di centinaia di progetti senza saturare memoria (un layer alla volta).

### PyQGIS senza trappole

Lo scheletro PyQGIS headless (inizializzazione `QgsApplication`, `gc.collect()`, `exitQgis()`) è documentato e testato. Niente segfault all'uscita (una insidia storica di QGIS desktop) se si rilasciano i layer prima di chiudere.

**Vedi:** il pattern in `examples/hello_qgis.py` — funziona, copialo.

---

## Vantaggi Operativi

### Automazione immediata

Niente interfaccia, niente click manuale: gli algoritmi si avviano con una riga di comando, i parametri sono JSON, l'output è leggibile da script successivi. Ideale per task cronici (elaborazione notturna di DTM, riconciliazione di layer, aggiornamento di database).

```bash
QT_QPA_PLATFORM=offscreen micromamba run -n qgis \
  qgis_process run native:buffer -- INPUT=in.shp DISTANCE=100 OUTPUT=out.gpkg
```

### Integrazione in pipeline CI/CD

Test automatici di algoritmi QGIS in GitHub Actions, GitLab CI, Jenkins — stessa esecuzione su ubuntu-latest, ubuntu-arm64, Windows. La CI valida che il codice PyQGIS non regredisce di versione in versione (QGIS 3.34, 3.40, etc.).

Template workflow già presente nel repo (`.github/workflows/ci.yml`).

### Logging e debugging preservati

Gli output Python (print, logging module) e gli errori QGIS non spariscono in una GUI — vanno diretti a stdout/stderr, catturabili da shell, salvabili in log file, parsabili dal team.

**Tip:** usa `python -u` per non bufferizzare quando pipei con `grep`.

### Reproducibilità garantita

L'ambiente QGIS è pinnato in `environment.yml` (versione esatta, dipendenze, GDAL, PROJ, GEOS, Qt). Chiunque ricloni il repo ottiene l'identico ambiente — niente "ma su questa macchina funziona" quando si passa a quella dell'utente.

**Valore:** baseline per bug reports, comparazione tra ambienti, rollback a una versione precedente.

### Batch processing massivo

Migliaia di file in sequenza, parallelizzabili per CPU/memoria disponibile. Nessun overhead GUI per ogni job: file → algoritmo → output → file successivo, in pochi secondi per feature.

**Esempio reale:** 10.000 centroidi estratti e proiettati in ~2 ore su una singola macchina 4-core.

### Monitoraggio e allert

Script headless può scrivere metriche, logare errori in syslog, inviare notifiche slack/email se un algoritmo fallisce. L'automazione infrastrutturale (Prometheus, Grafana, ELK stack) si integra naturalmente con processi senza GUI.

**Uso:** monitorare la qualità di layer importati, checker di coerenza dati, test di regressione su dataset storici.

---

## Vantaggi Economici

### Riduzione costi di infrastruttura

- **Server leggeri:** no X11, no GPU, no RAM per rendering GUI → hosting su t3.small AWS (1 GB RAM) anzichè m5.xlarge.
- **Container slim:** immagine Docker < 2 GB (base + micromamba + QGIS), containerizzabile in Kubernetes con limiti ristretti (512 MB mem request).
- **No QGIS Desktop:** se l'unico scopo è automazione, non servono 20 licenze Desktop a 600€/anno — QGIS è open source, i costi sono hosting + lavoro.

### Velocità di sviluppo

- **Test in CI:** feedback su errori in minuti, non giorni di manual testing.
- **Debugging remoto:** ssh sul server, runna lo script, vedi l'output in tempo reale — niente VPN per desktop remoto, niente trasferimento 50 MB di immagini di stato.
- **Skill per Claude Code:** il repo fornisce una skill QGIS headless per Claude Code — integri gli algoritmi in workflow e li validi in automatico.

### Manutenzione predittibile

- **Versioni pinnate:** aggiornamenti di QGIS sono controllati, testabili offline prima di produzione.
- **Rollback facile:** se la versione 3.42 ha un bug, torni a 3.40 in una riga di `environment.yml` e ricrei l'env.
- **Supporto open-source:** la comunità QGIS è attiva; issue e fix sono pubblici e tracciabili via GitHub.

---

## Casi d'uso concreti

### 🗺️ Batch rendering di mappe

Hai 500 comuni e un template di progetto QGIS (DTM, ortofoto, confini). Ogni notte scarichi i dati nuovi, lanci uno script Python che renderizza una PNG per comune e la carica in un geo-database. Headless: non occorre una macchina con monitor; l'ultimo rendering di martedì non ostacola l'aggiornamento di venerdì.

### 🔄 Pipeline ETL geografico

Importa shapefile da FTP, dissolvi le feature per provincia, esporta in GeoPackage con validazione spaziale, allerta Slack se fallisce. Orario di esecuzione: 23:00. QGIS headless: niente collegamento desktop, niente utente loggato, script cron o systemd timer.

### ⚡ Test di regressione continua

Un algoritmo custom in un plugin QGIS. Ogni commit, GitHub Actions runna 20 dataset di test e confronta i risultati con le baseline. Headless: test in 5 minuti, costo quasi zero (GitHub runner gratis).

### 📡 API geografica HTTP

Un endpoint `/buffer?shapefile=input.shp&distance=50` che torna il buffer in GeoJSON. Backend Python (FastAPI) chiama `qgis_process` headless e serializza il risultato. Headless: no overhead GUI per ogni request, prevedibile e scalabile.

### 🐳 Microservizio in Docker

Un container Debian slim + micromamba + QGIS headless che orchestri Kubernetes espone via gRPC un endpoint di processing. Headless: container < 2 GB, avviabile in 10 secondi, horizontally scalable (5 pod per gestire il carico).

### 🔍 Ispezione e validazione di progetti

Script che legge `.qgs`, dumpa metadati (layer, CRS, proprietà), valida che gli shapefile siano navigabili. Utile per audit, migrazione tra versioni QGIS, compliance. Headless: rapido, non interferisce con chi lavora in GUI.

---

## Confronto con le alternative

| Aspetto | QGIS headless | QGIS Desktop GUI | GeoServer | PostGIS puro |
|---|---|---|---|---|
| **Setup iniziale** | ✓ ~5 min | ✗ ~30 min + UI | ✗ ~1 ora | ✓ ~10 min |
| **Rendering di mappe** | ✓ Nativo, veloce | ✗ Manual click | ✓ WMS/PNG | ✗ Non supportato |
| **PyQGIS/Algoritmi** | ✓ Accesso completo | ✓ Accesso completo | ✗ No API | ✗ No API |
| **Consumo risorse** | ✓ Minimo (no GUI) | ✗ 1–2 GB sempre | ✗ 2–4 GB JVM | ✓ Minimo (DB only) |
| **CI/CD friendly** | ✓ Test deterministici | ✗ Manual | ✓ API HTTP | ✓ SQL testabile |
| **Curva di apprendimento** | ✓ Minima (se conosci QGIS) | ✓ GUI intuitiva | ✗ Steep (XML, WFS) | ✗ SQL specifico |
| **Reproducibilità** | ✓ Alta (env pinnato) | ✗ Bassa (dipende da config) | ✗ Bassa (config sparsa) | ✓ Alta (SQL is code) |

### Quando *non* usare QGIS headless

Se il tuo team ha bisogno di un'interfaccia grafica interattiva per editare, visualizzare e esplorare i dati, QGIS Desktop o GeoServer sono la scelta naturale. Headless è complementare, non un sostituto — il team usa il desktop per l'editing, l'automazione usa headless per la produzione.

---

## Limitazioni da conoscere

### Isolamento dai plugin desktop

I plugin QGIS desktop **non** sono caricati automaticamente in headless. Se uno dei tuoi algoritmi dipende da un plugin, devi compilarlo come QgsProcessingAlgorithm e registrarlo in headless (o riplasmare l'algoritmo per non dipendere dal plugin).

### Rendering stilistico

Se uno stile usa simboli custom, font esterne o effetti avanzati di Qt, il rendering headless potrebbe divergere leggermente dalla GUI. Le fonti integrate nella build QGIS funzionano; quelle system potrebbero non essere disponibili in container headless.

### Senza GUI per lo sviluppo

Se stai sviluppando un nuovo algoritmo, la GUI di QGIS è utile per testare i parametri in tempo reale. La soluzione: develop in GUI, poi porta il codice in headless. Non è un flusso retrocedere.

### Comportamento deterministico dipendente da ordine

Alcuni algoritmi (dissolvi, aggregazioni) possono avere ordine di output non-deterministico se le feature hanno lo stesso valore di dissoluzione (hash order). Soluzioni: ordina il dataset in input, o usa `sql_result_order` (PostGIS).

---

## Come iniziare

### 1. Setup (WSL2 o Windows)

```bash
git clone https://github.com/pigreco/qgis_headless_wsl2.git
cd qgis_headless_wsl2
bash setup.sh  # WSL2/Linux
# oppure
.\setup.ps1    # Windows PowerShell
```

### 2. Verifica

```bash
QT_QPA_PLATFORM=offscreen micromamba run -n qgis \
  python examples/hello_qgis.py
```

### 3. Esegui il tuo primo algoritmo

```bash
QT_QPA_PLATFORM=offscreen micromamba run -n qgis \
  qgis_process run native:buffer -- \
  INPUT=input.shp DISTANCE=100 OUTPUT=output.gpkg
```

### 4. Approfondisci

- **Documenti:** `README.md` nel repo (setup manuale, troubleshooting)
- **Esempi:** `examples/` (rendering, ispezione progetti, algoritmi custom)
- **CI/CD:** `.github/workflows/ci.yml` (template per GitHub Actions)
- **Skill Claude Code:** `skill/README.md` (integrazione con Claude Code)

---

## Conclusione

QGIS headless è uno strumento **complementare** che sblocca automazione, testing, e scalabilità per chiunque usi QGIS in produzione. Non sostituisce la GUI — la potenzia, permettendo al tuo team di usare QGIS desktop per l'analisi interattiva e QGIS headless per la pipeline robusta e reproducibile.

### Vantaggi principali in breve

- Nessun overhead GUI, consumo risorse minimale
- Automazione immediata: riga di comando, CI/CD, server
- Reproducibilità garantita (ambiente pinnato)
- Accesso completo agli algoritmi QGIS (non è un downgrade)
- Testing continuo e regressione tracciabile

Se la tua pipeline di dati geografici coinvolge elaborazioni batch, aggiornamenti notturni, o deploy automatico, QGIS headless ti risparmierà ore di lavoro manuale e te ne aggiungerà di fiducia — i tuoi algoritmi saranno testati, riproducibili, e scalabili.
