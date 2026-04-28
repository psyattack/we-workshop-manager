<div align="center">
  <img src="src/assets/icon.svg" alt="WEave Logo" width="128" height="128">
  
  # WEave
  
  > Modern desktop application for browsing, downloading, and managing Steam Workshop wallpapers for Wallpaper Engine
  
  [Русская версия](README.ru.md)
</div>

## Overview

WEave is a powerful Wallpaper Engine Workshop Manager built with Tauri 2 and React. It provides a seamless experience for discovering, downloading, and managing thousands of wallpapers from the Steam Workshop without opening Steam or a web browser.

## Features

### Workshop Browser
- Browse Steam Workshop wallpapers
- Search by keyword, sort by trending/popular/recent
- Filter by category, type, age rating, resolution, tags
- Tristate filtering (include/exclude/idle)
- Preview images with lazy loading
- View item details, ratings, descriptions, and author info
- Collections and related collections support
- Page preloading for faster navigation

### Download Management
- Multi-threaded download system using DepotDownloaderMod
- Multiple Steam account support (6 built-in + custom accounts)
- Real-time progress tracking with cancellation
- Batch download from IDs/URLs
- Queue management
- Auto-apply downloaded wallpapers (optional)

### Installed Wallpapers
- View all installed wallpapers from Wallpaper Engine
- Local filtering and sorting (date, title, size, type)
- Tag-based filtering with tristate support
- Apply wallpapers to specific monitors
- Delete wallpapers with active wallpaper detection
- Open wallpaper folders in Explorer
- Extract .pkg files

### Wallpaper Engine Integration
- Auto-detect Wallpaper Engine installation
- Apply wallpapers to monitors
- Launch Wallpaper Engine
- Read current wallpaper configuration
- Detect active wallpapers across all monitors

### Collections & Authors
- Browse Steam Workshop collections
- View collection contents and metadata
- Author profiles with items and collections
- Related collections discovery

### Customization
- 5 built-in themes (Dark, Light, Nord, Monokai, Solarized)
- 10 accent colors
- Multi-language support (English, Russian)

### Additional Features
- Steam authentication with cookie persistence
- Encrypted account storage (PBKDF2 + AES-256-GCM)
- Metadata caching for offline access
- Auto-update checker with GitHub releases
- Task management with history
- Image caching system
- Single instance enforcement

## Tech Stack

### Frontend
- **React 18** with TypeScript
- **Tauri 2** - Desktop framework
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **Framer Motion** - Animations
- **Radix UI** - Accessible components
- **Zustand** - State management
- **i18next** - Internationalization
- **Lucide React** - Icons

### Backend
- **Rust** - Tauri backend
- **Tokio** - Async runtime
- **Reqwest** - HTTP client
- **Scraper** - HTML parsing
- **AES-GCM + PBKDF2** - Encryption
- **Serde** - Serialization

## Platform Support

**Windows Only** - This application is designed exclusively for Windows 10/11 as it requires:
- Wallpaper Engine
- Windows-specific executables
- Windows file system integration

Linux and macOS are not supported.

## Installation

### For End Users

#### Prerequisites
- [.NET 8 Runtime](https://dotnet.microsoft.com/download/dotnet/8.0) or [.NET 9 Runtime](https://dotnet.microsoft.com/download/dotnet/9.0)
- Wallpaper Engine

#### Installation Steps

1. Install .NET 8 or .NET 9 Runtime if not already installed
2. Download the latest release from [GitHub Releases](https://github.com/psyattack/weave-tauri/releases)
3. Extract the archive (includes WEave executable, DepotDownloaderMod, and RePKG)
4. Run `weave.exe`

### For Developers

#### Prerequisites
- [Node.js](https://nodejs.org/) (v18 or higher)
- [Rust](https://www.rust-lang.org/) (v1.77 or higher)
- [.NET 8 Runtime](https://dotnet.microsoft.com/download/dotnet/8.0) or [.NET 9 Runtime](https://dotnet.microsoft.com/download/dotnet/9.0)
- Wallpaper Engine

#### Development Setup

1. Clone the repository:
```bash
git clone https://github.com/psyattack/weave-tauri.git
cd weave-tauri
```

2. Download required tools:
   - [DepotDownloaderMod](https://github.com/mmvanheusden/DepotDownloaderMod/releases) - Place in `plugins/` directory
   - [RePKG](https://github.com/notscuffed/repkg/releases) - Place in `plugins/` directory

3. Install dependencies:
```bash
npm install
```

4. Run in development mode:
```bash
npm run tauri dev
```

#### Building

Build the application:
```bash
npm run tauri build
```

The compiled application will be in `src-tauri/target/release/`.

## Usage

1. Launch WEave
2. Configure Wallpaper Engine directory in Settings (auto-detected by default)
3. Select a Steam account for downloads in Settings
4. Browse Workshop tab to discover wallpapers
5. Click Install to download and extract wallpapers
6. View installed wallpapers in the Installed tab
7. Apply wallpapers to your monitors

## Configuration

Configuration is stored in:  
`%LOCALAPPDATA%\com.weave.app\`  

## Project Structure

```
weave-tauri/
├── src/                     # React frontend
│   ├── components/          # React components
│   │   ├── common/          # Reusable components
│   │   ├── dialogs/         # Modal dialogs
│   │   ├── drawers/         # Side panels
│   │   └── workshop/        # Workshop-specific components
│   ├── views/               # Main view components
│   ├── stores/              # Zustand state stores
│   ├── lib/                 # Utilities and helpers
│   ├── locales/             # Frontend translations
│   └── styles/              # Global styles
└── src-tauri/               # Rust backend
    ├── src/
    │   ├── commands/        # Tauri commands
    │   ├── workshop/        # Workshop parser
    │   ├── wallpaper/       # Wallpaper Engine integration
    │   ├── download/        # Download manager
    │   ├── config/          # Configuration management
    │   └── utils/           # Rust utilities
    └── locales/             # Backend translations
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.

## Credits

- **Built with**: [Tauri](https://tauri.app/), [React](https://react.dev/), [Rust](https://www.rust-lang.org/)
- **Icons**: [Lucide](https://lucide.dev/)
- **UI Components**: [Radix UI](https://www.radix-ui.com/)
- **Download Tool**: [DepotDownloaderMod](https://gitlab.com/steamautocracks/DepotDownloaderMod)
- **Package Extractor**: [RePKG](https://github.com/notscuffed/repkg)

## Disclaimer

This application is not affiliated with or endorsed by Valve Corporation or Wallpaper Engine. Steam and Wallpaper Engine are trademarks of their respective owners.

## Support

For issues, questions, or feature requests, please open an issue on [GitHub](https://github.com/psyattack/weave-tauri/issues).

---
