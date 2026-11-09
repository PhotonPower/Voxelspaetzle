# Vorschlag für hp-FEM: lineare Elastizität mit Eigendehnung

> Entwurf aus Voxelspaetzle (D4); in hp-FEM nur lesend. Angelegt als PhotonPower/hp-FEM#213 (2026-11-09).
>
> Stand hp-FEM 0.2.0 (`64413c5`, gelesen 2026-11-09): keine Elastizität; vorhanden sind
> Maxwell-Löser und eine thermo-optische Kopplung (M9, stationäre Wärmeleitung).

Für die Schrumpfung gedruckter Teile genügt lineare Elastizität mit Eigendehnung:

    −∇·σ = 0,  σ = C : (ε(u) − ε*),  ε* = −s(α) I  (isotrope Schrumpfung, s aus dem Polymerisationsgrad α)

mit fester Einspannung an der Substratfläche und freien übrigen Rändern. hp-FEM hat H1-Räume;
gewünscht ist ein vektorieller H1-Pfad (3 Komponenten) mit isotropem C(E, ν) je Element,
Eigendehnung als Volumenfeld (Datenport) und Ausgabe der Verschiebung an den Knoten und an
Punkten der Oberfläche. Abnahme: freie Kugel (homogene Schrumpfung, exakt), gebundene dünne Platte
(analytisch), Patch-Test. Vorteil: keine fremden FEM-Pakete; dieselbe Vernetzung über Nurbforge.
