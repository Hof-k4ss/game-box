# GameBox offline installation

## Runtime target

The GameBox web UI is exposed on **TCP 6767** on the Ubuntu host:

```text
http://HOST-IP:6767
```

The container still listens internally on port 8080; only the host-side port is 6767.

## Preparation machine (Internet available)

Clone this repository and prepare the Docker image bundle:

```bash
./scripts/prepare-offline.sh
```

The script pulls the images declared in `.env`, then exports them to:

```text
offline/gamebox-images.tar
```

Before exporting, set a unique `ROMM_AUTH_SECRET_KEY` in `.env`, for example:

```bash
openssl rand -hex 32
```

Copy the resulting repository directory, including `offline/gamebox-images.tar`, to removable media.

### Runtime assets

A completely disconnected installation must have every browser-emulator asset required by the selected RomM release available locally. Do not use the `slim` image for this purpose. Validate the offline bundle on a staging machine by disconnecting Internet access before moving it to the production LAN.

RomM's current documentation notes that EmulatorJS Netplay can load some assets from its nightly CDN. This is a known limitation to validate for the exact pinned release; the GameBox project must not claim Internet-free Netplay until that validation passes.

## Offline Ubuntu machine

Copy the project to the machine, then:

```bash
./scripts/import-offline.sh
```

Check:

```bash
docker compose ps
```

Open from any LAN client:

```text
http://<ubuntu-ip>:6767
```

The first startup opens RomM's setup wizard. Create the local administrator account. No public metadata account is required just to play an already-imported local library, but automatic artwork/metadata enrichment normally needs a metadata provider and therefore must be prepared while connected or supplied locally.

## ROMs

Put game files under `roms/`, using platform directories. Example:

```text
roms/
├── nes/
│   ├── game-one.zip
│   └── game-two.zip
├── snes/
│   ├── game-one.zip
│   └── game-two.zip
├── n64/
├── gb/
├── gba/
├── genesis/
├── arcade/
└── dos/
```

Keep the files outside Git. The repository `.gitignore` already excludes ROMs, firmware and runtime data.

RomM supports browser emulation through EmulatorJS for many retro systems, including NES, SNES, Game Boy/Color/Advance, N64, PlayStation, Genesis/Mega Drive, arcade/MAME and MS-DOS. Exact compatibility depends on the core and game.

## ZIP files

Do not blindly extract every ZIP. ROMM can identify supported compressed game files during scanning. If a particular multi-file title or firmware package does not scan correctly, follow the platform-specific structure expected by RomM and the selected emulator core.

## Multiplayer

The project enables EmulatorJS Netplay, but multiplayer is a compatibility feature, not a universal guarantee. Test each desired game/core on the closed LAN. Good candidates include compatible party, fighting, racing and co-op games. Up to four players are supported by RomM's current EmulatorJS integration where the core/game supports it.

For a truly offline LAN, no public STUN/TURN service is configured. WebRTC direct host candidates may work on the same subnet; if the browser/core requires relay or external ICE, that game/core is not considered offline-ready until a local ICE solution is added and tested.

## Security

The service is intentionally exposed to the LAN. Do not forward port 6767 to the Internet. Change the default database passwords and auth secret before first production use.
