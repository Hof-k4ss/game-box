# 🎮 GameBox

GameBox transforme un PC Ubuntu **qui reste un PC de travail** en borne rétro accessible depuis un navigateur.

Le projet est volontairement isolé dans Docker : rien n'installe d'émulateur directement dans Ubuntu.

## Ce que fait GameBox

- interface web légère pensée pour clavier et manettes ;
- émulation dans le navigateur avec EmulatorJS ;
- cores EmulatorJS stockés localement dans l'image Docker ;
- ROMs conservées sur le disque de l'hôte ;
- importeur qui inspecte le contenu des archives avant de choisir la console ;
- jeux inconnus envoyés dans `roms/_a_trier/` au lieu d'être mal classés ;
- cache navigateur EmulatorJS pour accélérer les lancements suivants ;
- threads WebAssembly activés lorsque le navigateur les autorise ;
- Nginx sert directement les ROMs et les fichiers statiques.

## ⚡ Pourquoi cette architecture ?

Une fois le jeu chargé, le clavier/manette et le rendu restent côté navigateur. Le serveur ne fait pas transiter chaque touche pendant la partie.

GameBox ajoute plusieurs optimisations :

- fichiers statiques servis directement par Nginx ;
- ROMs servies directement avec support des requêtes HTTP Range ;
- cache EmulatorJS jusqu'à 4 Go dans le navigateur ;
- cores stockés localement : pas de téléchargement CDN pendant le jeu ;
- SharedArrayBuffer/threads activés avec les en-têtes nécessaires ;
- interface volontairement légère, sans gros framework.

Pour une latence absolument minimale, un émulateur natif reste toutefois plus direct qu'un émulateur WebAssembly dans un navigateur. GameBox privilégie ici le compromis **zéro installation sur Ubuntu + interface web + isolation Docker**.

## 🚀 Installation

### 1. Télécharger le projet

```bash
git clone https://github.com/Hof-k4ss/game-box.git
cd game-box
bash install.sh
```

Le script vérifie Docker, crée les dossiers nécessaires et prépare `.env`.

### 2. Choisir le dossier source des ROMs

Ouvre `.env` et modifie cette ligne :

```dotenv
ROM_SOURCE_DIR=/home/USER/downloads/ROMs
```

Remplace `USER` par ton nom d'utilisateur Linux, ou indique n'importe quel autre dossier contenant tes ROMs.

### 3. Démarrer GameBox

```bash
./gamebox start
```

La première construction télécharge les composants EmulatorJS dans l'image Docker. **Après cette construction, les cores sont servis localement par GameBox.**

### 4. Importer les jeux

```bash
./gamebox import
```

L'importeur inspecte les archives. Pour un ZIP ou un 7z, il regarde les fichiers qu'il contient et pas seulement le nom de l'archive.

Il utilise :

1. les extensions des fichiers contenus dans l'archive ;
2. certaines signatures internes ;
3. des règles spécifiques pour les archives arcade ;
4. une zone `roms/_a_trier/` lorsqu'il n'est pas suffisamment certain.

Avant de déplacer quoi que ce soit, tu peux faire une simulation :

```bash
./gamebox import-dry-run
```

### 5. Jouer

Depuis le PC :

```text
http://localhost:6767
```

Depuis une autre machine du réseau local :

```text
http://IP_DU_PC:6767
```

## ⏹️ Commandes simples

```bash
./gamebox start          # démarrer
./gamebox stop           # arrêter
./gamebox restart        # redémarrer
./gamebox status         # voir l'état
./gamebox logs           # voir les logs
./gamebox import         # classer les ROMs
./gamebox import-dry-run # simuler le classement
```

> Si le shell refuse `./gamebox` après un téléchargement ou un clone, lance une fois `chmod +x gamebox`.

## 📁 Organisation

```text
game-box/
├── app/                  # interface web
├── api/                  # API très légère de bibliothèque
├── importer/             # analyseur d'archives
├── nginx/                # serveur web optimisé
├── roms/                 # bibliothèque locale, non versionnée
│   ├── arcade/
│   ├── nes/
│   ├── snes/
│   ├── gb/
│   ├── gbc/
│   ├── gba/
│   ├── n64/
│   ├── genesis/
│   └── _a_trier/
├── bios/                 # BIOS locaux, non versionnés
├── docker-compose.yml
├── Dockerfile
├── .env
└── gamebox
```

## 🕹️ Systèmes

Le profil initial couvre notamment NES, SNES, Game Boy, Game Boy Color, Game Boy Advance, Nintendo 64, Mega Drive/Genesis et Arcade. D'autres systèmes pourront être ajoutés au classificateur au fur et à mesure.

## 🎮 Multiplayer

EmulatorJS permet de configurer les contrôles pour plusieurs joueurs. Pour une vraie borne, plusieurs manettes USB/Bluetooth sont préférables à plusieurs joueurs partageant un clavier.

Le netplay Internet n'est pas activé dans le profil de base.

## ⚠️ ROMs et BIOS

Le dépôt ne contient aucune ROM commerciale ni BIOS. Utilise uniquement les fichiers que tu as le droit d'utiliser.

## 📴 Fonctionnement hors ligne

Une fois l'image GameBox construite, les composants EmulatorJS sont servis localement. Aucun téléchargement de core n'est nécessaire pendant une partie.

Pour déplacer GameBox sur une autre machine sans Internet, il faudra transférer le dépôt ainsi que les images Docker déjà construites.
