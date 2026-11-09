# Spezifikation (V0)

> Entwurf 2026-11-09 zur Freigabe durch den Maintainer (Abnahme V0, `docs/roadmap.md`). Gilt
> zusammen mit `docs/konventionen.md`; Quellen nach `docs/quellen.md`, Lackdaten nach
> `docs/materialdaten.md`. Abschnittsnummern sind zitierfähig (Tests und Docstrings verweisen
> darauf, z. B. „Spezifikation §3.4“). Stufen V4 und V5 sind hier nur als Schnittstelle skizziert;
> ihre Gleichungen folgen mit der jeweiligen Stufe.

## 1. Zweck und Geltungsbereich

Voxelspaetzle bildet die Kette Schreibbahn → Schreibfokus → Dosis → Festkörper (→ Polymerisation
→ Schrumpfung) eines 2PP-Druckers nach und gibt das Modell des gedruckten Teils an die Programme
des Frameworks weiter (`docs/abhaengigkeiten.md`). Diese Spezifikation legt fest:

- die Größen, Gleichungen und Annahmen des Prozessmodells bis zum Schwellenmodell (V1–V3, §3),
- die Auflösungsgrößen, gegen die getestet wird (§4),
- die Datenformate zwischen den Stufen und nach außen (§5).

Nicht Gegenstand: Depletionsverfahren (STED-DLW, RAPID, 2PII; fischer2013, Abschn. 4–6). Sie sind
erst relevant, wenn ein Drucker der Prozessbibliothek sie nutzt (D1).

## 2. Größen und Einheiten

Interne Längen in µm mit Suffix `_um`, Austausch mit Raytatouille in mm (`docs/konventionen.md`).

| Größe | Symbol | Einheit | Bemerkung |
| --- | --- | --- | --- |
| Schreibwellenlänge (Vakuum) | λ_w | µm | Referenzprozesse: 0,78 |
| Gebrauchswellenlänge | λ | µm | |
| Numerische Apertur | NA | – | |
| Brechzahl des Lacks (Schreibwellenlänge) | n_w + iκ_w | – | `docs/materialdaten.md` |
| mittlere Laserleistung am Objektiveingang | P | mW | Prozessparameter „Leistung“ |
| Leistung im Fokus | P_f | mW | §3.3 |
| Repetitionsrate, Pulsdauer | f_rep, τ_p | MHz, fs | Referenz: 80 MHz, ≈ 100 fs (toulouse2021) |
| Scangeschwindigkeit | v | µm/s | Herstellerangaben in mm/s umrechnen |
| normierte Fokusverteilung | g(r) | 1/µm² | §3.2, ∫ g dA = 1 in der Fokusebene |
| Belichtungsdosis | D(r) | mW²·s/µm⁴ | §3.4 |
| Schwellendosis | D_th | mW²·s/µm⁴ | §3.6 |
| relative Dosis | D/D_th | – | wird gespeichert und ausgegeben |
| Polymerisationsgrad | α | – | 0 … 1 (V4) |

## 3. Prozessmodell

### 3.1 Schreibbahn

Die Schreibbahn besteht aus Segmenten mit Start- und Endpunkt r_a, r_b (µm, Druckerkoordinaten
über die Pose nach `docs/konventionen.md`), konstanter Leistung P und konstanter Geschwindigkeit
v. Die Fokuslage ist r_f(t) = r_a + v t ê mit ê = (r_b − r_a)/|r_b − r_a|. Punktbelichtungen sind
Segmente der Länge 0 mit Belichtungszeit Δt. Beschleunigung und Einschwingen der Stage (Piezo,
Galvo) sind nicht Teil von V1–V3; sie gehen als Fehlerquelle in V8 ein (schmid2023:
Einschwingzeit). Format: §5.2. Wie Schichten, Konturen und Hatching aus einem Körper entstehen,
legt §3.9 fest.

### 3.2 Schreibfokus

Der Fokus ist das vektorielle Feld E(r) einer aplanatischen Linse nach Debye bzw. Richards–Wolf
(fischer2013, Abschn. 3, mit Verweis auf eine vektorielle Debye-Rechnung). Parameter: λ_w, NA,
Brechzahl n_w des Fokusmediums, Polarisation (linear oder zirkular; Referenz in fischer2013:
zirkular), Ausleuchtung der Pupille (homogen als Standard, Gauß mit Füllfaktor als Option).

