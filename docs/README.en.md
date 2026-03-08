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
  <strong>Partial interface demonstration</strong>
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

WE Workshop Manager is a Python/PyQt6 desktop application that allows you to easily download, install, and manage wallpapers from Steam Workshop for Wallpaper Engine **without needing to run the Steam client**.

### <strong>Since version 1.3.7, Workshop pages load even faster than in the browser with the new Preload Next Page (BETA) feature!</strong>

### 🔑 Key Features:

- 🌐 Browse Steam Workshop and download wallpapers **with one click**
- 🗂️ Manage installed wallpapers (apply, remove, extract .pkg files, etc.)
- 📊 Download wallpapers by list of IDs and/or URLs
- 🎯 Track download/extraction status of wallpapers
- 🌍 Multilingual support
- ⚜️ Themes
- 🔰 Many other features

> [!NOTE]  
> - Wallpapers are downloaded to the default WE folder, **similar to a regular installation**  
> - The first login may take a while, please wait while Cookies are being created  
> - Workshop download speed depends on your internet connection speed, as well as Steam server availability (If it takes too long to download - log in again or click the Refresh button)

> [!WARNING]  
> - The app uses **public accounts** to download from the workshop  
> - The app **does not modify** the original Wallpaper Engine or Steam client  
> - The author **does not support** using this software for monetary gain, use it only as an alternative with additional functionality or if you cannot purchase a licensed version due to regional restrictions :)  

> [!WARNING]  
> If ever the app refuses to show "specific" content in the workshop, it means the system account hasn't logged in for some reason. You need to log into any steam account (without steam guard and with the content settings you need) in the app settings.  
> Similarly with downloading, if wallpapers don't load - try selecting another account from the list.

---

## 🚀 Installation

### 📦 Option 1: Packaged PyInstaller version

Download the latest version from the **[Releases](https://github.com/psyattack/we-workshop-manager/releases)** section  
> All dependencies are already in the archive, just extract the archive to a convenient location and run `WE Workshop Manager.exe`

---

### 💻 Option 2: Running from source code

#### 0. Initial setup

Install Python version 3.10 or higher from the [official website](https://www.python.org/downloads) if you haven't already  
The app was tested on Python 3.14.2

#### 1. Clone the repository

```bash
git clone https://github.com/psyattack/we-workshop-manager.git
cd we-workshop-manager
```

#### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

#### 3. Download required components

| Component | Where to place |
|-------------|----------------|
| [DepotDownloaderMod](https://github.com/SteamAutoCracks/DepotDownloaderMod/releases) | `Plugins/DepotDownloaderMod/` |
| [RePKG](https://github.com/notscuffed/repkg/releases) | `Plugins/RePKG/` |
| [.NET 9 Desktop Runtime](https://dotnet.microsoft.com/en-us/download/dotnet/9.0/runtime) | Install globally |

#### 4. Run the application

```bash
python app.py
```

---

## 📁 Project Structure

```
we-workshop-manager/
├── core/                  # Core logic
├── ui/                    # Interface
├── localization/          # Localization files
├── resources/             # Resources
├── utils/                 # Utility scripts
├── Plugins/               # DepotDownloaderMod and RePKG utilities (download separately)
├── Packages/              # .NET installer (install separately)
├── app.py                 # Entry point
└── requirements.txt       # Python dependencies
```

---

## 🙏 Acknowledgments

This project uses the following open resources and tools:

- **[DepotDownloaderMod](https://github.com/SteamAutoCracks/DepotDownloaderMod)** — modified workshop downloader
- **[RePKG](https://github.com/notscuffed/repkg)** — .pkg file unpacker tool
- **[WallpaperEngineWorkshopDownloader](https://github.com/SteamAutoCracks/WallpaperEngineWorkshopDownloader)** — for providing accounts to download from workshop
- **[icons8](https://icons8.com)** — free icons for the interface

---

## 📜 License

This project is licensed under the **[MIT](LICENSE)** license.

---

## 👁️‍🗨️ Known Issues

- [ ] Search partially differs from the website version
- [ ] Incorrect window state return after minimizing

---

## 📋 TODO & Support

- [x] Themes
- [x] Login via personal Steam account (For use with Steam failed 50 and similar)
- [ ] Autostart
- [ ] Tray + silent mode
- [ ] Original WE functions (Preset editor, creating playlists, profiles, etc.)
- [ ] Automatic updates
- [ ] Interface optimization for different screen sizes and formats

> If you have any problems or suggestions for improvement — create an [Issue](https://github.com/psyattack/we-workshop-manager/issues) in the repository.

---
