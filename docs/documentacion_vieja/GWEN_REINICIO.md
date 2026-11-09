# 🔄 Sistema de Reinicio de Gwen — Análisis completo

> **Para programar con Antigravity (deepseek-v4-flash / deepseek-v4-pro)**

---

## 📐 Diagrama de flujo completo

```
                    ┌──────────────────────────────────┐
                    │       Gwen en ejecución           │
                    │  main.py → JarvisBot → polling    │
                    │  + API Server thread              │
                    │  + Scheduler thread               │
                    │  + SQLite (WAL mode)              │
                    │  + Singleton socket :48729        │
                    └──────────┬───────────────────────┘
                               │
          ┌────────────────────┼────────────────────────┐
          │                    │                        │
     /reiniciar          "reiníciate"             /shutdown confirmar
   (jarvis.py:314)    (reconfig.py:249)          (sistema.py:77)
          │                    │                        │
          ▼                    ▼                        ▼
   _on_reiniciar()     _reiniciar()              handle_shutdown()
          │                    │                        │
          │                    │                        │
   ┌──────▼────────────────────▼────────────────────────▼──────┐
   │               SECUENCIA DE APAGADO                         │
   │                                                           │
   │  1. bot.stop_polling()      ← detiene Telegram            │
   │  2. db.close()  ★           ← cierra SQLite (solo jarvis) │
   │  3. scheduler.stop() ★      ← detiene tareas (solo jarvis)│
   │                                                           │
   └──────────────────────┬────────────────────────────────────┘
                          │
              ┌───────────▼───────────┐
              │ ¿Es shutdown o reinicio?│
              └───────────┬───────────┘
                    │           │
              REINICIO      SHUTDOWN
                    │           │
                    ▼           ▼
          ┌─────────────┐  sys.exit(0)
          │ subprocess   │
          │ Popen main.py│
          └──────┬──────┘
                 │
                 ▼
          ┌──────────────────────────────────┐
          │       NUEVA INSTANCIA            │
          │                                  │
          │  main.py                         │
          │  ├─ _asegurar_instancia_unica()  │ ← socket :48729
          │  │   old process died → socket   │
          │  │   freed → bind OK             │
          │  ├─ JarvisConfig().validated()   │
          │  ├─ HotConfig(cfg)               │
          │  ├─ setup_logging()              │
          │  ├─ ConnectionManager(db_path)   │
          │  ├─ JarvisBot(hot_cfg)           │
          │  ├─ API Server thread            │
          │  └─ bot.run() → polling          │
          └──────────────────────────────────┘
```

---

## 🔀 Tres caminos de reinicio/apagado

### Camino 1: `/reiniciar` desde Telegram

| Paso | Archivo:Línea | Acción |
|------|---------------|--------|
| Trigger | `jarvis.py:28` | Comando `/reiniciar` registrado |
| Handler | `jarvis.py:314` | `_on_reiniciar(message)` |
| 1 | `317-320` | `bot.stop_polling()` — detiene escucha Telegram |
| 2 | `321-325` | `ConnectionManager._instance.close()` — cierra SQLite |
| 3 | `326-330` | `self.scheduler.stop()` — detiene hilo tareas |
| 4 | `331-335` | Determina ejecutable: `pythonw.exe` sobre `python.exe` |
| 5 | `336-339` | `subprocess.Popen([exe, "main.py"])` — lanza nueva instancia |
| 6 | `340` | `sys.exit(0)` — sale del proceso actual |

```python
# jarvis.py:314-340 — _on_reiniciar()
def _on_reiniciar(self, message) -> None:
    self.bot.reply_to(message, "Reiniciando, Señor.")
    import subprocess, sys, os
    try:
        self.bot.stop_polling()
    except Exception:
        pass
    try:
        from database.connection import ConnectionManager
        ConnectionManager._instance.close()   # ← CIERRA DB
    except Exception:
        pass
    try:
        if hasattr(self, "scheduler") and self.scheduler:
            self.scheduler.stop()             # ← DETIENE SCHEDULER
    except Exception:
        pass
    exe = sys.executable
    if exe.endswith("python.exe"):
        pyw = exe[:-10] + "pythonw.exe"       # ← prefiere sin consola
        if os.path.isfile(pyw):
            exe = pyw
    kw = {"cwd": os.getcwd()}
    if os.name == "nt":
        kw["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    subprocess.Popen([exe, os.path.join(os.getcwd(), "main.py")], **kw)
    sys.exit(0)
```

### Camino 2: "reiníciate" por lenguaje natural

| Paso | Archivo:Línea | Acción |
|------|---------------|--------|
| Trigger | `reconfig.py:31` | Palabras clave: `"reiníciate", "reiniciate", "reiniciar"` |
| Handler | `reconfig.py:118` | `self._reiniciar(bot, cfg)` |
| 1 | `253-256` | `bot.stop_polling()` |
| 2 | `257-262` | Determina ejecutable: `pythonw.exe` sobre `python.exe` |
| 3 | `263-266` | `subprocess.Popen([exe, "main.py"])` |
| 4 | `267` | `sys.exit(0)` |
| ⚠ | — | **NO cierra DB, NO detiene scheduler** |

