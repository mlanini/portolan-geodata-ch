# AGENTS.md

Repository dedicato a un catalogo STAC completo dei geodati pubblicati da data.geo.ti.ch.

## Obiettivo

- mantenere un catalogo STAC completo, chiaro e facilmente rigenerabile;
- usare come fonte primaria il portale cantonale e i riferimenti istituzionali collegati;
- preservare la nomenclatura esplicita con codice dataset nel path.

## Collezioni documentate

Il catalogo contiene 118 dataset. Le collezioni sotto elencate hanno anche un README locale dedicato:

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
- mantenere nomenclatura esplicita con codice dataset nel path;
- mantenere nei documenti STAC i link `describedby` verso il README pertinente e `agents` verso AGENTS.md;
- preferire aggiornamenti nel generatore quando una modifica deve propagarsi a piu collezioni.
