# Plan und Stufen

> Erstfassung 2026-11-07; ergänzt 2026-11-09 um die Referenzprozesse schmid2023 (absorbierende
> Lacke, Mehrmaterialdruck, Schreibstrategie) und toulouse2021 (feine diffraktive Strukturen,
> Rauheit, Schrumpfung im System, Tintenfüllung). Entscheidungen des Maintainers stehen am Ende.

## Ziel

Ein Modell des gedruckten Teils aus der CAD-Auslegung, das die bekannten Ursachen von
Abweichungen enthält:

| Ursache | Wirkung | Stufe |
| --- | --- | --- |
| Voxelform (axial 2–4× länger), Slicing und Hatching | Treppen, periodische Rauheit, Flankenfehler | V1–V3 |
| Proximity (Dosisaddition benachbarter Linien) | Aufquellen dichter Bereiche, Kantenverrundung; Grenze der auflösbaren Gitterperiode im Vollmaterial (IP-Dip: 650 nm) | V2, V3 |
| Brechzahlsprung Immersion/Lack beim Schreiben in die Tiefe | Fokusverzerrung, axiale Skalierung | V2 |
| Absorption des Lacks bei der Schreibwellenlänge (IP-Black ≈ 1/mm bei 780 nm) | geringere Fokusintensität; Dosis ∝ I² hängt vom Lackweg ab (Modus: Dip-in, wrapped, Öl) | V2 |
| Polymerisationsgrad räumlich verschieden | Brechzahlgradienten (10⁻³–10⁻²) | V4 |
| Absorption bei der Gebrauchswellenlänge (absorbierende Lacke) | gedruckte Blenden; Teiltransparenz dünner Bereiche, Apodisation an Blendenrändern | V4, V6 |
| Schrumpfung bei Entwicklung und Nachhärtung, Substratbindung | Formfehler (Sag), Brennweitenfehler, Randverzug; Fokuslage und Dispersion in Systemen (Spektrometer) | V5 |
| Oberflächenrauheit je Lack (IP-Dip ≈ 100 nm, IP-S < 10 nm rms) | Streulicht, Rauschen, Auflösungsverlust refraktiver und diffraktiver Optik | V3, V6 |
| Zugang des Entwicklers | eingeschlossener flüssiger Lack in Hohlräumen (Abhilfe: Entwicklungslöcher) | V5 |
| Mehrmaterialdruck (mehrere Lacke und Schreibjobs, Zwischenentwicklung) | Justierfehler zwischen den Jobs, Grenzflächen zwischen Lacken | V1, V8 |
| Schreibstrategie: Hatchwinkel zwischen Schichten, Hatchrichtung an Merkmalen (Gitterlinien), Piezo-Einschwingzeit | Verformung bei parallelen Schichten, Spiralstruktur bei 30°; Abhilfe 90° und längere Einschwingzeit; Profiltreue feiner Gitter | V1, V3 |
| Nachbearbeitung ohne 2PP (Tinte füllen, Metall aufdampfen) | Füllgrad, Lage und Absorption der Fremdmaterialien; Spaltbreite, Streulicht | V1, V6, V8 |
| Feldwechsel (Stitching), Galvo-/Piezo-Fehler | Stufen, Beugung an Feldgrenzen | V1, V3 |

## Referenzprozesse

Bis zur Entscheidung D1 dienen zwei veröffentlichte Prozesse als Referenzfälle (Daten in
[materialdaten.md](materialdaten.md)); D1 wird als Prozessbibliothek angelegt, nicht als einzelnes
Setup.

- **A – schmid2023:** Nanoscribe Photonic Professional GT, 780 nm, 25×/0.8 im Dip-in-Modus mit
  „wrapped objective“, Lacke IP-S und IP-Black. Referenzteile: Lochkamera aus IP-Black, IP-S-Linse
  mit IP-Black-Blende (zwei Schreibjobs), telezentrische Linse mit Blende in der vorderen
  Brennebene, Linse und Blende in einem Schritt aus IP-Black.
- **B – toulouse2021:** Photonic Professional GT2, Dip-in, IP-Dip mit Slicing 100 nm und Hatching
  250 nm entlang der Gitterlinien; Spalt aus Silbertinte (NPS-J) im mitgedruckten Becken.
  Referenzteil: Mikrospektrometer 490–690 nm in 100 × 100 × 300 µm³ mit gechirptem, geblazetem
  Gitter (650–860 nm).

