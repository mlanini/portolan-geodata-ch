# AGENTS.md

Repository rifocalizzato su un subset iniziale di geodati da data.geo.ti.ch.

## Obiettivo

- mantenere una base STAC minima, chiara e facilmente estendibile;
- lavorare su 9 dataset reali del portale cantonale;
- escludere il perimetro federale precedente in questa fase.

## Collezioni presenti

- ch-base/ch-063-1-suddivisioni-amministrative
- ch-base/ch-181-1-cap-localita
- ti-base/ti-028b-1-piani-regolatori
- ti-base/ti-034-1-carta-pericoli-gradi
- ac/ac-009-1-piano-direttore-cantonale
- ac/ac-077-1-repertorio-toponomastico-ticinese
- ch-raster/ch-041-6r-swissalti3d
- ch-raster/ch-041-6r-swissaltiregio
- ch-raster/ch-041-7r-swisssurface3d

## Regole operative

- usare come fonte primaria il portale https://data.geo.ti.ch/;
- non reintrodurre riferimenti alla pipeline federale precedente;
- mantenere nomenclatura esplicita con codice dataset nel path.
