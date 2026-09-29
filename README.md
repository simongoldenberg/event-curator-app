# Event Curator · Version 0.1.0

Lokale Python-Anwendung für Konzerte, Parties, Raves und Open Airs in den Räumen
**Würzburg, Freiburg, Wien, Berlin und Frankfurt am Main**. Persönliche Profile, Künstlerlisten, Quellenkonfigurationen
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
`exports/digest-YYYY-MM-demo.md` und `.html`. Sie demonstrieren Rubriken, Filter, Karte und Regionsprüfung.
Ein Live-Lauf erzeugt separate Dateien ohne `-demo`. Öffne die HTML-Datei im Browser per Doppelklick.
Die Oberfläche funktioniert auch auf schmalen Handybildschirmen und lädt keine Schriften,
Kartenkacheln, Skripte oder Tracker von externen Servern.

### Die interaktive Übersicht bedienen

- Oben zu **Karte**, **Konzerte**, **Parties**, **Vier Länder**, **Venues**, **Downtempo-Radar** oder **Quellen** springen.
- Auf der Karte Orte, Eventart und Suchtext filtern. Die Eventkarten und Venue-Pins folgen derselben Auswahl.
- Einen Pin oder Venue-Eintrag antippen, um Details zu sehen; per Plus/Minus zoomen oder die Karte ziehen.
- In einer Eventkarte **Auf Karte** antippen, um zur Venue zu springen.
- Die schraffierten Kreise markieren ungefähr den eingestellten Suchradius. Die exakte
  Regionsprüfung erfolgt anhand der Koordinaten im Python-Code.
- Fehlt bei einer Quelle ein Venue-Name, heißt der Pin „Ort in … nicht benannt“. Die Event-Koordinate
  ist dann kein Beleg für einen bestimmten Club.

