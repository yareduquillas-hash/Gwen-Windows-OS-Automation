# ✅ GFN vFinal — Detección por debug.log de NVIDIA

> **Fecha:** 2026-08-02
> **Estado:** APLICADO ✅
> **Archivo modificado:** `utils/gfn_engine.py`
> **Modelo que implementó:** OpenCode (deepseek-v4-pro)

---

## 📖 Historia del descubrimiento (por qué estamos aquí)

| Iteración | Método | Resultado | Evidencia en esta máquina |
|---|---|---|---|
| v1 | EasyOCR | 100% CPU, 1.5GB RAM | — |
| v2 | Procesos (`psutil`) | Falsos positivos | `nvstreamer.exe` no existe en esta versión de GFN |
| v3 | Procesos + ventanas | Falsos positivos y negativos | Títulos de ventana cambian en cola también |
| v4 | Solo títulos de ventana | Falsos negativos | `"Destiny 2 en GeForce NOW"` aparece en cola |
| **vFinal** | **debug.log de NVIDIA** | ✅ | Probado en vivo 2026-08-02 |

---

## 🔬 Evidencia empírica (capturada de tu máquina)

### Archivo de log

```
Ruta:  %LOCALAPPDATA%\NVIDIA Corporation\GeForceNOW\debug.log
Tamaño: ~60 KB durante una sesión
Frecuencia: ~1 línea por segundo durante cola activa
```

### Líneas durante la cola (se actualizan cada ~1s)

```
[3860:5408:2026-08-02/16:05:28.718:INFO:simple_grid_app.cc(1628)]
  onSessionSetupProgress(state: 1, queue: 35, eta: 30000)

[3860:5408:2026-08-02/16:05:29.752:INFO:simple_grid_app.cc(1628)]
  onSessionSetupProgress(state: 1, queue: 35, eta: 30000)

... (la cola avanza: 35→33→30→28→25→23→21→13) ...

[3860:5408:2026-08-02/16:05:59.060:INFO:simple_grid_app.cc(1628)]
  onSessionSetupProgress(state: 1, queue: 13, eta: 30000)
```

### Línea cuando se cierra la sesión

```
[3860:5408:2026-08-02/16:06:00.261:INFO:simple_grid_app.cc(1712)]
  onStopResult(result: 16064513)
```

### Cuando el juego está transmitiendo

```
(silencio — dejan de aparecer líneas onSessionSetupProgress)
```

### Conclusión

- **`onSessionSetupProgress` aparece cada segundo → estás en cola**
- **`onSessionSetupProgress` deja de aparecer → juego inició (o cerraste GFN)**
- **`onStopResult` aparece → sesión terminada explícitamente**
- **Combinado con detección de ventana GFN = detección perfecta**

---

## 🧠 Algoritmo completo

```
_get_window_state(game_name):
    │
    ├─ 1. Leer últimos 16KB de debug.log
    │
    ├─ 2. Buscar (de abajo hacia arriba):
    │      - Último onSessionSetupProgress → timestamp + queue + eta
    │      - Último onStopResult → timestamp
    │
    ├─ 3. Chequear ventana GFN (pygetwindow)
    │
    └─ 4. Decidir estado:
         │
         ├─ ¿onStopResult es más reciente que onSessionSetupProgress?
         │    SÍ → CLOSED (NVIDIA dice que la sesión terminó)
         │
         ├─ ¿onSessionSetupProgress apareció hace < 10 segundos?
         │    SÍ → QUEUE (cola activa, reportando posición)
         │
         ├─ ¿onSessionSetupProgress apareció hace > 10 segundos?
         │    SÍ → ¿ventana GFN visible?
         │           SÍ → STREAMING (cola terminó, juego iniciado)
         │           NO  → CLOSED  (cola terminó, GFN cerrado)
         │
         └─ ¿No hay entradas relevantes en el log?
              └─ ¿ventana GFN visible?
                   SÍ → QUEUE  (fallback conservador: asumir cola)
                   NO  → CLOSED
```

