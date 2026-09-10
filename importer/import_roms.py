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
    "psx": {".cue", ".bin", ".img", ".iso", ".pbp", ".chd", ".ecm"},
    "nds": {".nds"},
    "psp": {".iso", ".cso"},
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
}

IGNORED_SUFFIXES = {".txt", ".nfo", ".jpg", ".jpeg", ".png", ".gif", ".sfv", ".md", ".db"}
ARCADE_EXTENSIONS = {".bin", ".rom", ".u1", ".u2", ".u3", ".u4", ".u5", ".u6", ".u7", ".u8", ".ic1", ".ic2", ".ic3", ".ic4"}
ARCADE_NAME_PATTERNS = re.compile(r"(?:[-_.](?:p1|p2|s1|m1|c1|c2|c3|c4|v1|v2|u1|u2|u3|u4|u5|u6|u7|u8))(?:[-_.]|$)", re.I)


def clean_name(value):
    return re.sub(r"\s+", " ", value.replace("_", " ")).strip()


def read_zip_members(path):
    with zipfile.ZipFile(path) as archive:
        return [(info.filename, b"") for info in archive.infolist() if not info.is_dir()]


def read_7z_members(path):
    result = subprocess.run(["7z", "l", "-slt", str(path)], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "7z n'a pas pu lire l'archive")
    members = []
    for line in result.stdout.splitlines():
        if line.startswith("Path = "):
            current = line[7:]
            if current not in {str(path), ""}:
                members.append((current, b""))
    return members


def member_names(path):
    suffix = path.suffix.lower()
    if suffix == ".zip":
        return read_zip_members(path)
    if suffix == ".7z":
        return read_7z_members(path)
    return [(path.name, b"")]


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


def detect_magic(path, member):
    if path.suffix.lower() != ".zip":
        return None
    try:
        with zipfile.ZipFile(path) as archive:
            with archive.open(member) as stream:
                data = stream.read(512)
    except Exception:
        return None

    if data[:4] == b"NES\x1a":
        return "nes"
    if len(data) >= 0x108 and data[0x104:0x108] == bytes.fromhex("ce ed 66 66"):
        return "gb"
    return None


def looks_like_arcade(path, names, meaningful):
    if path.suffix.lower() not in {".zip", ".7z"} or len(names) < 3:
        return False
    lower = " ".join(names).lower()
    explicit = ("neogeo", "pgm", "mame", "fbneo", "fba", "arcade")
    if any(marker in path.stem.lower() for marker in explicit):
        return True
    arcade_suffix_count = sum(1 for suffix in meaningful if suffix in ARCADE_EXTENSIONS)
    patterned_names = sum(1 for name in names if ARCADE_NAME_PATTERNS.search(name))
    # Arcade sets normally contain several chip dumps in one archive. We only
    # classify here when the internal structure looks like a romset rather than
    # a generic multi-file console/disc archive.
    return arcade_suffix_count >= 2 and (patterned_names >= 1 or arcade_suffix_count >= 3)


def detect_system(path):
    try:
        members = member_names(path)
    except Exception as exc:
        return None, 0, f"lecture archive impossible : {exc}"

    names = [name for name, _ in members]
    scores, meaningful = score_extensions(names)

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    if ranked[0][1] > 0:
        best, best_score = ranked[0]
        second_score = ranked[1][1] if len(ranked) > 1 else 0
        if best_score >= 1 and best_score > second_score:
            return best, 100, f"extension(s) interne(s) : {', '.join(sorted(set(meaningful)))}"

    if path.suffix.lower() == ".zip":
        for name, _ in members[:20]:
            system = detect_magic(path, name)
            if system:
                return system, 95, f"signature interne détectée dans {name}"

    if looks_like_arcade(path, names, meaningful):
        return "arcade", 85, "structure interne ressemblant à un ROMset arcade"

    return None, 0, f"aucune signature/extension suffisamment fiable ({', '.join(sorted(set(meaningful)) or ['aucune'])})"


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

    files = [p for p in SOURCE.rglob("*") if p.is_file() and not p.name.startswith(".")]
    print("\n🎮 GameBox — import des ROMs")
    print(f"Source : {SOURCE}")
    print(f"Destination : {ROMS}")
    print(f"Mode : {'SIMULATION' if DRY_RUN else 'IMPORT'}\n")

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
    print(f"Fichiers examinés : {len(files)}")
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
