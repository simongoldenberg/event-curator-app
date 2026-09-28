# Event Curator · Version 0.1.0

Lokale Python-Anwendung für Konzerte, Parties, Raves und Open Airs in den Räumen
**Würzburg, Freiburg und Wien**. Persönliche Profile, Künstlerlisten, Quellenkonfigurationen
und Reports bleiben außerhalb von Git. Quellcode unter MIT-Lizenz.

## Schnellstart

Voraussetzungen: Python **3.11+**; für GitHub zusätzlich Git und GitHub CLI (`gh`).
Die Anwendung benötigt **keine zusätzlichen Pakete** und funktioniert ohne API-Key im Beispielmodus.

PowerShell, im Projektordner:

```powershell
# Den tatsächlichen absoluten Pfad der eigenen Installation verwenden:
& 'C:\Pfad\zu\Python\python.exe' -m venv --without-pip .venv
& .\.venv\Scripts\python.exe main.py
& .\.venv\Scripts\python.exe main.py --interview
& .\.venv\Scripts\python.exe main.py --live --month 2026-10
```

Linux/macOS:

```bash
/absoluter/pfad/python3 -m venv --without-pip .venv
.venv/bin/python main.py
.venv/bin/python main.py --interview
.venv/bin/python main.py --live
```

`--without-pip` genügt, da nur die Standardbibliothek genutzt wird. Die Datei
`requirements.txt` dokumentiert diesen Stand. Eine aktivierte Python-Umgebung erlaubt
auch die Kurzform `python main.py --interview`.

Ohne Optionen entstehen **fiktive, deutlich markierte** Beispielberichte unter
`exports/digest-YYYY-MM-demo.md` und `.html`. Sie demonstrieren beide Rubriken und den Regionsfilter.
Ein Live-Lauf erzeugt separate Dateien ohne `-demo`. HTML enthält keine externen Fonts,
Skripte, Bilder oder Tracker.

## Eigene Künstler und Party-Profil

`data/sample_artists.csv` enthält ausschließlich erfundene Namen. Eine eigene Liste
als `data/artists.csv` oder `data/user_artists.csv` speichern:

```csv
artist,genres
Eigener Künstlername,Downtempo;Organic House
Anderer Künstlername,Berlin Techno;Hypnotic
```

UTF-8 (auch mit BOM), Komma, Semikolon oder Tab als Spaltentrenner werden unterstützt.
Mehrere Genres innerhalb einer Zelle mit Semikolon trennen; bei Semikolon als Spaltentrenner
die Genre-Zelle entsprechend in Anführungszeichen setzen. Doppelte Namen werden zusammengeführt
(die letzte Zeile gewinnt). Optional `--artists PFAD` verwenden.

Das Interview fragt Genres, Event-Konzepte, Club-/Festivalreferenzen, Regionen, Radius und
unerwünschte Begriffe ab. Es speichert erst nach Abschluss atomar in
`data/user_party_profile.json`; ein Abbruch lässt das vorhandene Profil bestehen.

## Regionen und Matching

- Standard: **75 km Luftlinie** um jede Zielstadt; im Interview 1–200 km einstellbar.
- Koordinaten werden per Haversine-Distanz geprüft. Grenznahe Orte sind zulässig,
  sofern sie innerhalb des Radius liegen.
- Ohne Koordinaten muss der exakte Stadtname einschließlich bekannter Schreibvarianten
  **und** das passende Land vorhanden sein. Unbekannte Orte werden ausgeschlossen.
- Nur kommende oder noch laufende Events im gewählten Kalendermonat werden berücksichtigt.
- Abgesagte/verschobene Events sowie Ausschlussbegriffe werden herausgefiltert.
- Gleicher Titel, Startzeit, Stadt und Venue werden dedupliziert. Abweichende Quellentitel
  können weiterhin doppelt erscheinen.
- Artist-Treffer: 50 Punkte; Genre-/Konzeptbegriffe: jeweils 10; heuristische Nähe zu einer
  gewählten Vibe-Referenz: 3. Der Bericht nennt die Gründe. Regionale Events ohne belegten
  Match stehen mit 0 Punkten darunter. Das ist keine Qualitätsbewertung.

Referenzen wie Kater Blau, Die Bucht, Fusion, Mystic Creatures und Moyn dienen dem
Interview als Orientierung. Ihre Zuordnung zu Begriffen ist eine editierbare Heuristik
in `event_curator/matching.py`, keine Aussage über ein aktuelles Line-up.

## Quellen

