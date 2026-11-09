# Konventionen

Verbindlich; dieselben wie Raytatouille, Fieldtracing, BWPM und RTT-Fusion.

- **Einheiten:** Längen in mm im Austausch mit Raytatouille, intern in µm erlaubt (im Namen
  kenntlich: `_um`); Wellenlänge in µm (Vakuum); Leistung in mW, Schreibgeschwindigkeit in µm/s,
  Dosis in mW²·s/µm³ (∫I² dt, relativ zur Schwelle angegeben).
- **Koordinaten:** rechtshändig; Substratoberfläche bei z = 0, Teil bei z > 0 (Schreibrichtung
  von unten nach oben, wie üblich); Druckerkoordinaten werden über eine Pose auf diese abgebildet.
- **Felder** (Schreibfokus): ∝ exp(i(k·r − ωt)), wie Fieldtracing.
- **Brechzahl und Absorption** (D7, Vorschlag, #8): reelle Brechzahl n und
  Intensitäts-Absorptionskoeffizient α in 1/mm (Beer-Lambert, Basis e: I(s) = I₀·exp(−α·s)),
  beide je Wellenlänge; in Feldrechnungen komplex n + iκ mit κ = α·λ/(4π) in gleichen
  Längeneinheiten (κ ≥ 0 dämpft bei exp(i(k·r − ωt))). Getrennt: bei der Gebrauchswellenlänge der
  Optik (Dispersion über Cauchy- oder Sellmeier-Parameter, α(λ) als Tabelle) und bei der
  Schreibwellenlänge (Fokus, Abschwächung, Dosis).
- **Material:** jedes Volumen trägt den Lack (z. B. `IP-S`, `IP-Black`) und beim Mehrmaterialdruck
  die Nummer des Schreibjobs; Lackdaten aus `docs/materialdaten.md` bzw. aus Messungen (D2).
- **Polymerisationsgrad:** 0 (flüssig) bis 1; Schwelle des Entwicklers als Parameter.
- **Ergebnisse:** Format `raytatouille-result` (ADR 0023); Flächen als Nurbforge-/STEP-Daten,
  Felder als reguläre Gitter.
