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
  <img src="public/screen_main.png" alt="Демонстрация основного интерфейса" width="700">
</p>

<p align="center">
  <strong>Демонстрация основного интерфейса</strong>
</p>

---

WEave (бывший WE Workshop Manager) — это десктопное приложение на Python/PyQt6, которое позволяет легко загружать, устанавливать и управлять обоями из Steam Workshop для Wallpaper Engine **без необходимости запускать клиент Steam**.

### <strong>В разработке 3.0 - миграция на Tauri (React) + Rust или PyWebView</strong>

### 🔑 Основные возможности:

- 🌐 Просмотр мастерской WE Steam и загрузка обоев **в один клик**
- 🗂️ Управление установленными обоями (применение, удаление, извлечение .pkg файлов и прочее)
- 📊 Загрузка обоев по списку ID и\или URL
- 🎯 Отслеживание статуса загрузки\извлечения обоев
- ⚜️ Темы + Полная кастомизация бекграунда у основных элементов UI
- 🔧 Загрузка страниц быстрее чем в браузере
- 🌍 Мультиязычность
- 🔰 Множество других функций

---

## Дочерний проект

**[WE Installer Extension](https://github.com/psyattack/we-installer-extension)** — расширение для браузера, которое добавляет кнопку быстрой установки обоев прямо на страницах Steam Workshop.

---

> [!NOTE]  
> - Обои загружаются в папку по умолчанию для WE, **аналогично обычной установке**  
> - Первый вход может быть долгим, пожалуйста, подождите пока производится вход в системный аккаунт  
> - Скорось загрузки Workshop зависит от скорости вашего интернет соединения, а так же доступности серверов Steam  
> - Если приложение не показывает "определённый" контент в Workshop, значит не произошёл вход в системный аккаунт, по той или иной причине. Вам нужно зайти в любой Steam аккаунт (без Steam Guard и с нужными вам настройками контента) в настройках приложения (General).  
> - Если обои не закружаются - попробуйте выбрать другой аккаунт из списка в настройках (Account).

> [!WARNING]  
> - Приложение использует **общедоступные аккаунты** для загрузки из мастерской  
> - Приложение **не модифицирует** оригинальный клиент Wallpaper Engine или Steam 

---

## 🚀 Установка

> [!IMPORTANT]
> **Для запуска из исходников (Вариант 2):**
> - Установите [Python 3.14+](https://www.python.org/downloads)
> - Установите [.NET 8](https://dotnet.microsoft.com/download/dotnet/8.0/runtime) Desktop Runtime
>
> **Для упакованной версии (Вариант 1):**
> - Установите только .NET 8 Desktop Runtime указанный выше

### 📦 Вариант 1: Упакованная через PyInstaller версия

Скачайте последнюю версию из раздела **[Releases](https://github.com/psyattack/WEave/releases)**  
> Все зависимости уже встроены, просто распакуйте архив в удобное место и запустите `WEave.exe`

---

### 💻 Вариант 2: Запуск из исходного кода

#### 1. Клонирование репозитория

```bash
git clone https://github.com/psyattack/WEave.git
cd WEave
```

#### 2. Установка зависимостей Python

```bash
pip install -r requirements.txt
```

#### 3. Загрузка необходимых компонентов

| Компонент | Куда поместить |
|-------------|----------------|
| [DepotDownloader](https://github.com/SteamRE/DepotDownloader/releases) | `plugins/DepotDownloader/` |
| [RePKG](https://github.com/notscuffed/repkg/releases) | `plugins/RePKG/` |

#### 4. Запуск приложения

```bash
python main.py
```

---

## 📁 Структура проекта

```
WEave/
├── bootstrap/              # Инициализация приложения
├── domain/                 # Модели и структуры данных
├── services/               # Сервисы приложения
├── infrastructure/         # Интеграции и внешняя логика
├── ui/                     # Интерфейс
├── shared/                 # Общие утилиты
├── localization/           # Переводы
├── plugins/                # Внешние инструменты (скачиваются отдельно)
├── main.py                 # Точка входа
└── requirements.txt        # Зависимости Python
```

---

## 🙏 Благодарности

Этот проект использует следующие открытые ресурсы и инструменты:

- **[DepotDownloader](https://github.com/SteamRE/DepotDownloader/releases)** — модифицированный загрузчик мастерской
- **[RePKG](https://github.com/notscuffed/repkg)** — инструмент распаковки .pkg файлов
- **[WallpaperEngineWorkshopDownloader](https://gitlab.com/steamautocracks/wallpaperengineworkshopdownloader)** — идея и аккаунты для загрузки
- **[icons8](https://icons8.com)** — бесплатные иконки для интерфейса

---

## 📜 Лицензия

Этот проект распространяется под лицензией **[MIT](LICENSE)**.

---

## 👁️‍🗨️ Известные проблемы

- [x] <strike>Некорректное возвращение состояния окна после предварительного сворачивания</strike>
- [x] <strike>Белые диалоговые окна при очистке фильтров</strike>
- [x] <strike>PyInstaller --onefile ломает перезапуск, если будете собирать из исходников собирайте в --onedir (~500мб)</strike>

---

## 📋 TODO & Support

- [x] <strike>Темы</strike>
- [x] <strike>Логин через личный Steam аккаунт (Для использования при Steam failed 50 и подобных)</strike>
- [ ] Автозапуск
- [ ] Трей + silent mode
- [ ] Ряд оригинальных функций WE (Редактор пресетов, создание плейлистов, профили и тд.)
- [ ] Автоматическое обновление
- [x] <strike>Оптимизация интерфейса под разные размеры и форматы экранов + возможность resize окна</strike>

> Если у вас возникли проблемы или есть предложения по улучшению — создайте [Issue](https://github.com/psyattack/WEave/issues) в репозитории.

---