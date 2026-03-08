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
  <strong>Demonstração parcial da interface</strong>
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

WE Workshop Manager é um aplicativo de desktop Python/PyQt6 que permite baixar, instalar e gerenciar facilmente wallpapers do Steam Workshop para Wallpaper Engine **sem precisar executar o cliente Steam**.

### <strong>Desde a versão 1.3.7, as páginas do Workshop carregam mais rápido que no navegador com o novo recurso Preload Next Page (BETA)!</strong>

### 🔑 Principais recursos:

- 🌐 Navegar pelo Steam Workshop e baixar wallpapers **com um clique**
- 🗂️ Gerenciar wallpapers instalados (aplicar, remover, extrair arquivos .pkg, etc.)
- 📊 Baixar wallpapers por lista de IDs e/ou URLs
- 🎯 Rastrear status de download/extração de wallpapers
- 🌍 Multilíngue
- ⚜️ Temas
- 🔰 Muitos outros recursos

> [!NOTE]  
> - Os wallpapers são baixados para a pasta padrão do WE, **similar a uma instalação normal**  
> - O primeiro login pode demorar um pouco, por favor espere enquanto os Cookies estão sendo criados  
> - A velocidade de download do Workshop depende da velocidade da sua conexão com a Internet, bem como da disponibilidade dos servidores da Steam (Se demorar muito para baixar - faça login novamente ou clique no botão Atualizar)

> [!WARNING]  
> - O aplicativo usa **contas públicas** para baixar do workshop  
> - O aplicativo **não modifica** o cliente original do Wallpaper Engine ou Steam  
> - O autor **não apoia** o uso deste software para ganho financeiro, use-o apenas como uma alternativa com funcionalidades adicionais ou se não puder comprar uma versão licenciada devido a restrições regionais :)  

> [!WARNING]  
> Se algum dia o aplicativo se recusar a mostrar conteúdo "específico" no workshop, significa que a conta do sistema não fez login por algum motivo. Você precisa fazer login em qualquer conta steam (sem steam guard e com as configurações de conteúdo que você precisa) nas configurações do aplicativo.  
> Similar com o download, se os wallpapers não carregam - tente selecionar outra conta da lista.

---

## 🚀 Instalação

### 📦 Opção 1: Versão empacotada com PyInstaller

Baixe a versão mais recente da seção **[Releases](https://github.com/psyattack/we-workshop-manager/releases)**  
> Todas as dependências já estão no arquivo, basta extrair o arquivo para um local conveniente e executar `WE Workshop Manager.exe`

---

### 💻 Opção 2: Execução a partir do código-fonte

#### 0. Configuração inicial

Instale o Python versão 3.10 ou superior do [site oficial](https://www.python.org/downloads) se ainda não fez  
O aplicativo foi testado no Python 3.14.2

#### 1. Clonar o repositório

```bash
git clone https://github.com/psyattack/we-workshop-manager.git
cd we-workshop-manager
```

#### 2. Instalar dependências do Python

```bash
pip install -r requirements.txt
```

#### 3. Baixar componentes necessários

| Componente | Onde colocar |
|-------------|----------------|
| [DepotDownloaderMod](https://github.com/SteamAutoCracks/DepotDownloaderMod/releases) | `Plugins/DepotDownloaderMod/` |
| [RePKG](https://github.com/notscuffed/repkg/releases) | `Plugins/RePKG/` |
| [.NET 9 Desktop Runtime](https://dotnet.microsoft.com/en-us/download/dotnet/9.0/runtime) | Instalar globalmente |

#### 4. Executar o aplicativo

```bash
python app.py
```

---

## 📁 Estrutura do projeto

```
we-workshop-manager/
├── core/                  # Lógica principal
├── ui/                    # Interface
├── localization/          # Arquivos de localização
├── resources/             # Recursos
├── utils/                 # Utilitários
├── Plugins/               # Utilitários DepotDownloaderMod e RePKG (baixar separadamente)
├── Packages/              # Instalador .NET (instalar separadamente)
├── app.py                 # Ponto de entrada
└── requirements.txt       # Dependências Python
---

---

## 🙏 Agradecimentos

Este projeto usa os seguintes recursos e ferramentas abertas:

- **[DepotDownloaderMod](https://github.com/SteamAutoCracks/DepotDownloaderMod)** — baixador de workshop modificado
- **[RePKG](https://github.com/notscuffed/repkg)** — ferramenta de extração de arquivos .pkg
- **[WallpaperEngineWorkshopDownloader](https://github.com/SteamAutoCracks/WallpaperEngineWorkshopDownloader)** — por fornecer contas para baixar do workshop
- **[icons8](https://icons8.com)** — ícones gratuitos para a interface

---

## 📜 Licença

Este projeto está sob a licença **[MIT](LICENSE)**.

---

## 👁️‍🗨️ Problemas conhecidos

- [ ] Busca difere parcialmente da versão do site
- [ ] Retorno incorreto do estado da janela após minimizar

---

## 📋 TODO e Suporte

- [x] Temas
- [x] Login via conta Steam pessoal (Para uso com Steam failed 50 e similares)
- [ ] Inicialização automática
- [ ] Bandeja + modo silencioso
- [ ] Funções originais do WE (Editor de presets, criar playlists, perfis, etc.)
- [ ] Atualizações automáticas
- [ ] Otimização da interface para diferentes tamanhos e formatos de tela

> Se você tiver problemas ou sugestões de melhoria — crie uma [Issue](https://github.com/psyattack/we-workshop-manager/issues) no repositório.

---
