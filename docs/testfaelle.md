# Testfälle

Status: ✅ umgesetzt und grün, ◐ teilweise, ○ geplant.

| Nr. | Prüfung | Referenz | Stufe | Status |
| --- | --- | --- | --- | --- |
| P1 | Schreibbahn: Volumen und Oberfläche gegen das CAD, Schichtabstände | analytische Körper (Kugelkappe, Zylinder) | V1 | ○ |
| P2 | Schreibfokus im Lack | Fieldtracing (Debye/Richards-Wolf), Brechzahlsprung analytisch | V2 | ○ |
| P3 | Dosis von Punkt und Linie | analytische Integrale des Gauß-Fokus | V2 | ○ |
| P4 | Voxelbreite und -länge über Leistung | Schwellenmodell analytisch, Literaturmessungen | V3 | ○ |
| P5 | Treppen und Rauheit | Fourieranalyse der Bahn | V3 | ○ |
| P6 | Polymerisation ohne Diffusion = Schwelle | Grenzfall | V4 | ○ |
| P7 | Schrumpfung | freie Kugel, gebundene Platte analytisch | V5 | ○ |
| P8 | Flächenfit und Rundreise nach Raytatouille | Wellenfront der gefitteten Fläche | V6 | ○ |
| P9 | Vorhersage nach Kalibrierung | Messdaten (D2) | V7 | ○ |
| P10 | Vorkompensierte Testlinse | Modell, später Messung | V8 | ○ |
| P11 | Transmission über die Dicke (Beer-Lambert, absorbierender Lack) | schmid2023: ≈ 75 % bei 25 µm, < 5 % bei 250 µm (450–650 nm), > 95 % Absorption bei 500 µm | V4, V6 | ○ |
| P12 | Abschwächung des Schreibfokus im absorbierenden Lack | schmid2023: ≈ 1/mm bei 780 nm, ≈ 70 % Leistung im Fokus (wrapped, Dip-in, Arbeitsabstand 380 µm) | V2 | ○ |
| P13 | Brechzahl IP-Black: Sellmeier (polymerisiert), Sättigung Δn ≈ 0,02 | schmid2023 (Kontrollwerte in `docs/materialdaten.md`, #9) | V4 | ○ |
| P14 | Systemtest Blenden: Michelson-Kontrast ×4 (IP-S-Linse mit IP-Black-Blende), ×7 (Einschrittlinse IP-Black), Schärfentiefe ×3 (telezentrisch) | schmid2023, Messung | V10 | ○ |
| P15 | Hatchwinkel zwischen Schichten: 90° glatt, parallel verformt, 30° Spirale (qualitativ) | schmid2023 | V3 | ○ |
| P16 | eingeschlossene Volumina (Zugang des Entwicklers) | analytische Körper: Hohlkugel, Becher mit und ohne Entwicklungsloch | V5 | ○ |