**Quelle des Fokus (D8):** Das vektorielle Feld kommt aus Raytatouille ab v1, nach dem Port von
Field Tracing nach C++; die Python-Prototypen in Fieldtracing werden dort ersetzt und sind keine
Abhängigkeit. Bis dahin rechnet Voxelspaetzle mit dem **Gauß-Kern** aus §3.6,
g(ρ, z) = (2/(π w₀²)) exp(−2ρ²/w₀²) exp(−2z²/w_z²), mit w₀ und w_z als Prozessparametern. Die
Dosisrechnung (§3.4) nimmt den Fokus nur als Kern g auf dem Gitter entgegen, sodass der Tausch
keine andere Stelle berührt.

- **Maßgebliche Größe ist |E|², nicht die Intensität des Poynting-Vektors.** Photoinitiatoren
  werden über elektrische Dipolübergänge angeregt; |E|² ist die Verteilung für Einphotonen-,
  |E|⁴ die für Zweiphotonenabsorption (fischer2013, Abschn. 3). Bei linearer Polarisation und
  hoher NA ist |E|² in Polarisationsrichtung gestreckt.
- Normierung: g(r) = |E(r)|² / ∫_Fokusebene |E|² dA, sodass P_f·g(r) die Intensität in mW/µm² im
  Sinne von |E|² ist.
- **Dip-in:** Lack und Immersion sind dasselbe Medium; der Fokus wird im homogenen Medium mit n_w
  gerechnet. **Öl-Modus** (Fokus durch Deckglas in den Lack, Tiefenaberration) ist nicht Teil von
  V2; er braucht den Fokus durch eine Grenzfläche aus Raytatouille (D8) und wird erst mit D1
  entschieden.
- Absorption innerhalb des Fokusvolumens wird vernachlässigt: über 1 µm Fokuslänge schwächt
  IP-Black (κ_w = 6,2·10⁻⁵) um etwa 10⁻³ relativ ab.

### 3.3 Abschwächung bis zum Fokus

P_f = P · T_obj · exp(−4π κ_w L / λ_w)

mit der Transmission T_obj des Objektivs (Prozessparameter, Standard 1, da die Herstellerleistung
meist am Objektiveingang angegeben und über D_th kalibriert wird) und dem geometrischen Lackweg L
bis zum Fokus (Raytatouille ADR 0021, Punkt 5; `docs/konventionen.md`). L hängt vom Modus ab:

| Modus | L |
| --- | --- |
| Dip-in mit „wrapped objective“ | konstant, Prozessparameter `resist_path_um` (Referenz A: ≈ Arbeitsabstand; schmid2023) |
| Dip-in ohne Hülle | Prozessparameter `resist_path_um`; wie L von der Schreibhöhe abhängt, ist mit D1 zu klären |
| Öl (später, D8) | Lackdicke über dem Fokus |

Fehlt `resist_path_um` bei einem absorbierenden Lack, ist das ein Fehler. Für nicht absorbierende
Lacke (κ_w = 0) ist P_f = P·T_obj. Weg durch bereits belichteten Lack (anderes κ) behandelt V4.

**Kegelmittelung** (Testfall P12): Randstrahlen laufen länger. Mit einer ebenen Grenze im
Abstand L, homogen ausgeleuchteter Pupille (Gewicht sin θ cos θ dθ) und sin θ_m = NA/n_w ist die
mittlere Transmission

T_Kegel = ∫₀^θm exp(−a/cos θ) sin θ cos θ dθ / (sin²θ_m/2) = 2 [E₃(a) − E₃(a u_m)/u_m²] / sin²θ_m

mit a = 4πκ_w L/λ_w, u_m = 1/cos θ_m und dem Exponentialintegral E₃ (Substitution u = 1/cos θ;
eigene Herleitung). In erster Ordnung T_Kegel ≈ 1 − a·2/(1 + cos θ_m) statt 1 − a auf der Achse.
Der Standard ist die axiale Transmission; die Kegelmittelung ist als Option verfügbar.

