# Portolan DEMO mirroring data.geo.ti.ch

![Mirror CI](https://github.com/mlanini/portolan-geodata-ch/actions/workflows/mirror-publish.yml/badge.svg)

Questo repository contiene un catalogo STAC parziale dei geodati pubblicati tramite il Geoportale del Cantone Ticino (Svizzera) geo.ti.ch, strutturato come mirror per Portolan.

Portolan è un progetto open source per la pubblicazione e l'uso di dati geospaziali tramite cataloghi statici, formati cloud-native e metadati leggibili sia da persone sia da agenti. Il progetto combina specifiche aperte, un registry pubblico dei cataloghi e tooling dedicato per validazione, pubblicazione ed esplorazione.

Scopo attuale:

- mantenere una struttura STAC chiara, valida e facilmente rigenerabile;
- fornire un indice dei dataset pubblicati sul portale cantonale;
- pubblicare un mirror statico compatibile con il profilo Portolan.

Riferimenti Portolan:

- sito del progetto: [portolan-sdi.org](https://www.portolan-sdi.org/)
- registry pubblico dei cataloghi: [portolan-sdi.org/registry](https://www.portolan-sdi.org/registry)
- specifica del catalogo: [portolan-spec](https://github.com/portolan-sdi/portolan-spec)
- strumenti e componenti dell'ecosistema: [ecosystem](https://www.portolan-sdi.org/#ecosystem)

## Catalogo corrente

Il catalogo indicizza oltre 100 dataset distribuiti in quattro sottocataloghi:

- CH vettori
- TI vettori
- AC vettori
- CH raster

## Fonte ufficiale

- Portale: [data.geo.ti.ch](https://data.geo.ti.ch/)
- Ente: Repubblica e Cantone Ticino, Ufficio della geomatica

## Note operative

- Questa base e volutamente essenziale e orientata alla documentazione/catalogazione.
- Il catalogo viene rigenerato da `scripts/generate_catalog.py` a partire dall'indice ufficiale di `data.geo.ti.ch`.
- I documenti STAC root, category e collection devono includere il link `agents` ad AGENTS.md; per le collezioni il link `describedby` punta a una pagina Markdown esterna stabile.
- Quando cambia la struttura dei link STAC conviene rigenerare con `--force` per riallineare anche le collezioni curate manualmente.

## Pubblicazione come mirror Portolan

Questo repository include una pipeline GitHub Actions che:

- valida tutti i file STAC (`Catalog`/`Collection`/`Item`);
- verifica la raggiungibilita dei link HTTP/HTTPS esterni presenti in `links` e `assets`;
- pubblica il catalogo statico su GitHub Pages dopo una validazione riuscita su `main`.

Workflow: `.github/workflows/mirror-publish.yml`.

Il workflow gira anche ogni giorno (cron) per monitorare la salute dei link esterni.

### Attivazione

1. Pubblica il repository su GitHub.
2. In GitHub, abilita Pages con source `GitHub Actions`.
3. Esegui un push su `main` oppure avvia manualmente il workflow (`workflow_dispatch`).

### URL del catalogo

Una volta completato il deploy, il root STAC e disponibile a:

- `https://<owner>.github.io/<repo>/catalog.json`

Esempio sottocatalogo:

- `https://<owner>.github.io/<repo>/ch-base/catalog.json`

### Pubblicazione nel registry Portolan

Per registrare il catalogo nel registry pubblico di Portolan (https://www.portolan-sdi.org/registry), è possibile farlo in due modalità:

#### 1. Riferimento esterno (consigliato)

Fornisci semplicemente l'URL del root STAC al registry di Portolan, senza duplicare i file:

- Accedi a [portolan-sdi.org/registry](https://www.portolan-sdi.org/registry)
- Usa l'opzione "Add Catalog" o "Submit Catalog"
- Inserisci l'URL root del catalogo:
  ```
  https://<owner>.github.io/<repo>/catalog.json
  ```

Il registry Portolan leggerà dinamicamente i metadati dal tuo catalogo ogni volta che viene acceduto. **Questo approccio è consigliato** perché:
- Non richiede duplicazione dei dati
- Mantiene automaticamente i metadati sincronizzati
- Minimizza i costi di storage

#### 2. Copia statica nel repository Portolan

Se preferisci una copia statica nel registry Portolan:

- Fork il repository [portolan-sdi/registry](https://github.com/portolan-sdi/registry)
- Aggiungi il tuo catalogo nella cartella appropriata del registry
- Crea una pull request
- Una volta approvata, il tuo catalogo sarà disponibile permanentemente nel registry

Consulta la documentazione di Portolan per i dettagli di integrazione: [Portolan Ecosystem](https://www.portolan-sdi.org/#ecosystem)

## Fonti metadati

Per questo catalogo i metadati dei singoli dataset sono stati incrociati da:

- `data.geo.ti.ch` per schede, file di download e riferimenti ai dataset;
- `map.geo.ti.ch` per la conferma del contesto cartografico e delle geocategorie;
- `Geoportale Ticino` e le sue condizioni di utilizzo per contesto istituzionale e riferimenti di responsabilità.
