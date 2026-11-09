# Materialdaten (Literatur)

> Literaturwerte bis zu eigenen Messungen (D2). Jede Angabe mit Quelle (`docs/quellen.md`).
> **Abgeleitet** markierte Werte stehen nicht in der Quelle, sondern sind daraus berechnet; sie
> sind keine Sollwerte für Tests, solange der Maintainer sie nicht freigibt.

## Referenzprozess (schmid2023)

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
3,9 TW/cm² – vermutlich die Annahmen der Autoren. Das Modell rechnet mit Pulsenergie bzw. Leistung,
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

Schreibparameter für Linsen siehe oben (schmid2023). Dispersion: schmid2019 (nur zitiert).
