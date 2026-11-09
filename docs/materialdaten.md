# Materialdaten (Literatur)

> Literaturwerte bis zu eigenen Messungen (D2); Referenzprozesse zu D1. Jede Angabe mit Quelle (`docs/quellen.md`).
> **Abgeleitet** markierte Werte stehen nicht in der Quelle, sondern sind daraus berechnet; sie
> sind keine Sollwerte für Tests, solange der Maintainer sie nicht freigibt.

## Referenzprozess A (schmid2023)

| Größe | Wert |
| --- | --- |
| Drucker | Nanoscribe Photonic Professional GT |
| Laser | 780 nm, 80 MHz; 100 % Leistung ≈ 58 mW (Pulsenergie 725 pJ) |
| Objektiv | Zeiss LCI Plan-Neofluar 25×/0.8, Arbeitsabstand 380 µm |
| Modus | Dip-in mit „wrapped objective“ (toulouse2022): konstanter Strahlweg durch den Lack, daher konstante Fokusintensität; Strukturhöhen über dem Arbeitsabstand möglich (500 µm gezeigt) |
| Substrat | ITO-beschichtetes Glas |
| Entwicklung | mr-Dev 600, 15 min; danach Isopropanol, 5 min; hohe Strukturen mit Entwicklungslöchern im unteren Teil |
| Mehrmaterialdruck | erst IP-S, Entwicklung, dann IP-Black; Justierung über Marker aus dem ersten Schreibjob |

Intensitätsangaben im Paper: 3,7 TW/cm² (100 %), 2,6 TW/cm² (70 %). Pulsdauer und Fleckgröße
sind nicht angegeben. **Abgeleitet:** mit 100 fs und einem Fleckdurchmesser λ/(2NA) ergeben sich
3,9 TW/cm² – vermutlich die Annahmen der Autoren (toulouse2021 nennt für die GT2 etwa 100 fs an
der Quelle). Das Modell rechnet mit Pulsenergie bzw. Leistung,
nicht mit diesen Intensitäten.

### Schreibparameter

| Bauteil | Lack | Slicing | Hatching | Leistung | Scangeschwindigkeit |
| --- | --- | --- | --- | --- | --- |
| Blenden, Transmissions-Patches | IP-Black | 2 µm | 1 µm | 100 % (725 pJ) | 40 mm/s |
| Brechzahl-Patch (Ø 5 mm, 250 µm hoch) | IP-Black | 0,2 µm | 0,5 µm | wie Patches | wie Patches |
| Linsenoberfläche | IP-Black | 0,2 µm | 0,5 µm | nicht angegeben | nicht angegeben |
| Linse (Ø 150 µm, 20 µm hoch) | IP-S | 0,2 µm | 0,5 µm | 70 % (508 pJ) | 50 mm/s |

Schreibstrategie für die IP-Black-Linse: Hatchwinkel 90° zwischen den Schichten am besten;
parallele Schichten führen zu Verformungen, 30° zu einer kleinen Spiralstruktur auf der Linse.
Piezo-Einschwingzeit von 2 s oder 5 s verringert die Verformungen.

## Referenzprozess B (toulouse2021)

Mikrospektrometer (490–690 nm) in 100 × 100 × 300 µm³, in einem Schritt gedruckt; Spalt danach
mit Silbertinte gefüllt.

| Größe | Wert |
| --- | --- |
| Drucker | Nanoscribe Photonic Professional GT2, Dip-in; Objektiv nicht angegeben |
| Laser | Faserlaser 780 nm, spezifiziert 120 mW, ≈ 100 fs an der Quelle, ≈ 80 MHz |
| Lack | IP-Dip auf ITO-beschichtetem Glas |
| Schreibparameter | Slicing 100 nm, Hatching 250 nm, Hatchrichtung strikt entlang der Gitterlinien (y), 7,5 mW, 15 mm/s; Druckzeit knapp 2 h |
| Bauhöhe | < 300 µm, damit im Hub des Piezo-z-Tischs und im Arbeitsabstand (kein Stitching); Bildebene = Glasoberfläche |
| Entwicklung | PGMEA 8 min, Isopropanol 2 min, Trocknen mit N₂ |
| Nachbearbeitung | Silbertinte NPS-J per Super-Fine-Inkjet (SIJ-S030) in das mitgedruckte Tintenbecken um den Spalt; Nadel < 10 µm durch einen 25-µm-Spalt neben der Kollektorlinse |

