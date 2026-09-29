# Änderungsprotokoll

## Unveröffentlicht

- Öffentlichen Club- und Festival-Katalog im HTML-Bericht ergänzt: 19 Berliner Orte,
  weitere regionale Programme sowie Bucht, Fusion und Moyn mit klar gekennzeichneter
  Suchabdeckung. Zusätzliche allgemeine Programmseiten fließen in den monatlichen
  lokalen Artist-Abgleich ein; Hinweise bleiben von bestätigten Events getrennt.

## In Entwicklung — 2026-09-29

### 🚀 Added
- Gretchen als direkte Quelle für datierte Konzerte und Clubnächte; Live-Auftritte erscheinen in der Konzert-Rubrik.
- Romare als öffentlich belegter Downtempo-/Electronica-Vorschlag im Artist-Radar.
- Würzburg-Probe mit datierten Terminen aus offiziellen Clubprogrammen und direktem Quellenlink; weitere regionale Programme in der lokalen Recherchekonfiguration.
- Lokale Windows-Monatsaufgabe eingerichtet; erfolgreiche Monate werden nur einmal verarbeitet.
- Privater Abgleich aller 200 Artists mit allgemein abgerufenen Clubseiten; Namenshinweise bleiben von bestätigten Events getrennt.
- Eigene Reiserubrik für passende Termine in Deutschland, Frankreich, der Schweiz und Österreich.
- Privater Venue-Scout mit Auftrittsbelegen und Programm-Links; lokal geprüfte Termine werden im Live-Lauf geladen.
- Länderabfragen über die öffentliche Goabase-API und eine größere Offline-Karte.
- Direkter Programmparser für Ritter Butzke in Berlin.

### 🔄 Changed
- Würzburg-Suchradius auf mindestens 100 km Luftlinie erweitert; übrige Städte bleiben standardmäßig bei 50 km. Karte und Live-Abfrage verwenden dieselbe Regel.
- Lokale Eventimporte nutzen denselben Musikfokus wie Live-Berichte.
- Spotify-Import wertet die 200 wichtigsten statt 80 Artists aus.
- Monatsansicht mit klarerem Einstieg, mobiler Navigation und kompakteren Venue-Karten überarbeitet.

## In Entwicklung — 2026-09-28

### 🚀 Added
- Responsive HTML-Oberfläche mit Sprungmarken, Orts- und Typfiltern, Suche und interaktiver Offline-Karte.
- Berlin und Frankfurt als Zielregionen sowie öffentlich belegter Downtempo-Artist-Radar.
- Direkte Programmquellen für Kater, Beate Uwe und Tanzhaus West mit Line-up- und Datumsprüfung.
- Lokaler Import einer Spotify-Audio-Historie in eine von Git ignorierte Künstlerliste.

### 🔄 Changed
- Standardsuchradius von 75 auf 50 Kilometer reduziert.
- Monatsberichte zeigen Venues als Kartenpunkte, sofern Koordinaten verfügbar sind.
- Live-Berichte gewichten Downtempo und Melodic stärker und blenden Events ohne passenden Stil oder Artist aus.
- Fiktive Artist-Genres aus der Beispiel-CSV beeinflussen Live-Berichte nicht mehr.

## Version 0.1.0 — 2026-09-28

### 🚀 Added
- Modulare lokale Python-CLI ohne zusätzliche Paketabhängigkeiten.
- Künstler-CSV und schrittweises Party-Interview mit lokalem Profil.
- Goabase- und Bandsintown-Adapter sowie konfigurierbare JSON-LD-Veranstaltungsseiten.
- Strikte Filter für Würzburg, Freiburg und Wien; nachvollziehbare Relevanzpunkte.
- Markdown-/HTML-Monatsberichte mit Quellenstatus und fiktivem Offline-Beispielmodus.
- Recherche früherer Venues, weiterer Artists und öffentlicher SoundCloud-Gighinweise.
- Geschützte Datenablagen, Git-Prüfung, GitHub-Setup und lokale Monatsroutine.
- Offline-Tests und deutschsprachige Projektdokumentation.

> [!CAUTION]
> ### 🐙 Known Issues
> - Künstlerbezogene Live-Suche benötigt einen freigegebenen Bandsintown-Zugang.
> - RA, SoundCloud und Clubseiten können strukturierte Daten verweigern oder JavaScript erfordern.
> - Unbekannte Venue-Domains müssen als Quellen ergänzt werden; keine universelle Websuche.
> - Unbekannte Orte werden ausgeschlossen, abweichende Quellentitel können Duplikate erzeugen.
> - Die Monatsroutine muss auf dem lokalen Rechner eingerichtet werden.