### 3.4 Belichtungsdosis

Für Zweiphotonenabsorption ist die Dosis einer einzelnen Belichtung proportional zu |E|⁴·Δt
(fischer2013, Abschn. 3). Längs der Bahn:

D(r) = k_p · ∫ P_f(t)² g(r − r_f(t))² dt

- **Punkt:** D(r) = k_p P_f² g(r)² Δt.
- **Segment** mit Geschwindigkeit v längs ê: D(r) = (k_p P_f² / v) ∫ g(r − r_a − s ê)² ds über
  die Segmentlänge.
- **Pulsfaktor** k_p: Die zeitlich gemittelte Zweiphotonenrate gepulster Laser ist um einen Faktor
  ∝ 1/(f_rep τ_p) größer als bei Dauerstrich gleicher mittlerer Leistung. Bei festen
  Laserparametern ist k_p eine Konstante und wird zusammen mit D_th kalibriert; gespeichert wird
  nur D/D_th. Den Formfaktor der Pulse belegt die Spezifikation erst mit einer Quelle (offen,
  §6). Das Modell rechnet deshalb mit Pulsenergie bzw. mittlerer Leistung, nicht mit
  Spitzenintensitäten in TW/cm² (`docs/materialdaten.md`).
- **Numerik** (V2c): Die Bahn wird in Stützpunkte mit Abstand ds ≤ min(Gitterschritt, w)/4
  zerlegt; jeder trägt das Gewicht k_p P_f² ds/v (Punkte: k_p P_f² Δt) und wird trilinear auf die
  acht Nachbarknoten des Gitters verteilt. Die Dosis ist die Faltung dieses Quellgitters mit g²,
  auf dem Gitter abgetastet und bei 4 Halbachsen abgeschnitten (Rest < e⁻⁶⁴), per FFT. Das setzt
  einen ortsfesten Fokus voraus (Dip-in, homogenes Medium); ein ortsabhängiger Fokus (Öl-Modus)
  braucht später eine andere Summation. Ohne kalibrierte Schwelle wird k_p = 1 gesetzt und die
  Dosis absolut gespeichert (§5.3).

### 3.5 Akkumulation

Dosen aufeinanderfolgender Belichtungen addieren sich linear (der Lack „erinnert“ sich). Das ist
die konservative Annahme in fischer2013 (Abschn. 2) und nach den dort zitierten Experimenten oft
zutreffend; ein „vergessender“ Lack (Schwarzschild-Effekt, Diffusion) würde Unterschwellendosen
verlieren. Abweichungen von der linearen Akkumulation gehören in das Reaktionsmodell (V4), nicht
in V2/V3.

### 3.6 Schwellenmodell (V3)

Fest ist, wo D(r) ≥ D_th; der Rest wird entwickelt (digitales Schwellenmodell, fischer2013,
Abschn. 2). D_th ist ein Lack- und Prozessparameter. Als Beispielwert nennt fischer2013 eine
Schwelle bei 75 % der Spitzendosis (Abb. 3, Abschn. 4.2); er ist kein Lackwert.

Grenzen des Modells, aus fischer2013 (Abschn. 2, 4.3) und für die Tests festgehalten:

- Mit perfekter Schwelle wäre die Linienbreite beliebig klein; real liegen die kleinsten Breiten
  bei etwa 40 % der Halbwertsbreite der Zweiphotonen-Dosis. Breiten darunter liefert das Modell,
  sie sind aber nicht belastbar (Warnung).
- Nahe der Schwelle reagiert die Linienbreite stark auf Schwankungen: 5 % rms Leistung (≈ 10 %
  Dosis) gaben im Beispiel 42 % rms Linienbreite. Das geht in die Toleranzanalyse (V8) ein; V3
  berechnet dazu ∂(Breite)/∂(P) am Arbeitspunkt.

**Gauß-Näherung** (eigene Herleitung, Sollwert für P3, P4): Mit
g(ρ, z) = (2/(π w₀²)) exp(−2ρ²/w₀²) exp(−2z²/w_z²) und D₀ als Dosis im Zentrum gilt