```python
# reconfig.py:249-267 — _reiniciar()
def _reiniciar(self, bot, cfg=None) -> None:
    import subprocess, sys, os
    try:
        bot.stop_polling()
    except Exception:
        pass
    cwd = str(cfg.project_root) if cfg and hasattr(cfg, 'project_root') else os.getcwd()
    exe = sys.executable
    if exe.endswith("python.exe"):
        pyw = exe[:-10] + "pythonw.exe"
        if os.path.isfile(pyw):
            exe = pyw
    kw = {"cwd": cwd}
    if os.name == "nt":
        kw["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    subprocess.Popen([exe, os.path.join(cwd, "main.py")], **kw)
    sys.exit(0)
    # ⚠ M7: No cierra DB ni detiene scheduler
```

### Camino 3: `/shutdown confirmar` (apagado definitivo)

| Paso | Archivo:Línea | Acción |
|------|---------------|--------|
| Trigger | `jarvis.py:57` | Comando `/shutdown` |
| Handler | `sistema.py:77` | `handle_shutdown(message, bot, cfg, scheduler)` |
| 1 | `87-88` | `scheduler.stop()` — detiene hilo tareas |
| 2 | `89` | `bot.stop_polling()` |
| 3 | `90-91` | `sys.exit(0)` — sale sin relanzar |
| ⚠ | — | **NO cierra DB** |

```python
# sistema.py:77-91 — handle_shutdown()
def handle_shutdown(message, bot, cfg, scheduler) -> None:
    texto = (message.text or "").strip().lower()
    if "/shutdown confirmar" not in texto:
        bot.reply_to(message, "Debe confirmar con /shutdown confirmar")
        return
    bot.reply_to(message, f"Apagando Gwen. Hasta la próxima, Señor.")
    if scheduler:
        scheduler.stop()
    bot.stop_polling()
    import sys
    sys.exit(0)
```

---

## 🔐 Singleton: prevención de instancias duplicadas

```python
# main.py:14-22 — _asegurar_instancia_unica()
def _asegurar_instancia_unica(port: int = 48729) -> bool:
    global _SINGLETON_SOCKET
    import socket
    try:
        _SINGLETON_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _SINGLETON_SOCKET.bind(("127.0.0.1", port))  # ← lock exclusivo
        return True
    except OSError:
        return False  # ← YA hay otra instancia corriendo
```

**Mecanismo:** El primer proceso bindea el puerto `127.0.0.1:48729`. Si otro proceso intenta arrancar, el `bind()` falla → `_notificar_duplicado()` muestra MessageBox "Gwen ya se encuentra en línea" y sale.

**En reinicio:** El proceso viejo hace `sys.exit(0)` → el kernel libera el socket automáticamente → el nuevo proceso puede bindear sin problema. La ventana de colisión es < 1ms.

**Puerto:** Hardcodeado a `48729`. No configurable desde `.env`.

---

## 🧵 Hilos que deben morir y renacer en un reinicio

| Hilo | Dueño | Creado en | Muerto por | ¿Se limpia bien? |
|------|-------|-----------|------------|------------------|
| Telegram polling | TeleBot | `bot.infinity_polling()` | `bot.stop_polling()` | ✅ Sí |
| Scheduler | TaskScheduler | `jarvis.py:81` | `scheduler.stop()` | ✅ Solo en `/reiniciar` |
| API Server | FastAPI/uvicorn | `main.py:71` (daemon) | `sys.exit()` del padre | ✅ Al ser daemon |
| GFN monitor | GFNEngine | `geforcenow.py:72` (daemon) | Autodestrucción o `sys.exit()` | ✅ Al ser daemon |
| Subprocess OpenCode | opencode_runner | `opencode_runner.py:59` | Timeout o `sys.exit()` | ⚠ Puede quedar zombie |
| Subprocess FFmpeg | pydub | `voz.py:61` (transitorio) | Se completa solo | ✅ |

---

## ⚠️ Riesgos y bugs identificados

### M7 (Medio): `_reiniciar()` de ReconfigModule no limpia DB ni scheduler

**Archivo:** `modules/reconfig.py:249-267`
**Impacto:** Si el usuario dice "reiníciate" en vez de usar `/reiniciar`, la DB no se cierra limpiamente. En WAL mode SQLite sobrevive, pero el scheduler no se detiene y su hilo daemon puede competir con la nueva instancia por las tareas programadas.

**Fix:**
```python
def _reiniciar(self, bot, cfg=None) -> None:
    # ... código existente hasta bot.stop_polling() ...
    try:
        from database.connection import ConnectionManager
        ConnectionManager._instance.close()
    except Exception:
        pass
    # ... resto del código ...
```

