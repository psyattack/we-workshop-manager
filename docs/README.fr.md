# WE Workshop Manager

<p align="center">
  <a href="README.md">🇷🇺 Русский</a> |
  <a href="README.en.md">🇬🇧 English</a> |
  <a href="README.de.md">🇩🇪 Deutsch</a> |
  <a href="README.es.md">🇪🇸 Español</a> |
  <a href="README.fr.md">🇫🇷 Français</a> |
  <a href="README.ja.md">🇯🇵 日本語</a> |
  <a href="README.pt.md">🇧🇷 Português</a> |
  <a href="README.zh.md">🇨🇳 中文</a>
</p>

<p align="center">
  <img src="../screenshots/screen_main.png" alt="WE Workshop Manager" width="700">
</p>

<p align="center">
  <strong>Démonstration partielle de l'interface</strong>
</p>

<p align="center">
  <a href="../LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT">
  </a>
  <a href="#installation">
    <img src="https://img.shields.io/badge/platform-Windows_10%2F11-0078D6.svg" alt="Platform: Windows">
  </a>
  <a href="#installation">
    <img src="https://img.shields.io/badge/python-3.10%2B-3776AB.svg" alt="Python 3.10+">
  </a>
</p>

---

WE Workshop Manager est une application de bureau Python/PyQt6 qui vous permet de télécharger, installer et gérer facilement des wallpapers depuis le Steam Workshop pour Wallpaper Engine **sans avoir besoin d'exécuter le client Steam**.

### <strong>Depuis la version 1.3.7, les pages du Workshop se chargent encore plus rapidement que dans le navigateur avec la nouvelle fonction Preload Next Page (BETA) !</strong>

### 🔑 Fonctionnalités principales:

- 🌐 Parcourir le Steam Workshop et télécharger des wallpapers **en un clic**
- 🗂️ Gérer les wallpapers installés (appliquer, supprimer, extraire les fichiers .pkg, etc.)
- 📊 Télécharger des wallpapers par liste d'IDs et/ou URLs
- 🎯 Suivre le statut de téléchargement/extraction des wallpapers
- 🌍 Multilingue
- ⚜️ Thèmes
- 🔰 De nombreuses autres fonctionnalités

> [!NOTE]  
> - Les wallpapers sont téléchargés dans le dossier par défaut de WE, **comme une installation normale**  
> - La première connexion peut prendre un moment, veuillez patienter pendant la création des Cookies  
> - La vitesse de téléchargement du Workshop dépend de la vitesse de votre connexion Internet, ainsi que de la disponibilité des serveurs Steam (Si le téléchargement prend trop de temps - reconnectez-vous ou cliquez sur le bouton Actualiser)

> [!WARNING]  
> - L'application utilise des **comptes publics** pour télécharger depuis le workshop  
> - L'application **ne modifie pas** le client Wallpaper Engine ou Steam d'origine  
> - L'auteur **ne soutient pas** l'utilisation de ce logiciel pour des gains financiers, utilisez-le uniquement comme alternative avec des fonctionnalités supplémentaires ou si vous ne pouvez pas acheter une version légal en raison de restrictions régionales :)  

> [!WARNING]  
> Si jamais l'application refuse d'afficher un contenu "spécifique" dans le workshop, cela signifie que le compte système ne s'est pas connecté pour une raison ou une autre. Vous devez vous connecter sur n'importe quel compte steam (sans steam guard et avec les paramètres de contenu dont vous avez besoin) dans les paramètres de l'application.  
> De même pour le téléchargement, si les wallpapers ne se chargent pas - essayez de sélectionner un autre compte dans la liste.

---

## 🚀 Installation

### 📦 Option 1: Version empaquetée PyInstaller

Téléchargez la dernière version depuis la section **[Releases](https://github.com/psyattack/we-workshop-manager/releases)**  
> Toutes les dépendances sont déjà dans l'archive, extrayez simplement l'archive à un endroit pratique et exécutez `WE Workshop Manager.exe`

---

### 💻 Option 2: Exécution à partir du code source

#### 0. Configuration initiale

Installez Python version 3.10 ou supérieure depuis le [site officiel](https://www.python.org/downloads) si ce n'est pas encore fait  
L'application a été testée sur Python 3.14.2

#### 1. Cloner le dépôt

```bash
git clone https://github.com/psyattack/we-workshop-manager.git
cd we-workshop-manager
```

#### 2. Installer les dépendances Python

```bash
pip install -r requirements.txt
```

#### 3. Télécharger les composants requis

| Composant | Où placer |
|-------------|----------------|
| [DepotDownloaderMod](https://github.com/SteamAutoCracks/DepotDownloaderMod/releases) | `Plugins/DepotDownloaderMod/` |
| [RePKG](https://github.com/notscuffed/repkg/releases) | `Plugins/RePKG/` |
| [.NET 9 Desktop Runtime](https://dotnet.microsoft.com/en-us/download/dotnet/9.0/runtime) | Installer globalement |

#### 4. Lancer l'application

```bash
python app.py
```

---

## 📁 Structure du projet

```
we-workshop-manager/
├── core/                  # Logique principale
├── ui/                    # Interface
├── localization/          # Fichiers de localisation
├── resources/             # Ressources
├── utils/                 # Utilitaires
├── Plugins/               # Utilitaires DepotDownloaderMod et RePKG (télécharger séparément)
├── Packages/              # Installateur .NET (installer séparément)
├── app.py                 # Point d'entrée
└── requirements.txt       # Dépendances Python
```

---

## 🙏 Remerciements

Ce projet utilise les ressources et outils ouverts suivants:

- **[DepotDownloaderMod](https://github.com/SteamAutoCracks/DepotDownloaderMod)** — téléchargeur de workshop modifié
- **[RePKG](https://github.com/notscuffed/repkg)** — outil d'extraction de fichiers .pkg
- **[WallpaperEngineWorkshopDownloader](https://github.com/SteamAutoCracks/WallpaperEngineWorkshopDownloader)** — pour avoir fourni des comptes pour télécharger depuis le workshop
- **[icons8](https://icons8.com)** — icônes gratuites pour l'interface

---

## 📜 Licence

Ce projet est sous licence **[MIT](LICENSE)**.

---

## 👁️‍🗨️ Problèmes connus

- [ ] La recherche diffère partiellement de la version du site
- [ ] Retour incorrect de l'état de la fenêtre après la réduction

---

## 📋 TODO et Support

- [x] Thèmes
- [x] Connexion via un compte Steam personnel (Pour utilisation avec Steam failed 50 et similaire)
- [ ] Démarrage automatique
- [ ] Barre d'état + mode silencieux
- [ ] Fonctions originales de WE (Éditeur de préréglages, création de playlists, profils, etc.)
- [ ] Mises à jour automatiques
- [ ] Optimisation de l'interface pour différentes tailles et formats d'écran

> Si vous avez des problèmes ou des suggestions d'amélioration — créez une [Issue](https://github.com/psyattack/we-workshop-manager/issues) dans le dépôt.

---
