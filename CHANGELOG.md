# Changelog

Format nach [Keep a Changelog](https://keepachangelog.com/de/1.1.0/).

## [Unreleased]

### Hinzugefügt

- V3a: Schwellenmodell mit Linienquerschnitt (Breite, Höhe, Halbwertsbreite, Warnung,
  Empfindlichkeit), Festkörper als Materialfeld, Höhenkarte der Oberseite im Format
  `voxelspaetzle-heightmap`, Wandprofil und Spektrum (`voxelspaetzle.threshold`); Spezifikation
  §3.6 (Messgrößen, Welligkeit, Grenzen) und §5.5; Testfälle P4, P5; P15 und P17 neu eingeordnet.
- V2b: Abschwächung bis zum Fokus mit Umrechnung κ ↔ α und Kegelmittelung
  (`voxelspaetzle.attenuation`); Testfall P12.
- V2c: Belichtungsdosis auf einem Volumengitter mit austauschbarem Fokus-Kern, Gauß-Kern bis D8,
  separierbare FFT-Faltung (`voxelspaetzle.focus`, `voxelspaetzle.dose`); Volumenfelder im Format
  `voxelspaetzle-field`; Fokusparameter in der Prozessbibliothek (`null` bis zur Kalibrierung);
  Testfall P3.
- Entscheidung D8: der vektorielle Fokus kommt aus Raytatouille v1; Spezifikation §3.2–§3.4, §5.1,
  §5.3 entsprechend.
- V1c: Offsets von Schnittschleifen mit Gehrung, Bereinigung kollabierter Kanten und Prüfung auf
  Schnitte (`voxelspaetzle.offset`); mehrere Konturen mit Offset und Hatch-Offset im Slicer;
  Prozessbibliothek `voxelspaetzle-process` mit den Referenzprozessen `schmid2023-A` und
  `toulouse2021-B` (`voxelspaetzle.process`), `BodySpec.from_process`; Spezifikation §3.9 und
  §5.1 ergänzt; Testfälle P25, P26.
- V1b: Schreibfelder mit Teilung an Feldgrenzen, Feldtabelle und Schreibreihenfolge
  (`voxelspaetzle.fields`); Schreibjobs und Mehrmaterial aus benannten STEP-Körpern mit
  Überlappungsregel `error`/`priority` auf dem Schreibraster und Nachbearbeitung `fill`
  (`voxelspaetzle.assembly`); Hatching mit ausgeschlossenen Bereichen; Spezifikation §3.10,
  §3.11 und Format §5.2 (`field`, `fields`, `field_size_um`, `after_job`); Testfälle P1 (✅) und
  P24.
- V1a: Schichthöhen nach der Mittelpunktregel ohne Schnitt auf kritischen Höhen, Schnitte über
  Nurbforge mit Sehnentoleranz (`voxelspaetzle.geometry`), Hatching auf festem Gitter mit
  halboffener Regel und Winkel je Schicht (`voxelspaetzle.hatching`), Slicer
  (`voxelspaetzle.slicer`), Datenmodell und Format der Schreibbahn (`voxelspaetzle.path`),
  JSON-Hülle mit `.npz` für große Arrays (`voxelspaetzle.envelope`); Spezifikation §3.9; Testfall
  P1 teilweise (Volumen, Schnitte, Schichten); Nurbforge als Laufzeitabhängigkeit, in der CI
  gecacht.
- V0-Spezifikation `docs/spezifikation.md`: Prozessmodell bis zum Schwellenmodell (Fokus über
  |E|², Abschwächung, Dosis ∝ |E|⁴, lineare Akkumulation, Gauß-Näherung), Auflösungsgrößen aus
  fischer2013, Datenformate für Prozessbibliothek, Schreibbahn, Volumenfelder und Ausgaben;
  fischer2013 im Volltext gelesen; Testfall P23.
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
  und Raytatouille (gechirpte Gitterphase, Priorität der Flächentypen), dort als Issues angelegt
  (RTT-Fusion#20, Nurbforge#44, Raytatouille#363 und #316, hp-FEM#213); Testfall P22.

### Geändert

- V1d (Import der Maschinendatei) zurückgestellt, bis Beispieldateien und Formatbeschreibung vorliegen.
- `WriteParameters.contour` ersetzt durch `contour_count` (0 = keine Kontur) mit Offsets.
- Einheit der Dosis in den Konventionen korrigiert: mW²·s/µm⁴ statt mW²·s/µm³.
- Entscheidungen D3–D6 als freigegeben eingetragen.
- Konvention „Brechzahl“ um Absorption (ñ = n + iκ wie Raytatouille, BWPM und RTT-Fusion) und
  Material je Volumen (Lacke und Füllmaterialien, benannte STEP-Körper) erweitert (D7, freigegeben
  2026-11-09).
- V2 und V6 an die vorhandenen Eingänge der Programme angepasst.
- Titel von schmid2019 ergänzt.