Die Kartenbasis stammt aus den gemeinfreien
[Natural-Earth-Kartendaten](https://www.naturalearthdata.com/about/terms-of-use/) und liegt als SVG im Projekt.
Zum Reproduzieren gibt es `scripts/build_map_asset.py`; dafür ist einmalig Internet nötig.

## Eigene Künstler und Party-Profil

### Spotify-Hörverlauf lokal importieren

Wenn du den „Extended Streaming History“-Export von Spotify besitzt, gib seinen **lokalen
Ordner** an (mit Anführungszeichen bei Leerzeichen):

```powershell
& .\.venv\Scripts\python.exe main.py --import-spotify 'C:\Pfad\zu\Spotify Extended Streaming History'
& .\.venv\Scripts\python.exe main.py --live --month 2026-10
```

Der Import liest nur `Streaming_History_Audio_*.json`. Videos, Podcasts, Hörbücher,
als übersprungen markierte Stücke, Wiedergaben unter 30 Sekunden und doppelte Einträge
fließen nicht ein. Neuere
Wiedergaben zählen stärker; die 200 meistgehörten Artists landen in der ignorierten Datei
`data/user_artists.csv` mit gerundeten Hörstunden, Anzahl und letztem Hörjahr. Tracktitel,
IP-Adressen und der rohe Verlauf werden nicht kopiert. Spotify liefert in diesen Dateien
keine verlässlichen Genre-Tags; die App leitet daraus keine behaupteten Genres ab.
Die Künstlerliste wird nur lokal mit Event-Line-ups abgeglichen. Eine bestehende Liste bleibt
erhalten; `--replace-import` ersetzt sie ausdrücklich bei einem erneuten Import.

**Datenschutz:** Der aktuelle Projektordner liegt unter OneDrive. Prüfe dessen Synchronisation,
wenn auch die abgeleitete CSV und die Reports ausschließlich auf diesem Gerät bleiben sollen.

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

- Regionaler Teil: **100 km Luftlinie um Würzburg**, **50 km** um Freiburg, Wien, Berlin und Frankfurt. Ein größerer persönlicher Radius (1–200 km) gilt auch für Würzburg; dort bleibt das Minimum 100 km. Dadurch können Erlangen und Nürnberg in der Würzburg-Rubrik erscheinen.
- Die dritte Rubrik zeigt passende Events außerhalb dieser Kreise in **Deutschland, Frankreich,
  der Schweiz und Österreich**. Die Länderabdeckung hängt von den erreichbaren Quellen ab.
- Koordinaten werden per Haversine-Distanz geprüft. Grenznahe Orte sind zulässig,
  sofern sie innerhalb des Radius liegen.
- Ohne Koordinaten muss der exakte Stadtname einschließlich bekannter Schreibvarianten
  **und** das passende Land vorhanden sein. Unbekannte Orte werden ausgeschlossen.
- Nur kommende oder noch laufende Events im gewählten Kalendermonat werden berücksichtigt.
- Abgesagte/verschobene Events sowie Ausschlussbegriffe werden herausgefiltert.
- Gleicher Titel, Startzeit, Stadt und Venue werden dedupliziert. Abweichende Quellentitel
  können weiterhin doppelt erscheinen.
- Live-Berichte zeigen nur Termine mit belegtem Downtempo-/Melodic-Stil, einem passenden
  eigenen Artist oder einer ausdrücklich gewählten Musikrichtung. Reine Goa-/Psytrance-Funde
  ohne diesen Bezug erscheinen nicht. Der Offline-Demomodus zeigt weiterhin alle Beispiele.
- Persönlicher Artist-Treffer: 50 Punkte; Stiltreffer: 18–38 Punkte; ein belegter Name aus
  dem öffentlichen Downtempo-Radar: 14 Punkte; weitere Genre-/Konzeptbegriffe: jeweils 10;
  heuristische Nähe zu einer Vibe-Referenz: 3. Der Bericht nennt die Gründe. Das ist keine
  Qualitätsbewertung. Fiktive Genres aus `sample_artists.csv` beeinflussen Live-Berichte nicht.

Referenzen wie Kater Blau, Die Bucht, Fusion, Mystic Creatures und Moyn dienen dem
Interview als Orientierung. Ihre Zuordnung zu Begriffen ist eine editierbare Heuristik
in `event_curator/matching.py`, keine Aussage über ein aktuelles Line-up.

## Quellen

| Quelle | Anbindung | Voraussetzung / Grenze |
|---|---|---|
| Goabase | Öffentliche JSON-API, Region, vier Länder, Datum und regionale Detaildaten | Mit `--live`; Schwerpunkt Goa/Psytrance, keine vollständige Techno-/Downtempo-Abdeckung; Länderlisten auf 500 Einträge begrenzt |
| [Kater](https://www.katerclub.de/), [Beate Uwe](https://beate-uwe.de/), [Ritter Butzke](https://club.ritterbutzke.com/events), [Tanzhaus West](https://tanzhaus-west.de/programm/) | Offizielle Programme einschließlich Datum, Beschreibung bzw. Line-up | Mit `--live` automatisch; Änderungen am Seitenaufbau werden als fehlende/fehlerhafte Quelle angezeigt |
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
Die vier Clubseiten werden nur bei gewählten Regionen Berlin bzw. Frankfurt abgefragt.
Mit `--no-clubs` lassen sie sich für einen Lauf auslassen. Beate-Uwes Reihe „Beate Barfuß“
wird anhand der [Beschreibung des Clubs](https://beate-uwe.de/) als Downtempo markiert;
bei anderen Clubnächten wird der Stil aus dem jeweiligen Programmtext oder bekannten Artists abgeleitet.
Der frühere Berliner Club [Mensch Meier ist geschlossen](https://www.clubcommission.de/tschuessi-mensch-meier/)
und wird daher nicht als aktuelle Terminquelle geführt.

### Recherchierte Venues und geprüfte Termine

`data/user_venues.json` enthält die lokal recherchierten Verbindungen zwischen eigenen Artists
und Clubprogrammen. Die Datei bleibt ignoriert. Im HTML-Bericht erscheint ein Venue-Scout mit
Links zum aktuellen Programm und zum konkreten Auftrittsbeleg. Ein früherer Auftritt gilt
**nicht** als neuer Termin. Die erste Recherche gleicht die private 200er-Auswahl unter anderem
mit den offiziellen Archiven von [Gretchen](https://www.gretchen-club.de/hall_of_fame/) und
[Klunkerkranich](https://klunkerkranich.org/artistswhoplayedwithus/) ab. Im Gretchen-Archiv
wurden 20 exakte Namen aus der 200er-Auswahl gefunden. Berlin ist am besten
belegt; für Würzburg liegt noch kein verifizierter Artist-Club-Beleg vor.

Einzelne sicher belegte kommende Konzerte stehen in `data/user_verified_events.json` und werden
bei `--live` automatisch zusätzlich geladen. Vor der Anreise den verlinkten Termin prüfen.
Diese lokale Datei wird ebenfalls nicht hochgeladen. Neue Clubs liefern dadurch nicht automatisch
maschinenlesbare Events: Die Programm-Links sind der Einstieg zur Prüfung; JSON-LD-Seiten lassen
sich wie unten beschrieben in `data/user_sources.json` konfigurieren.

### Würzburg-Probe und monatliche Routine

Die Probe vom 29.09.2026 prüfte das offizielle [Dornheim-Programm](https://waldschaenke-dornheim.de/club/),
das [E-Werk Erlangen](https://www.e-werk.de/programm/partys/),
[Die Rakete Nürnberg](https://dierakete.com/programm/),
den [Airport Würzburg](https://club-airport.com/) und die [Posthalle](https://www.posthalle.de/programm/).
Passende, datierte Termine wurden lokal in `data/user_verified_events.json` erfasst. Für einen
Bericht nur aus diesen einzeln belegten Daten:

```powershell
& .\.venv\Scripts\python.exe main.py --events data\user_verified_events.json --month 2026-10
```

Die lokale Windows-Aufgabe `EventCurator-Monthly` startet die Live-Abfragen um 9 Uhr. Sie
prüft täglich, ob der laufende Monat schon erfolgreich verarbeitet wurde, und schreibt dann
nur einmal einen Digest; nach Quellenausfällen versucht sie es erneut. Sie wurde mit
`scripts/install_monthly_task.ps1 -PythonExe .\.venv\Scripts\python.exe -Discover`
eingerichtet. Die zusätzlichen Würzburg-/Umkreis-Programme liegen als allgemeine
Recherche-Seiten in der ignorierten `data/user_sources.json`. Die automatische Recherche
wertet nur maschinenlesbare Termine direkt aus; andere Clubseiten liefern Hinweise, die
manuell auf Datum, Ort und Line-up geprüft werden müssen. Sie durchsucht ohne eigene
Bandsintown-ID nicht automatisch jeden der 200 Artists einzeln. Künstlernamen werden ohne
`--include-bandsintown` nicht an externe Dienste übertragen.

Mit `-Discover` ruft die Aufgabe außerdem die sieben konfigurierten Clubseiten ohne
Artist-Suchparameter ab und vergleicht deren sichtbaren Text **lokal mit allen 200 Artists**
und den öffentlichen Stilvorschlägen. Das Ergebnis steht in
`exports/artist-scan-YYYY-MM.md`. Ein Namenshinweis kann auch ein alter Auftritt sein;
erst nach Prüfung von Datum, Stadt und Line-up wird er als Termin übernommen.

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

Recherche darf über die fünf Zielregionen hinausgehen. Der Event-Digest trennt Treffer innerhalb
der lokalen Suchregionen (Würzburg 100 km, sonst standardmäßig 50 km) und Fernziele in den vier Ländern.
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
  venue_catalog.py            Ignorierte lokale Liste belegter Venues laden
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
