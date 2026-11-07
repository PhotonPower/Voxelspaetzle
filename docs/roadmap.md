# Plan und Stufen

> Erstfassung 2026-11-07. Entscheidungen des Maintainers (offen: D1–D6) stehen am Ende.

## Ziel

Ein Modell des gedruckten Teils aus der CAD-Auslegung, das die bekannten Ursachen von
Abweichungen enthält:

| Ursache | Wirkung | Stufe |
| --- | --- | --- |
| Voxelform (axial 2–4× länger), Slicing und Hatching | Treppen, periodische Rauheit, Flankenfehler | V1–V3 |
| Proximity (Dosisaddition benachbarter Linien) | Aufquellen dichter Bereiche, Kantenverrundung | V2, V3 |
| Brechzahlsprung Immersion/Lack beim Schreiben in die Tiefe | Fokusverzerrung, axiale Skalierung | V2 |
| Polymerisationsgrad räumlich verschieden | Brechzahlgradienten (10⁻³–10⁻²) | V4 |
| Schrumpfung bei Entwicklung und Nachhärtung, Substratbindung | Formfehler (Sag), Brennweitenfehler, Randverzug | V5 |
| Feldwechsel (Stitching), Galvo-/Piezo-Fehler | Stufen, Beugung an Feldgrenzen | V1, V3 |

## Stufen

| Stufe | Inhalt | Abnahme |
| --- | --- | --- |
| **V0 Spezifikation** | Prozessmodell (Dosis ∝ ∫I² dt, Schwelle, Polymerisation), Größen und Einheiten, Konventionen, Datenformate (Schreibbahn, Felder, Ausgaben), Prozessparameter des Druckers (D1), Messdaten (D2); Volltext der Kernquellen | Spezifikation freigegeben |
| **V1 Geometrie und Schreibbahn** | CAD über Nurbforge (STEP, NURBS, optische Flächen aus Raytatouille), Slicing und Hatching (Kontur, Schale und Gerüst, Füllung), Schreibfelder; Import/Export der Maschinendatei, soweit dokumentiert (D3) | Volumen und Oberfläche der Bahn gegen das CAD, Schichtabstände, Feldgrenzen |
| **V2 Schreibfokus und Dosisfeld** | vektorieller Fokus im Lack aus Fieldtracing (NA, Immersion, Tiefe), Zwei-Photonen-Dosis entlang der Bahn auf einem Volumengitter | Fokus gegen Fieldtracing-Sollwerte; Dosis einer Linie und eines Punktes analytisch |
| **V3 Schwellenmodell und Form** | Isofläche der Dosis → Festkörper; Voxel- und Linienbreite über Leistung und Geschwindigkeit; Treppen und Rauheit als Spektrum | analytische Voxelgröße (Gauß-Fokus), Fourieranalyse der Bahn gegen Rauheitsspektrum |
| **V4 Polymerisation und Brechzahl** | Reaktions-Diffusions-Modell (Radikale, Sauerstoffinhibierung, Diffusion) → Polymerisationsgrad; Brechzahl aus dem Polymerisationsgrad (Kalibrierung) | Grenzfälle (ohne Diffusion = Schwellenmodell), Literaturwerte, Messdaten (D2) |
| **V5 Entwicklung und Schrumpfung** | lineare Elastizität mit Eigendehnung ∝ Polymerisationsgrad, Substratbindung; Löser über hp-FEM (Vorschlag) oder kleiner eigener Tetraederlöser (D4) | analytische Fälle (freie Kugel, gebundene Platte), Balken- und Kuppeltests gegen Messung |
| **V6 Ausgabe an die Gesamtsimulation** | Flächenmodell (Fit Zernike/XY plus Restgitter über Nurbforge) für Raytatouille; Brechzahlfeld für BWPM und GRIN-Tracing; Rauheitsspektrum für Streulicht (TIS, SpeckleBem); STL/STEP | Fit-Restfehler, Rundreise Fläche → Raytatouille → Wellenfront |
| **V7 Kalibrierung** | Parameter (Schwelle, Schrumpfung, Brechzahlzuwachs, Proximity) aus Messdaten mit Unsicherheiten | Vorhersage an nicht zur Kalibrierung genutzten Teilen |
| **V8 Vorkompensation und Toleranzen** | inverses Problem: CAD so ändern, dass das **gedruckte** Teil die optische Zielgröße erfüllt (Strehl, Spot, Kopplung); Raytatouilles Optimierer; Toleranzanalyse über die Prozessstreuung | kompensierte Testlinse im Modell; später gedruckt und gemessen |
| **V9 C++/CUDA-Kern** | Dosisfeld und Polymerisation auf großen Gittern (wie BWPM B4) | Sollwertdateien, Laufzeit |
| **V10 Fusion und Pilot** | Adapter und Datenports für RTT-Fusion; Pilot: gedruckte Linse/Kappe auf der Faser (BWPM K6), gemeinsamer Pilot mit Scattuccino (gedruckte OCT-Sonde im Gewebephantom) | Konformitätssatz der Fusion; Vergleich Entwurf – Druckmodell – Messung |

## Entscheidungen (offen, Issues mit Label `frage`)

| Nr. | Frage | Vorschlag |
| --- | --- | --- |
| D1 | Drucker, Lacke, Modus (z. B. Nanoscribe GT2/Quantum X, IP-S/IP-Dip/IP-Q, Dip-in/Öl) | offen – bestimmt Fokusmodell, Lackdaten und Schreibstrategien |
| D2 | Messdaten für die Kalibrierung (Profile, Brechzahl, Fokusmessungen) | offen; bis dahin Literaturwerte |
| D3 | Schreibbahn | eigener Slicer/Hatcher; Import der Maschinendatei, soweit das Format dokumentiert ist |
| D4 | Mechanik für die Schrumpfung | hp-FEM um vektorielle H1-Elastizität erweitern (Vorschlag dort); bis dahin kleiner eigener P1-Tetraederlöser als Referenz |
| D5 | Sprache und Kern | Python-Referenz (V1–V8), C++/CUDA-Kern für Dosis und Polymerisation (V9) |
| D6 | Geometriekern | Nurbforge für CAD, Slicing, Fits und Export (keine fremden CAD-Bibliotheken) |
