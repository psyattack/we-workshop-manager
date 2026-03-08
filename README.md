# WE Workshop Manager

<p align="center">
  <a href="README.md">🇷🇺 Русский</a> |
  <a href="docs/README.en.md">🇬🇧 English</a> |
  <a href="docs/README.de.md">🇩🇪 Deutsch</a> |
  <a href="docs/README.es.md">🇪🇸 Español</a> |
  <a href="docs/README.fr.md">🇫🇷 Français</a> |
  <a href="docs/README.ja.md">🇯🇵 日本語</a> |
  <a href="docs/README.pt.md">🇧🇷 Português</a> |
  <a href="docs/README.zh.md">🇨🇳 中文</a>
</p>

<p align="center">
  <img src="screenshots/screen_main.png" alt="WE Workshop Manager" width="700">
</p>

<p align="center">
  <strong>Частичная демонстрация интерфейса</strong>
</p>

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
</p>

---

WE Workshop Manager — это десктопное приложение на Python/PyQt6, которое позволяет легко загружать, устанавливать и управлять обоями из Steam Workshop для Wallpaper Engine **без необходимости запускать клиент Steam**.

### <strong>С версии 1.3.7 страницы в Workshop загружаюстся даже быстрее чем в браузере с новой функцией Preload Next Page (BETA)!</strong>

### 🔑 Основные возможности:

- 🌐 Просмотр мастерской Steam и загрузка обоев **в один клик**
- 🗂️ Управление установленными обоями (применение, удаление, извлечение .pkg файлов и прочее)
- 📊 Загрузка обоев по списку ID и\или URL
- 🎯 Отслеживание статуса загрузки\извлечения обоев
- 🌍 Мультиязычность
- ⚜️ Темы
- 🔰 Множество других функций

> [!NOTE]  
> - Обои загружаются в папку по умолчанию для WE, **аналогично обычной установке**  
> - Первый вход может быть долгим, пожалуйста, подождите пока создаются Cookies  
> - Скорось загрузки Workshop зависит от скорости вашего интернет соединения, а так же доступности серверов Steam (Если долго не загружается - перезайдите или нажмите на кнопку Refresh)

> [!WARNING]  
> - Приложение использует **общедоступные аккаунты** для загрузки из мастерской  
> - Приложение **не модифицирует** оригинальный клиент Wallpaper Engine или Steam  
> - Автор **не поддерживает** использование данного ПО для получения материальной выгоды, используйте его лишь как альтернативу с доп. функционалом или при невозможности приобрести лицензионную версию по региональным ограничениям :)  

> [!WARNING]  
> Если вдруг, когда-нибудь, приложение наотрез откажется показывать "определённый" контент в workshop, значит не произошёл вход в системный аккаунт, по той или иной причине. Вам нужно зайти в любой steam аккаунт (без steam guard и с нужными вам настройками контента) в настройках приложения.  
> Аналогично с загрузкой, если обои не закружаются - попробуйте выбрать другой аккаунт из списка.

---

## 🚀 Установка

### 📦 Вариант 1: Упакованная через PyInstaller версия

Скачайте последнюю версию из раздела **[Releases](https://github.com/psyattack/we-workshop-manager/releases)**  
> Все зависимости уже есть в архиве, просто распакуйте архив в удобное место и запустите `WE Workshop Manager.exe`

---

### 💻 Вариант 2: Запуск из исходного кода

#### 0. Первоначальная настройка

Установите Python версии 3.10 или выше с [оффициального сайта](https://www.python.org/downloads), если ещё не сделали это  
Приложение тестировалось на версии Python 3.14.2

#### 1. Клонирование репозитория

```bash
git clone https://github.com/psyattack/we-workshop-manager.git
cd we-workshop-manager
```

#### 2. Установка зависимостей Python

```bash
pip install -r requirements.txt
```

#### 3. Загрузка необходимых компонентов

| Компонент | Куда поместить |
|-------------|----------------|
| [DepotDownloaderMod](https://github.com/SteamAutoCracks/DepotDownloaderMod/releases) | `Plugins/DepotDownloaderMod/` |
| [RePKG](https://github.com/notscuffed/repkg/releases) | `Plugins/RePKG/` |
| [.NET 9 Desktop Runtime](https://dotnet.microsoft.com/en-us/download/dotnet/9.0/runtime) | Установите глобально |

#### 4. Запуск приложения

```bash
python app.py
```

---

## 📁 Структура проекта

```
we-workshop-manager/
├── core/                  # Основная логика
├── ui/                    # Интерфейс
├── localization/          # Файлы локализации
├── resources/             # Ресурсы
├── utils/                 # Вспомогательные утилиты
├── Plugins/               # Утилиты DepotDownloaderMod и RePKG (загружать отдельно)
├── Packages/              # Установщик .NET (устанавливать отдельно)
├── app.py                 # Точка входа
└── requirements.txt       # Зависимости Python
```

---

## 🙏 Благодарности

Этот проект использует следующие открытые ресурсы и инструменты:

- **[DepotDownloaderMod](https://github.com/SteamAutoCracks/DepotDownloaderMod)** — модифицированный загрузчик мастерской
- **[RePKG](https://github.com/notscuffed/repkg)** — инструмент распаковки .pkg файлов
- **[WallpaperEngineWorkshopDownloader](https://github.com/SteamAutoCracks/WallpaperEngineWorkshopDownloader)** — за предоставление аккаунтов для загрузки из мастерской
- **[icons8](https://icons8.com)** — бесплатные иконки для интерфейса

---

## 📜 Лицензия

Этот проект распространяется под лицензией **[MIT](LICENSE)**.

---

## 👁️‍🗨️ Известные проблемы

- [ ] Поиск частично отличается от версии на сайте
- [ ] Некорректное возвращение состояния окна после предварительного сворачивания
- [ ] Белые диалоговые окна при очистке фильтров

---

## 📋 TODO & Support

- [x] Темы
- [x] Логин через личный Steam аккаунт (Для использования при Steam failed 50 и подобных)
- [ ] Автозапуск
- [ ] Трей + silent mode
- [ ] Ряд оригинальных функций WE (Редактор пресетов, создание плейлистов, профили и тд.)
- [ ] Автоматическое обновление
- [ ] Оптимизация интерфейса под разные размеры и форматы экранов

> Если у вас возникли проблемы или есть предложения по улучшению — создайте [Issue](https://github.com/psyattack/we-workshop-manager/issues) в репозитории.

---