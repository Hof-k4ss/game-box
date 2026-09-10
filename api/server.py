import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROMS_DIR = Path(os.environ.get("ROMS_DIR", "/srv/roms"))
PORT = 8000

SYSTEMS = {
    "arcade": "Arcade",
    "nes": "NES",
    "snes": "SNES",
    "gb": "Game Boy",
    "gbc": "Game Boy Color",
    "gba": "Game Boy Advance",
    "n64": "Nintendo 64",
    "genesis": "Mega Drive / Genesis",
    "segaMD": "Mega Drive / Genesis",
    "psx": "PlayStation",
    "nds": "Nintendo DS",
    "psp": "PSP",
    "dos": "MS-DOS",
    "sms": "Master System",
    "gg": "Game Gear",
    "pce": "PC Engine",
    "atari2600": "Atari 2600",
    "atari7800": "Atari 7800",
    "amiga": "Amiga",
    "c64": "Commodore 64",
    "_a_trier": "À trier",
}

SUPPORTED_FILES = {
    ".zip", ".7z", ".nes", ".fds", ".sfc", ".smc", ".gb", ".gbc", ".gba",
    ".n64", ".z64", ".v64", ".md", ".gen", ".bin", ".iso", ".cue", ".chd",
    ".nds", ".3ds", ".cia", ".pbp", ".cso", ".adf", ".d64", ".t64", ".a26",
    ".a78", ".lnx", ".pce", ".gg", ".sms", ".exe", ".com",
}

_cache = {"timestamp": 0.0, "games": []}
_cache_lock = threading.Lock()


def system_from_path(path: Path):
    rel = path.relative_to(ROMS_DIR)
    folder = rel.parts[0] if rel.parts else "_a_trier"
    return folder, SYSTEMS.get(folder, folder.replace("_", " ").title())


def scan_games():
    games = []
    if not ROMS_DIR.exists():
        return games

    for path in ROMS_DIR.rglob("*"):
        if not path.is_file() or path.name.startswith("."):
            continue
        if path.suffix.lower() not in SUPPORTED_FILES:
            continue
        try:
            system, label = system_from_path(path)
            rel = path.relative_to(ROMS_DIR).as_posix()
            games.append({
                "id": rel,
                "name": path.stem,
                "file": rel,
                "url": "/roms/" + "/".join(part.replace(" ", "%20") for part in rel.split("/")),
                "system": system,
                "systemLabel": label,
                "size": path.stat().st_size,
            })
        except (OSError, ValueError):
            continue

    games.sort(key=lambda g: (g["systemLabel"].lower(), g["name"].lower()))
    return games


def get_games():
    # Short cache avoids walking a very large ROM library for every UI action.
    import time
    now = time.time()
    with _cache_lock:
        if now - _cache["timestamp"] > 3:
            _cache["games"] = scan_games()
            _cache["timestamp"] = now
        return _cache["games"]


class Handler(BaseHTTPRequestHandler):
    def send_json(self, payload, status=200):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        route = urlparse(self.path).path
        if route == "/health":
            self.send_json({"status": "ok"})
            return
        if route == "/api/games":
            games = get_games()
            systems = {}
            for game in games:
                systems.setdefault(game["system"], {"id": game["system"], "label": game["systemLabel"], "count": 0})
                systems[game["system"]]["count"] += 1
            self.send_json({"games": games, "systems": list(systems.values())})
            return
        self.send_json({"error": "Not found"}, 404)

    def log_message(self, *_):
        return


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
