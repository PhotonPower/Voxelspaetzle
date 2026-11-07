# Konventionen

Verbindlich; dieselben wie Raytatouille, Fieldtracing, BWPM und RTT-Fusion.

- **Einheiten:** Längen in mm im Austausch mit Raytatouille, intern in µm erlaubt (im Namen
  kenntlich: `_um`); Wellenlänge in µm (Vakuum); Leistung in mW, Schreibgeschwindigkeit in µm/s,
  Dosis in mW²·s/µm³ (∫I² dt, relativ zur Schwelle angegeben).
- **Koordinaten:** rechtshändig; Substratoberfläche bei z = 0, Teil bei z > 0 (Schreibrichtung
  von unten nach oben, wie üblich); Druckerkoordinaten werden über eine Pose auf diese abgebildet.
- **Felder** (Schreibfokus): ∝ exp(i(k·r − ωt)), wie Fieldtracing.
- **Brechzahl:** reell bei der Gebrauchswellenlänge der Optik (Dispersion über Cauchy- oder
  Sellmeier-Parameter des Lacks); getrennt davon die Brechzahl bei der Schreibwellenlänge.
- **Polymerisationsgrad:** 0 (flüssig) bis 1; Schwelle des Entwicklers als Parameter.
- **Ergebnisse:** Format `raytatouille-result` (ADR 0023); Flächen als Nurbforge-/STEP-Daten,
  Felder als reguläre Gitter.