Entwurf (Zemax, Glasmodell IP-Dip nach gissibl2017): Kollektor 50 × 50 µm², NA 0,42 am Spalt
(90 µm Lackweg); Spalt 1,3 µm (erstes Beugungsminimum bei 550 nm passend zur NA); Gitter
geblazet für 550 nm in der ersten Ordnung, Periode gechirpt 650–860 nm über 38 µm, 51 beleuchtete
Linien; Hauptstrahlwinkel in der Bildebene ≤ 16°. Der Prozess schafft sonst Strukturen bis etwa
100 nm; im Vollmaterial sinkt die Auflösung aber durch akkumulierte Dosis (Haupttext).

Gitter im Rasterelektronenmikroskop (Supplementary, Abb. S3): Ein Ausschnitt des Spektrometers
wurde separat auf Glas gedruckt, das Gitter dabei zu höheren Frequenzen hin verlängert. Oberhalb
der ersten genutzten Linie, also unter 650 nm Periode, ist die Topografie nicht mehr aufgelöst;
deshalb die Untergrenze 650 nm. Die kleinste dort gedruckte Periode ist nicht angegeben – 650 nm
ist also eine Schranke, kein gemessener Grenzwert. Auch im genutzten Bereich ist das
Dreiecksprofil (Beispiel im Entwurf: 750 nm) nur angenähert; die Autoren nennen das endliche
Voxelvolumen als Grund. Folge: Beugung in unerwünschte Ordnungen und geringere Effizienz; diese
Ordnungen liegen räumlich getrennt vom Messsignal.

Messungen (Vergleich in `docs/testfaelle.md`, P17–P20):

| Größe | Messung | Simulation bzw. Grenze |
| --- | --- | --- |
| Spaltbreite (FWHM) | 1,3 µm; Rauschen im Mittel 5 % ± 3 %, maximal 15 % | Entwurf 1,3 µm |
| Dispersion | 9,1 ± 1,1 nm/µm (532 nm), 7,2 ± 0,7 nm/µm (633 nm) | Raytracing: kleiner (mehr µm je nm); Ursache laut Autoren vermutlich Schrumpfung (Fokus näher am letzten Linsenblock) |
| Linienbreite (FWHM) | 1,01 µm (532 nm), 2,48 µm (633 nm) | — |
| Spektrale Auflösung | 9,2 ± 1,1 nm (532 nm), 17,8 ± 1,7 nm (633 nm) | WPM 12,5 ± 1,5 nm bzw. 14,5 ± 1,4 nm; Beugungsgrenze λ/N = 10,4 nm bzw. 12,4 nm |
| Rauschen in Spektrenmessungen | Rauschfläche im Mittel 51 % der Signalfläche; gleicher Verlauf von Rot nach Blau in allen Einzelmessungen | — |

Die Linienbreite des Monochromators liegt in der Größenordnung der Auflösung (Supplementary,
Abb. S2); die Profile aus den Monochromatormessungen sind daher verbreitert, die Auflösung stammt
nur aus den Lasermessungen. Das Halogenspektrum fällt zu beiden Enden ab, dort ist das
Signal-Rausch-Verhältnis schlechter. Rauschauswertung: gefittete sinc²-Funktion von jeder Messung
abziehen, negative Werte null setzen, nach Signalstärke gewichtet mitteln (Supplementary,
Abschnitt 4).

**Abgeleitet:** 1,34 µm⁻¹ · 38 µm = 51 Linien; λ/51 = 10,4 nm und 12,4 nm; Dispersion × Linienbreite
= 9,2 nm und 17,9 nm; NA des Kollektors mit n ≈ 1,54 und 25 µm / 90 µm: 0,41; erstes
Spaltminimum λ/b = 0,55/1,3 = 0,42. Alles konsistent mit dem Paper.

## IP-Black (Nanoscribe, Prototyp)

Kationisch härtendes Einkomponenten-Epoxidharz, Photoinitiator im UV, Viskosität 300 mPa·s
(schmid2023).

### Brechzahl

