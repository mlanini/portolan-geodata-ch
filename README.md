# Portolan Geodata CH/TI - subset iniziale da data.geo.ti.ch

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

- Portale: https://data.geo.ti.ch/
- Ente: Repubblica e Cantone Ticino, Ufficio della geomatica

## Note operative

- Questa base e volutamente essenziale e orientata alla documentazione/catalogazione.
- I metadati possono essere estesi in seguito con link di download puntuali, versioni e workflow ETL.