- Punkt: D(ρ, z) = D₀ exp(−4ρ²/w₀² − 4z²/w_z²), D₀ = k_p P_f² (2/(π w₀²))² Δt;
- Linie längs x: D(y, z) = D₀ exp(−4y²/w₀² − 4z²/w_z²), D₀ = k_p P_f² (2/(π w₀²))² (√π w₀/2)/v;
- Breite und Höhe des Voxels bzw. der Linie für D₀ > D_th:
  d_xy = w₀ √(ln(D₀/D_th)), d_z = w_z √(ln(D₀/D_th)).

Die Form entspricht den Skalierungsgesetzen für Voxel (sun2003, nur zitiert); die Herleitung oben
ist unabhängig davon.

### 3.7 Polymerisation (V4, Schnittstelle)

Der Polymerisationsgrad α(r) ∈ [0, 1] folgt aus der Dosisgeschichte. Grenzfall ohne Diffusion und
mit sofortiger Reaktion: α = 1 für D ≥ D_th, sonst 0, also das Schwellenmodell (P6). Brechzahl
und Absorption hängen von α ab: n(α), κ(α) zwischen flüssig (α = 0) und gesättigt (α = 1);
Kalibrierpunkt IP-Black Δn ≈ 0,02 bei Sättigung (schmid2023). Die Reaktionsgleichungen legt V4
fest.

### 3.8 Schrumpfung (V5, Schnittstelle)

Eigendehnung ε* = −s(α) I, Substrat eingespannt (`docs/vorschlaege/hpfem-elastizitaet.md`).
Literaturpunkt: Wegener et al. kompensierten die axiale Schrumpfung von Woodpiles mit dem Faktor
1,28 in z (fischer2013, Abschn. 6). Die Gleichungen legt V5 fest.

### 3.9 Schichten, Konturen und Hatching (V1a)

- **Schichthöhen:** z_k = z_min + (k + ½)·Δz für alle k mit z_k < z_max (Mittelpunktregel; bei
  glatten Körpern Volumenfehler O(Δz²)). Liegt z_k näher als ε = 10⁻⁶ µm an einer kritischen Höhe
  des Körpers (Nurbforge `critical_heights`: Ecken, ebene Flächen senkrecht zu z, Höhenextrema),
  wird es auf diese Höhe plus ε gelegt; geschnitten wird nie auf einer kritischen Höhe.
- **Schnitt:** Nurbforge `section` liefert orientierte Schleifen (Körper links: außen gegen den
  Uhrzeigersinn, Löcher im Uhrzeigersinn, von +z gesehen). Sie werden Kurve für Kurve abgetastet,
  bis die Sehnenabweichung höchstens `chord_tol_um` beträgt (Standard 1 nm); die Orientierung wird
  gegen die vorzeichenbehaftete Fläche aus Nurbforge geprüft.
- **Konturen** (V1c): `contour_count` Konturen je Schleife vor dem Hatching; die erste um
  `contour_offset_um` ins Material versetzt (typisch die halbe Linienbreite; sie folgt aus V3,
  bis dahin Prozessparameter), jede weitere um `contour_spacing_um` (Standard: Hatchabstand)
  weiter innen. Das Hatching füllt den um `hatch_offset_um` versetzten Schnitt. Standard:
  eine Kontur, alle Offsets 0.
- **Offset:** Jede Kante wird um δ nach links, also ins Material, verschoben; benachbarte Kanten
  treffen sich in ihrem Schnittpunkt (Gehrung, auch an einspringenden Ecken des Materials, ohne
  Rundung). Kanten, deren versetzte Richtung der ursprünglichen entgegenläuft, sind kollabiert und
  werden entfernt, bis keine mehr übrig sind; gegenläufig parallele Nachbarn mit negativem
  Abstand ebenso. Schleifen mit weniger als drei Kanten oder umgekehrter Orientierung entfallen,
  ebenso Löcher, die in keiner äußeren Schleife mehr liegen, und äußere Schleifen, die in einem
  Loch liegen. Schneiden sich danach noch Kanten (etwa zwei Arme, die sich auf weniger als 2δ
  nähern), bricht der Slicer mit Ort und Offset ab; das ist die Grenze dieser Stufe.
