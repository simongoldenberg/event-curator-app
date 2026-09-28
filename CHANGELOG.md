# Änderungsprotokoll

## In Entwicklung — 2026-09-28

### 🚀 Added
- Responsive HTML-Oberfläche mit Sprungmarken, Orts- und Typfiltern, Suche und interaktiver Offline-Karte.
- Berlin und Frankfurt als Zielregionen sowie öffentlich belegter Downtempo-Artist-Radar.

### 🔄 Changed
- Standardsuchradius von 75 auf 50 Kilometer reduziert.
- Monatsberichte zeigen Venues als Kartenpunkte, sofern Koordinaten verfügbar sind.

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
