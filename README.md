# Voxelspaetzle

Prozesssimulation zwei-photonen-gedruckter Mikrooptik – benannt nach der Spätzlepresse: Der Laser
„drückt“ das Teil Voxel für Voxel aus dem flüssigen Lack.

**Ziel:** von der CAD-Auslegung zu einem Modell des **tatsächlich gedruckten** Teils – Form,
Brechzahlfeld, Rauheit – und dieses in die Gesamtsimulation einbauen; dazu Kalibrierung an
Messdaten, Vorkompensation (CAD so ändern, dass das gedruckte Teil die optische Funktion erfüllt)
und Toleranzanalyse über die Prozessstreuung.

**Kette:** CAD (Nurbforge/Raytatouille) → Schreibbahn (Slicing, Hatching) → Schreibfokus
(Fieldtracing) → Dosisfeld → Polymerisationsgrad → Entwicklung und Schrumpfung → Form, Brechzahl,
Rauheit → Raytatouille, BWPM, RTT-Fusion.

**Stand:** V0 (Spezifikation) abgeschlossen, V1a umgesetzt: Schichten, Konturen und Hatching aus
einem Körper (Nurbforge) und die Schreibbahn im Format `voxelspaetzle-path`. Siehe
[docs/roadmap.md](docs/roadmap.md).

## Installation

```bash
pip install "nurbforge @ git+https://github.com/PhotonPower/Nurbforge@v0.6.0"   # C++-Build
pip install -e .
```

```python
from voxelspaetzle.slicer import WriteParameters, slice_shell

params = WriteParameters(slicing_um=0.2, hatching_um=0.5, power_mW=20.0, speed_um_per_s=5e4)
path = slice_shell(shell, params, resist="IP-S", process="schmid2023-A")  # shell: nurbforge.Shell in µm
path.save("lens.path.json")
```

## Dokumentation

- [Plan und Stufen](docs/roadmap.md)
- [Spezifikation](docs/spezifikation.md)
- [Konventionen](docs/konventionen.md)
- [Abhängigkeiten](docs/abhaengigkeiten.md)
- [Testfälle](docs/testfaelle.md)
- [Materialdaten (Literatur)](docs/materialdaten.md)
- [Quellen](docs/quellen.md)
- [Regeln für Programmieragenten](AGENTS.md)

## Lizenz

MIT, siehe [LICENSE](LICENSE).
