# WEave

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
  <img src="../screenshots/screen_main.png" alt="WEave (anciennement WE Workshop Manager)" width="700">
</p>

<p align="center">
  <strong>Démonstration de l'interface principale</strong>
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

WEave (anciennement WE Workshop Manager) est une application de bureau Python/PyQt6 qui vous permet de télécharger, installer et gérer facilement des wallpapers depuis le Steam Workshop pour Wallpaper Engine **sans avoir besoin d'exécuter le client Steam**.

### <strong>En développement 2.0 - migration vers Tauri (React) + Rust ou PyWebView</strong>

### 🔑 Fonctionnalités principales:

- 🌐 Parcourir le Steam Workshop et télécharger des wallpapers **en un clic**
- 🗂️ Gérer les wallpapers installés (appliquer, supprimer, extraire les fichiers .pkg, etc.)
- 📊 Télécharger des wallpapers par liste d'IDs et/ou URLs
- 🎯 Suivre le statut de téléchargement/extraction des wallpapers
- 🔧 Chargement rapide des pages
- 🌍 Multilingue
- ⚜️ Thèmes
- 🔰 De nombreuses autres fonctionnalités

> [!NOTE]  
> - Les wallpapers sont téléchargés dans le dossier par défaut de WE, **comme une installation normale**  
> - La première connexion peut prendre un moment, veuillez patienter pendant la connexion au compte système
> - La vitesse de téléchargement du Workshop dépend de la vitesse de votre connexion Internet, ainsi que de la disponibilité des serveurs Steam
> - Si l'application n'affiche pas de contenu "spécifique" dans le Workshop, cela signifie que le compte système ne s'est pas connecté pour une raison ou une autre. Vous devez vous connecter sur n'importe quel compte Steam (sans Steam Guard et avec les paramètres de contenu dont vous avez besoin) dans les paramètres de l'application (Général).
> - Si les wallpapers ne se chargent pas - essayez de sélectionner un autre compte dans la liste des paramètres (Compte).

> [!WARNING]  
> - L'application utilise des **comptes publics** pour télécharger depuis le workshop  
> - L'application **ne modifie pas** le client Wallpaper Engine ou Steam d'origine  

---

## 🚀 Installation

> [!IMPORTANT]
> **Pour exécuter à partir du code source (Option 2) :**
> - Installez [Python 3.10+](https://www.python.org/downloads) (testé sur Python 3.14.2)
> - Installez [.NET 8](https://dotnet.microsoft.com/download/dotnet/8.0/runtime) ou [.NET 9](https://dotnet.microsoft.com/download/dotnet/9.0/runtime) Desktop Runtime
>
> **Pour la version empaquetée (Option 1) :**
> - Seulement le .NET Runtime mentionné ci-dessus

### 📦 Option 1: Version empaquetée PyInstaller

Téléchargez la dernière version depuis la section **[Releases](https://github.com/psyattack/we-workshop-manager/releases)**  
> Toutes les dépendances sont déjà dans l'archive, extrayez simplement l'archive à un endroit pratique et exécutez `WEave.exe`

---

### 💻 Option 2: Exécution à partir du code source

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
| [DepotDownloaderMod](https://github.com/SteamAutoCracks/DepotDownloaderMod/releases) | `plugins/DepotDownloaderMod/` |
| [RePKG](https://github.com/notscuffed/repkg/releases) | `plugins/RePKG/` |

#### 4. Lancer l'application

```bash
python main.py
```

---

## 📁 Structure du projet

```
we-workshop-manager/
├── bootstrap/              # Initialisation de l'application
├── domain/                 # Modèles et structures de données
├── services/               # Services de l'application
├── infrastructure/         # Intégrations et logique externe
├── ui/                     # Interface
├── shared/                 # Utilitaires communs
├── localization/           # Traductions
├── plugins/                # Outils externes (télécharger séparément)
├── main.py                 # Point d'entrée
└── requirements.txt        # Dépendances Python
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

- [ ] Retour incorrect de l'état de la fenêtre après la pré-réduction
- [x] Dialogues blancs lors du nettoyage des filtres
- [ ] PyInstaller --onefile casse le redémarrage, si compilé depuis les sources, compiler en --onedir (~500mb)

---

## 📋 TODO et Support

- [x] Thèmes
- [x] Connexion via un compte Steam personnel (Pour utilisation avec Steam failed 50 et similaire)
- [ ] Démarrage automatique
- [ ] Barre d'état + mode silencieux
- [ ] Fonctions originales de WE (Éditeur de préréglages, création de playlists, profils, etc.)
- [ ] Mises à jour automatiques
- [x] Optimisation de l'interface pour différentes tailles et formats d'écran + capacité de redimensionnement de fenêtre

> Si vous avez des problèmes ou des suggestions d'amélioration — créez une [Issue](https://github.com/psyattack/we-workshop-manager/issues) dans le dépôt.

---
