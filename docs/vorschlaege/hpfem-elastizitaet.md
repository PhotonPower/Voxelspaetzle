# Vorschlag für hp-FEM: lineare Elastizität mit Eigendehnung

> Entwurf aus Voxelspaetzle (D4); in hp-FEM nur lesend. Zur Entscheidung durch den Maintainer.

Für die Schrumpfung gedruckter Teile genügt lineare Elastizität mit Eigendehnung:

    −∇·σ = 0,  σ = C : (ε(u) − ε*),  ε* = −s(α) I  (isotrope Schrumpfung, s aus dem Polymerisationsgrad α)

mit fester Einspannung an der Substratfläche und freien übrigen Rändern. hp-FEM hat H1-Räume;
gewünscht ist ein vektorieller H1-Pfad (3 Komponenten) mit isotropem C(E, ν) je Element,
Eigendehnung als Volumenfeld (Datenport) und Ausgabe der Verschiebung an den Knoten und an
Punkten der Oberfläche. Abnahme: freie Kugel (homogene Schrumpfung, exakt), gebundene dünne Platte
(analytisch), Patch-Test. Vorteil: keine fremden FEM-Pakete; dieselbe Vernetzung über Nurbforge.
