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

**Stand:** Plan (Stufe V0). Siehe [docs/roadmap.md](docs/roadmap.md).

## Dokumentation

- [Plan und Stufen](docs/roadmap.md)
- [Konventionen](docs/konventionen.md)
- [Abhängigkeiten](docs/abhaengigkeiten.md)
- [Testfälle](docs/testfaelle.md)
- [Materialdaten (Literatur)](docs/materialdaten.md)
- [Quellen](docs/quellen.md)
- [Regeln für Programmieragenten](AGENTS.md)

## Lizenz

MIT, siehe [LICENSE](LICENSE).
