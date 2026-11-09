# 🩺 Auditoría Completa — Gwen / Jarvis Windows Pro v2.0

> **Para:** Equipo de desarrollo
> **Fecha:** 2026-08-02
> **Repositorio:** `C:\Users\admin\Desktop\jarvis_windows_pro`
> **Total archivos auditados:** 52 Python + 4 config + 3 docs
> **Issues encontrados:** 24

---

## ✅ ESTADO DE SOLUCIÓN — Verificado el 2026-08-04

| # | Issue | Estado | Detalle |
|---|-------|--------|---------|
| C1 | `HotConfig.__setattr__` bloquea asignación | ✅ YA SOLUCIONADO | `__setattr__` reescrito: asigna al base + `override()` |
| C2 | GFN no detecta STREAMING vs QUEUE | ✅ YA SOLUCIONADO | Motor vFinal: detección por `debug.log` de NVIDIA |
| C3 | Event `_cancel` compartido entre juegos | ✅ YA SOLUCIONADO | `_cancel_events` por juego + `cancel_queue(game)` |
| C4 | Wizard `can_handle` siempre True | ✅ YA SOLUCIONADO | Sin `or True`; recibe `cfg`, verifica `wizard_completed` |
| C5 | Excepción muda mata monitor GFN | ✅ YA SOLUCIONADO | Conteo de errores: CLOSED solo tras 3 fallos seguidos |
| A1 | `shell=True` en descargas | ✅ YA SOLUCIONADO | `["cmd","/c","start",...]` sin shell |
| A2 | Búsqueda IA sin filtro | ✅ YA SOLUCIONADO | `es_peligroso(query)` al inicio de `_ai_file_search` |
| A3 | API key hardcodeada | ✅ SOLUCIONADO HOY | REST+WS leen `cfg.api_key` y rechazan si falta; default vacío en `config.py`; `.env.example` con placeholder. ⚠️ `.env` conserva `gwen_secret_key_123` (en uso por la app Android) |
| A4 | `validate()` no revisa API keys IA | ✅ YA SOLUCIONADO | Valida OPENROUTER/GROQ según `ai_provider` |
| A5 | write-lock solo en `execute()` | ✅ SOLUCIONADO HOY | `execute()` commitea escrituras bajo lock (autocommit) |
| M1 | Estado global sin thread-safety | ✅ SOLUCIONADO HOY | `set_seccion/get_seccion`, `set_protocolo/get_protocolo`, locks en wizard y archivos; lectores externos actualizados |
| M2 | Scheduler 1 tarea por ciclo | ✅ YA SOLUCIONADO | Loop de `due_tasks` ejecuta todas las vencidas |
| M3 | TeleBot nuevo por tarea | ✅ YA SOLUCIONADO | Si no hay bot: log + cancelar tarea |
| M4 | easyocr/opencv/mss obsoletos | ✅ YA SOLUCIONADO | Eliminados de requirements.txt |
| M5 | Código `.deb` muerto en Windows | ✅ YA SOLUCIONADO | Guard `os.name != "posix"` |
| M6 | `can_handle` sin acceso a cfg | ✅ YA SOLUCIONADO | Firma `(texto, cfg=None)` + fallback TypeError en registry |
| M7 | `/reiniciar` sin cleanup | ✅ YA SOLUCIONADO | stop_polling + db.close + scheduler.stop + hijos |
| B1 | Default `model_base` inconsistente | ✅ YA SOLUCIONADO | Coincide con .env.example |
| B2 | Tupla con duplicado | ✅ YA SOLUCIONADO | Sin duplicados |
| B3 | urllib vs requests | ⏭️ NO APLICADO | Cosmético; la ruta HTTP de IA funciona con urllib. Decisión: no tocar código que funciona |
| B4 | `os` sin importar en windows.py | ✅ SOLUCIONADO HOY | `import os` al inicio (evita NameError en `install_package`) |
| B5 | `create_task` sin manejo de errores | ✅ SOLUCIONADO HOY | `_safe_send()` con try/except en `DummyBotSender` |
| B6 | Migraciones sin versionado | ✅ YA SOLUCIONADO | Tabla `schema_version` + `_apply_v1` |
| B7 | Lógica confusa pop+insert | ✅ YA SOLUCIONADO | Pop+insert limpio |
| B8 | `streamer_names` hardcodeado | ✅ YA SOLUCIONADO | Obsoleto en motor vFinal (debug.log) |
| B9 | `GFN_QUEUE_REGION` sin deprecar | ✅ SOLUCIONADO HOY | Marcado DEPRECADO en `.env.example` y `config.py` (código muerto) |