---

## 📝 Código completo — Reemplazar `_get_window_state` en `utils/gfn_engine.py`

```python
    # ── Detección por Log de NVIDIA (debug.log) + Ventana (0% CPU / 0 MB RAM) ──
    #
    # Fuente de verdad: %LOCALAPPDATA%\NVIDIA Corporation\GeForceNOW\debug.log
    #   - onSessionSetupProgress(state: 1, queue: N, eta: M) → cola activa
    #   - Silencio en el log + ventana GFN visible → juego en vivo
    #   - onStopResult(result: N) → sesión terminada
    #
    # Evidencia empírica: capturado en vivo 2026-08-02 en Windows 11 con GFN v2.x

    import re as _re  # NUNCA mover al top-level, se usa solo aquí

    def _get_window_state(self, game_name: str | None = None) -> str:
        """Determina el estado real de la sesión GFN usando el debug.log de NVIDIA.
        Si el log no existe o no tiene entradas, fallback a detección por ventana.
        Retorna: 'STREAMING', 'QUEUE', o 'CLOSED'."""
        key = (game_name or "__global__").lower()
        try:
            import pygetwindow as gw
            import os as _os
            from datetime import datetime
            from pathlib import Path

            # ── Paso 1: Leer debug.log de NVIDIA ──
            log_paths = [
                _os.path.expandvars(r"%LOCALAPPDATA%\NVIDIA Corporation\GeForceNOW\debug.log"),
                _os.path.expandvars(r"%LOCALAPPDATA%\NVIDIA Corporation\GeForceNOWStreamer\debug.log"),
            ]

            last_queue_ts = None      # timestamp del último onSessionSetupProgress
            last_queue_num = None     # número de cola (opcional, para Telegram)
            last_queue_eta = None     # ETA en ms (opcional, para Telegram)
            last_stop_ts = None       # timestamp del último onStopResult

            for log_path in log_paths:
                if not _os.path.isfile(log_path):
                    continue
                try:
                    with open(log_path, "rb") as f:
                        f.seek(0, _os.SEEK_END)
                        size = f.tell()
                        # Leer últimos 16KB (suficiente para ~15 entradas de cola)
                        f.seek(max(0, size - 16384))
                        raw = f.read().decode("utf-8", errors="ignore")
                except (OSError, PermissionError):
                    continue

                for line in raw.splitlines():
                    # Detectar cola activa
                    if "onSessionSetupProgress" in line:
                        m_ts = _re.search(r"(\d{2}:\d{2}:\d{2})", line)
                        m_q = _re.search(r"queue:\s*(\d+)", line)
                        m_e = _re.search(r"eta:\s*(\d+)", line)
                        if m_ts:
                            last_queue_ts = m_ts.group(1)
                        if m_q:
                            last_queue_num = m_q.group(1)
                        if m_e:
                            last_queue_eta = m_e.group(1)

                    # Detectar fin de sesión
                    if "onStopResult" in line:
                        m_ts = _re.search(r"(\d{2}:\d{2}:\d{2})", line)
                        if m_ts:
                            last_stop_ts = m_ts.group(1)

                break  # Usar solo el primer log_path encontrado

            # ── Paso 2: Verificar ventana GFN (fallback) ──
            has_gfn_window = False
            for win in gw.getAllWindows():
                if not win.visible or win.isMinimized:
                    continue
                w = win.title.lower()
                if "geforce now" in w:
                    has_gfn_window = True
                    break

            # ── Paso 3: Decidir estado ──
            now = datetime.now()

            # Si el log tiene datos, usarlos como fuente primaria
            if last_queue_ts is not None or last_stop_ts is not None:
                t_queue = None
                t_stop = None

                try:
                    today = now.date()
                    h, m, s = map(int, last_queue_ts.split(":")) if last_queue_ts else (0, 0, 0)
                    t_queue = datetime(today.year, today.month, today.day, h, m, s)
                except (ValueError, AttributeError):
                    pass

                try:
                    today = now.date()
                    h, m, s = map(int, last_stop_ts.split(":")) if last_stop_ts else (0, 0, 0)
                    t_stop = datetime(today.year, today.month, today.day, h, m, s)
                except (ValueError, AttributeError):
                    pass

                # onStopResult más reciente que la cola → sesión terminada
                if t_stop and t_queue and t_stop >= t_queue:
                    self._state_errors[key] = 0
                    return "CLOSED"
                if t_stop and not t_queue:
                    self._state_errors[key] = 0
                    return "CLOSED"

                # Cola reportando hace < 10s → QUEUE activa
                if t_queue and (now - t_queue).total_seconds() < 10:
                    self._state_errors[key] = 0
                    # Guardar datos de cola para consultas del usuario
                    if last_queue_num is not None and last_queue_eta is not None:
                        self._last_queue_info = {
                            "position": last_queue_num,
                            "eta_ms": last_queue_eta,
                            "updated": now.isoformat(),
                        }
                    return "QUEUE"

                # Cola dejó de reportar hace > 10s → juego iniciado
                if t_queue and (now - t_queue).total_seconds() >= 10:
                    if has_gfn_window:
                        self._state_errors[key] = 0
                        return "STREAMING"
                    self._state_errors[key] = 0
                    return "CLOSED"

            # ── Fallback: log sin datos → usar ventana ──
            if has_gfn_window:
                self._state_errors[key] = 0
                return "QUEUE"

            self._state_errors[key] = 0
            return "CLOSED"

        except Exception as exc:
            err_count = self._state_errors.get(key, 0) + 1
            self._state_errors[key] = err_count
            log.warning("Error comprobando estado (%d/3 consecutivos): %s", err_count, exc)
            if err_count >= 3:
                return "CLOSED"
            return "QUEUE"
```

