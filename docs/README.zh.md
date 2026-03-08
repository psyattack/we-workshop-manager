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
  <strong>界面部分演示</strong>
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

WE Workshop Manager 是一个 Python/PyQt6 桌面应用程序，让您可以轻松地从 Wallpaper Engine 的 Steam Workshop 下载、安装和管理壁纸，**无需运行 Steam 客户端**。

### <strong>自 1.3.7 版本起，Workshop 页面通过新的预加载下一页 (BETA) 功能加载速度比浏览器更快！</strong>

### 🔑 主要功能：

- 🌐 浏览 Steam Workshop 并**一键下载**壁纸
- 🗂️ 管理已安装的壁纸（应用、删除、提取 .pkg 文件等）
- 📊 通过 ID 列表和/或 URL 下载壁纸
- 🎯 跟踪壁纸下载/提取状态
- 🌍 多语言支持
- ⚜️ 主题
- 🔰 许多其他功能

> [!NOTE]  
> - 壁纸将下载到默认的 WE 文件夹，**与常规安装相同**  
> - 首次登录可能需要一些时间，请等待 Cookie 创建完成  
> - Workshop 下载速度取决于您的网络连接速度以及 Steam 服务器的可用性（如果下载时间过长 - 请重新登录或点击刷新按钮）

> [!WARNING]  
> - 该应用使用**公共账户**从 Workshop 下载  
> - 该应用**不会修改**原始的 Wallpaper Engine 或 Steam 客户端  
> - 作者**不支持**使用此软件获取经济利益，仅将其作为具有附加功能的替代方案，或在因区域限制无法购买许可版本时使用 :)  

> [!WARNING]  
> 如果应用程序拒绝显示 Workshop 中的"特定"内容，则意味着系统账户出于某种原因未登录。您需要在应用程序设置中登录任何 steam 账户（无 steam guard 并包含您需要的内容设置）。  
> 同样，如果壁纸无法加载 - 请尝试从列表中选择另一个账户。

---

## 🚀 安装

### 📦 选项 1：PyInstaller 打包版本

从 **[Releases](https://github.com/psyattack/we-workshop-manager/releases)** 部分下载最新版本  
> 所有依赖项已在压缩包中，只需将压缩包解压到方便的位置并运行 `WE Workshop Manager.exe`

---

### 💻 选项 2：从源代码运行

#### 0. 初始设置

如果尚未安装，请从[官方网站](https://www.python.org/downloads)安装 Python 3.10 或更高版本  
该应用已在 Python 3.14.2 上测试

#### 1. 克隆仓库

```bash
git clone https://github.com/psyattack/we-workshop-manager.git
cd we-workshop-manager
```

#### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

#### 3. 下载所需组件

| 组件 | 放置位置 |
|-------------|----------------|
| [DepotDownloaderMod](https://github.com/SteamAutoCracks/DepotDownloaderMod/releases) | `Plugins/DepotDownloaderMod/` |
| [RePKG](https://github.com/notscuffed/repkg/releases) | `Plugins/RePKG/` |
| [.NET 9 Desktop Runtime](https://dotnet.microsoft.com/en-us/download/dotnet/9.0/runtime) | 全局安装 |

#### 4. 运行应用程序

```bash
python app.py
```

---

## 📁 项目结构

```
we-workshop-manager/
├── core/                  # 核心逻辑
├── ui/                    # 界面
├── localization/          # 本地化文件
├── resources/             # 资源
├── utils/                 # 实用工具
├── Plugins/               # DepotDownloaderMod 和 RePKG 实用工具（单独下载）
├── Packages/              # .NET 安装程序（单独安装）
├── app.py                 # 入口点
└── requirements.txt       # Python 依赖
```

---

## 🙏 致谢

本项目使用以下开源资源和工具：

- **[DepotDownloaderMod](https://github.com/SteamAutoCracks/DepotDownloaderMod)** — 修改后的 Workshop 下载器
- **[RePKG](https://github.com/notscuffed/repkg)** — .pkg 文件解包工具
- **[WallpaperEngineWorkshopDownloader](https://github.com/SteamAutoCracks/WallpaperEngineWorkshopDownloader)** — 提供从 Workshop 下载的账户
- **[icons8](https://icons8.com)** — 界面免费图标

---

## 📜 许可证

本项目基于 **[MIT](LICENSE)** 许可证发布。

---

## 👁️‍🗨️ 已知问题

- [ ] 搜索与网站版本部分不同
- [ ] 最小化后窗口状态返回不正确

---

## 📋 TODO 与支持

- [x] 主题
- [x] 通过个人 Steam 账户登录（用于 Steam failed 50 等情况）
- [ ] 自动启动
- [ ] 托盘 + 静默模式
- [ ] 原始 WE 功能（预设编辑器、创建播放列表、个人资料等）
- [ ] 自动更新
- [ ] 针对不同屏幕尺寸和格式的界面优化

> 如果您遇到问题或有改进建议 — 请在仓库中创建 [Issue](https://github.com/psyattack/we-workshop-manager/issues)。

---
