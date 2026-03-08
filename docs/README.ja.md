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
  <strong>インターフェースの部分的なデモ</strong>
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

WE Workshop Managerは、Python/PyQt6制成的桌面アプリケーションで、Steamクライアントを実行せずにWallpaper EngineのSteam Workshopから壁紙を簡単にダウンロード、インストール、管理できます。

### <strong>バージョン1.3.7以降、Workshopページは新しいPreload Next Page（BETA）機能でブラウザよりも高速に読み込まれます！</strong>

### 🔑主な機能:

- 🌐Steam Workshopを閲覧し、**ワンクリック**で壁纸をダウンロード
- 🗂️インストール済み壁纸を管理（適用、削除、.pkgファイルの抽出など）
- 📊IDリストやURLから壁纸をダウンロード
- 🎯ダウンロード/抽出ステータスを追跡
- 🌍多言語サポート
- ⚜️テーマ
- 🔰その他の多くの機能

> [!NOTE]  
> - 壁纸は通常のインストールと同様にデフォルトのWEフォルダーにダウンロードされます  
> - 最初のログインには時間がかかることがあります。Cookieの作成をお待ちください  
> - Workshopのダウンロード速度はインターネット接続速度とSteamサーバーの可用性に依存します（ダウンロードに時間がかかる場合は、再ログインするか更新ボタンをクリックしてください）

> [!WARNING]  
> - アプリンはWorkshopからダウンロードするために**パブリックアカウント**を使用しています  
> - アプリンは元のWallpaper EngineクライアントやSteamクライアントを**変更しません**  
> - 著者はこのソフトウェアを経済的利益のために使用することを**支持していません**。追加機能としての代替手段、または地域制限によりライセンス版を購入できない場合のみ使用してください :)  

> [!WARNING]  
> アプリンがWorkshopで特定のコンテンツを表示することを拒否した場合、それは何らかの理由でシステムアカウントがログインしていないことを意味します。アプリンの設定で、（Steam Guardがなく、必要なコンテンツ設定を持つ）任意のSteamアカウントにログインする必要があります。  
> 同様に、ダウンロードで壁纸が読み込まれない場合は、リストから別のアカウントを選択してみてください。

---

## 🚀インストール

### 📦オプション1: PyInstallerパッケージバージョン

**[Releases](https://github.com/psyattack/we-workshop-manager/releases)** セクションから最新バージョンをダウンロードしてください  
> すべての依存関係はすでにアーカイブに含まれています。アーカイブ удобное местоして `WE Workshop Manager.exe` を実行するだけです

---

### 💻オプション2: ソースコードからの実行

#### 0. 初期設定

まだの場合は、[公式ウェブサイト](https://www.python.org/downloads)からPython 3.10以降をインストールしてください  
Python 3.14.2でテストされています

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
| [DepotDownloaderMod](https://github.com/SteamAutoCracks/DepotDownloaderMod/releases) | `Plugins/DepotDownloaderMod/` |
| [RePKG](https://github.com/notscuffed/repkg/releases) | `Plugins/RePKG/` |
| [.NET 9 Desktop Runtime](https://dotnet.microsoft.com/en-us/download/dotnet/9.0/runtime) | グローバルにインストール |

#### 4. アプリケーションを実行

```bash
python app.py
```

---

## 📁プロジェクト構造

```
we-workshop-manager/
├── core/                  # コアロジック
├── ui/                    # インターフェース
├── localization/          # ローカライゼーションファイル
├── resources/             # リソース
├── utils/                 # ユーティリティ
├── Plugins/               # DepotDownloaderModとRePKGユーティリティ（別途ダウンロード）
├── Packages/              # .NETインスレーター（別途インストール）
├── app.py                 # エントリポイント
└── requirements.txt       # Python依存関係
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

- [ ] 検索がウェブサイト版と一部異なる
- [ ] 最小化後のウィンドウ状態の不適切な復帰

---

## 📋 TODOとサポート

- [x] テーマ
- [x] 個人Steamアカウントでのログイン（Steam failed 50などの場合に使用）
- [ ] 自動起動
- [ ] トレイ + シレットモード
- [ ] 元のWE機能（プリセットエディター、プレイリスト作成、プロファイルなど）
- [ ] 自動更新
- [ ] 異なる画面サイズと形式への対応最適化

> 問題がある場合や改善提案がある場合は、リポジトリに[Issue](https://github.com/psyattack/we-workshop-manager/issues)を作成してください。

---