- **Hatching:** Linien in Richtung d = (cos a, sin a) auf einem festen Gitter c_j = phase + j·h
  längs der Normalen (−sin a, cos a), verankert im Ursprung; Standard phase = h/2. Eine Kante
  schneidet die Linie c, wenn c im halboffenen Intervall [min v, max v) ihrer Endpunkte liegt;
  innen nach der Gerade-ungerade-Regel. So zählen Ecken und Kanten auf einer Linie eindeutig, und
  es entstehen keine Segmente der Länge 0. Optional schlangenförmig (jede zweite Linie rückwärts).
- **Winkel je Schicht:** a_k = (a₀ + k·Δa) mod π, Standard Δa = π/2 (gekreuzte Schichten,
  schmid2023).
- **Prüfmaß (P1):** geschriebenes Volumen Σ Segmentlänge · h · Δz der Hatch-Segmente.

### 3.10 Schreibfelder (V1b)

Ein Schreibfeld ist der Bereich, den der Drucker ohne Bewegung des Verfahrtischs schreibt
(Galvo- bzw. Piezo-Hub).

- **Raster:** quadratische Felder der Kantenlänge s_xy; Feld (i, j) überdeckt
  x ∈ [o_x + (i − ½)s_xy, o_x + (i + ½)s_xy), y entsprechend, also liegen die Feldmitten
  (Tischpositionen) auf o + (i, j)·s_xy. Höhenblöcke der Höhe s_z (Hub des z-Tischs):
  Block k überdeckt z ∈ [o_z + k·s_z, o_z + (k + 1)·s_z); s_z = ∞ heißt ein Block.
- **Teilung:** Segmente werden an den Feldgrenzen geteilt (halboffen: ein Punkt auf der Grenze
  gehört zum oberen Feld); Kreuzungen in x und y am selben Punkt ergeben einen Schnitt. Jedes
  Stück trägt den Index seines Feldes; Längen und Volumen bleiben bis auf Rundung erhalten.
- **Feldtabelle und Reihenfolge:** je Job die berührten Felder mit Index (i, j, k) und
  Tischposition, in Schreibreihenfolge: Höhenblöcke aufwärts, darin Zeilen j aufwärts, in jeder
  Zeile i abwechselnd vorwärts und rückwärts. Geschrieben wird Feld für Feld, im Feld Schicht für
  Schicht.
- **Nicht in V1b:** Überlappung benachbarter Felder, Scherwinkel der Blockgrenzen,
  Positionierfehler des Tischs (V3, V8).

### 3.11 Schreibjobs und Mehrmaterial (V1b)

- **Eingang:** STEP in µm mit benannten Körpern (`docs/konventionen.md`) oder Körper im Speicher;
  zu jedem verwendeten Körper eine Rolle: Material, Parametersatz und Art `write` oder `fill`.
- **Jobs:** jeder `write`-Körper wird ein Job mit seinem Lack, in der angegebenen Reihenfolge.
  Justiermarken gibt der Aufrufer vor; sie werden unverändert in den Job übernommen (ihre
  Erzeugung hängt am Drucker, D1).
