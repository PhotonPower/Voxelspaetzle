# Testfälle

Status: ✅ umgesetzt und grün, ◐ teilweise, ○ geplant.

| Nr. | Prüfung | Referenz | Stufe | Status |
| --- | --- | --- | --- | --- |
| P1 | Schreibbahn: Volumen und Oberfläche gegen das CAD, Schichtabstände | analytische Körper (Kugelkappe, Zylinder) | V1 | ○ |
| P2 | Schreibfokus im Lack | Fieldtracing (Debye/Richards-Wolf), Brechzahlsprung analytisch | V2 | ○ |
| P3 | Dosis von Punkt und Linie | Gauß-Näherung analytisch (Spezifikation §3.6); Dosis ∝ \|E\|⁴·Δt (fischer2013, Abschn. 3); lineare Akkumulation (§3.5) | V2 | ○ |
| P4 | Voxel- und Linienbreite über Leistung und Geschwindigkeit | d = w √(ln(D₀/D_th)) (Spezifikation §3.6); Warnung unter ≈ 40 % der Halbwertsbreite der Dosis (fischer2013, Abschn. 2); Literaturmessungen | V3 | ○ |
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
| P17 | kleinste auflösbare Gitterperiode im Vollmaterial (Proximity) | toulouse2021 (Supplementary, Abb. S3): unter 650 nm Periode keine aufgelöste Topografie (IP-Dip, Slicing 100 nm, Hatching 250 nm); kleinste gedruckte Periode nicht angegeben, daher nur Schranke; Strukturen sonst bis ≈ 100 nm | V2, V3 | ○ |
| P18 | Dispersion des gedruckten Spektrometers gegen den Entwurf | toulouse2021: 9,1 ± 1,1 nm/µm (532 nm), 7,2 ± 0,7 nm/µm (633 nm), größer als im Raytracing; Ursache (Schrumpfung) im Modell bestätigen oder widerlegen | V5, V6 | ○ |
| P19 | Auflösungsverlust durch Rauheit | toulouse2021: 17,8 ± 1,7 nm gemessen gegen 14,5 ± 1,4 nm (WPM) bei 633 nm; Rauheit IP-Dip ≈ 100 nm | V3, V6 | ○ |
| P20 | Spalt aus Tinte im gedruckten Becken und Trennung der Beugungsordnungen | toulouse2021: Spaltbreite 1,3 µm (FWHM), 0. Ordnung räumlich getrennt von der 1.; Rauschen 5–20 %, Rauschfläche im Mittel 51 % der Signalfläche (Supplementary, Abschnitt 4) | V6, V10 | ○ |
| P21 | Profiltreue des geblazeten Gitters (Dreiecksprofil, Nebenordnungen) | toulouse2021 (Supplementary, Abb. S3c, d): Profil nur angenähert, qualitativ im REM; Effizienzverlust in Nebenordnungen | V3, V6 | ○ |
| P22 | Rundreise gedrucktes Teil → STEP → FourierGrating | Nurbforge `read_step_named`: Körper, Namen und Volumen unverändert; FourierGrating: Richtungen der Ordnungen nach der Gittergleichung, Energieerhaltung über die Ordnungen (wie RTT-Fusion K1) | V6 | ○ |
| P23 | Auflösungsgrenzen des Fokus | fischer2013: Gl. 1–3; verallgemeinertes Sparrow-Kriterium mit vektorieller Debye-Rechnung (λ = 0,8 µm, NA = 1,4, n = 1,52, zirkular): Zweiphotonen a_xy = 200 nm, a_z = 500 nm; Einphotonen 288 nm, 726 nm | V2 | ○ |
