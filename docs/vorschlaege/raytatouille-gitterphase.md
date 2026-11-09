# Vorschlag für Raytatouille: gechirpte Gitterphase und Flächen für gedruckte Optik

> Entwurf aus Voxelspaetzle (V6, V8); in Raytatouille nur lesend. Stand Raytatouille 0.9.0
> (`9002b71`, gelesen 2026-11-09). Angelegt als PhotonPower/Raytatouille#363 (Flächentypen: Kommentar in Raytatouille#316) (2026-11-09).

## Kontext

Das gedruckte Spektrometer toulouse2021 nutzt ein Gitter, dessen Periode als Polynom in einer
lateralen Koordinate variiert (650–860 nm über 38 µm), entworfen in Zemax. Raytatouille hat als
Phasenschichten `LinearGratingPhase` (konstante Frequenz G) und `RadialPhasePolynomial`
(ADR 0025); weitere Phasen sind unter F3 (Roadmap-Erweiterungen) als Idee notiert.

## Vorschlag

1. **Phasenschicht mit polynomialer Gitterfrequenz** in Richtung ψ:
   G(u) = Σₖ gₖ uᵏ (Linien je mm), u = x cos ψ + y sin ψ, Phase φ(u) = 2π Σₖ gₖ u^(k+1)/(k+1),
   ∇φ analytisch. Mit nur g₀ ist sie `LinearGratingPhase`. Die Effizienz je Ordnung kommt wie
   bisher aus `diffraction_efficiency` bzw. aus der Beugungstabelle (RTT-Fusion R6/R12) – für ein
   gedrucktes Profil aus FourierGrating.
2. **Priorität für die geplanten Flächen** Zernike-Sag, XY-Polynom und Grid-Sag: Voxelspaetzle V6
   gibt die gedruckte Form als Fit plus Restgitter aus; ohne diese Typen ist sie in Raytatouille
   nicht einlesbar.

GRIN (X1) bleibt wie geplant nach v1.0; bis dahin geht das Brechzahlfeld gedruckter Teile über
BWPM.

## Abnahme (Vorschlag)

Nur g₀: bitgleich zu `LinearGratingPhase`; lokale Ablenkung gegen die Gittergleichung mit G(u) am
Auftreffpunkt; ∇φ gegen zentrale Differenzen; Phase stetig über u = 0.
