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

**Stand:** V0 (Spezifikation) abgeschlossen, V1a–V1c umgesetzt: Schichten, Konturen mit Offset und
Hatching aus Körpern (Nurbforge), Schreibfelder, Schreibjobs und Mehrmaterial aus benannten
STEP-Körpern, Prozessbibliothek mit den Referenzprozessen, Schreibbahn im Format
`voxelspaetzle-path`. Aus V2: Abschwächung im Lack und Belichtungsdosis auf einem Volumengitter
mit Gauß-Kern; der vektorielle Fokus folgt mit Raytatouille v1 (D8). Aus V3: Schwellenmodell mit
Linienbreiten, Festkörper, Höhenkarten und Rauheitsspektren. Aus V4a: Polymerisationsgrad,
Materialdaten (IP-Black) und das optische Feld (n, κ) des gedruckten Teils. Aus V5a: Schrumpfung
mit linearer Elastizität auf den Voxeln und der Zugang des Entwicklers. Aus V6a: Ausgaben an
BWPM (Labelgitter), FourierGrating (Schichten) und als STL. Siehe
[docs/roadmap.md](docs/roadmap.md).

## Installation

```bash
pip install "nurbforge @ git+https://github.com/PhotonPower/Nurbforge@v0.6.0"   # C++-Build
pip install -e .
```

```python
from voxelspaetzle.assembly import BodySpec, read_step_bodies, slice_assembly
from voxelspaetzle.fields import FieldGrid
from voxelspaetzle.process import load_process

process = load_process("schmid2023-A")
bodies = read_step_bodies("hybrid_lens.step")  # STEP in µm, one named body per material
specs = [
    BodySpec.from_process("Lens", process, "IP-S", "lens"),
    BodySpec.from_process("Aperture", process, "IP-Black", "aperture"),
]
path = slice_assembly(bodies, specs, process=process.name, fields=FieldGrid(size_xy_um=200.0))
path.save("hybrid_lens.path.json")
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
