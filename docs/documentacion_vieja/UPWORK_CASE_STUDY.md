# Case Study: Gwen / Jarvis Windows Pro
## Remote AI Tele-Control & OS Automation Platform

### The Origin Story: Building a Personal "Jarvis"
Gwen was born out of a developer's dream to build a real-life "Jarvis"—a dedicated, intelligent assistant living inside his personal Windows PC. Frustrated by existing bloated automation tools that lack personal touch and deep hardware integration, the creator engineered Gwen to solve his exact daily needs: monitoring PC battery levels from his phone, launching cloud gaming queues on NVIDIA GeForce NOW without sitting at his desk, controlling system volume and media playback remotely, managing large file uploads to Google Drive, running quick CLI commands, and interacting seamlessly via voice notes and text messages through Telegram.

---

### Elevator Pitch
Gwen/Jarvis Windows Pro is an enterprise-grade, headless Windows OS tele-control and AI automation system that enables users to remotely monitor, command, and manage their desktop hardware and workflows from anywhere via Telegram and FastAPI WebSockets.

---

### Core Use Case
Modern founders, remote engineers, and power users frequently need real-time access to their desktop workstation's computational power, active background tasks, local files, and media environments while away from their primary machines. Gwen/Jarvis Windows Pro converts any Windows PC into an intelligent, voice-and-text accessible personal server—enabling remote command-line execution, automated cloud file delivery, low-overhead session tracking, and multi-model AI assistant queries with zero desktop latency.

---

### Telegram API Integration Architecture
Telegram's Bot API (`pyTelegramBotAPI`) serves as the universal mobile command center bridging the user's mobile device directly to the local Windows kernel:
* **Security & Authorization Decorator (`_require_auth`):** Every incoming Telegram message is intercepted by an authentication wrapper enforcing strict Chat ID verification, blocking unauthorized access at the network boundary.
* **Multimodal Input Handlers:** Native Telegram handlers digest text commands, incoming documents/photos, and voice notes. Voice messages are captured, processed using Google SpeechRecognition (STT), dispatched to the core engine, and replied to with low-latency neural speech via Microsoft Edge TTS (`edge-tts`).
* **Interactive Command Routing:** Over 20 specialized commands (`/bateria`, `/sistema`, `/volumen`, `/captura`, `/lanza`, `/descargas`, `/memoria`) are registered with decorator hooks, executing background routines and streaming status updates back to the Telegram chat UI.

---

### Modular Architecture & Dynamic Plugin Discovery
The core of Gwen is engineered around a zero-boilerplate, highly extensible **Dynamic Module Registry (`ModuleRegistry`)**:
* **Automated Discovery (`pkgutil` + `importlib`):** On startup, the engine scans the `modules/` package directory dynamically using `pkgutil.iter_modules`. It imports module files dynamically without hardcoded list declarations.
* **Polymorphic Base Class (`BaseModule`):** Every feature module inherits from `BaseModule`, implementing `@abstractmethod` contracts: `can_handle(texto)` and `handle(texto, chat_id, bot, cfg, platform)`.
* **Priority-Based Chain of Responsibility:** Modules define explicit execution priorities (`prioridad`). Incoming messages pass through a sorted responsibility chain. The first module to match the intent handles the request and short-circuits execution.
* **Hot-Toggle & Feature Flagging:** Modules can be individually enabled/disabled via `.env` configuration flags without breaking the main engine loop.
* **Graceful LLM Fallback Pipeline:** If no static module claims the message intent, the registry seamlessly routes the request through a multi-tier AI fallback pipeline (Direct LLM Runner -> OpenCode CLI Engine), guaranteeing intelligent responses for arbitrary user requests.

---

### Tech Stack & Integrations
* **Languages & Runtimes:** Python 3.13, PowerShell 7, Windows Management Instrumentation (WMI / CIM / WinRT).
* **Frameworks & API Servers:** FastAPI, Uvicorn (ASGI), WebSockets, Asyncio, `pyTelegramBotAPI` (`telebot`).
* **AI & LLM Integrations:** OpenRouter API (DeepSeek-R1 / DeepSeek-v4), Groq API (Llama 3.3 70B Versatile), OpenCode CLI Engine (`opencode-ai`).
* **Native APIs & Hardware Interfaces:** Windows COM Interfaces (`comtypes`, `pycaw`), WinRT OCR Engine (`Windows.Media.Ocr`), `pyautogui`, `pygetwindow`, `psutil`.
* **Voice & Media Engines:** Microsoft Edge TTS (`edge-tts`), PyAudio, SpeechRecognition, PyDub.
* **Cloud & Storage Integrations:** Google Drive REST API v3 (`google-api-python-client`), `transfer.sh` HTTP API fallback router.
* **Database & Persistence:** SQLite 3 (`jarvis_memoria.db` with WAL mode for high-concurrency memory & state retention).

---

### Top 3 Technical Features

#### 1. Zero-CPU Event-Driven Session & Queue State Machine (NVIDIA Log Parser)
* **Logic & Engineering:** Instead of relying on resource-heavy screen scraping or high-frequency polling loops that consume CPU/GPU cycles during active background tasks, this engine parses NVIDIA GeForce NOW’s native log streams (`debug.log`) in real time using backward byte-offset seeking (`os.SEEK_END`). It inspects session state events (`onSessionSetupProgress`, `onStopResult`), extracts live queue position data and ETAs via regex pattern matching, and correlates state changes with window visibility. This achieves zero CPU overhead and near-zero memory footprint while delivering instant Telegram notifications upon session ready states.

#### 2. Security-Filtered Dual-Mode File Routing Pipeline (Google Drive + transfer.sh + Telegram)
* **Logic & Engineering:** Remote file transfers are governed by a multi-tiered security and payload-aware routing engine. Incoming and outgoing file paths undergo recursive path sanitization to block sensitive extensions (`.env`, `.db`, `.key`, `.log`) and protected directories (`AppData`, `System32`). Payloads under 50 MB are dispatched directly via Telegram's native Bot API streams. When file sizes exceed 50 MB, the system automatically redirects transfer streams through OAuth2 resumable chunked uploads (`MediaIoBaseUpload`) to Google Drive or fallback multi-part HTTP PUT requests to `transfer.sh`, generating secure, publicly accessible URLs on the fly.

#### 3. Multi-Provider AI Fallback Router & Platform Abstraction Layer (Windows WinRT / COM Integration)
* **Logic & Engineering:** Built around the Platform Adapter design pattern, the codebase decouples high-level Telegram bot interfaces from underlying OS calls. System health diagnostics, screenshot capturing, audio volume manipulation via native COM interfaces (`IAudioEndpointVolume`), and optical character recognition via native PowerShell WinRT wrappers (`Windows.Media.Ocr.OcrEngine`) are executed cleanly across both REST/WebSocket API endpoints and bot command handlers. Concurrently, a resilient AI dispatcher manages query routing across OpenRouter, Groq, and OpenCode CLI instances while maintaining persistent SQLite conversation state and context memory.
