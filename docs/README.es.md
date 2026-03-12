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
  <img src="../screenshots/screen_main.png" alt="WEave (anteriormente WE Workshop Manager)" width="700">
</p>

<p align="center">
  <strong>Demostración de la interfaz principal</strong>
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

WEave (anteriormente WE Workshop Manager) es una aplicación de escritorio Python/PyQt6 que te permite descargar, instalar y gestionar fácilmente fondos de pantalla del Steam Workshop para Wallpaper Engine **sin necesidad de ejecutar el cliente de Steam**.

### <strong>En desarrollo 2.0 - migración a Tauri (React) + Rust o PyWebView</strong>

### 🔑 Características principales:

- 🌐 Explorar el Steam Workshop y descargar fondos de pantalla **con un clic**
- 🗂️ Gestionar los fondos de pantalla instalados (aplicar, eliminar, extraer archivos .pkg, etc.)
- 📊 Descargar fondos de pantalla por lista de IDs y/o URLs
- 🎯 Seguimiento del estado de descarga/extracción de fondos de pantalla
- 🔧 Carga rápida de páginas
- 🌍 Multilingüe
- ⚜️ Temas
- 🔰 Muchas otras funciones

> [!NOTE]  
> - Los fondos de pantalla se descargan en la carpeta predeterminada de WE, **similar a una instalación regular**  
> - El primer inicio de sesión puede tardar un rato, por favor espere mientras se inicia sesión en la cuenta del sistema
> - La velocidad de descarga del Workshop depende de la velocidad de tu conexión a Internet, así como de la disponibilidad de los servidores de Steam
> - Si la aplicación no muestra contenido "específico" en el Workshop, significa que la cuenta del sistema no ha iniciado sesión por alguna razón. Necesitas iniciar sesión en cualquier cuenta de Steam (sin Steam Guard y con la configuración de contenido que necesites) en la configuración de la aplicación (General).
> - Si los fondos de pantalla no se cargan - intenta seleccionar otra cuenta de la lista en la configuración (Cuenta).

> [!WARNING]  
> - La aplicación usa **cuentas públicas** para descargar del workshop  
> - La aplicación **no modifica** el cliente original de Wallpaper Engine o Steam  

---

## 🚀 Instalación

> [!IMPORTANT]
> **Para ejecutar desde el código fuente (Opción 2):**
> - Instale [Python 3.10+](https://www.python.org/downloads) (probado en Python 3.14.2)
> - Instale [.NET 8](https://dotnet.microsoft.com/download/dotnet/8.0/runtime) o [.NET 9](https://dotnet.microsoft.com/download/dotnet/9.0/runtime) Desktop Runtime
>
> **Para la versión empaquetada (Opción 1):**
> - Solo el .NET Runtime mencionado arriba

### 📦 Opción 1: Versión empaquetada con PyInstaller

Descarga la última versión desde la sección **[Releases](https://github.com/psyattack/we-workshop-manager/releases)**  
> Todas las dependencias ya están en el archivo, simplemente extrae el archivo a un lugar conveniente y ejecuta `WEave.exe`

---

### 💻 Opción 2: Ejecución desde el código fuente

#### 1. Clonar el repositorio

```bash
git clone https://github.com/psyattack/we-workshop-manager.git
cd we-workshop-manager
```

#### 2. Instalar dependencias de Python

```bash
pip install -r requirements.txt
```

#### 3. Descargar componentes necesarios

| Componente | Dónde colocar |
|-------------|----------------|
| [DepotDownloaderMod](https://github.com/SteamAutoCracks/DepotDownloaderMod/releases) | `plugins/DepotDownloaderMod/` |
| [RePKG](https://github.com/notscuffed/repkg/releases) | `plugins/RePKG/` |

#### 4. Ejecutar la aplicación

```bash
python main.py
```

---

## 📁 Estructura del proyecto

```
we-workshop-manager/
├── bootstrap/              # Inicialización de la aplicación
├── domain/                 # Modelos y estructuras de datos
├── services/               # Servicios de la aplicación
├── infrastructure/         # Integraciones y lógica externa
├── ui/                     # Interfaz
├── shared/                 # Utilidades comunes
├── localization/           # Traducciones
├── plugins/                # Herramientas externas (descargar por separado)
├── main.py                 # Punto de entrada
└── requirements.txt        # Dependencias de Python
```

---

## 🙏 Agradecimientos

Este proyecto utiliza los siguientes recursos y herramientas abiertas:

- **[DepotDownloaderMod](https://github.com/SteamAutoCracks/DepotDownloaderMod)** — descargador de workshop modificado
- **[RePKG](https://github.com/notscuffed/repkg)** — herramienta de extracción de archivos .pkg
- **[WallpaperEngineWorkshopDownloader](https://github.com/SteamAutoCracks/WallpaperEngineWorkshopDownloader)** — por proporcionar cuentas para descargar del workshop
- **[icons8](https://icons8.com)** — iconos gratuitos para la interfaz

---

## 📜 Licencia

Este proyecto está bajo la licencia **[MIT](LICENSE)**.

---

## 👁️‍🗨️ Problemas conocidos

- [ ] Retorno incorrecto del estado de la ventana después de pre-minimizar
- [x] Diálogos blancos al limpiar filtros
- [ ] PyInstaller --onefile rompe el reinicio, si compila desde el código fuente compile en --onedir (~500mb)

---

## 📋 TODO y Soporte

- [x] Temas
- [x] Inicio de sesión a través de cuenta personal de Steam (Para usar con Steam failed 50 y similares)
- [ ] Inicio automático
- [ ] Bandeja + modo silencioso
- [ ] Funciones originales de WE (Editor de presets, crear listas de reproducción, perfiles, etc.)
- [ ] Actualizaciones automáticas
- [x] Optimización de la interfaz para diferentes tamaños y formatos de pantalla + capacidad de cambiar tamaño de ventana

> Si tienes problemas o sugerencias de mejora — crea un [Issue](https://github.com/psyattack/we-workshop-manager/issues) en el repositorio.

---
