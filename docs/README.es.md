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
  <strong>Demostración parcial de la interfaz</strong>
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

WE Workshop Manager es una aplicación de escritorio Python/PyQt6 que te permite descargar, instalar y gestionar fácilmente fondos de pantalla del Steam Workshop para Wallpaper Engine **sin necesidad de ejecutar el cliente de Steam**.

### <strong>¡Desde la versión 1.3.7, las páginas de Workshop se cargan más rápido que en el navegador con la nueva función Preload Next Page (BETA)!</strong>

### 🔑 Características principales:

- 🌐 Explorar el Steam Workshop y descargar fondos de pantalla **con un clic**
- 🗂️ Gestionar los fondos de pantalla instalados (aplicar, eliminar, extraer archivos .pkg, etc.)
- 📊 Descargar fondos de pantalla por lista de IDs y/o URLs
- 🎯 Seguimiento del estado de descarga/extracción de fondos de pantalla
- 🌍 Multilingüe
- ⚜️ Temas
- 🔰 Muchas otras funciones

> [!NOTE]  
> - Los fondos de pantalla se descargan en la carpeta predeterminada de WE, **similar a una instalación regular**  
> - El primer inicio de sesión puede tardar un rato, por favor espere mientras se crean las Cookies  
> - La velocidad de descarga del Workshop depende de la velocidad de tu conexión a Internet, así como de la disponibilidad de los servidores de Steam (Si tarda demasiado en descargar - vuelve a iniciar sesión o haz clic en el botón Actualizar)

> [!WARNING]  
> - La aplicación usa **cuentas públicas** para descargar del workshop  
> - La aplicación **no modifica** el cliente original de Wallpaper Engine o Steam  
> - El autor **no apoya** el uso de este software para obtener ganancias económicas, úsalo solo como una alternativa con funcionalidad adicional o si no puedes comprar una versión licenciada debido a restricciones regionales :)  

> [!WARNING]  
> Si alguna vez la aplicación se niega a mostrar contenido "específico" en el workshop, significa que la cuenta del sistema no ha iniciado sesión por alguna razón. Necesitas iniciar sesión en cualquier cuenta de steam (sin steam guard y con la configuración de contenido que necesites) en la configuración de la aplicación.  
> Del mismo modo con la descarga, si los fondos de pantalla no se cargan - intenta seleccionar otra cuenta de la lista.

---

## 🚀 Instalación

### 📦 Opción 1: Versión empaquetada con PyInstaller

Descarga la última versión desde la sección **[Releases](https://github.com/psyattack/we-workshop-manager/releases)**  
> Todas las dependencias ya están en el archivo, simplemente extrae el archivo a un lugar conveniente y ejecuta `WE Workshop Manager.exe`

---

### 💻 Opción 2: Ejecución desde el código fuente

#### 0. Configuración inicial

Instala Python versión 3.10 o superior desde el [sitio oficial](https://www.python.org/downloads) si aún no lo has hecho  
La aplicación fue probada en Python 3.14.2

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
| [DepotDownloaderMod](https://github.com/SteamAutoCracks/DepotDownloaderMod/releases) | `Plugins/DepotDownloaderMod/` |
| [RePKG](https://github.com/notscuffed/repkg/releases) | `Plugins/RePKG/` |
| [.NET 9 Desktop Runtime](https://dotnet.microsoft.com/en-us/download/dotnet/9.0/runtime) | Instalar globalmente |

#### 4. Ejecutar la aplicación

```bash
python app.py
```

---

## 📁 Estructura del proyecto

```
we-workshop-manager/
├── core/                  # Lógica principal
├── ui/                    # Interfaz
├── localization/          # Archivos de localización
├── resources/             # Recursos
├── utils/                 # Utilidades
├── Plugins/               # Utilidades de DepotDownloaderMod y RePKG (descargar por separado)
├── Packages/              # Instalador de .NET (instalar por separado)
├── app.py                 # Punto de entrada
└── requirements.txt       # Dependencias de Python
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

- [ ] La búsqueda difiere parcialmente de la versión del sitio web
- [ ] Retorno incorrecto del estado de la ventana después de minimizar

---

## 📋 TODO y Soporte

- [x] Temas
- [x] Inicio de sesión a través de cuenta personal de Steam (Para usar con Steam failed 50 y similares)
- [ ] Inicio automático
- [ ] Bandeja + modo silencioso
- [ ] Funciones originales de WE (Editor de presets, crear listas de reproducción, perfiles, etc.)
- [ ] Actualizaciones automáticas
- [ ] Optimización de la interfaz para diferentes tamaños y formatos de pantalla

> Si tienes problemas o sugerencias de mejora — crea un [Issue](https://github.com/psyattack/we-workshop-manager/issues) en el repositorio.

---
