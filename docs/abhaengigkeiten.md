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

| Programm | Nutzung in Voxelspaetzle |
| --- | --- |
| Nurbforge | CAD-Eingang (STEP, NURBS, B-Rep), Flächen aus optischen Formen (Asphären, Zernike, XY), Schnitte (Slicing), Punkt-im-Körper, Fit der gedruckten Form auf Zernike/XY, STEP-/STL-Export |
| Raytatouille | Flächen eines Optikentwurfs als Eingang, gedruckte Form als Flächenmodell zurück, GRIN-Tracing (Entwurf X1) für das Brechzahlfeld, Optimierer für die Vorkompensation, Toleranzanalyse |
| Fieldtracing | vektorieller Schreibfokus im Lack (hohe NA, Brechzahlsprung Immersion/Lack, Aberration mit der Tiefe) |
| BWPM | Volumenrechnung gedruckter Teile mit Brechzahlfeld (Faserfacetten, Kappen) |
| hp-FEM | Vorschlag: vektorielle H1-Elastizität für die Schrumpfung (lineare Elastizität mit Eigendehnung) |
| SpeckleBem | Streulicht der Rauheit (Treppen, Hatching) |
| RTT-Fusion | Adapter, Port-Typen, Datenports (Form, Brechzahlfeld, Rauheit) |
| Scattuccino | gemeinsamer Pilot (gedruckte Sonde im Gewebe) |

## Bewusst nicht verwendet

- Herstellersoftware (z. B. DeScribe) nur als Lieferant von Maschinendateien, nicht als Abhängigkeit.
- Fremde FEM-Pakete (FEniCS, CalculiX): stattdessen hp-FEM erweitern oder ein kleiner eigener Elastizitätslöser.
- gmsh nur indirekt über Nurbforge (dort bereits eingesetzt).

Jede neue externe Abhängigkeit braucht eine Entscheidung im Plan (`docs/roadmap.md`).