## Stufen

| Stufe | Inhalt | Abnahme |
| --- | --- | --- |
| **V0 Spezifikation** | Prozessmodell (Dosis ∝ ∫I² dt, Schwelle, Polymerisation), Größen und Einheiten, Konventionen, Materialmodell je Volumen (Lack oder Füllmaterial, reelle Brechzahl und Absorptionskoeffizient je Wellenlänge, D7), Prozessbibliothek (D1), Datenformate (Schreibbahn, Schreibjobs, Felder, Ausgaben), Prozessparameter des Druckers (D1), Lackdaten aus der Literatur (`docs/materialdaten.md`), Messdaten (D2); Volltext der Kernquellen | Spezifikation freigegeben |
| **V1 Geometrie und Schreibbahn** | CAD über Nurbforge (STEP, NURBS, optische Flächen aus Raytatouille), Slicing und Hatching (Kontur, Schale und Gerüst, Füllung), Hatchwinkel je Schicht und Hatchrichtung je Bereich (z. B. entlang Gitterlinien), Schreibfelder; Schreibjobs mit Lack, Reihenfolge, Zwischenentwicklung und Justiermarkern; Nachbearbeitung (Tinte füllen) als Prozessschritt mit Füllvolumen; Import/Export der Maschinendatei, soweit dokumentiert (D3) | Volumen und Oberfläche der Bahn gegen das CAD, Schichtabstände, Feldgrenzen, Lack je Volumen |
| **V2 Schreibfokus und Dosisfeld** | vektorieller Fokus im Lack aus Fieldtracing (`debye_focus`, `richards_wolf` im homogenen Medium – ausreichend für Dip-in; Öl-Modus mit Grenzfläche und Tiefenaberration braucht eine Erweiterung von Fieldtracing, falls D1 ihn enthält), Abschwächung entlang des Strahlwegs durch flüssigen und belichteten Lack (exp(−4πκt/λ); Weglänge je nach Modus), Zwei-Photonen-Dosis entlang der Bahn auf einem Volumengitter | Fokus gegen Fieldtracing-Sollwerte; Dosis einer Linie und eines Punktes analytisch; Abschwächung gegen schmid2023 (P12) |
| **V3 Schwellenmodell und Form** | Isofläche der Dosis → Festkörper; Voxel- und Linienbreite über Leistung und Geschwindigkeit; Treppen und Rauheit als Spektrum | analytische Voxelgröße (Gauß-Fokus), Fourieranalyse der Bahn gegen Rauheitsspektrum; Hatchwinkel qualitativ (P15); kleinste Gitterperiode (P17), Gitterprofil (P21); Rauheit (P19) |
| **V4 Polymerisation und Brechzahl** | Reaktions-Diffusions-Modell (Radikale, Sauerstoffinhibierung, Diffusion) → Polymerisationsgrad; Brechzahl und Absorption aus dem Polymerisationsgrad (Kalibrierung) | Grenzfälle (ohne Diffusion = Schwellenmodell), Literaturwerte (P13), Messdaten (D2) |
| **V5 Entwicklung und Schrumpfung** | lineare Elastizität mit Eigendehnung ∝ Polymerisationsgrad, Substratbindung; Löser über hp-FEM (Vorschlag) oder kleiner eigener Tetraederlöser (D4); Zugang des Entwicklers (eingeschlossene Volumina) | analytische Fälle (freie Kugel, gebundene Platte), Balken- und Kuppeltests gegen Messung; eingeschlossene Volumina (P16); Dispersion des Spektrometers (P18) |
| **V6 Ausgabe an die Gesamtsimulation** | Ausgaben in den Eingangsformaten der Programme (`docs/abhaengigkeiten.md`): gedruckte Form als STEP in µm mit benannten Körpern je Material und Prozessschritt (Nurbforge; FourierGrating für die Beugungseffizienz gedruckter Gitter); (n, κ)-Volumengitter für BWPM, quantisiert auf Brechzahlstufen mit kontrolliertem Fehler (Blenden, Apodisation, Brechzahlgradienten); Höhenkarten der Oberfläche für SpeckleBem (periodische Rauheit aus Hatching und Treppen) und als Rauheitsspektrum (TIS); Flächenfits (Zernike/XY plus Restgitter über Nurbforge) für Raytatouille, sobald Zernike-Sag, XY-Polynom bzw. Grid-Sag dort umgesetzt sind; Brechzahlfeld für GRIN-Tracing erst mit Raytatouille X1; Datenport über RTT-Fusion (Vorschlag) | Fit-Restfehler, Rundreise Fläche → Raytatouille → Wellenfront; STEP-Rundreise und Gittergleichung über FourierGrating (P22); Quantisierungsfehler des BWPM-Gitters (Konvergenz in der Zahl der Stufen); Transmission über die Dicke (P11); Spalt und Beugungsordnungen (P20) |
| **V7 Kalibrierung** | Parameter (Schwelle, Schrumpfung, Brechzahlzuwachs, Proximity) aus Messdaten mit Unsicherheiten | Vorhersage an nicht zur Kalibrierung genutzten Teilen |
| **V8 Vorkompensation und Toleranzen** | inverses Problem: CAD so ändern, dass das **gedruckte** Teil die optische Zielgröße erfüllt (Strehl, Spot, Kopplung); Raytatouilles Optimierer; Toleranzanalyse über die Prozessstreuung einschließlich Justierfehler zwischen Schreibjobs | kompensierte Testlinse im Modell; später gedruckt und gemessen |
| **V9 C++/CUDA-Kern** | Dosisfeld und Polymerisation auf großen Gittern (wie BWPM B4) | Sollwertdateien, Laufzeit |
| **V10 Fusion und Pilot** | Adapter und Datenports für RTT-Fusion; Pilot: gedruckte Linse/Kappe auf der Faser (BWPM K6), gemeinsamer Pilot mit Scattuccino (gedruckte OCT-Sonde im Gewebephantom); Referenzteile aus schmid2023 und toulouse2021 | Konformitätssatz der Fusion; Vergleich Entwurf – Druckmodell – Messung; Kontrast und Schärfentiefe (P14), Spektrometer (P18–P20) |

