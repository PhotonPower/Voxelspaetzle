# Plan und Stufen

> Erstfassung 2026-11-07; ergänzt 2026-11-09 um den Referenzprozess schmid2023 (absorbierende
> Lacke, Mehrmaterialdruck, Schreibstrategie). Entscheidungen des Maintainers stehen am Ende.

## Ziel

Ein Modell des gedruckten Teils aus der CAD-Auslegung, das die bekannten Ursachen von
Abweichungen enthält:

| Ursache | Wirkung | Stufe |
| --- | --- | --- |
| Voxelform (axial 2–4× länger), Slicing und Hatching | Treppen, periodische Rauheit, Flankenfehler | V1–V3 |
| Proximity (Dosisaddition benachbarter Linien) | Aufquellen dichter Bereiche, Kantenverrundung | V2, V3 |
| Brechzahlsprung Immersion/Lack beim Schreiben in die Tiefe | Fokusverzerrung, axiale Skalierung | V2 |
| Absorption des Lacks bei der Schreibwellenlänge (IP-Black ≈ 1/mm bei 780 nm) | geringere Fokusintensität; Dosis ∝ I² hängt vom Lackweg ab (Modus: Dip-in, wrapped, Öl) | V2 |
| Polymerisationsgrad räumlich verschieden | Brechzahlgradienten (10⁻³–10⁻²) | V4 |
| Absorption bei der Gebrauchswellenlänge (absorbierende Lacke) | gedruckte Blenden; Teiltransparenz dünner Bereiche, Apodisation an Blendenrändern | V4, V6 |
| Schrumpfung bei Entwicklung und Nachhärtung, Substratbindung | Formfehler (Sag), Brennweitenfehler, Randverzug | V5 |
| Zugang des Entwicklers | eingeschlossener flüssiger Lack in Hohlräumen (Abhilfe: Entwicklungslöcher) | V5 |
| Mehrmaterialdruck (mehrere Lacke und Schreibjobs, Zwischenentwicklung) | Justierfehler zwischen den Jobs, Grenzflächen zwischen Lacken | V1, V8 |
| Schreibstrategie: Hatchwinkel zwischen Schichten, Piezo-Einschwingzeit | Verformung bei parallelen Schichten, Spiralstruktur bei 30°; Abhilfe 90° und längere Einschwingzeit | V1, V3 |
| Feldwechsel (Stitching), Galvo-/Piezo-Fehler | Stufen, Beugung an Feldgrenzen | V1, V3 |

## Referenzprozess

Bis zur Entscheidung D1 ist der Prozess aus schmid2023 der Referenzfall (Daten in
[materialdaten.md](materialdaten.md)): Nanoscribe Photonic Professional GT, 780 nm, 25×/0.8 im
Dip-in-Modus mit „wrapped objective“, Lacke IP-S und IP-Black. Die Demonstratoren des Papers
dienen als Referenzteile: Lochkamera aus IP-Black, IP-S-Linse mit IP-Black-Blende (zwei
Schreibjobs), telezentrische Linse mit Blende in der vorderen Brennebene, Linse und Blende in
einem Schritt aus IP-Black.

## Stufen

