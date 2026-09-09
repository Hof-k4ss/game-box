# GameBox

Offline-first retro gaming box for a closed LAN.

GameBox is designed for an Ubuntu machine with Docker, no Internet access at runtime, and a single browser UI for browsing and launching a personal game library.

## Goals

- One web interface for a large local game library.
- Keyboard-first play.
- Local saves and save states.
- LAN multiplayer where the selected emulator/core supports it.
- No runtime dependency on the public Internet.
- Easy offline export/import so the whole stack can be moved by USB.

## Important scope

GameBox does **not** ship commercial ROMs, BIOS files, or other copyrighted game content. Put only game files and firmware you are legally entitled to use in the local library.

The repository contains the infrastructure, configuration, automation, and documentation needed to run the box.

## Architecture

The first implementation uses RomM as the game-library and browser-play foundation, with MariaDB for metadata and Valkey for background-task state. RomM exposes the game library and EmulatorJS-backed browser emulation through one web application.

The compose stack is intentionally configured for local operation. Metadata-provider credentials are optional and are not required for the basic offline library workflow.

## Project layout

```text
.
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
├── roms/
│   └── README.md
├── scripts/
│   ├── prepare-offline.sh
│   ├── export-offline.sh
│   └── import-offline.sh
└── docs/
    └── offline.md
```

## Supported library families

The exact playable set depends on the emulator cores included by the selected RomM/EmulatorJS release and on the files in the local library. The project is intended to cover common systems such as NES, SNES, Game Boy/Color/Advance, Mega Drive/Genesis, Nintendo 64, PlayStation, PSP, arcade/MAME-compatible titles, and DOS-class software where browser emulation supports the title.

## Multiplayer

LAN multiplayer is treated as a feature to validate rather than something this project blindly promises. Emulator compatibility, browser input behavior, and the current netplay implementation vary by platform/core. The first milestone will verify local single-player operation offline, then test multiplayer on the isolated LAN and document the working combinations.

## Offline workflow

1. On an Internet-connected preparation machine, pull/build the required Docker images and cache every runtime asset needed by the chosen configuration.
2. Export the images and GameBox configuration into an offline bundle.
3. Move the bundle to the isolated Ubuntu machine by USB.
4. Import the images and start the compose stack.
5. Add your legally obtained game files under `roms/` and run the library scan.
6. Open the GameBox web UI from another machine on the LAN.

See `docs/offline.md` for the detailed procedure.

## Status

Initial repository bootstrap. The next commits will add the compose stack, offline packaging scripts, library layout, and then the LAN/netplay validation layer.
