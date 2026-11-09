# Abhängigkeiten

> Grundsatz des Maintainers (2026-11-07): so wenig externe Abhängigkeiten wie möglich; bevorzugt
> die Programme im eigenen GitHub-Konto (PhotonPower), notfalls werden sie erweitert.

## Erlaubt ohne Rückfrage

| Paket | Zweck |
| --- | --- |
| Python ≥ 3.10, NumPy, SciPy | Referenzimplementierung, Numerik |
| pytest, ruff, mypy | Entwicklung (`requirements-dev.txt`) |
| CMake, C++20-Compiler, CUDA ≥ 12.6 | ab dem C++/CUDA-Kern, wie BWPM |

## Programme des Maintainers (lesend; Erweiterungen als Vorschlag)

Stand gelesen am 2026-11-09 (Commit in Klammern). „Lücke“ heißt: fehlt für Voxelspaetzle; der
Weg dazu steht in der letzten Spalte.

| Programm | Nutzung in Voxelspaetzle | Vorhanden | Lücke und Weg |
| --- | --- | --- | --- |
| Nurbforge 0.6.0 (`ee0edd8`) | V1: CAD-Eingang, Schnitte (Slicing), Punkt-im-Körper; V6: Fit der gedruckten Form, STEP-/STL-Export | `section` (orientierte Schnittschleifen, exakt bei Extrusionen und Rotationen), `critical_heights`, `is_extrusion_band`, Punkt-im-Körper, Boolesche Operationen, STEP lesen/schreiben in µm mit benannten Körpern (`read_step_named`), Fits für Asphären, Zernike, XY-Polynome und Sag-Funktionen | Hatching (Füllung der Schleifen mit Bahnlinien) fehlt → in V1 selbst auf `section` aufbauen; Vorschlag [nurbforge-hatching.md](vorschlaege/nurbforge-hatching.md), Nurbforge#44 |
| FourierGrating 0.18 (`a599bde`) | V6, V10: Beugungseffizienz gedruckter Gitter (P21, Spektrometer toulouse2021) | Differentialmethode und RCWA, 1D/2D, komplexe Materialien, CAD-Slicer STEP → Schichten über Nurbforge (ein benannter Körper je Material, µm), Python-Paket | – (STEP-Konvention in `docs/konventionen.md` übernommen) |
| RTT-Fusion (`51bba21`) | V10: Ports und Adapter | Port-Typen G/S mit komplexem ñ, Adapter für FourierGrating, BWPM, hp-FEM, SpeckleBem, CliffordBem, BioOptoMD; Pilot K1 (Gitterspektrometer, Effizienztabelle im Raytracer), `DiffractionTable` in C++ | Datenport N nur als reelles n(z) in 1D → Vorschlag 3D-Datenport [rtt-fusion-datenport.md](vorschlaege/rtt-fusion-datenport.md), RTT-Fusion#20 |
| Raytatouille 0.9.0 (`9002b71`) | V6: Flächenmodell; V8: Optimierer, Toleranzanalyse | ñ = n + iκ, n/k-Tabellen, Volumenabsorption (ADR 0021); Flächen: Ebene, Konik, gerade/ungerade Asphäre, Biconic, Toroid, Zylinder, Axicon, Q-con/Q-bfs; Phasenschichten lineares Gitter und radiales Polynom; Toleranzierung (M7), Ergebnisformat (ADR 0023) | Zernike-Sag, XY-Polynom, Grid-Sag geplant, nicht umgesetzt → Flächenfits erst danach; GRIN (X1) erst nach v1.0 → Brechzahlfeld vorerst nur über BWPM; gechirpte Polynom-Gitterphase fehlt → Vorschlag [raytatouille-gitterphase.md](vorschlaege/raytatouille-gitterphase.md), Raytatouille#363; Flächentypen in Raytatouille#316 (M8) |
| BWPM (`ef2de94`) | V6: Volumenrechnung gedruckter Teile mit Brechzahl- und Absorptionsfeld; V10: Pilot Faserkappe (K6) | komplexes ñ, 2D/3D, C++/CUDA-Kern (B4), Pilot K6 (Kappe aus IP-Q) in 2D | Brechzahlen als diskrete Stufen je Pixel (E4), Aufwand ∝ M² → V6 muss ein kontinuierliches Feld quantisieren; Reflexe nur an z-senkrechten Flächen quantitativ (E5) |
| Fieldtracing (`6da9983`) | V2: vektorieller Schreibfokus | `debye_focus` (FFT-Kette), `richards_wolf` (aplanatisch, x-polarisiert) im homogenen Medium – reicht für Dip-in, wo Lack und Immersion dasselbe Medium sind | Fokus durch eine Grenzfläche (Öl-Modus, Tiefenaberration) fehlt → Vorschlag erst, wenn D1 den Öl-Modus enthält |
| hp-FEM 0.2.0 (`64413c5`) | V5: Schrumpfung (D4) | Maxwell-Löser, hp-Adaptivität, thermo-optische Kopplung (M9) | keine Elastizität → Vorschlag [hpfem-elastizitaet.md](vorschlaege/hpfem-elastizitaet.md), hp-FEM#213; bis dahin eigener P1-Tetraederlöser (D4) |
| SpeckleBem (`4f04efe`) | V6: Streulicht der Rauheit (Treppen, Hatching) | rigorose SIE für rauhe Flächen (Gauß) und **importierte Höhenkarten**, STL; Zeitkonvention e^(+jωt) (Umrechnung im RTT-Fusion-Adapter) | keine Mehrschichtsubstrate; gedruckte Rauheit ist periodisch → V6 gibt Höhenkarten aus, nicht nur ein Spektrum |
| Scattuccino (`e7cbddd`) | V10: gemeinsamer Pilot (gedruckte OCT-Sonde im Gewebephantom) | Datenport zu Voxelspaetzle und Pilot in S12 vorgesehen | – |

Ohne Bezug zu Voxelspaetzle: BioOptoMD (Molekulardynamik an Sensoroberflächen), BindOptiX (bisher
nur README), CliffordBem (Nano-Optik-BEM; bei Bedarf Querprobe zu SpeckleBem).

## Bewusst nicht verwendet

- Herstellersoftware (z. B. DeScribe) nur als Lieferant von Maschinendateien, nicht als Abhängigkeit.
- Fremde FEM-Pakete (FEniCS, CalculiX): stattdessen hp-FEM erweitern oder ein kleiner eigener Elastizitätslöser.
- gmsh nur indirekt über Nurbforge (dort bereits eingesetzt).

Jede neue externe Abhängigkeit braucht eine Entscheidung im Plan (`docs/roadmap.md`).