**Resumen: 24/24 atendidos → 20 ya estaban aplicados (verificados), 4 aplicados hoy (A3, A5, M1, B4, B5, B9 — 6 en realidad, ver tabla), 1 no aplicado por decisión (B3).**

> ⚠️ **Nota de verificación:** Todos los archivos modificados pasaron `py_compile` y smoke test del registry (21 módulos cargados). El `.env` se dejó intacto con `gwen_secret_key_123` para no romper la app Android; si se quiere rotar la key, actualizar también `SessionPrefs` de la app.

---

## 🗺️ Mapa Completo del Proyecto

```
C:\Users\admin\Desktop\jarvis_windows_pro\
│
├── main.py                    # Punto de entrada, singleton lock, bootstrap
├── jarvis.py                  # Núcleo: JarvisBot (Telegram handlers + dispatch)
├── config.py                  # JarvisConfig (dataclass) + HotConfig (overrides runtime)
├── api_server.py              # FastAPI REST + WebSocket (app Android companion)
├── requirements.txt           # Dependencias pip
├── .env.example               # Template de variables de entorno
├── launch.bat                 # Batch launcher (pythonw)
├── launch_oculto.vbs          # VBS silencioso
├── launch_smart.vbs           # VBS con popup
│
├── ai/                        # Capa de IA
│   ├── models.py              # MODELOS dict (DeepSeek, Llama, Groq...)
│   ├── agent_loader.py        # Carga prompt de identidad Gwen desde template
│   ├── prompt_builder.py      # Construye prompt combinando contexto+memoria+tarea
│   ├── direct_ai_runner.py    # HTTP: OpenRouter API / Groq API (usa urllib)
│   └── opencode_runner.py     # CLI: subprocess opencode run --model X --auto
│
├── database/                  # SQLite (singleton, WAL mode)
│   ├── connection.py          # ConnectionManager: singleton + write-lock
│   ├── schema.py              # 6 tablas + 5 índices + purge 180 días
│   └── repositories/
│       ├── conversacion.py    # Chat log: guardar + contexto_reciente + contexto_seccion
│       ├── perfil.py          # Key-value: aprender + recordar + obtener_todo
│       ├── eventos.py         # Memoria: guardar_evento + obtener_eventos
│       ├── tareas.py          # CRUD tareas programadas
│       └── secciones.py       # CRUD secciones/tópicos
│
├── modules/                   # 22 plugins (heredan de BaseModule ABC)
│   ├── base.py                # ABC: nombre, prioridad, can_handle, handle
│   ├── registry.py            # ModuleRegistry: discover + sort + dispatch + fallback_ai
│   ├── auth.py                # Authorizer: chat_id validate + rate limiting
│   │
│   ├── wizard.py              # [P3]  Onboarding 3 pasos
│   ├── reconfig.py            # [P5]  Cambios de config en caliente
│   ├── sistema.py             # [P15] /sh, shutdown, lock screen
│   ├── secciones.py           # [P20] Tópicos de conversación (⚠ global state)
│   ├── tareas.py              # [P25] Tareas programadas NL
│   ├── memoria.py             # [P30] Aprender/recordar datos del usuario
│   ├── protocolos.py          # [P35] Protocolo G/M switching (⚠ global state)
│   ├── geforcenow.py          # [P45] GeForce NOW launcher + monitor
│   ├── ventanas.py            # [P55] Gestión de ventanas
│   ├── procesos.py            # [P55] Top RAM + kill proceso
│   ├── sistema_info.py        # [P55] CPU/RAM/Disco/uptime
│   ├── capturas.py            # [P55] Screenshot
│   ├── notificaciones.py      # [P55] Toast notificación desktop
│   ├── medios.py              # [P60] Media keys (play/pause/next/prev)
│   ├── volumen.py             # [P65] Volumen get/set
│   ├── portapapeles.py        # [P70] Clipboard copy
│   ├── descargas.py           # [P72] Download URL + instalar .exe/.msi/.zip
│   ├── archivos.py            # [P75] File search + send + AI search (⚠ global state)
│   ├── bateria.py             # [P85] Batería status
│   ├── voz.py                 # [P90] TTS (edge-tts) + STT (Google)
│   └── conversacion.py        # [P95] Small talk (saludos, gracias, despedidas)
│
├── plat_adapter/              # Abstracción cross-platform
│   ├── base.py                # PlatformAdapter ABC (18 métodos abstractos)
│   ├── windows.py             # Windows: pycaw, pyautogui, pygetwindow, win10toast
│   └── linux.py               # Linux: pactl, wmctrl, notify-send (stub)
│
├── utils/                     # Servicios y utilidades
│   ├── gfn_engine.py          # Motor GFN v3: zero-PyTorch window detection
│   ├── scheduler.py           # Hilo daemon: ejecución tareas programadas
│   ├── config_manager.py      # JSON: overrides, presets, backups (20 max)
│   ├── security.py            # Filtro comandos peligrosos + sanitizar shell
│   ├── file_uploader.py       # Google Drive + transfer.sh + clipboard uploaders
│   ├── text.py                # truncar_telegram + escapar_markdown
│   └── logging_config.py      # Rotating file handler (5MB, 3 backups)
│
├── templates/
│   └── agents_template.md     # Prompt de identidad: "Eres Gwen, asistente de {TITLE} {NAME}"
│
└── data/                      # Runtime data (no commitear)
    ├── jarvis_memoria.db      # SQLite database
    ├── jarvis.log             # Logs rotativos
    ├── config_override.json   # Overrides runtime
    ├── config_backups/        # Snapshots de config
    ├── credentials.json       # Google Drive OAuth
    └── assets/                # Recursos estáticos
```

