# Vorschlag für RTT-Fusion: Datenports für gedruckte Teile

> Entwurf aus Voxelspaetzle (V6, V10); in RTT-Fusion nur lesend. Stand RTT-Fusion `51bba21`
> (gelesen 2026-11-09). Angelegt als PhotonPower/RTT-Fusion#20 (2026-11-09).

## Kontext

Datenport N trägt heute ein reelles Profil n(z) in 1D (BioOptoMD, Pilot K4); Datenports tragen
Wellenlänge, Lage zur Bezugsfläche, Seite und Streuung über Replicas (`docs/adr-entwurf-fusion.md`,
Nachtrag R8–R10). Voxelspaetzle liefert dagegen das Modell eines gedruckten Teils in 3D: Form,
Brechzahl und Absorption im Volumen, Oberflächenrauheit. Die Konsumenten sind BWPM (Volumen),
FourierGrating (Gitterzelle), SpeckleBem (rauhe Oberfläche) und über Scattuccino der gemeinsame
Pilot.

## Vorschlag

Drei Datenports, alle in den Konventionen von RTT-Fusion (mm, µm, ñ = n + iκ, κ ≥ 0), mit Pose zur
Bezugsfläche, Herkunft (Voxelspaetzle-Version, Hash der Prozessparameter) und Replicas für die
Prozessstreuung wie bei N:

1. **Volumen (N3):** reguläres Gitter (Ursprung, dx, dy, dz in mm) mit einem Materiallabel je
   Voxel und einer Materialtabelle (n/k je Vakuumwellenlänge, wie `rtt-material`); optional ein
   Zuschlag Δñ je Voxel für Gradienten aus dem Polymerisationsgrad. Labels plus Tabelle bleiben
   kompakt und gelten für mehrere Wellenlängen; das komplexe Feld je Wellenlänge bildet der
   Adapter.
2. **Form (B):** STEP in µm mit einem benannten Körper je Material und Prozessschritt (Nurbforge
   `write_step`, wie der CAD-Slicer von FourierGrating); die Namen verweisen auf die
   Materialtabelle.
3. **Höhenkarte (H):** z(x, y) auf einem regulären Gitter über einer Bezugsebene, mit den Materialien
   beider Seiten; für SpeckleBem (Import von Höhenkarten vorhanden) und Rauheitsspektren.

Adapter: BWPM quantisiert N3 auf Brechzahlstufen (BWPM E4) mit berichtetem Fehler; FourierGrating
liest B direkt; SpeckleBem bekommt H mit der bestehenden Umrechnung der Zeitkonvention (X2).

## Offene Punkte

- Dateiformat großer Volumina: Hülle `raytatouille-result` (ADR 0023) ist JSON; für 10⁸ Voxel
  braucht es einen Binärteil (z. B. `.npz` neben der Hülle).
- Name und Nummer der Port-Typen; Verhältnis zu N (N ist der 1D-Sonderfall von N3).

## Abnahme (Vorschlag)

Rundreise je Port bitgleich; N3 mit einer Schicht = N; BWPM-Ergebnis über den Port gleich dem
direkten Aufruf; Quantisierungsfehler fällt mit der Zahl der Stufen; H aus einer analytischen
Sinusfläche gegen die Gittergleichung (SpeckleBem bzw. FourierGrating).
