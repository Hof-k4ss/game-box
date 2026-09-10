import hashlib
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

SOURCE = Path(os.environ.get("SOURCE_DIR", "/source"))
ROMS = Path(os.environ.get("ROMS_DIR", "/srv/roms"))
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() in {"1", "true", "yes", "on"}

EXTENSIONS = {
    "nes": {".nes", ".fds", ".unf", ".unif"},
    "snes": {".sfc", ".smc", ".fig", ".swc", ".bsx"},
    "gb": {".gb"},
    "gbc": {".gbc"},
    "gba": {".gba"},
    "n64": {".n64", ".z64", ".v64"},
    "genesis": {".md", ".gen", ".smd"},
    "psx": {".cue", ".bin", ".img", ".pbp", ".chd", ".ecm"},
    "nds": {".nds"},
    "psp": {".cso"},
    "dos": {".exe", ".com", ".bat"},
    "sms": {".sms"},
    "gg": {".gg"},
    "pce": {".pce", ".sgx"},
    "atari2600": {".a26", ".bin"},
    "atari7800": {".a78"},
    "amiga": {".adf", ".adz", ".hdf"},
    "c64": {".d64", ".t64", ".crt"},
}

DISPLAY = {
    "nes": "NES", "snes": "SNES", "gb": "Game Boy", "gbc": "Game Boy Color",
    "gba": "Game Boy Advance", "n64": "Nintendo 64", "genesis": "Mega Drive / Genesis",
    "psx": "PlayStation", "nds": "Nintendo DS", "psp": "PSP", "dos": "MS-DOS",
    "sms": "Master System", "gg": "Game Gear", "pce": "PC Engine", "atari2600": "Atari 2600",
    "atari7800": "Atari 7800", "amiga": "Amiga", "c64": "Commodore 64",
    "saturn": "Sega Saturn",
}

IGNORED_SUFFIXES = {".txt", ".nfo", ".jpg", ".jpeg", ".png", ".gif", ".sfv", ".md", ".db", ".html", ".htm"}
ARCHIVE_SUFFIXES = {".zip", ".7z", ".rar"}
CANDIDATE_SUFFIXES = ARCHIVE_SUFFIXES | {suffix for values in EXTENSIONS.values() for suffix in values} | {".iso", ".cue"}
ARCADE_EXTENSIONS = {".bin", ".rom", ".u1", ".u2", ".u3", ".u4", ".u5", ".u6", ".u7", ".u8", ".ic1", ".ic2", ".ic3", ".ic4"}
ARCADE_NAME_PATTERNS = re.compile(r"(?:[-_.](?:p1|p2|s1|m1|c1|c2|c3|c4|v1|v2|u1|u2|u3|u4|u5|u6|u7|u8))(?:[-_.]|$)", re.I)


def clean_name(value):
    return re.sub(r"\s+", " ", value.replace("_", " ")).strip()


def read_zip_members(path):
    with zipfile.ZipFile(path) as archive:
        return [(info.filename, "zip") for info in archive.infolist() if not info.is_dir()]


def read_7z_members(path):
    result = subprocess.run(["7z", "l", "-slt", str(path)], capture_output=True, text=True, check=False)
    members = []
    current = None
    for line in result.stdout.splitlines():
        if line.startswith("Path = "):
            current = line[7:]
            if current not in {str(path), ""}:
                members.append((current, "7z"))
    if not members:
        message = "archive illisible ou incomplète"
        detail = result.stderr.strip() or result.stdout.strip()
        if "Unexpected end of archive" in detail:
            message = "archive incomplète (fin manquante)"
        elif detail and result.returncode != 0:
            message = "archive illisible"
        raise RuntimeError(message)
    return members


def member_names(path):
    """Lit une archive en se fiant au contenu réel, pas seulement à son extension."""
    suffix = path.suffix.lower()
    errors = []
    readers = [read_zip_members, read_7z_members]
    if suffix in {".7z", ".rar"}:
        readers = [read_7z_members, read_zip_members]

    for reader in readers:
        try:
            members = reader(path)
            if members:
                actual = members[0][1]
                expected = suffix.lstrip(".")
                note = ""
                if expected in {"zip", "7z"} and actual != expected:
                    note = f" — archive détectée comme {actual.upper()} malgré l’extension .{expected}"
                return members, note
        except Exception as exc:
            errors.append(str(exc))

    detail = errors[-1] if errors else "format inconnu"
    raise RuntimeError(detail)