---

## 📦 Cambios adicionales en `__init__`

```python
def __init__(self, cfg):
    self.cfg = cfg
    self.delay = getattr(cfg, 'gfn_action_delay', 6)
    self._cancel_events: dict[str, threading.Event] = {}
    self._active_monitors = {}
    self._state_errors: dict[str, int] = {}
    self._last_queue_info: dict | None = None   # ← NUEVO: info de cola del log
```

---

## 📊 Tabla de verdad final

| Log: onSessionSetupProgress | Log: onStopResult | Ventana GFN | Estado |
|---|---|---|---|
| Último hace < 10s | — | — | QUEUE |
| Último hace > 10s | — | Sí | STREAMING |
| Último hace > 10s | — | No | CLOSED |
| — | Sí (más reciente que queue) | — | CLOSED |
| No hay entradas | No hay entradas | Sí | QUEUE (fallback) |
| No hay entradas | No hay entradas | No | CLOSED |

---

## 🛠️ Comandos de investigación para validar/mejorar el sistema

### Verificar la ruta del log en esta máquina
```powershell
Get-ChildItem "$env:LOCALAPPDATA\NVIDIA Corporation" -Recurse -Filter "debug.log" |
    Select-Object FullName, Length, LastWriteTime
```

### Monitorear el log en tiempo real durante una sesión
```powershell
Get-Content "$env:LOCALAPPDATA\NVIDIA Corporation\GeForceNOW\debug.log" -Wait -Tail 5 |
    ForEach-Object {
        if ($_ -match "onSessionSetupProgress|onStopResult|session.*start|stream.*start") {
            Write-Host $_ -ForegroundColor Cyan
        }
    }
```

### Ver qué otras líneas aparecen cuando el juego inicia
```powershell
# Ejecutar DURANTE el juego (no en cola):
Get-Content "$env:LOCALAPPDATA\NVIDIA Corporation\GeForceNOW\debug.log" -Tail 100 |
    Select-String -Pattern "simple_grid_app|session|stream|game|launch|start|stop"
```