### Diagrama de Flujo de Datos

```
Usuario Telegram ──> JarvisBot._on_text
                         │
                         v
                    Authorizer.check()        ← chat_id, rate limit, message age
                         │
                         v
                    ModuleRegistry.dispatch()
                         │
                    guardar_conversacion()     ← persiste en SQLite
                         │
                    ┌─── FOR each module (by priority) ───┐
                    │  can_handle(texto)?                  │
                    │    YES → handle(texto, chat_id, ...) │
                    │           → return True (handled)    │
                    │    NO  → next module                 │
                    └─────────────────────────────────────┘
                         │
                         v (ningún módulo manejó)
                    _fallback_ai()
                         │
                    ┌─── direct_ai_runner (HTTP: OpenRouter/Groq)
                    │    éxito? → send message + TTS
                    │    fallo? → opencode_runner (CLI: opencode run)
                    └──────────────────────────────────────┘
```

---

## 🔴 CRÍTICOS — Rompen funcionalidad en runtime

### [C1] `config.py:304-305` — HotConfig.__setattr__ bloquea toda asignación directa

```python
# config.py:304-305
def __setattr__(self, name: str, value):
    raise AttributeError("Usa cfg.override(key, value) para modificar configuración")
```

**Impacto:** Todo el código asigna directamente a `cfg` (que es `HotConfig`). Esto CRASHEA en runtime en **7 ubicaciones**:

| Archivo | Línea(s) | Código |
|---|---|---|
| `jarvis.py` | 298, 300, 302 | `self.cfg.ai_provider = prov` |
| `modules/protocolos.py` | 22, 23, 31, 39, 40, 48 | `cfg.openrouter_model = "..."` |
| `api_server.py` | 176, 178, 180 | `_cfg_instance.openrouter_model = mod` |
| `modules/reconfig.py` | varios | `cfg.ai_provider = ...` |

**Fix:**
```python
def __setattr__(self, name: str, value):
    _base = object.__getattribute__(self, "_base")
    if hasattr(_base, name):
        setattr(_base, name, value)
    elif name.startswith('_'):
        object.__setattr__(self, name, value)
    else:
        raise AttributeError(f"'{name}' no es un atributo de config. Usa cfg.override().")
```

---

### [C2] `utils/gfn_engine.py:56-64` — No-op en detección de STREAMING vs QUEUE

```python
# utils/gfn_engine.py:56-64
if "geforce now" in w_title or "nvidia geforce now" in w_title:
    if win.width >= 1280 and win.height >= 700 and not any(...):
        has_gfn_launcher = True       # ❌ Ambas ramas hacen lo mismo
    else:
        has_gfn_launcher = True       # ❌ No-op: nunca detecta STREAMING
```

