# Portolan Geodata CH/TI - catalogo completo da data.geo.ti.ch

![Mirror CI](https://github.com/mlanini/portolan-geodata-ch/actions/workflows/mirror-publish.yml/badge.svg)

Questo repository contiene un catalogo STAC completo dei geodati pubblicati tramite data.geo.ti.ch, arricchito con riferimenti istituzionali da Geoportale Ticino e map.geo.ti.ch.

Scopo attuale:

- mantenere una struttura STAC semplice e leggibile;
- fornire un indice completo dei dataset pubblicati sul portale cantonale;
- evitare riferimenti a pipeline esterne non necessarie.

## Catalogo corrente (118 dataset)

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
	- Il catalogo viene rigenerato da `scripts/generate_catalog.py` a partire dall'indice ufficiale di `data.geo.ti.ch`.
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
