import json
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.robotparser import RobotFileParser

USER_AGENT = "EventCurator/0.1 (personal event research)"
MAX_BYTES = 4 * 1024 * 1024


class SourceError(Exception):
    pass


def safe_url(url):
    try:
        parts = urlsplit(url)
        return parts.scheme == "https" and bool(parts.hostname) and not parts.username and not parts.password and not any(ord(c) < 32 for c in url)
    except ValueError:
        return False


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Jeder Zielwechsel würde eine neue robots-/Quellenprüfung erfordern.
        raise SourceError("Weiterleitung: bitte die endgültige HTTPS-URL konfigurieren.")


class HttpClient:
    def __init__(self, interval=1.0):
        self.interval = interval
        self.last = 0.0
        self.opener = build_opener(NoRedirect)
        self.robots = {}

    def get(self, url, empty_on_404=False):
        if not safe_url(url):
            raise SourceError("Nur HTTPS-URLs ohne eingebettete Zugangsdaten sind erlaubt.")
        for attempt in range(3):
            time.sleep(max(0, self.interval - (time.monotonic() - self.last)))
            self.last = time.monotonic()
            try:
                request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json,text/html,text/plain"})
                with self.opener.open(request, timeout=20) as response:
                    raw = response.read(MAX_BYTES + 1)
                    if len(raw) > MAX_BYTES:
                        raise SourceError("Antwort überschreitet die Größenbegrenzung.")
                    # Einige Clubseiten deklarieren einen alten Charset, senden aber UTF-8.
                    try:
                        return raw.decode("utf-8")
                    except UnicodeDecodeError:
                        return raw.decode(response.headers.get_content_charset() or "utf-8", errors="replace")
            except HTTPError as exc:
                if exc.code == 404 and empty_on_404:
                    return ""
                if exc.code in (429, 500, 502, 503, 504) and attempt < 2:
                    # Keine Wiederholung vor dem vom Server gewünschten Zeitpunkt.
                    retry = exc.headers.get("Retry-After", "")
                    if retry and (not retry.isdigit() or int(retry) > 30):
                        raise SourceError("Quelle verlangt eine spätere Wiederholung.") from None
                    time.sleep(max(2 ** attempt, int(retry or 0)))
                    continue
                raise SourceError(f"HTTP {exc.code}; Quelle nicht verfügbar oder Zugriff abgelehnt.") from None
            except (URLError, TimeoutError, OSError):
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                raise SourceError("Netzwerkfehler oder Zeitüberschreitung.") from None
        raise SourceError("Quelle nicht erreichbar.")

    def json(self, url, empty_on_404=False):
        text = self.get(url, empty_on_404)
        try:
            return json.loads(text) if text else None
        except ValueError:
            raise SourceError("Quelle lieferte kein gültiges JSON.") from None

    def page(self, url):
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        if origin not in self.robots:
            robot_text = self.get(origin + "/robots.txt", empty_on_404=True)
            robot = RobotFileParser()
            robot.parse(robot_text.splitlines() if robot_text else ["User-agent: *", "Disallow:"])
            self.robots[origin] = robot
        robot = self.robots[origin]
        if not robot.can_fetch(USER_AGENT, url):
            raise SourceError("Abruf durch robots.txt ausgeschlossen.")
        delay = robot.crawl_delay(USER_AGENT) or 0
        if delay > 30:
            raise SourceError("Crawl-Abstand über 30 Sekunden; manuell importieren.")
        if delay:
            time.sleep(max(0, delay - (time.monotonic() - self.last)))
        return self.get(url)