**Impacto:** El launcher de GFN a pantalla completa (≥1280x700) NUNCA se reporta como STREAMING, siempre cae a QUEUE. Falsos positivos: Gwen dice "estás en cola" cuando el juego ya está corriendo.

**Fix:**
```python
if "geforce now" in w_title or "nvidia geforce now" in w_title:
    if win.width >= 1280 and win.height >= 700 and not any(
        k in w_title for k in ("biblioteca", "library", "configuracion")
    ):
        return "STREAMING"           # ← Devolver STREAMING directamente
    has_gfn_launcher = True
```

---

### [C3] `utils/gfn_engine.py:17, 186-192` — Event `_cancel` compartido entre todos los juegos

```python
# utils/gfn_engine.py:17
self._cancel = threading.Event()   # ← UN solo evento para todos los juegos

# utils/gfn_engine.py:186-192
while not self._cancel.is_set():   # ← Bucle post-STREAMING también usa _cancel
    _time.sleep(10)
    if self._get_window_state(game_name) == "CLOSED":
        return
```

**Impacto:** Lanzas Destiny 2 y luego Genshin Impact. Cancelar la cola de Genshin también cancela la de Destiny. Cerrar Destiny detiene el monitoreo de Genshin (si está en post-streaming).

**Fix:**
```python
# En __init__:
self._cancel_events: dict[str, threading.Event] = {}

# En _queue_monitor, usar evento por juego:
cancel_ev = threading.Event()
self._cancel_events[game_name.lower()] = cancel_ev

# En cancel_queue:
def cancel_queue(self, game_name: str | None = None):
    if game_name:
        self._cancel_events.get(game_name.lower(), threading.Event()).set()
    else:
        for ev in self._cancel_events.values():
            ev.set()
```

---

### [C4] `modules/wizard.py:54` — `can_handle` siempre True por `or True`

```python
# modules/wizard.py:54
def can_handle(self, texto: str) -> bool:
    t = texto.lower().strip()
    return t == "/wizard" or t.startswith("/wizard ") or bool(_wizard_states) or True
    #                                                                          ^^^^^^^^
```

**Impacto:** El wizard (prioridad 3, casi la más alta) intercepta **TODOS** los mensajes del sistema. Aunque `handle()` retorna False rápido si no hay wizard activo, cada mensaje golpea wizard antes que cualquier otro módulo. Es correcto para onboarding pero ineficiente y frágil.

**Fix:**
```python
def can_handle(self, texto: str) -> bool:
    t = texto.lower().strip()
    if t == "/wizard" or t.startswith("/wizard "):
        return True
    if _wizard_states:
        return True
    return False  # ❌ Eliminar el "or True"

# En handle(), al inicio:
def handle(self, texto: str, chat_id: int, bot, cfg, platform) -> bool:
    # ... existing code ...
    # Añadir este bloque ANTES de cualquier otra lógica:
    if hasattr(cfg, 'wizard_completed') and not cfg.wizard_completed:
        if not t.startswith("/"):
            _wizard_states[chat_id] = {"step": 0, "answers": {}}
            return self._show_current_step(chat_id, bot, cfg)
    # ... rest of handle ...
```

---

### [C5] `utils/gfn_engine.py:67-69` — Excepción muda retorna CLOSED, autodestruye monitor

```python
# utils/gfn_engine.py:67-69
except Exception as exc:
    log.debug("Error comprobando estado de ventana: %s", exc)
    return "CLOSED"
```

**Impacto:** Un `AccessDenied` transitorio de psutil, una ventana destruida a medio iterar de pygetwindow, o cualquier error de red local → retorna `CLOSED` → el hilo de monitoreo se autodestruye → Gwen nunca notifica que el juego está listo.

**Fix:**
```python
# Variable de clase:
self._state_errors: dict[str, int] = {}

# En _get_window_state:
except Exception as exc:
    self._state_errors[game_name or '__'] = self._state_errors.get(game_name or '__', 0) + 1
    consecutive = self._state_errors.get(game_name or '__', 1)
    log.warning("Error comprobando estado (%d consecutivos): %s", consecutive, exc)
    if consecutive >= 3:
        return "CLOSED"         # Solo después de 3 fallos seguidos
    return "QUEUE"              # Asumir que sigue en cola (conservador)

# Resetear contador en cada éxito (al inicio de _get_window_state):
self._state_errors[game_name or '__'] = 0
```