| Quelle | Anbindung | Voraussetzung / Grenze |
|---|---|---|
| Goabase | Öffentliche JSON-API, Region, Datum und Detaildaten | Mit `--live`; Schwerpunkt Goa/Psytrance, keine vollständige Techno-/Downtempo-Abdeckung |
| Bandsintown | Künstler-Events | Eigene freigegebene App-ID, eigene Künstlerliste und `--include-bandsintown` |
| Clubs, Festivals, regionale Seiten, Resident Advisor | Konfigurierbare HTTPS-Seiten, JSON-LD und begrenztes Nachladen von Eventlinks | Strukturierte Daten und erlaubter Abruf nötig; kein garantierter RA-Zugriff |
| SoundCloud / Künstler-Websites | Öffentliche HTML-/Metabeschreibungen und verfügbare SoundCloud-Hydration | `--discover`; Gig-Hinweise bleiben unbestätigt, kein Login-/Schutzumgehen |
| Eigene Eventdateien | JSON oder CSV | `--events data/user_events.json`; offline nutzbar |

Die Implementierung richtet sich nach der offiziellen
[Goabase-API-Beschreibung](https://www.goabase.net/api/party/), der
[Goabase-Spezifikation](https://www.goabase.net/api/schema/goabase.json) und der
[Bandsintown-Dokumentation](https://help.artists.bandsintown.com/en/articles/9186477-api-documentation).
Goabase-Quellenlinks bleiben im Digest erhalten. Abfrage-/Seitenlimits und Quellenausfälle
erscheinen im Bericht. Ein fehlender Treffer bedeutet nicht, dass es keine Veranstaltung gibt.

### Bandsintown aktivieren

`.env.example` nach `.env` kopieren und eine **eigene** App-ID eintragen:

```dotenv
BANDSINTOWN_APP_ID=
```

```powershell
& .\.venv\Scripts\python.exe main.py --live --include-bandsintown
```

Die CSV und das Profil werden nicht hochgeladen. Für diesen explizit aktivierten Adapter
werden aber einzelne Künstlernamen und der API-Key an Bandsintown übertragen. Ohne diese
Option bleiben die Künstlernamen beim lokalen Matching. Goabase erhält Suchmonat und
Regionskoordinaten; konfigurierte Websites erhalten gewöhnliche Seitenabrufe.

### Club-, Festival-, Regional- und SoundCloud-Seiten konfigurieren

```powershell
& .\.venv\Scripts\python.exe main.py --init-sources
```

Erzeugt die ignorierte Datei `data/user_sources.json`. Sie enthält Recherche-Vorlagen
für die aktuelle [Kater-Seite](https://www.katerclub.de/) und
[Tanzhaus West](https://tanzhaus-west.de/). Konkrete Festival-, Club-, Archiv-, RA- und
SoundCloud-URLs ergänzen. Beispielstruktur (Platzhalter ersetzen):

```json
{
  "sites": [
    {
      "name": "Regionaler Club",
      "url": "https://club.example/programm/",
      "category": "party",
      "link_contains": "/events/",
      "max_pages": 10,
      "enabled": false
    }
  ],
  "research_pages": [
    {
      "name": "Artist auf SoundCloud",
      "artist": "Eigener Künstlername",
      "url": "https://soundcloud.com/PROFILNAME",
      "enabled": false
    }
  ],
  "venue_sites": [
    {
      "venue": "Exakter Venue-Name aus früherem Auftritt",
      "name": "Clubprogramm nach Auftrittshistorie",
      "url": "https://club.example/programm/",
      "category": "party",
      "link_contains": "/events/",
      "max_pages": 10,
      "enabled": false
    }
  ]
}
```

`sites` wird bei Live-Läufen abgefragt, `research_pages` bei `--discover`.
`venue_sites` wird bei `--discover` nachgeladen, wenn ein früherer Favoriten-Auftritt in
dieser Venue belegt ist. Einmal konfigurierte Clubdomains werden wiederverwendet;
unbekannte Domains werden nicht anhand eines Namens geraten. Archivseiten können in
`sites` aufgenommen werden. Bei Veranstaltungsseiten kann `category` auch `live` sein.

Pro Site werden maximal 30 Seiten gelesen, nur passende Links derselben Domain und
nur eine Linkebene. `robots.txt`, Zeitlimits und Abrufabstände werden berücksichtigt.
Weiterleitungen werden gemeldet; dann die endgültige URL konfigurieren. JavaScript-only-Seiten,
Login-Schranken und Zugriffssperren werden nicht umgangen. Der JSON-LD-Adapter benötigt
Titel, Startdatum und verwertbare Ortsdaten. Seiten ohne strukturierte Eventdaten können
als `research_pages` allgemeine Recherchehinweise liefern.

Für eine eindeutig benannte Artist-Sektion sind `artist_section_start` und
`artist_section_end` konfigurierbar (Kater: `Residents` bis `Radio`). Die extrahierten
Namen sind Vorschläge mit Quellenbezug, die vor Übernahme geprüft werden sollten.

### Frühere Auftritte → Clubs → weitere Artists

```powershell
& .\.venv\Scripts\python.exe main.py --live --discover --include-bandsintown
# Alternativ ohne Künstler-API, mit eigener historischer Eventdatei:
& .\.venv\Scripts\python.exe main.py --discover --events data/user_events.json
```

Bandsintown wird im Discovery-Lauf für die letzten zwei Jahre bis zum Ende des Zielmonats
abgefragt. Historische Events aus lokalen Dateien und konfigurierten Archivseiten fließen
ebenfalls ein. Aus belegten Favoriten-Auftritten werden Venues abgeleitet. Weitere Artists
aus geladenen Events derselben Venue erscheinen als Vorschläge, mit Datum und Quelle der
Verbindung. Gemeinsame Venues beweisen noch keine musikalische Ähnlichkeit.

Recherche darf über die drei Zielregionen hinausgehen: Berlin und Frankfurt sind also
als Referenzen sinnvoll. **Der Event-Digest behält trotzdem seinen Regionsfilter.**
Ergebnisse: `data/user_discovery.json` und `exports/discovery.md`. Favoriten und Profil werden
nicht automatisch verändert. SoundCloud-Gigtexte ohne belastbares Datum/Ort werden nicht
zu bestätigten Events umgedeutet. Sie können nach Prüfung in die lokale Eventdatei übernommen werden.

Der historische Berliner Club Mensch Meier sollte mit einer konkreten Archivquelle eingebunden
werden; gleichnamige Clubs dürfen nicht verwechselt werden. Das System liefert keine
universelle Suchmaschine für unbekannte Clubdomains. Ohne eigene Artists und passende
Archivquellen ist die persönliche Auftrittshistorie naturgemäß noch leer.

### Lokaler Eventimport

```json
[
  {
    "title": "Selbst geprüfter Event",
    "start": "2030-05-12T21:00:00+02:00",
    "end": "2030-05-13T04:00:00+02:00",
    "city": "Wien",
    "country": "AT",
    "venue": "Beispielclub",
    "category": "party",
    "artists": ["Eigener Künstlername"],
    "tags": ["Downtempo", "Open Air"],
    "latitude": 48.2082,
    "longitude": 16.3738,
    "url": "https://example.org/event",
    "status": "scheduled"
  }
]
```

`title` und `start` sind Pflicht, Kategorie ist `party` oder `live`.
Für einen Digest sind zusätzlich belastbare Ortsdaten erforderlich. CSV nutzt dieselben
Spalten, mit Semikolon getrennten Artists/Tags und Komma als Spaltentrenner.
Zeitangaben werden als lokale Zeit laut Quelle angezeigt; fehlende Zeitzonen werden nicht geraten.

## Monatliche Routine

```powershell
& .\scripts\run_monthly.ps1 -PythonExe "$PWD\.venv\Scripts\python.exe"
# Optional mit Künstler-Abfragen und Recherche:
& .\scripts\run_monthly.ps1 -PythonExe "$PWD\.venv\Scripts\python.exe" -Bandsintown -Discover
```

Erfolgreiche Läufe werden in `data/user_monthly_state.json` gespeichert. Ein weiterer Aufruf
im selben Monat überspringt die Abfrage, sofern die Berichte noch existieren. Mit
`main.py --live --monthly --force` erneut ausführen, etwa nach Profil-/Quellenänderungen.
Bei Quellenausfällen entsteht ein Teilbericht und Exitcode 2; der Monat bleibt offen.
Exitcode 1 bedeutet Eingabe-/Dateifehler, 130 Abbruch, 0 Erfolg.

Optional die **lokale Windows-Aufgabenplanung** einrichten:

```powershell
& .\scripts\install_monthly_task.ps1 -PythonExe "$PWD\.venv\Scripts\python.exe" -Discover
```

Die Aufgabe prüft täglich um 09:00 Uhr und holt den ersten erfolgreichen Monatslauf nach.
Sie läuft mit Benutzerrechten bei angemeldetem Benutzer, speichert kein Passwort und wurde
nicht automatisch installiert. Es wird kein E-Mail-Versand eingerichtet. Gleichzeitige geplante
Läufe werden unterbunden. Parallele manuelle Monatsläufe vermeiden.

Linux/macOS, alternativ eigene Crontab (absoluten Projekt- und Interpreterpfad einsetzen):

```cron
0 9 * * * EVENT_CURATOR_PYTHON=/absoluter/projektpfad/.venv/bin/python /bin/bash /absoluter/projektpfad/scripts/run_monthly.sh
```

## Datenschutz und GitHub

- Ganz `data/` ist ignoriert, mit genau einer Ausnahme: `sample_artists.csv`.
- Zusätzlich ignoriert: `data/user_*`, `.env` und Varianten, `exports/`, alle übrigen CSVs,
  JSON/JSONL, Datenbanken, private Schlüssel, Logs und virtuelle Umgebungen.
- Keine persönlichen Voreinstellungen im öffentlichen `config.py` eintragen.
- Die `.gitignore` ist kein Verschlüsselungs-/Backup-Schutz. Der aktuelle Projektordner liegt
  in **OneDrive**: dessen Dateisynchronisation kann auch ignorierte Daten übertragen.
  Für ausschließlich lokale Speicherung den gesamten Projektordner außerhalb von OneDrive
  verwenden oder dessen Synchronisation für diesen Ordner deaktivieren.
- `scripts/check_privacy.py` prüft den Git-Index und die erreichbare Commit-Historie auf
  freigegebene Dateipfade und bekannte Schlüsselformate. Es erkennt nicht jeden beliebigen
  personenbezogenen Text; den Diff vor Veröffentlichung zusätzlich ansehen.
- Unter Unix erhalten neue private Dateien restriktive Dateirechte; unter Windows gelten
  die Rechte des Benutzerordners. Reports enthalten persönliche Matches und gehören nicht ins Repo.

### Repository anlegen und veröffentlichen

Das PowerShell-Skript stellt den interaktiven GitHub-Login bereit, prüft den persönlichen
Zielaccount, setzt die Commit-E-Mail **nur für dieses Repository**, führt Tests und
Datenschutzprüfungen aus und erstellt ein öffentliches Repository. Owner und E-Mail
werden beim Aufruf übergeben und nicht im Skript hinterlegt.

```powershell
& .\scripts\setup_github.ps1 `
  -PythonExe "$PWD\.venv\Scripts\python.exe" `
  -Owner 'DEIN-GITHUB-NAME' `
  -CommitEmail 'DEINE-COMMIT-EMAIL' `
  -RepoName 'event-curator-app' `
  -PublishMain
```

`-PublishMain` gibt ausdrücklich die **erste** Veröffentlichung des geprüften `develop`-Stands
als `main` frei. Existiert `main` bereits, wird es nicht verändert. Die weitere Entwicklung
bleibt auf `develop`; spätere Releases erfolgen nach Bestätigung per PR. Ohne diesen Schalter
wird nur `develop` veröffentlicht. Das Skript legt keine PRs an und überschreibt kein
vorhandenes fremdes Remote. Es kann keine Browser-Anmeldung ohne deine Mitwirkung abschließen.
Eine normale Commit-E-Mail ist in öffentlichen Commits sichtbar; eine GitHub-Noreply-Adresse
kann stattdessen übergeben werden.

## Struktur und Verifikation

```text
main.py / config.py            Einstieg, Pfade und öffentliche Standardwerte
event_curator/
  cli.py                      Ablauf und Kommandozeilenargumente
  models.py / storage.py      Datenmodelle, CSV, atomare lokale Speicherung
  interview.py                Schrittweises Party-Interview
  matching.py                 Region, Datum, Relevanz, Ausschlüsse
  discovery.py                Auftrittshistorie, Artist-/Venue-Vorschläge, Gigtexte
  reports.py                  Sichere Markdown-/HTML-Ausgabe
  sources/                    HTTP, Bandsintown, Goabase, JSON-LD, lokale Beispiele
data/sample_artists.csv        Öffentliche, fiktive Beispieldaten
scripts/                      GitHub-Setup, Datenschutzprüfung, Monatsroutine
tests/test_core.py             Offline-Tests mit synthetischen Daten
exports/                      Lokale Reports, niemals in Git
```

```powershell
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
& .\.venv\Scripts\python.exe scripts/check_privacy.py
```

Tests prüfen Regions-/Datumsgrenzen, Absagen, CSV/BOM, Interview-Abbruch, HTML-Escaping,
Adapterformate, Rechercheverbindungen und Git-Datenschutzregeln. Live-Verfügbarkeit,
API-Zugriff und ein vollständiges Clubprogramm lassen sich mit Offline-Tests nicht garantieren.