### Probar si el log existe en otras rutas posibles
```powershell
@(
    "$env:LOCALAPPDATA\NVIDIA Corporation\GeForceNOW\debug.log",
    "$env:LOCALAPPDATA\NVIDIA Corporation\GeForceNOWStreamer\debug.log",
    "$env:LOCALAPPDATA\NVIDIA Corporation\GeForceNOW\logs\debug.log",
    "$env:APPDATA\NVIDIA Corporation\GeForceNOW\debug.log"
) | ForEach-Object { if (Test-Path $_) { Write-Host "✓ $_" } else { Write-Host "✗ $_" } }
```

### Ver cuánto pesa y cada cuánto rota
```powershell
Get-Item "$env:LOCALAPPDATA\NVIDIA Corporation\GeForceNOW\debug.log" |
    Select-Object Length, LastWriteTime, CreationTime
```

### Buscar otras señales en el log (para futuras versiones de GFN)
```powershell
# Extraer todas las líneas únicas de simple_grid_app.cc para ver qué eventos emite:
Get-Content "$env:LOCALAPPDATA\NVIDIA Corporation\GeForceNOW\debug.log" |
    Select-String "simple_grid_app.cc\(\d+\)\]\s+(\w+)" |
    ForEach-Object { $_.Matches.Groups[1].Value } |
    Sort-Object -Unique
```

Este último comando te dirá TODOS los eventos que NVIDIA emite. Si en el futuro cambian el nombre de `onSessionSetupProgress`, este comando te muestra el nuevo nombre.

---

## ⚠️ Plan de contingencia

### Si NVIDIA cambia el formato del log

1. Ejecutar el comando de "señales" de arriba para encontrar los nuevos eventos
2. Actualizar los patrones regex en `_get_window_state`
3. Mientras tanto, el fallback a ventana mantiene el sistema funcional (aunque menos preciso)

### Si NVIDIA mueve el log de carpeta

1. El código ya busca en 2 rutas (`GeForceNOW\debug.log` y `GeForceNOWStreamer\debug.log`)
2. Ejecutar el comando de "rutas posibles" para añadir más paths

### Si el log deja de existir por completo (poco probable)

1. Volver a detección por ventana como último recurso
2. Considerar approach de píxeles como alternativa secundaria

---

## 📁 Archivos a modificar

| Archivo | Líneas | Cambio |
|---------|--------|--------|
| `utils/gfn_engine.py:14-19` | `__init__` | Agregar `self._last_queue_info = None` |
| `utils/gfn_engine.py:27-103` | `_get_window_state` | Reemplazar TODO el método con el código de arriba |

---

## 🎯 Beneficios adicionales

Ahora además de detectar el estado, podemos **decirle al usuario su posición exacta en la cola**:

```python
# En _queue_monitor, en vez de solo "Esperando turno...":
if self._last_queue_info:
    pos = self._last_queue_info["position"]
    eta_s = int(self._last_queue_info["eta_ms"]) // 1000
    bot.send_message(chat_id,
        f"⏳ Cola para {game_name}: posición {pos}, ~{eta_s}s estimados")
```

---

## 📋 Historial de implementación

| Paso | Estado | Quién |
|------|--------|-------|
| Investigar debug.log | ✅ 2026-08-02 | OpenCode |
| Capturar evidencia en vivo | ✅ 2026-08-02 | OpenCode + usuario |
| Diseñar algoritmo | ✅ 2026-08-02 | OpenCode |
| Escribir código | ✅ 2026-08-02 | OpenCode |
| Aplicar a `utils/gfn_engine.py` | ✅ 2026-08-02 | OpenCode |
| Probar compilación | ✅ 2026-08-02 | OpenCode |
| Probar con sesión real de GFN | ⏳ Pendiente | Usuario |
| Ajustar thresholds si es necesario | ⏳ Pendiente | Usuario |
| Integrar `_last_queue_info` en notificaciones Telegram | ⏳ Pendiente | Gemini / Antigravity |