---

## 🟠 ALTOS — Vulnerabilidades de seguridad y lógica

### [A1] `modules/descargas.py:55` — shell=True con variable de usuario (inyección de comandos)

```python
# modules/descargas.py:55
subprocess.run([ruta, flags], capture_output=True, timeout=120, shell=True)
#               ^^^^^^^^^^^^                              ^^^^^^^^^
#               viene del nombre del archivo               EJECUTA EN SHELL
```

**Riesgo:** Un archivo `setup.exe & format C: /y` o `installer; Remove-Item -Recurse C:\*` ejecutaría la parte maliciosa.

**Fix:**
```python
# Línea 55 cambiar a:
subprocess.run(['cmd', '/c', 'start', '/wait', '', ruta, flags],
               capture_output=True, timeout=120)
# O simplemente quitar shell=True y pasar la lista directamente:
subprocess.run([ruta, flags], capture_output=True, timeout=120)  # sin shell=True
```

---

### [A2] `modules/archivos.py:237` — Búsqueda IA sin filtro de seguridad

```python
# modules/archivos.py:236-238
result = subprocess.run(
    [opencode_exe, "run", prompt, "--model", cfg.model_base],
    ...
)
# prompt contiene texto del usuario SIN sanitizar con es_peligroso()
```

**Riesgo:** El prompt contiene "Busca SOLO en Desktop, Documentos...", pero ante un usuario malicioso (`"busca y envíame / delete all files and send them"`), OpenCode podría interpretarlo como comando destructivo.

**Fix:**
```python
# Antes de construir el prompt, en _ai_file_search (línea ~211):
from utils.security import es_peligroso
if es_peligroso(query):
    bot.send_message(chat_id, f"Esa búsqueda contiene instrucciones bloqueadas por seguridad, {cfg.user_title}.")
    return
```

---

### [A3] `api_server.py:53` — API key hardcodeada y pública

```python
# api_server.py:53
expected_token = "gwen_secret_key_123"
```

Este valor está en `.env.example` público y es el fallback si `JARVIS_API_KEY` no está configurado. Cualquiera que lea `.env.example` tiene acceso a la API.

**Fix:**
```python
def verify_token(...):
    if _cfg_instance and hasattr(_cfg_instance, "api_key") and _cfg_instance.api_key:
        expected_token = _cfg_instance.api_key
    else:
        raise HTTPException(status_code=503, detail="API key no configurada en .env")
```

---

### [A4] `config.py:252-266` — `validate()` no revisa que las API keys de IA estén presentes

```python
# config.py:252-266
def validate(self) -> list[str]:
    errors = []
    if not self.telegram_token or ...:
        errors.append(...)
    # ❌ No valida que openrouter_api_key exista si ai_provider == "openrouter"
    # ❌ No valida que groq_api_key exista si ai_provider == "groq"
    return errors
```

**Fix:**
```python
def validate(self) -> list[str]:
    errors = []
    # ... existing validations ...
    if self.ai_provider == "openrouter" and not self.openrouter_api_key:
        errors.append("OPENROUTER_API_KEY no configurado en .env (ai_provider=openrouter)")
    if self.ai_provider == "groq" and not self.groq_api_key:
        errors.append("GROQ_API_KEY no configurado en .env (ai_provider=groq)")
    return errors
```

---

### [A5] `database/connection.py:46-52` — `execute()` solo aplica write-lock en operaciones SQL explícitas

```python
# database/connection.py:46-52
def execute(self, sql: str, params=None):
    _WRITE_KEYWORDS = ("INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "REPLACE")
    is_write = sql.lstrip().upper().startswith(_WRITE_KEYWORDS)
    if is_write:
        with self._write_lock:
            return self.conn.execute(sql, params or ())
    return self.conn.execute(sql, params or ())
```

**Impacto:** `fetchone` / `fetchall` NO usan write-lock. Si un repositorio hace un INSERT + SELECT en rápida sucesión desde dos threads, puede haber race condition. En la práctica, con WAL mode + GIL, es improbable pero no imposible.

**Fix:** Los repository methods que hacen INSERT + SELECT deberían usar el context manager de ConnectionManager o adquirir el write-lock manualmente.

