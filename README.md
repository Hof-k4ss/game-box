# 🎮 GameBox

Offline-first retro gaming box for a closed LAN.

GameBox turns an Ubuntu machine into a small browser-based arcade: open one web page, pick a game, and play with the keyboard. The runtime is designed not to require Internet access.

## 🌐 Web interface

The GameBox host exposes RomM on **TCP port 6767**:

```text
http://<GAMEBOX-IP>:6767
```

Example:

```text
http://192.168.1.50:6767
```

## What it is for

- Solo retro games in the browser.
- Same-browser local multiplayer with multiple keyboard mappings where the emulator/core supports it.
- Local saves and save states.
- One searchable library instead of launching individual emulators.
- Closed-LAN operation after the offline bundle has been prepared.

RomM provides EmulatorJS browser emulation for many retro systems, including NES, SNES, Game Boy/Color/Advance, Nintendo 64, PlayStation, Genesis/Mega Drive, arcade/MAME and MS-DOS. Exact compatibility depends on the core and game.

## ROM library

Put your own legally obtained game files under `roms/`:

```text
roms/
├── nes/
├── snes/
├── gb/
├── gbc/
├── gba/
├── n64/
├── genesis/
├── arcade/
└── dos/
```

ZIP archives are supported for supported ROM formats. Do not commit ROMs or firmware to this Git repository; `.gitignore` excludes them.

## Keyboard multiplayer

The baseline GameBox profile deliberately keeps EmulatorJS Netplay disabled. Current RomM documentation notes that Netplay can load some assets from the public nightly CDN, which conflicts with a strict no-Internet runtime.

Instead, multiplayer on one machine uses the emulator's multiple player inputs and a shared keyboard. See `docs/keyboard.md`.

This is suitable for games such as Bomberman, fighting games, beat-'em-ups, party games and some racing games. N64 multiplayer, including Mario Kart 64, must be tested per game/core. Worms Armageddon is not a baseline browser-supported title; a compatible Worms release on a supported platform/core can be tested separately.

## 100% offline workflow

### 1. Connected preparation machine

Install Docker, clone this repository and run:

```bash
bash scripts/prepare-offline.sh
```

This pulls the pinned images and creates `offline/gamebox-images.tar`.

Before doing this, create a unique secret:

```bash
openssl rand -hex 32
```

Put the result in `.env` as `ROMM_AUTH_SECRET_KEY`.

### 2. Transfer by USB

Copy the repository and the offline image bundle to the isolated Ubuntu machine.

Copy your game library into `roms/`.

### 3. Start offline

```bash
bash scripts/import-offline.sh
```

Then open:

```text
http://<GAMEBOX-IP>:6767
```

No public Internet connection is needed at runtime for the baseline browser-emulation stack. The offline bundle must be prepared and tested before disconnecting the preparation machine.

## Metadata and artwork

Automatic metadata/artwork providers normally require Internet access. For a closed LAN, prepare metadata while connected or use local metadata/import files. Playing local ROMs does not require an online account with a metadata provider.

## Current status

The repository contains the offline stack, port 6767 configuration, local RomM config, ROM directory layout, keyboard guidance, and USB image import/export scripts. The final validation step is to build the bundle on a connected staging machine, disconnect it, and verify game boot, saves, ZIP scanning and same-browser multiplayer before production deployment.
