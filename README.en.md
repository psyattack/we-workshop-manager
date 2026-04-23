<h1 align="center">
  <img src="public/icon_128.png" alt="WEave icon" width="100" height="100"><br>
  WEave
  <p align="center">
    <a href="LICENSE">
      <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT">
    </a>
    <a href="#installation">
      <img src="https://img.shields.io/badge/platform-Windows_10%2F11-0078D6.svg" alt="Platform: Windows">
    </a>
    <a href="#installation">
      <img src="https://img.shields.io/badge/python-3.10%2B-3776AB.svg" alt="Python 3.10+">
    </a>
    <br>
    <a href="README.md">
      <img src="https://img.shields.io/badge/Русский-ru-white.svg" alt="Русский">
    </a>
    <a href="README.en.md">
      <img src="https://img.shields.io/badge/English-en-white.svg" alt="English">
    </a>
  </p>
</h1>

<p align="center">
  <img src="public/screen_main.png" alt="Main interface demonstration" width="700">
</p>

<p align="center">
  <strong>Main interface demonstration</strong>
</p>

---

WEave (formerly WE Workshop Manager) is a Python/PyQt6 desktop application that allows you to easily download, install, and manage wallpapers from Steam Workshop for Wallpaper Engine **without needing to run the Steam client**.

### <strong>In development 3.0 - migration to Tauri (React) + Rust or PyWebView</strong>

### 🔑 Key Features:

- 🌐 Browse Steam Workshop and download wallpapers **with one click**
- 🗂️ Manage installed wallpapers (apply, remove, extract .pkg files, etc.)
- 📊 Download wallpapers by list of IDs and/or URLs
- 🎯 Track download/extraction status of wallpapers
- ⚜️ Themes + Full customization of the background of the main UI elements
- 🔧 Pages load faster than in the browser
- 🌍 Multilingual support
- 🔰 Many other features

---

## Related Project

**[WE Installer Extension](https://github.com/psyattack/we-installer-extension)** — a browser extension that adds a quick install button directly on Steam Workshop pages.

---

> [!NOTE]  
> - Wallpapers are downloaded to the default WE folder, **similar to a regular installation**  
> - The first login may take a while, please wait while the system account is logging in
> - Workshop download speed depends on your internet connection speed, as well as Steam server availability
> - If the app doesn't show "specific" content in Workshop, it means the system account hasn't logged in for some reason. You need to log into any Steam account (without Steam Guard and with the content settings you need) in the app settings (General).
> - If wallpapers don't load - try selecting another account from the list in settings (Account).

> [!WARNING]  
> - The app uses **public accounts** to download from the workshop  
> - The app **does not modify** the original Wallpaper Engine or Steam client  

---

## 🚀 Installation

> [!IMPORTANT]
> **To run from source (Option 2):**
> - Install [Python 3.14+](https://www.python.org/downloads)
> - Install [.NET 8](https://dotnet.microsoft.com/download/dotnet/8.0/runtime) Desktop Runtime
>
> **For packaged version (Option 1):**
> - Only the .NET 8 Runtime mentioned above

### 📦 Option 1: Packaged PyInstaller version

Download the latest version from the **[Releases](https://github.com/psyattack/WEave/releases)** section  
> All dependencies are already built in, just unzip the archive to a convenient location and run `WEave.exe`

---

### 💻 Option 2: Running from source code

#### 1. Clone the repository

```bash
git clone https://github.com/psyattack/WEave.git
cd WEave
```

#### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

#### 3. Download required components

| Component | Where to place |
|-------------|----------------|
| [DepotDownloader](https://github.com/SteamRE/DepotDownloader/releases) | `plugins/DepotDownloader/` |
| [RePKG](https://github.com/notscuffed/repkg/releases) | `plugins/RePKG/` |

#### 4. Run the application

```bash
python main.py
```

---

## 📁 Project Structure

```
WEave/
├── bootstrap/              # Application initialization
├── domain/                 # Models and data structures
├── services/               # Application services
├── infrastructure/         # Integrations and external logic
├── ui/                     # Interface
├── shared/                 # Common utilities
├── localization/           # Translations
├── plugins/                # External tools (downloaded separately)
├── main.py                 # Entry point
└── requirements.txt        # Python dependencies
```

---

## 🙏 Acknowledgments

This project uses the following open resources and tools:

- **[DepotDownloader](https://github.com/SteamRE/DepotDownloader/releases)** — modified workshop downloader
- **[RePKG](https://github.com/notscuffed/repkg)** — .pkg file unpacker tool
- **[WallpaperEngineWorkshopDownloader](https://gitlab.com/steamautocracks/wallpaperengineworkshopdownloader)** — for providing accounts to download from workshop
- **[icons8](https://icons8.com)** — free icons for the interface

---

## 📜 License

This project is licensed under the **[MIT](LICENSE)** license.

---

## 👁️‍🗨️ Known Issues

- [x] <strike>Incorrect window state return after pre-minimizing</strike>
- [x] <strike>White dialogs when clearing filters</strike>
- [x] <strike>PyInstaller --onefile breaks restart, if building from source build in --onedir (~500mb)</strike>

---

## 📋 TODO & Support

- [x] <strike>Themes</strike>
- [x] <strike>Login via personal Steam account (For use with Steam failed 50 and similar)</strike>
- [ ] Autostart
- [ ] Tray + silent mode
- [ ] Original WE functions (Preset editor, creating playlists, profiles, etc.)
- [ ] Automatic updates
- [x] <strike>Interface optimization for different screen sizes and formats + window resize capability</strike>

> If you have any problems or suggestions for improvement — create an [Issue](https://github.com/psyattack/WEave/issues) in the repository.

---