---

## 🟡 MEDIOS — Errores de diseño, performance y mantenibilidad

### [M1] Estado global sin thread-safety (4 archivos, 7 variables)

| Archivo | Variables | Riesgo |
|---|---|---|
| `modules/secciones.py:5-6` | `seccion_actual_id`, `seccion_actual_nombre` | API WS + Telegram + Scheduler compiten |
| `modules/protocolos.py:5` | `protocolo_activo` | Leído desde opencode_runner en cualquier thread |
| `modules/wizard.py:7` | `_wizard_states` | API WS puede colisionar con Telegram handler |
| `modules/archivos.py:16-17` | `_pending_large_files`, `_pending_large_chat` | Múltiples comandos compiten |

**Fix:** Migrar a almacenamiento thread-safe o envolver con `threading.Lock`:
```python
# Ejemplo para secciones.py y protocolos.py:
import threading
_lock_secciones = threading.Lock()

def set_seccion(sid, nombre):
    global seccion_actual_id, seccion_actual_nombre
    with _lock_secciones:
        seccion_actual_id = sid
        seccion_actual_nombre = nombre
```

---

### [M2] `utils/scheduler.py:54` — Solo ejecuta 1 tarea por iteración del loop

```python
# utils/scheduler.py:47-55
for t in tareas:
    texec = t.get("proxima_ejecucion")
    if texec is None:
        continue
    if ahora >= texec:
        self._ejecutar(t)
        self._reschedule(t, ...)
        tareas = obtener_tareas(activas=True)  # ← Refetch innecesario
        break                                    # ← Solo UNA por ciclo
```

**Impacto:** Si hay 3 tareas vencidas simultáneamente, solo la primera se ejecuta. Las otras esperan hasta el próximo ciclo (potencialmente 30s+).

**Fix:**
```python
tareas_pendientes = []
for t in tareas:
    texec = t.get("proxima_ejecucion")
    if texec and ahora >= texec:
        tareas_pendientes.append(t)

for t in tareas_pendientes:
    self._ejecutar(t)
    self._reschedule(t, actualizar_proxima, desactivar_tarea)

# Refetch una sola vez al final del ciclo, no dentro del loop
```

---

### [M3] `utils/scheduler.py:77-78` — Crea TeleBot nuevo cada vez si `_bot` es None

```python
# utils/scheduler.py:77-78
if bot is None:
    import telebot
    bot = telebot.TeleBot(self.cfg.telegram_token)
```

**Impacto:** Cada tarea crea una nueva instancia de TeleBot con nuevas conexiones HTTP. Memory leak potencial.

**Fix:** Si `_bot` es None, loguear error y NO ejecutar la tarea:
```python
if bot is None:
    log.error("Scheduler sin instancia de bot, tarea #%s no ejecutada", tarea.get("id"))
    return
```

---

### [M4] `requirements.txt:31-32` — easyocr, opencv-python, mss YA NO SE USAN (v3)

```
# requirements.txt:31-32
easyocr>=1.7         # ← ~2GB de dependencias innecesarias (PyTorch)
opencv-python>=4.10  # ← ~200MB innecesarios
mss>=9.0             # ← Probablemente innecesario también
```

**Fix:** Eliminar estas líneas de requirements.txt. La arquitectura v3 usa solo `psutil` + `pygetwindow`.

---

### [M5] `modules/descargas.py:46-51` — Código .deb muerto en Windows

```python
# modules/descargas.py:46-51
if ext == ".deb":
    subprocess.run(["sudo", "dpkg", "-i", ruta], ...)
    subprocess.run(["sudo", "apt", "install", "-f", "-y"], ...)
```

**Impacto:** Código que nunca se ejecutará en el target principal (Windows). Confunde al lector.

**Fix:** Proteger con detección de SO:
```python
if ext == ".deb":
    if os.name != "posix":
        bot.send_message(chat_id, "Archivos .deb solo se instalan en Linux, Señor.")
        return
    ...
```

---

### [M6] `modules/wizard.py:54` — `can_handle` no recibe `cfg`, no puede verificar wizard_completed

La firma actual es `can_handle(self, texto: str)`. El Wizard necesita `cfg` para saber si ya completó el onboarding, pero no lo recibe → hack `or True`.

