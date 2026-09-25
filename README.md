# Portolan Geodata CH/TI - subset iniziale da data.geo.ti.ch

![Mirror CI](https://github.com/<owner>/<repo>/actions/workflows/mirror-publish.yml/badge.svg)

Questo repository e stato rifocalizzato su un sottoinsieme minimo di geodati pubblicati dal Cantone Ticino tramite data.geo.ti.ch.

Scopo attuale:

- partire con 9 dataset reali e facilmente verificabili;
- mantenere una struttura STAC semplice e leggibile;
- evitare, in questa fase, dipendenze e flussi del perimetro federale precedente.

## Sottoinsieme corrente (9 dataset)

Categoria CH (competenza cantonale):

- CH-063.1 - Suddivisioni amministrative - AN
- CH-181.1 - CAP e localita

Categoria TI (diritto cantonale):

- TI-028b.1 - Piani regolatori
- TI-034.1 - Carta dei pericoli - Gradi

Categoria AC (amministrazione cantonale):

- AC-009.1 - Piano direttore cantonale
- AC-077.1 - Repertorio toponomastico ticinese

Categoria CH raster (Cloud Optimized GeoTIFF):

- CH-041.6 Raster - swissALTI3D
- CH-041.6 Raster - swissALTIregio
- CH-041.7 Raster - swissSURFACE3D

## Fonte ufficiale

- Portale: [data.geo.ti.ch](https://data.geo.ti.ch/)
- Ente: Repubblica e Cantone Ticino, Ufficio della geomatica

## Note operative

- Questa base e volutamente essenziale e orientata alla documentazione/catalogazione.
- I metadati possono essere estesi in seguito con link di download puntuali, versioni e workflow ETL.

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

## Fonti metadati

Per questo catalogo i metadati dei singoli dataset sono stati incrociati da:

- `data.geo.ti.ch` per schede, file di download e riferimenti ai dataset;
- `map.geo.ti.ch` per la conferma del contesto cartografico e delle geocategorie;
- `Geoportale Ticino` e le sue condizioni di utilizzo per contesto istituzionale e riferimenti di responsabilità.
