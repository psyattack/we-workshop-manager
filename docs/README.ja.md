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
  <img src="../screenshots/screen_main.png" alt="WEave (元 WE Workshop Manager)" width="700">
</p>

<p align="center">
  <strong>メインインターフェースのデモ</strong>
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

WEave (元 WE Workshop Manager)は、Steamクライアントを実行せずにWallpaper EngineのSteam Workshopから壁紙を簡単にダウンロード、インストール、管理できるPython/PyQt6制成的桌面アプリケーションです。

### <strong>開発中 2.0 - Tauri (React) + Rust または PyWebView への移行</strong>

### 🔑主な機能:

- 🌐Steam Workshopを閲覧し、**ワンクリック**で壁紙をダウンロード
- 🗂️インストール済み壁紙を管理（適用、削除、.pkgファイルの抽出など）
- 📊IDリストやURLから壁紙をダウンロード
- 🎯ダウンロード/抽出ステータスを追跡
- 🔧ページの高速読み込み
- 🌍多言語サポート
- ⚜️テーマ
- 🔰その他の多くの機能

> [!NOTE]  
> - 壁紙は通常のインストールと同様にデフォルトのWEフォルダーにダウンロードされます  
> - 最初のログインには時間がかかることがあります。システムアカウントへのログインをお待ちください  
> - Workshopのダウンロード速度はインターネット接続速度とSteamサーバーの可用性に依存します
> - アプリがWorkshopで特定のコンテンツを表示しない場合、システムアカウントがログインしていない可能性があります。アプリの設定（一般）で、（Steam Guardがなく、必要なコンテンツ設定を持つ）任意のSteamアカウントにログインする必要があります。
> - 壁纸が読み込まれない場合は、設定（アカウント）のリストから別のアカウントを選択してみてください。

> [!WARNING]  
> - アップはWorkshopからダウンロードするために**パブリックアカウント**を使用しています  
> - アップは元のWallpaper EngineクライアントやSteamクライアントを**変更しません**  

---

## 🚀インストール

> [!IMPORTANT]
> **ソースから実行する場合（オプション2）：**
> - [Python 3.10+](https://www.python.org/downloads)をインストール（Python 3.14.2でテスト済み）
> - [.NET 8](https://dotnet.microsoft.com/download/dotnet/8.0/runtime)または[.NET 9](https://dotnet.microsoft.com/download/dotnet/9.0/runtime) Desktop Runtimeをインストール
>
> **パックバージョン（オプション1）の場合：**
> - 上記の.NET Runtimeのみ

### 📦オプション1: PyInstallerパッケージバージョン

**[Releases](https://github.com/psyattack/we-workshop-manager/releases)** セクションから最新バージョンをダウンロードしてください  
> すべての依存関係はすでにアーカイブに含まれているので、アーカイブを удобное место выпрямите и `WEave.exe` を実行するだけです

---

### 💻オプション2: ソースコードからの実行

#### 1. リポジトリをクローン

```bash
git clone https://github.com/psyattack/we-workshop-manager.git
cd we-workshop-manager
```

#### 2. Python依存関係をインストール

```bash
pip install -r requirements.txt
```

#### 3. 必要なコンポーネントをダウンロード

| コンポーネント | 配置場所 |
|-------------|----------------|
| [DepotDownloaderMod](https://github.com/SteamAutoCracks/DepotDownloaderMod/releases) | `plugins/DepotDownloaderMod/` |
| [RePKG](https://github.com/notscuffed/repkg/releases) | `plugins/RePKG/` |

#### 4. アプリケーションを実行

```bash
python main.py
```

---

## 📁プロジェクト構造

```
we-workshop-manager/
├── bootstrap/              # アプリケーションの初期化
├── domain/                 # モデルとデータ構造
├── services/               # アプリケーションサービス
├── infrastructure/         # 統合と外部ロジック
├── ui/                     # インターフェース
├── shared/                 # 共通のユーティリティ
├── localization/           # 翻訳
├── plugins/                # 外部ツール（別途ダウンロード）
├── main.py                 # エントリポイント
└── requirements.txt        # Python依存関係
```

---

## 🙏謝辞

このプロジェクトでは以下のオープンツールとリソースを使用しています:

- **[DepotDownloaderMod](https://github.com/SteamAutoCracks/DepotDownloaderMod)** — 改造されたWorkshopダウンローダー
- **[RePKG](https://github.com/notscuffed/repkg)** — .pkgファイルアンパッカーツール
- **[WallpaperEngineWorkshopDownloader](https://github.com/SteamAutoCracks/WallpaperEngineWorkshopDownloader)** — Workshopからのダウンロード用アカウントの提供
- **[icons8](https://icons8.com)** — インターフェース用の無料アイコン

---

## 📜ライセンス

このプロジェクトは**[MIT](LICENSE)**ライセンスの下で公開されています。

---

## 👁️‍🗨️既知の問題

- [ ] 最小化後のウィンドウ状態の不適切な復帰
- [x] フィルターをクリアする際の白いダイアログ
- [ ] PyInstaller --onefileは再起動を壊すため、ソースからビルドする場合は--onedirでビルドしてください（~500mb）

---

## 📋 TODOとサポート

- [x] テーマ
- [x] 個人Steamアカウントでのログイン（Steam failed 50などの場合に使用）
- [ ] 自動起動
- [ ] トレイ + シレットモード
- [ ] 元のWE機能（プリセットエディター、プレイリスト作成、プロファイルなど）
- [ ] 自動更新
- [x] 異なる画面サイズと形式に合わせてインターフェースを最適化 + ウィンドウのリサイズ機能

> 問題がある場合や改善提案がある場合は、リポジトリに[Issue](https://github.com/psyattack/we-workshop-manager/issues)を作成してください。

---
