# Changelog

Format nach [Keep a Changelog](https://keepachangelog.com/de/1.1.0/).

## [Unreleased]

### Hinzugefügt

- V0 begonnen: Plan mit Stufen V0–V10, Konventionen, Abhängigkeiten, Testfälle, Quellen, Regeln
  für Agenten, CI.
- Referenzprozess schmid2023 (IP-S und IP-Black, Nanoscribe Photonic Professional GT, Dip-in mit
  „wrapped objective“): Quelle (Volltext), `docs/materialdaten.md`, Testfälle P11–P16.
- Plan ergänzt um Absorption beim Schreiben und im Gebrauch, Mehrmaterialdruck, Hatchwinkel und
  Piezo-Einschwingzeit, Zugang des Entwicklers; Vorschlag für D1, neue Entscheidung D7.
- Zweiter Referenzprozess toulouse2021 (IP-Dip, GT2, Mikrospektrometer mit Tintenspalt): Quellen,
  Materialdaten IP-Dip und Silbertinte NPS-J, Testfälle P17–P21 (mit Supplementary).
- Plan ergänzt um Gitterauflösung im Vollmaterial, lackabhängige Rauheit, Schrumpfung im System,
  Hatchrichtung je Bereich, Nachbearbeitung ohne 2PP; D1 als Prozessbibliothek.
- Stand der Framework-Programme in `docs/abhaengigkeiten.md` (gelesen 2026-11-09), FourierGrating
  als neue Abhängigkeit; Erweiterungsvorschläge für RTT-Fusion (Datenports), Nurbforge (Hatching)
  und Raytatouille (gechirpte Gitterphase, Priorität der Flächentypen); Testfall P22.

### Geändert

- Entscheidungen D3–D6 als freigegeben eingetragen.
- Konvention „Brechzahl“ um Absorption (ñ = n + iκ wie Raytatouille, BWPM und RTT-Fusion) und
  Material je Volumen (Lacke und Füllmaterialien, benannte STEP-Körper) erweitert (Vorschlag D7).
- V2 und V6 an die vorhandenen Eingänge der Programme angepasst.
- Titel von schmid2019 ergänzt.