| Zustand | Brechzahl 400–900 nm | Quelle |
| --- | --- | --- |
| flüssig | 1,505 … 1,48 | schmid2023, Abb. 2 |
| UV 15 min (365 nm, 250 mW/cm², Schicht ≈ 1 mm) | zwischen flüssig und gesättigt | schmid2023, Abb. 2 |
| UV ≥ 30 min, gesättigt | 1,528 … 1,50 (Δn ≈ +0,02 zur flüssigen Phase) | schmid2023 |
| 2PP (Patch, Parameter oben) | ≈ gesättigter Wert | schmid2023 |

Sellmeier-Fit (polymerisiert, λ in µm), Standardform:

    n(λ)² = 1 + B₁λ²/(λ² − C₁) + B₂λ²/(λ² − C₂) + B₃λ²/(λ² − C₃)

| B₁ | C₁ [µm²] | B₂ | C₂ [µm²] | B₃ | C₃ [µm²] |
| --- | --- | --- | --- | --- | --- |
| 1,03051 | 4,92832·10⁻³ | 2,20788·10⁻¹ | 3,002·10⁻² | 1,00968 | 1,03560·10² |

Im Paper steht im dritten Term B₁ statt B₃ (Satzfehler, #9). **Abgeleitet** (Standardform):
n = 1,5276 (400 nm), 1,5113 (587,6 nm), 1,5051 (780 nm), 1,5027 (900 nm); Abbe-Zahl 56,2
(Paper: 55). Dispersion laut Paper nahezu gleich IP-S.

### Absorption

| Wellenlänge | Angabe | Quelle |
| --- | --- | --- |
| 780 nm | Extinktionskoeffizient ≈ 1/mm; Leistung im Fokus ≈ 70 % (wrapped, Dip-in) | schmid2023 |
| 450–650 nm | Transmission < 5 % bei 250 µm Dicke; > 95 % Absorption bei 500 µm (Blendenhülle) | schmid2023 |
| sichtbar | Transmission ≈ 75 % bei 25 µm (Minimum des Spektrums); unter 450 nm und über 650 nm deutlich höher | schmid2023, Abb. 1b |

Die Basis des Extinktionskoeffizienten ist nicht angegeben. **Abgeleitet** (Basis e, Intensität):
exp(−1/mm · 0,38 mm) = 0,68 bei einem Lackweg gleich dem Arbeitsabstand – passt zu ≈ 70 %.
Aus 75 % bei 25 µm folgt α ≈ 11,5/mm im Absorptionsmaximum und damit 5,6 % bei 250 µm – grob
konsistent mit „< 5 %“. Das Spektrum α(λ) liegt nur grafisch vor (Abb. 1b); Rohdaten laut Paper
beim Autor auf Anfrage. Die Transmission ist auf eine lackfreie Stelle desselben Substrats
normiert (Beleuchtung NA ≤ 0,65, Abbildung NA 0,70).

## IP-S (Nanoscribe)

Schreibparameter für Linsen siehe Referenzprozess A (schmid2023). Dispersion: schmid2019 (nur
zitiert). Oberflächenrauheit unter 10 nm rms (laut toulouse2021, dort nach Gissibl et al.,
Nat. Commun. 7 (2016) 11763; Quelle noch nicht erfasst).

## IP-Dip (Nanoscribe)

Hochauflösender Lack für kleine Voxel (Referenzprozess B). Brechzahl: gissibl2017 (nur zitiert).
Extinktion unter 0,1/mm im Infraroten bis 1600 nm (schmid2019, nach toulouse2021). Die Absorption
im Sichtbaren prägt laut Haupttext zusammen mit dem Monochromatorspektrum das gemessene
Spaltspektrum; die Supplementary (Abb. S2) zeigt nur den Monochromator, quantitative Werte für
IP-Dip fehlen (→ schmid2019).
Oberflächenrauheit ≈ 100 nm (kirchner2017, nach toulouse2021) – für refraktive Flächen nachteilig;
die Autoren führen die schlechtere Auflösung bei 633 nm darauf zurück.

## Silbertinte NPS-J (Harimatec, Nanopaste Series)

Leitfähige Tinte mit 65 Massen-% Silber-Nanopartikeln (Partikelgröße 12 nm); Tropfen 0,1 fl bis
10 pl aus einer Nadel unter 10 µm (Super-Fine-Inkjet bei Hochspannung). Füllt gedruckte Becken und
Hohlräume als Absorber; Transmission geringer als IP-Black (schmid2023, toulouse2021). Absorption
nicht quantifiziert; in der WPM-Rechnung von toulouse2021 als perfekter Absorber (E = 0) angenommen.