def score_extensions(names):
    scores = {system: 0 for system in EXTENSIONS}
    meaningful = []
    for name in names:
        suffix = Path(name).suffix.lower()
        if suffix in IGNORED_SUFFIXES:
            continue
        meaningful.append(suffix)
        for system, extensions in EXTENSIONS.items():
            if suffix in extensions:
                scores[system] += 1
    return scores, meaningful


def read_member_bytes(path, member, limit=2 * 1024 * 1024):
    try:
        kind = member[1] if isinstance(member, tuple) else "zip"
        name = member[0] if isinstance(member, tuple) else member
        if kind == "zip":
            with zipfile.ZipFile(path) as archive, archive.open(name) as stream:
                return stream.read(limit)
        process = subprocess.Popen(["7z", "x", "-so", str(path), name], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        try:
            data = process.stdout.read(limit)
            process.kill()
            process.wait(timeout=2)
            return data
        finally:
            if process.poll() is None:
                process.kill()
    except Exception:
        return b""


def detect_disc_signature(data):
    if not data:
        return None
    upper = data.upper()
    if b"PSP_GAME" in upper[:1024 * 1024] or b"UMD_VIDEO" in upper[:1024 * 1024]:
        return "psp"
    if b"SEGASATURN" in upper[:2 * 1024 * 1024] or b"SEGA SATURN" in upper[:2 * 1024 * 1024]:
        return "saturn"
    psx_markers = (b"PLAYSTATION", b"SCUS_", b"SLUS_", b"SLES_", b"SCES_", b"SLPS_", b"SCPM_")
    if any(marker in upper[:2 * 1024 * 1024] for marker in psx_markers):
        return "psx"
    return None


def filename_hint(path):
    name = path.stem.lower()
    if re.search(r"\b(psp|playstation portable)\b", name):
        return "psp"
    if re.search(r"\b(sega[ _-]?saturn|saturn)\b", name):
        return "saturn"
    return None


def inspect_disc(path, members=None):
    """Essaie d'identifier un ISO/CUE/CSO par sa signature avant le nom."""
    if members:
        candidates = [member for member in members if Path(member[0]).suffix.lower() in {".iso", ".cso", ".bin"}]
        for member in candidates[:3]:
            system = detect_disc_signature(read_member_bytes(path, member))
            if system:
                return system
    else:
        try:
            with path.open("rb") as stream:
                data = stream.read(2 * 1024 * 1024)
            return detect_disc_signature(data)
        except OSError:
            return None
    return None


def looks_like_arcade(path, names, meaningful):
    if path.suffix.lower() not in ARCHIVE_SUFFIXES or len(names) < 3:
        return False
    explicit = ("neogeo", "pgm", "mame", "fbneo", "fba", "arcade")
    if any(marker in path.stem.lower() for marker in explicit):
        return True
    arcade_suffix_count = sum(1 for suffix in meaningful if suffix in ARCADE_EXTENSIONS)
    patterned_names = sum(1 for name in names if ARCADE_NAME_PATTERNS.search(name))
    return arcade_suffix_count >= 2 and (patterned_names >= 1 or arcade_suffix_count >= 3)


def detect_system(path):
    suffix = path.suffix.lower()
    if suffix in {".iso", ".cso"}:
        system = inspect_disc(path)
        if system:
            return system, 98, "signature disque détectée"
        hint = filename_hint(path)
        if hint:
            return hint, 70, "système probable d’après le nom du fichier (à confirmer)"
        return None, 0, "disque sans signature système exploitable"

    if suffix == ".cue":
        try:
            text = path.read_text(errors="ignore").upper()
            if any(marker in text for marker in ("PSP_GAME", "UMD_VIDEO")):
                return "psp", 80, "indice PSP dans le fichier CUE"
            if "SATURN" in text:
                return "saturn", 80, "indice Saturn dans le fichier CUE"
            if any(marker in text for marker in ("SCUS_", "SLUS_", "SLES_", "SCES_", "SLPS_")):
                return "psx", 90, "identifiant PlayStation détecté dans le CUE"
        except OSError:
            pass
        hint = filename_hint(path)
        if hint:
            return hint, 70, "système probable d’après le nom du fichier (à confirmer)"

    try:
        members, archive_note = member_names(path)
    except Exception as exc:
        hint = filename_hint(path)
        if hint:
            return None, 0, f"archive endommagée — système probable : {DISPLAY.get(hint, hint)} ({exc})"
        return None, 0, f"lecture archive impossible : {exc}"

    names = [name for name, _ in members]
    scores, meaningful = score_extensions(names)
    extension_summary = ", ".join(sorted(set(meaningful))) or "aucune"

    disc_system = inspect_disc(path, members)
    if disc_system:
        return disc_system, 98, f"signature disque détectée dans l’archive{archive_note}"

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    if ranked[0][1] > 0:
        best, best_score = ranked[0]
        second_score = ranked[1][1] if len(ranked) > 1 else 0
        if best_score >= 1 and best_score > second_score:
            return best, 100, f"extension(s) interne(s) : {extension_summary}{archive_note}"

    if any(kind == "zip" for _, kind in members):
        for name, kind in members[:20]:
            if kind != "zip":
                continue
            data = read_member_bytes(path, (name, kind), 512)
            if data[:4] == b"NES\x1a":
                return "nes", 95, f"signature NES détectée dans {name}{archive_note}"
            if len(data) >= 0x108 and data[0x104:0x108] == bytes.fromhex("ce ed 66 66"):
                return "gb", 95, f"signature Game Boy détectée dans {name}{archive_note}"

    if looks_like_arcade(path, names, meaningful):
        return "arcade", 85, f"structure interne ressemblant à un ROMset arcade{archive_note}"

    return None, 0, f"aucune signature/extension suffisamment fiable ({extension_summary}){archive_note}"


def destination_for(system, source_name):
    folder = system if system else "_a_trier"
    target_dir = ROMS / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / source_name
    if not target.exists():
        return target
    digest = hashlib.sha1(source_name.encode("utf-8")).hexdigest()[:8]
    return target_dir / f"{Path(source_name).stem} [{digest}]{Path(source_name).suffix}"


def main():
    if not SOURCE.exists() or not SOURCE.is_dir():
        print(f"ERREUR : dossier source introuvable : {SOURCE}")
        return 2
    ROMS.mkdir(parents=True, exist_ok=True)

    files = [
        p for p in SOURCE.rglob("*")
        if p.is_file() and not p.name.startswith(".") and p.suffix.lower() in CANDIDATE_SUFFIXES
    ]
    skipped = [
        p for p in SOURCE.rglob("*")
        if p.is_file() and not p.name.startswith(".") and p.suffix.lower() not in CANDIDATE_SUFFIXES
    ]

    print("\n🎮 GameBox — import des ROMs")
    print(f"Source : {SOURCE}")
    print(f"Destination : {ROMS}")
    print(f"Mode : {'SIMULATION' if DRY_RUN else 'IMPORT'}")
    print(f"Fichiers ignorés (non-ROM) : {len(skipped)}\n")

    counts = {}
    unknown = []
    moved = 0

    for path in sorted(files):
        system, confidence, reason = detect_system(path)
        if system:
            label = DISPLAY.get(system, system)
            destination = destination_for(system, path.name)
            counts[system] = counts.get(system, 0) + 1
            print(f"✓ {clean_name(path.name)}")
            print(f"  → {label} ({confidence}%) — {reason}")
            if not DRY_RUN:
                shutil.move(str(path), str(destination))
            moved += 1
        else:
            destination = destination_for(None, path.name)
            unknown.append((path, reason))
            print(f"? {clean_name(path.name)}")
            print(f"  → À TRIER — {reason}")
            if not DRY_RUN:
                shutil.move(str(path), str(destination))

    print("\nRésumé")
    print("-------")
    print(f"Fichiers ROM examinés : {len(files)}")
    print(f"Classés : {moved}")
    print(f"À vérifier : {len(unknown)}")
    for system, count in sorted(counts.items()):
        print(f"  {DISPLAY.get(system, system):20} {count}")
    if unknown:
        print("\nFichiers à vérifier :")
        for path, reason in unknown:
            print(f"  - {path.name}: {reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