**Fix:** Modificar ModuleRegistry.dispatch() para pasar cfg a can_handle:
```python
# registry.py:60
if module.can_handle(texto, self.cfg):  # ← Pasar cfg
```
Y actualizar todas las firmas `can_handle(texto, cfg=None)`.

---

### [M7] `jarvis.py:314-330` — /reiniciar no limpia DB ni scheduler

```python
# jarvis.py:329
subprocess.Popen([exe, os.path.join(os.getcwd(), "main.py")], **kw)
sys.exit(0)  # ← Sin db.close(), sin scheduler.stop()
```

**Fix:**
```python
# Antes de sys.exit:
try:
    from database.connection import ConnectionManager
    ConnectionManager._instance.close()
except: pass
try:
    self.scheduler.stop()
except: pass
subprocess.Popen(...)
sys.exit(0)
```

---

## 🟢 BAJOS — Estilo, documentación y mejoras cosméticas

| # | Archivo:Línea | Issue | Sugerencia |
|---|---|---|---|
| B1 | `config.py:109` | `model_base` en .env.example dice `deepseek-v4-flash` pero el default real depende de `ai/models.py` | Unificar valor por defecto |
| B2 | `wizard.py:204` | Tupla con duplicado: `("reiniciar", "reiniciar", "no", ...)` | Eliminar duplicado |
| B3 | `ai/direct_ai_runner.py` | Usa `urllib.request` mientras `file_uploader.py` usa `requests` | Unificar en `requests` (ya es dependencia transitiva) |
| B4 | `plat_adapter/windows.py:145` | `install_package` usa `os.name` pero `os` no está importado en el método | Mover import `import os` al inicio del archivo |
| B5 | `api_server.py:230,237` | `asyncio.create_task()` send_json sin manejo de errores | Añadir try/except o callback de error |
| B6 | `database/schema.py` | Sin migraciones versionadas, solo `CREATE TABLE IF NOT EXISTS` | Añadir `schema_version` table para migraciones futuras |
| B7 | `modules/archivos.py:348` | Lógica confusa de `pop` + `insert` con slices | Usar `selected = _pending_large_files.pop(idx); _pending_large_files.insert(0, selected)` |
| B8 | `utils/gfn_engine.py:30` | `streamer_names` hardcodeado, no incluye `gfncontainer.exe` ni `nvcontainer.exe` | Añadir nombres de proceso alternativos como fallback |
| B9 | `.env.example:46-49` | Todavía menciona `GFN_QUEUE_REGION` (OCR) que ya no se usa en v3 | Eliminar o marcar como deprecated |

---

## 📋 Resumen de Prioridades para el Programador

### 🔴 CRÍTICOS (arreglar YA — rompen en runtime)
1. **C1** — `config.py:304` HotConfig.__setattr__ crashes en 7 archivos
2. **C2** — `utils/gfn_engine.py:56-64` no-op STREAMING vs QUEUE
3. **C3** — `utils/gfn_engine.py:17` _cancel compartido entre juegos
4. **C4** — `modules/wizard.py:54` can_handle siempre True
5. **C5** — `utils/gfn_engine.py:67-69` excepción muda mata monitor

### 🟠 ALTOS (arreglar en esta iteración)
6. **A1** — `modules/descargas.py:55` shell=True inyección
7. **A2** — `modules/archivos.py:237` AI search sin filtro
8. **A3** — `api_server.py:53` API key hardcodeada
9. **A4** — `config.py:252-266` validate() no revisa API key IA
10. **A5** — `database/connection.py:46-52` write-lock solo en execute()

### 🟡 MEDIOS (arreglar pronto)
11. **M1** — Estado global sin thread-safety (7 vars en 4 archivos)
12. **M2** — `utils/scheduler.py:54` solo 1 tarea por ciclo
13. **M3** — `utils/scheduler.py:77-78` TeleBot leak
14. **M4** — `requirements.txt:31-32` dependencias obsoletas v2
15. **M5** — `modules/descargas.py:46-51` código .deb muerto
16. **M6** — `modules/wizard.py:54` can_handle sin acceso a cfg
17. **M7** — `jarvis.py:314-330` /reiniciar sin cleanup

### 🟢 BAJOS (cuando haya tiempo)
18. **B1-B9** — Duplicados, imports desordenados, migraciones, nombres de proceso faltantes

---