| Stufe | Inhalt | Abnahme |
| --- | --- | --- |
| **V0 Spezifikation** | Prozessmodell (Dosis ∝ ∫I² dt, Schwelle, Polymerisation), Größen und Einheiten, Konventionen, Materialmodell je Volumen (Lack, reelle Brechzahl und Absorptionskoeffizient je Wellenlänge, D7), Datenformate (Schreibbahn, Schreibjobs, Felder, Ausgaben), Prozessparameter des Druckers (D1), Lackdaten aus der Literatur (`docs/materialdaten.md`), Messdaten (D2); Volltext der Kernquellen | Spezifikation freigegeben |
| **V1 Geometrie und Schreibbahn** | CAD über Nurbforge (STEP, NURBS, optische Flächen aus Raytatouille), Slicing und Hatching (Kontur, Schale und Gerüst, Füllung), Hatchwinkel je Schicht, Schreibfelder; Schreibjobs mit Lack, Reihenfolge, Zwischenentwicklung und Justiermarkern; Import/Export der Maschinendatei, soweit dokumentiert (D3) | Volumen und Oberfläche der Bahn gegen das CAD, Schichtabstände, Feldgrenzen, Lack je Volumen |
| **V2 Schreibfokus und Dosisfeld** | vektorieller Fokus im Lack aus Fieldtracing (NA, Immersion, Tiefe), Abschwächung entlang des Strahlwegs durch flüssigen und belichteten Lack (Beer-Lambert; Weglänge je nach Modus), Zwei-Photonen-Dosis entlang der Bahn auf einem Volumengitter | Fokus gegen Fieldtracing-Sollwerte; Dosis einer Linie und eines Punktes analytisch; Abschwächung gegen schmid2023 (P12) |
| **V3 Schwellenmodell und Form** | Isofläche der Dosis → Festkörper; Voxel- und Linienbreite über Leistung und Geschwindigkeit; Treppen und Rauheit als Spektrum | analytische Voxelgröße (Gauß-Fokus), Fourieranalyse der Bahn gegen Rauheitsspektrum; Hatchwinkel qualitativ (P15) |
| **V4 Polymerisation und Brechzahl** | Reaktions-Diffusions-Modell (Radikale, Sauerstoffinhibierung, Diffusion) → Polymerisationsgrad; Brechzahl und Absorption aus dem Polymerisationsgrad (Kalibrierung) | Grenzfälle (ohne Diffusion = Schwellenmodell), Literaturwerte (P13), Messdaten (D2) |
| **V5 Entwicklung und Schrumpfung** | lineare Elastizität mit Eigendehnung ∝ Polymerisationsgrad, Substratbindung; Löser über hp-FEM (Vorschlag) oder kleiner eigener Tetraederlöser (D4); Zugang des Entwicklers (eingeschlossene Volumina) | analytische Fälle (freie Kugel, gebundene Platte), Balken- und Kuppeltests gegen Messung; eingeschlossene Volumina (P16) |
| **V6 Ausgabe an die Gesamtsimulation** | Flächenmodell (Fit Zernike/XY plus Restgitter über Nurbforge) für Raytatouille; Brechzahl- und Absorptionsfeld für BWPM und GRIN-Tracing (Blenden, Apodisation); Rauheitsspektrum für Streulicht (TIS, SpeckleBem); STL/STEP | Fit-Restfehler, Rundreise Fläche → Raytatouille → Wellenfront; Transmission über die Dicke (P11) |
| **V7 Kalibrierung** | Parameter (Schwelle, Schrumpfung, Brechzahlzuwachs, Proximity) aus Messdaten mit Unsicherheiten | Vorhersage an nicht zur Kalibrierung genutzten Teilen |
| **V8 Vorkompensation und Toleranzen** | inverses Problem: CAD so ändern, dass das **gedruckte** Teil die optische Zielgröße erfüllt (Strehl, Spot, Kopplung); Raytatouilles Optimierer; Toleranzanalyse über die Prozessstreuung einschließlich Justierfehler zwischen Schreibjobs | kompensierte Testlinse im Modell; später gedruckt und gemessen |
| **V9 C++/CUDA-Kern** | Dosisfeld und Polymerisation auf großen Gittern (wie BWPM B4) | Sollwertdateien, Laufzeit |
| **V10 Fusion und Pilot** | Adapter und Datenports für RTT-Fusion; Pilot: gedruckte Linse/Kappe auf der Faser (BWPM K6), gemeinsamer Pilot mit Scattuccino (gedruckte OCT-Sonde im Gewebephantom); Referenzteile aus schmid2023 | Konformitätssatz der Fusion; Vergleich Entwurf – Druckmodell – Messung; Kontrast und Schärfentiefe der Referenzteile (P14) |

## Entscheidungen (Issues mit Label `frage`)

| Nr. | Frage | Stand |
| --- | --- | --- |
| D1 | Drucker, Lacke, Modus (z. B. Nanoscribe GT2/Quantum X, IP-S/IP-Dip/IP-Q, Dip-in/Öl) | offen (#1) – bestimmt Fokusmodell, Lackdaten und Schreibstrategien. **Vorschlag** (2026-11-09): Referenzprozess schmid2023 (Abschnitt oben); Bestätigung aus dem Labor offen |
| D2 | Messdaten für die Kalibrierung (Profile, Brechzahl, Fokusmessungen) | offen (#2); bis dahin Literaturwerte, zuerst schmid2023 (`docs/materialdaten.md`) |
| D3 | Schreibbahn | **freigegeben** 2026-11-07 (#3): eigener Slicer/Hatcher; Import der Maschinendatei, soweit das Format dokumentiert ist |
| D4 | Mechanik für die Schrumpfung | **freigegeben** 2026-11-07 (#4): hp-FEM um vektorielle H1-Elastizität erweitern (Vorschlag dort); bis dahin kleiner eigener P1-Tetraederlöser als Referenz |
| D5 | Sprache und Kern | **freigegeben** 2026-11-07 (#5): Python-Referenz (V1–V8), C++/CUDA-Kern für Dosis und Polymerisation (V9) |
| D6 | Geometriekern | **freigegeben** 2026-11-07 (#6): Nurbforge für CAD, Slicing, Fits und Export (keine fremden CAD-Bibliotheken) |
| D7 | Absorption in Konventionen und Datenformaten | offen (#8). **Vorschlag:** reelle Brechzahl n plus Intensitäts-Absorptionskoeffizient α in 1/mm je Wellenlänge, getrennt für Schreib- und Gebrauchswellenlänge; in Feldrechnungen n + iκ (`docs/konventionen.md`) |
