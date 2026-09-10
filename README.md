# 🎮 GameBox

GameBox transforme un PC Ubuntu **qui reste un PC de travail** en borne rétro accessible depuis un navigateur.

Le projet est volontairement isolé dans Docker : rien n'installe d'émulateur directement dans Ubuntu.

## Ce que fait GameBox

- interface web simple pensée pour clavier et manettes ;
- émulation dans le navigateur avec **EmulatorJS** ;
- cores EmulatorJS stockés localement dans l'image Docker : pas de CDN nécessaire au runtime ;
- ROMs conservées sur le disque de l'hôte ;
- importeur qui inspecte le contenu des archives avant de choisir la console ;
- jeux inconnus envoyés dans `roms/_a_trier/` au lieu d'être mal classés ;
- cache navigateur EmulatorJS activé pour accélérer les lancements suivants ;
- SharedArrayBuffer/threads activés lorsque le navigateur le permet ;
- Nginx sert directement les ROMs et les fichiers statiques pour éviter un détour inutile par l'API.

EmulatorJS exécute RetroArch compilé en WebAssembly dans le navigateur. C'est donc le navigateur qui fait réellement tourner le jeu, tandis que Docker sert l'interface, les cores et les fichiers. citeturn2search8turn1search0

## ⚡ Pourquoi cette architecture pour éviter les lags ?

Le serveur ne traite pas les touches de clavier pendant la partie. Une fois le jeu chargé, les entrées et le rendu restent côté navigateur.

GameBox ajoute plusieurs optimisations :

- fichiers statiques servis par Nginx avec `sendfile` ;
- ROMs servies directement, avec support HTTP Range ;
- cache local EmulatorJS jusqu'à 4 Go ;
- cores locaux pour supprimer les téléchargements CDN pendant le jeu ;
- cores threads activés lorsque le navigateur fournit `SharedArrayBuffer` ;
- interface volontairement légère, sans gros framework ;
- mode plein écran disponible.

EmulatorJS documente le mode threads et précise qu'il nécessite les en-têtes COOP/COEP ; son cache peut conserver cores, ROMs et BIOS dans IndexedDB. citeturn1search0turn2search0

**Important :** aucune solution web ne peut garantir exactement la latence d'un émulateur natif. Pour une latence minimale absolue, RetroArch natif reste supérieur au WebAssembly navigateur. RetroArch documente lui-même ses mécanismes de réduction de latence et indique que sa version navigateur est plus limitée que la version complète. citeturn0search0turn0search2

## 🚀 Installation

### 1. Préparer le dossier

```bash
git clone https://github.com/Hof-k4ss/game-box.git
cd game-box
cp .env.example .env
```

### 2. Choisir le dossier source des ROMs

Ouvre `.env` et modifie :

```dotenv
ROM_SOURCE_DIR=/home/TON_UTILISATEUR/Téléchargements/ROMs
```

Le dossier peut être n'importe où sur le PC.

### 3. Construire et démarrer

```bash
./gamebox start
```

La première construction télécharge les composants EmulatorJS dans l'image Docker. **Après cette construction, GameBox n'a pas besoin du CDN EmulatorJS pour fonctionner.**

### 4. Importer les jeux

```bash
./gamebox import
```

L'importeur inspecte les archives. Pour un ZIP, il regarde les fichiers qu'il contient, pas seulement le nom du ZIP. Il utilise ensuite les extensions reconnues, les signatures et les règles système.

Exemple :

```text
Téléchargements/ROMs/
├── Super Mario Kart.zip
├── Pokemon Yellow.zip
└── Worms Armageddon.zip
```

peut devenir :

```text
roms/
├── snes/Super Mario Kart.zip
├── gb/Pokemon Yellow.zip
└── n64/Worms Armageddon.zip
```

Un fichier impossible à identifier reste ici :

```text
roms/_a_trier/
```

L'importeur affiche toujours son diagnostic et ne prétend pas connaître un système lorsqu'il n'est pas suffisamment certain.

### 5. Ouvrir la borne

```text
http://localhost:6767
```

ou depuis une autre machine du LAN :

```text
http://IP_DU_PC:6767
```

## ⏹️ Commandes simples

```bash
./gamebox start       # démarrer
./gamebox stop        # arrêter
./gamebox restart     # redémarrer
./gamebox status      # voir l'état
./gamebox logs        # voir les logs
./gamebox import      # analyser et classer les ROMs
```

## 📁 Organisation

```text
game-box/
├── app/                  # interface GameBox
├── importer/             # importeur Docker
├── nginx/                # serveur web + optimisation
├── roms/                 # bibliothèque locale (non versionnée)
│   ├── arcade/
│   ├── nes/
│   ├── snes/
│   ├── gb/
│   ├── gbc/
│   ├── gba/
│   ├── n64/
│   ├── genesis/
│   └── _a_trier/
├── docker-compose.yml
├── Dockerfile
├── .env
└── gamebox
```

## 🕹️ Systèmes

Le profil initial couvre notamment NES, SNES, Game Boy, Game Boy Color, Game Boy Advance, Nintendo 64, Mega Drive/Genesis et Arcade. EmulatorJS supporte également de nombreux autres systèmes ; ils pourront être ajoutés progressivement au classificateur. citeturn4search0

## 🎮 Multiplayer

EmulatorJS permet de configurer les contrôles pour jusqu'à 4 joueurs. Pour une borne locale, plusieurs manettes USB/Bluetooth sont préférables à plusieurs joueurs partageant un clavier. citeturn2search9

Le netplay Internet n'est pas activé dans le profil de base.

## ⚠️ ROMs et BIOS

Le dépôt ne contient aucune ROM commerciale ni BIOS. Utilise uniquement les fichiers que tu as le droit d'utiliser.

## 📴 Fonctionnement hors ligne

Une fois l'image GameBox construite, les composants EmulatorJS sont servis localement. Aucun téléchargement de core n'est nécessaire pendant une partie.

Pour faire une installation complètement hors ligne sur une autre machine, transfère le dépôt et les images Docker déjà construites.