## Entscheidungen (Issues mit Label `frage`)

| Nr. | Frage | Stand |
| --- | --- | --- |
| D1 | Drucker, Lacke, Modus (z. B. Nanoscribe GT2/Quantum X, IP-S/IP-Dip/IP-Q, Dip-in/Öl) | offen (#1) – bestimmt Fokusmodell, Lackdaten und Schreibstrategien. **Vorschlag** (2026-11-09): Prozessbibliothek statt eines einzelnen Setups (mindestens GT und GT2; IP-S, IP-Dip, IP-Black; Nachbearbeitung mit Tinte), zunächst mit den Referenzprozessen A und B (Abschnitt oben); Bestätigung aus dem Labor offen |
| D2 | Messdaten für die Kalibrierung (Profile, Brechzahl, Fokusmessungen) | offen (#2); bis dahin Literaturwerte, zuerst schmid2023 (`docs/materialdaten.md`) |
| D3 | Schreibbahn | **freigegeben** 2026-11-07 (#3): eigener Slicer/Hatcher; Import der Maschinendatei, soweit das Format dokumentiert ist |
| D4 | Mechanik für die Schrumpfung | **freigegeben** 2026-11-07 (#4): hp-FEM um vektorielle H1-Elastizität erweitern (Vorschlag dort); bis dahin kleiner eigener P1-Tetraederlöser als Referenz |
| D5 | Sprache und Kern | **freigegeben** 2026-11-07 (#5): Python-Referenz (V1–V8), C++/CUDA-Kern für Dosis und Polymerisation (V9) |
| D6 | Geometriekern | **freigegeben** 2026-11-07 (#6): Nurbforge für CAD, Slicing, Fits und Export (keine fremden CAD-Bibliotheken) |
| D7 | Absorption in Konventionen und Datenformaten | offen (#8). **Vorschlag** (2026-11-09 an das Framework angeglichen): komplexe Brechzahl n + iκ wie Raytatouille, BWPM und RTT-Fusion, Materialdaten als Dispersionsformel und n/k-Tabellen getrennt für Schreib- und Gebrauchswellenlänge; α nur beim Einlesen von Messungen; Material je Volumen einschließlich Füllmaterialien, als benannte STEP-Körper (`docs/konventionen.md`) |
