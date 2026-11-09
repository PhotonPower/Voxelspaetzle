# Vorschlag für Nurbforge: Hatching aus Schnittschleifen

> Entwurf aus Voxelspaetzle (V1, D3, D6); in Nurbforge nur lesend. Stand Nurbforge 0.6.0
> (`ee0edd8`, gelesen 2026-11-09). Zur Entscheidung durch den Maintainer.

## Kontext

`section(shell, plane)` liefert orientierte geschlossene Schleifen (Körper links), exakt bei
Extrusionen und Rotationen; `critical_heights` findet die Höhen, an denen sich die Topologie
ändert. Für die Schreibbahn eines 2PP-Druckers fehlt der nächste Schritt: die Füllung jeder
Schicht mit Bahnlinien (Hatching) und Konturlinien.

## Vorschlag

`hatch(loops, direction, spacing, phase=0, contours=[], min_length=0)` in der Schnittebene:

- Parallelen in Richtung `direction` mit Abstand `spacing`, verschoben um `phase`; Schnitt mit den
  Schleifenkurven (Kurve–Kurve-Schnitt vorhanden), Parameter sortieren, Innen nach der
  Orientierung (nicht gerade/ungerade, damit Inseln und Löcher stimmen); tangentiale Berührungen
  wie bei den Booleschen Operationen mit Toleranz.
- Konturen als Offset-Kurven nach innen (`contours` = Liste von Abständen; planare Offsets
  vorhanden).
- Ausgabe: Liste von Segmenten (Start, Ende) und Konturkurven, je Schleife zugeordnet.

Die Schreibstrategie (Winkel je Schicht, Richtung je Bereich, z. B. entlang Gitterlinien wie in
toulouse2021) bleibt in Voxelspaetzle; Nurbforge liefert nur die Geometrie.

## Übergang

Bis dahin baut Voxelspaetzle das Hatching in V1 auf `section` selbst, auf Polygonen der Schleifen
(NumPy). Die Nurbforge-Version wäre exakt und schneller und könnte auch anderen Programmen dienen.

## Abnahme (Vorschlag)

Kreis: Sehnenlängen analytisch; gedrehtes Quadrat: Segmentzahl und -längen exakt; Summe
spacing × Segmentlänge gegen die Fläche der Schleifen (Green) mit Fehler O(spacing); Ring (Loch)
und zwei Inseln; Linie tangential an einer Schleife (keine Nullsegmente).
