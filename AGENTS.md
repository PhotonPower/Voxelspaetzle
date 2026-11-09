# Regeln für Programmieragenten

Diese Datei liest jeder Agent zu Beginn jeder Sitzung. Sie gilt zusammen mit `docs/roadmap.md`,
`docs/konventionen.md`, `docs/abhaengigkeiten.md`, `docs/quellen.md` und `docs/testfaelle.md`.

## Projekt in einem Satz

Voxelspaetzle simuliert die Herstellung zwei-photonen-gedruckter Mikrooptik (2PP/DLW): aus der CAD-Auslegung über Schreibbahn, Dosis, Polymerisation, Entwicklung und Schrumpfung zu einem Modell des gedruckten Teils (Form, Brechzahlfeld, Rauheit), das in die Gesamtsimulation (Raytatouille, BWPM, RTT-Fusion) eingeht, mit Kalibrierung an Messdaten und Vorkompensation.

## Bauen und testen

```bash
pip install "nurbforge @ git+https://github.com/PhotonPower/Nurbforge@v0.6.0"  # C++-Build
pip install "fouriergrating @ git+https://github.com/PhotonPower/FourierGrating@2c35800cf3a743bec00555a026160438f7e323bb"  # optional, Tests P21/P22
pip install -r requirements-dev.txt && pip install -e .
pytest
ruff check . && ruff format --check . && mypy
```

## Arbeitsregeln

1. **Ein Auftrag = ein Ziel einer Stufe** aus `docs/roadmap.md`. Stufen nicht vorziehen.
2. **Erst Test, dann Code.** Sollwerte aus analytischen Lösungen, unabhängigen Rechnungen oder
   veröffentlichten Messungen, nie aus dem geprüften Code. Tests und Sollwerte nur mit Freigabe
   des Maintainers ändern.
3. **Konventionen sind Gesetz** (`docs/konventionen.md`): die von Raytatouille und der Fusion.
4. **Abhängigkeiten minimal** (`docs/abhaengigkeiten.md`): NumPy und SciPy; sonst bevorzugt die
   Programme des Maintainers (PhotonPower). Fehlt dort etwas, wird ein Erweiterungsvorschlag unter
   `docs/vorschlaege/` geschrieben (dort nur lesend). Neue externe Abhängigkeiten nur mit Freigabe.
5. **Fremder Code:** GPL- oder unklar lizenzierter Code wird nicht übernommen, nur als Vergleich
   über veröffentlichte Ergebnisse genutzt.
6. **Formeln mit Quelle** (`docs/quellen.md`); Gleichungsnummern nur aus dem Volltext. Status
   jeder Quelle festhalten (Volltext gelesen / nur zitiert).
7. **Determinismus:** Zufall nur mit explizitem Seed; Monte-Carlo-Ergebnisse mit Standardfehler.
8. **Keine Geheimnisse** in Dateien, Commits, Remote-URLs.
9. **Unklarheit = Frage**: Issue mit Label `frage`; Abweichung von einer Quelle: Label `paper`.

## Sprache und Stil

- Code, Kommentare, Docstrings, Commit-Messages englisch; Projektdokumentation deutsch.
- ruff (Zeilenlänge 100), mypy strict; Commits im Imperativ, ein Thema pro Commit.

## Definition of Done (PR-Checkliste)

- [ ] CI grün
- [ ] Referenztests mit unabhängigem Sollwert
- [ ] `docs/testfaelle.md` aktualisiert (Status, Messwerte)
- [ ] neue Quellen in `docs/quellen.md`
- [ ] Docstrings mit Einheiten, Vorzeichen und Verweis
- [ ] `CHANGELOG.md` unter „Unreleased“