### M7b (Medio): `/shutdown confirmar` no cierra DB

**Archivo:** `modules/sistema.py:77-91`
**Impacto:** Al apagar definitivamente, la conexión SQLite queda abierta al hacer `sys.exit()`. El WAL checkpoint puede no completarse, dejando datos en el `.db-wal` sin consolidar.

**Fix:**
```python
def handle_shutdown(message, bot, cfg, scheduler) -> None:
    # ... validación ...
    if scheduler:
        scheduler.stop()
    bot.stop_polling()
    try:
        from database.connection import ConnectionManager
        ConnectionManager._instance.close()
    except Exception:
        pass
    sys.exit(0)
```

### Riesgo: Subprocess OpenCode zombie en reinicio

Si Gwen está ejecutando `opencode run` (por AI fallback o búsqueda de archivos) y se reinicia, el proceso hijo de OpenCode **no se mata automáticamente** con `sys.exit()`. En Windows, `subprocess.Popen` sin `start_new_session` no garantiza que el hijo muera.

**Mitigación actual:** `opencode_runner.py` usa `timeout=cfg.opencode_timeout` (300s por defecto), así que eventualmente muere por timeout. Pero durante el reinicio, puede quedar huérfano consumiendo recursos.

**Fix sugerido:** Guardar referencias a todos los `Popen` activos en una lista global y hacer `.terminate()` antes del `sys.exit()`.

---

## 🚀 Flujo de arranque (main.py)

```
main.py:main()
  │
  ├─ 1. _asegurar_instancia_unica()    → bind puerto :48729
  │     └─ Si falla → _notificar_duplicado() → MessageBox → exit
  │
  ├─ 2. os.chdir(project_root)         → directorio del proyecto
  │
  ├─ 3. JarvisConfig().validated()     → carga .env + valida
  │
  ├─ 4. HotConfig(cfg)                 → carga overrides de config_override.json
  │
  ├─ 5. setup_logging()                → consola + rotating file
  │
  ├─ 6. cfg.ensure_dirs()             → data/, descargas/, cache/, ...
  │
  ├─ 7. ConnectionManager(db_path)     → abre SQLite + WAL + schema
  │
  ├─ 8. JarvisBot(hot_cfg)            → crea bot, autorizador, registry
  │
  ├─ 9. API Server (thread daemon)    → FastAPI en :8000
  │
  └─ 10. bot.run()                    → scheduler.start() + infinity_polling()
```

---

## 📋 Secuencia ideal de reinicio (referencia para Antigravity)

```python
def reiniciar_gwen(bot, cfg):
    """Implementación de referencia — junta lo mejor de los 3 caminos."""
    import subprocess, sys, os

    # Fase 1: Notificar
    bot.send_message(cfg.telegram_chat_id, "Reiniciando, Señor.")

    # Fase 2: Detener servicios activos
    try:
        bot.stop_polling()
    except Exception:
        pass
    try:
        if hasattr(bot, 'scheduler') and bot.scheduler:
            bot.scheduler.stop()
    except Exception:
        pass

    # Fase 3: Cerrar base de datos limpiamente
    try:
        from database.connection import ConnectionManager
        ConnectionManager._instance.close()
    except Exception:
        pass

    # Fase 4: Matar subprocesos hijos (OpenCode, FFmpeg, etc)
    import psutil
    current = psutil.Process()
    for child in current.children(recursive=True):
        try:
            child.terminate()
        except Exception:
            pass

    # Fase 5: Relanzar
    exe = sys.executable
    if exe.endswith("python.exe"):
        pyw = exe[:-10] + "pythonw.exe"
        if os.path.isfile(pyw):
            exe = pyw
    kw = {"cwd": os.getcwd()}
    if os.name == "nt":
        kw["creationflags"] = subprocess.CREATE_NO_WINDOW
    subprocess.Popen([exe, os.path.join(os.getcwd(), "main.py")], **kw)
    sys.exit(0)
```

---

## 🎯 Lo que Antigravity necesita saber para modificar este sistema

| ¿Qué quieres hacer? | Archivos a tocar | Nivel de riesgo |
|---|---|---|
| Cambiar el puerto singleton | `main.py:17` (cambiar `48729`) | Bajo |
| Agregar limpieza a shutdown | `modules/sistema.py:77-91` | Bajo |
| Arreglar M7 en reconfig | `modules/reconfig.py:249-267` | Bajo |
| Matar subprocesos en reinicio | `jarvis.py:314-340` | Medio (psutil requerido) |
| Cambiar pythonw → python | `jarvis.py:332-335` + `reconfig.py:259-262` | Bajo |
| Agregar confirmación al reinicio | `jarvis.py:314` (agregar check antes de reply) | Bajo |
| Hacer el puerto configurable | `main.py:14-22` + `config.py` + `.env.example` | Medio |
| Graceful shutdown con timeout | `jarvis.py:314-340` | Medio |
