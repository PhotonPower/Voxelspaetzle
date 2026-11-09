# Konventionen

Verbindlich; dieselben wie Raytatouille, Fieldtracing, BWPM und RTT-Fusion.

- **Einheiten:** Längen in mm im Austausch mit Raytatouille, intern in µm erlaubt (im Namen
  kenntlich: `_um`); Wellenlänge in µm (Vakuum); Leistung in mW, Schreibgeschwindigkeit in µm/s,
  Dosis in mW²·s/µm³ (∫I² dt, relativ zur Schwelle angegeben).
- **Koordinaten:** rechtshändig; Substratoberfläche bei z = 0, Teil bei z > 0 (Schreibrichtung
  von unten nach oben, wie üblich); Druckerkoordinaten werden über eine Pose auf diese abgebildet.
- **Felder** (Schreibfokus): ∝ exp(i(k·r − ωt)), wie Fieldtracing.
- **Brechzahl und Absorption** (D7, Vorschlag, #8): komplexe Brechzahl ñ = n + iκ mit κ ≥ 0
  (Dämpfung bei exp(i(k·r − ωt))), wie Raytatouille (`docs/architecture.md`, „Konventionen“;
  ADR 0021), BWPM und RTT-Fusion. Materialdaten im Sinne von `rtt-material`: Dispersionsformel
  (Sellmeier, Cauchy, …) für n und tabellierte n/k-Werte, getrennt für die Gebrauchswellenlänge
  der Optik und die Schreibwellenlänge (Fokus, Abschwächung, Dosis). Abschwächung längs eines
  geometrischen Wegs t: I = I₀·exp(−4πκt/λ) (Raytatouille ADR 0021, Punkt 5). Gespeichert wird κ;
  der Absorptionskoeffizient α = 4πκ/λ (1/mm, Basis e) dient nur zum Einlesen von
  Transmissionsmessungen und zur Anzeige und trägt die Einheit im Namen (`alpha_per_mm`).
  Löser mit anderer Zeitkonvention (SpeckleBem: e^(+jωt)) werden im Adapter von RTT-Fusion
  umgerechnet, nicht hier.
- **Material:** jedes Volumen trägt sein Material – Lack (z. B. `IP-S`, `IP-Dip`, `IP-Black`) oder
  Füllmaterial aus der Nachbearbeitung (z. B. Silbertinte `NPS-J`) – und den Prozessschritt, der es
  erzeugt hat (Schreibjob bzw. Nachbearbeitung); Materialdaten aus `docs/materialdaten.md` bzw. aus
  Messungen (D2). Austausch der Form als STEP in µm mit **einem benannten Körper je Material und
  Prozessschritt** (Nurbforge `write_step(…, unit="um", names=[…])`), wie ihn der CAD-Slicer von
  FourierGrating erwartet; der Name verweist auf die Materialdaten.
- **Polymerisationsgrad:** 0 (flüssig) bis 1; Schwelle des Entwicklers als Parameter.
- **Ergebnisse:** Format `raytatouille-result` (ADR 0023); Flächen als Nurbforge-/STEP-Daten,
  Felder als reguläre Gitter.