- **Überlappung** zweier `write`-Körper: `error` (Standard) bricht ab, `priority` lässt in
  späteren Jobs das Volumen aller früheren Körper aus. Beides wird auf dem Schreibraster
  bestimmt: Schicht für Schicht die gemeinsame bzw. abzuziehende Länge der Innenintervalle längs
  der Hatchlinien (§3.9). Bei `priority` fallen außerdem Konturstücke weg, deren Mitte in einem
  früheren Körper liegt; die gemeinsame Grenzfläche schreibt die Kontur des früheren Jobs.
  3D-Boolesche Operationen werden dafür nicht verwendet (Nurbforge 0.6.0: Differenz mit
  koplanaren Flächen nicht geschlossen, Nurbforge#45; Schnittmengen langsam, von STEP-Körpern
  etwa neunmal langsamer, Nurbforge#46).
- **`fill`-Körper** (z. B. Tinte NPS-J) werden nicht geschnitten; sie stehen als Nachbearbeitung
  nach dem zuletzt davor genannten Job in der Schreibbahn. Ein `fill` vor dem ersten Job ist ein
  Fehler.

## 4. Auflösungsgrößen für Tests

Aus fischer2013 (Gleichungsnummern aus dem Volltext); λ Vakuumwellenlänge, n Brechzahl des
Mediums, α der halbe Öffnungswinkel, NA = n sin α.

| Größe | Gleichung | Beispiel (λ = 0,8 µm, NA = 1,4) |
| --- | --- | --- |
| laterale Abbe-Grenze | a_xy ≥ λ/(2 NA) (Gl. 1) | 286 nm |
| Halbwertsbreite der Zweiphotonen-Dosis eines Gitters an der Abbe-Grenze | a_xy · 2 acos(0,5^¼)/π ≈ a_xy/2,75 = λ/(5,5 NA) (Gl. 2) | 104 nm |
| axiale Abbe-Grenze | a_z ≥ λ/(n − √(n² − NA²)) (Gl. 3) | λ/0,96 bei n = 1,5 |
| verallgemeinertes Sparrow-Kriterium, Zweiphotonen | numerisch, vektorielle Debye-Rechnung, n = 1,52, zirkular | a_xy = 200 nm, a_z = 500 nm |
| dasselbe, Einphotonen | wie oben | a_xy = 288 nm, a_z = 726 nm |
| Näherungsformeln | a_xy ≈ λ/(2√2 NA), a_z ≈ λA/(2√2 NA), A ≈ 2,5 | 202 nm, 505 nm |

Linienbreite und Auflösung sind verschieden: Die Breite ist mit Schwelle nicht durch Beugung
begrenzt, die Auflösung (kleinste Periode) bei linearer Akkumulation schon (fischer2013,
Abschn. 2, 3). Tests prüfen deshalb Breiten (P4) und Perioden (P17, P23) getrennt.

## 5. Datenformate

Gemeinsam für alle Formate:

- JSON-Hülle wie `raytatouille-result` (Raytatouille ADR 0023): `{"format": "<name>",
  "schema_version": "0.1.0", "data": {…}}`; Arrays als `{"dtype", "shape", "values"}`, NaN und
  Unendlich als Zeichenketten, komplexe Zahlen als `[re, im]`.
- Große Arrays (> 10⁶ Werte) in einer `.npz` neben der Hülle; die Hülle verweist mit
  `{"npz": "<datei>", "key": "<name>"}` darauf und trägt deren SHA-256.
- Einheiten im Feldnamen (`_um`, `_mW`, `_um_per_s`, `_s`); Winkel in rad, mit `_deg` in Grad.
- Jede Ausgabe trägt Herkunft: Voxelspaetzle-Version, Hash der Eingaben, Seed bei Zufall.

### 5.1 Prozessbibliothek (`voxelspaetzle-process`)

Ein Prozess je Datei; mitgeliefert unter `src/voxelspaetzle/processes/` sind die Referenzprozesse
`schmid2023-A` und `toulouse2021-B` (`docs/materialdaten.md`). Werte, die eine Quelle nicht
nennt, stehen als `null`; ein Parametersatz mit fehlender Leistung, Geschwindigkeit, Slicing oder
Hatching lässt sich nicht verwenden (Fehler statt erfundener Zahl).

| Feld | Inhalt |
| --- | --- |
| `name` | z. B. `schmid2023-A` |
| `printer` | Modell; `wavelength_um`, `rep_rate_MHz`, `pulse_fs`, `power_100pct_mW` |
| `objective` | Name, `na`, `magnification`, `working_distance_um`, `design_index` |
| `mode` | `dip_in_wrapped`, `dip_in`, `oil` |
| `resist_path_um` | L für §3.3 (bei `dip_in_wrapped`) |
| `polarization` | `linear_x`, `circular_left`, `circular_right` |
| `focus` | Fokus-Kern: `kind` (`gauss` bis D8), `w0_um`, `wz_um` (§3.2, §3.6; `null`, solange nicht kalibriert) |
| `resists` | je Lack (Name verweist auf die Materialdaten): `parameter_sets` mit benannten Sätzen (`slicing_um`, `hatching_um`, `power_mW` oder `power_percent` bezogen auf `printer.power_100pct_mW`, `speed_um_per_s`, optional `hatch_angle_deg`, `hatch_angle_step_deg`, Kontur- und Hatch-Offsets, `notes`) und `threshold_dose` (D_th, sobald kalibriert) |
| `development` | Schritte mit Medium und Dauer |
| `postprocess` | erlaubte Nachbearbeitungen (z. B. Tinte NPS-J) |
| `sources` | Kürzel aus `docs/quellen.md` |
| `notes` | Annahmen und Hinweise in Worten |

### 5.2 Schreibbahn (`voxelspaetzle-path`)

| Feld | Inhalt |
| --- | --- |
| `process` | Name des Prozesses (§5.1) |
| `pose` | Druckerkoordinaten → Bauteilkoordinaten (4 × 4, µm) |
| `jobs` | Liste der Schreibjobs in Druckreihenfolge |
| `jobs[].resist` | Lack des Jobs |
| `jobs[].markers` | Justiermarken (Lage, Form) für den nächsten Job |
| `jobs[].fields` | Feldtabelle in Schreibreihenfolge: `index` (i, j, k), `center_um` (Tischposition) (§3.10) |
| `jobs[].field_size_um` | (s_xy, s_xy, s_z) oder `null` ohne Feldraster |
| `jobs[].layers` | Liste der Schichten: `z_um`, `hatch_angle_rad` |
| `layers[].segments` | Arrays je Segment: `start_um` (N, 3), `end_um` (N, 3), `power_mW` (N), `speed_um_per_s` (N), `kind` (N; 0 Kontur, 1 Hatching, 2 Punkt), `dwell_s` (N; nur Punkte), `region` (N; Bereich für die Hatchrichtung), `field` (N; Index in `fields`) |
| `postprocess` | Nachbearbeitungen: `type` (`fill`), `material`, `body` (Name des Zielkörpers in der STEP-Datei), `after_job` (Index des Jobs davor) |
| `source` | Herkunft: Slicer von Voxelspaetzle oder importierte Maschinendatei (D3) |

### 5.3 Volumenfelder (`voxelspaetzle-field`)

Reguläres Gitter: `origin_um` (3, untere Ecke), `step_um` (3, Reihenfolge x, y, z), `shape` (3,
Reihenfolge z, y, x), dazu je Feld ein Array der Form `shape`: `dose_rel` (D/D_th) oder, solange
keine Schwelle kalibriert ist, `dose_mW2s_per_um4` (k_p = 1), `alpha`, `material` (uint8, Index in
`materials`), `materials` (Namen), optional `n` und `kappa` je Wellenlänge (`wavelengths_um`).
Gitterwerte gelten in den Zellmittelpunkten origin + (Index + ½)·step. Dazu `focus` (Art und
Parameter des Kerns) und `source` (Herkunft).

### 5.4 Ausgaben an das Framework

| Ausgabe | Format | Empfänger |
| --- | --- | --- |
| Form | STEP in µm, ein benannter Körper je Material und Prozessschritt (`docs/konventionen.md`) | Nurbforge, FourierGrating |
| Volumen (n, κ) | §5.3, bei Bedarf auf Brechzahlstufen quantisiert (mit Fehlerangabe) | BWPM; später Datenport N3 (RTT-Fusion#20) |
| Oberfläche | Höhenkarte z(x, y) auf regulärem Gitter mit den Materialien beider Seiten | SpeckleBem, Rauheitsspektrum |
| Flächenmodell | Fit über Nurbforge | Raytatouille, sobald Zernike-/XY-/Grid-Sag umgesetzt sind (Raytatouille#316) |

## 6. Offene Punkte

- **D1:** Polarisation, Pulsdauer und Ausleuchtung der Pupille der realen Drucker; Objektiv bei
  Referenzprozess B; ob der Öl-Modus gebraucht wird.
- **D2:** Schwellendosen und Kalibrierdaten; bis dahin relative Dosen.
- **Pulsformfaktor** in k_p (§3.4): Quelle erfassen, bevor Absolutwerte gebraucht werden.
- **sun2003** (Skalierung der Voxel) und die vektorielle Debye-Quelle aus fischer2013 (van de Nes
  et al. 2004) nur zitiert.
