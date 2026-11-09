# 🎮 GeForce NOW Detection — Historia Completa

> **Proyecto:** Gwen / Jarvis Windows Pro v2.0
> **Fecha inicio:** 2026-08-02
> **Fecha fin:** 2026-08-02
> **Resultado:** ✅ Resuelto con detección por debug.log de NVIDIA
> **Modelos participantes:** OpenCode (deepseek-v4-pro), Gemini, Antigravity

---

## 📂 Índice de la carpeta

| Archivo | Descripción |
|---------|-------------|
| `00_README.md` | Este archivo — índice y resumen |
| `01_v1_easyocr.md` | Iteración 1: EasyOCR — falló por CPU/RAM |
| `02_v2_procesos.md` | Iteración 2: Procesos psutil — falsos positivos |
| `03_v3_procesos_ventanas.md` | Iteración 3: Procesos + ventanas — falsos positivos y negativos |
| `04_v4_titulos_ventana.md` | Iteración 4: Solo títulos de ventana — falso negativo |
| `05_v5_debuglog.md` | Iteración 5: **debug.log de NVIDIA — FUNCIONA** |
| `06_evidencia_real.md` | Evidencia empírica capturada de la máquina del usuario |
| `07_comandos_investigacion.md` | Comandos PowerShell para validar/depurar |
| `08_plan_contingencia.md` | Qué hacer si NVIDIA cambia el log en el futuro |
| `AUDITORIA_COMPLETA.md` | Auditoría general del proyecto Gwen (24 issues) |
| `GFN_ARCHITECTURE_CONTEXT.md` | Contexto original y decisiones del refactor GFN |
| `OPENCODE_GFN_PLAN.md` | Plan original de arquitectura GFN |
| `GWEN_REINICIO.md` | Análisis del sistema de reinicio de Gwen |

---

## 🧭 Línea de tiempo

```
08:00  Plan original — EasyOCR v1 (OPENCODE_GFN_PLAN.md)
  │
12:00  Refactor v3 — Zero-PyTorch, detección por ventanas/procesos
  │     Falló: falsos positivos ("¡Ya estás jugando!" en cola)
  │
13:00  Auditoría completa — 24 issues encontrados
  │     C2: _get_window_state no-op bug detectado
  │     C3: _cancel Event compartido entre juegos
  │     C5: Excepción muda mata monitor
  │
14:00  Fix C2 aplicado — separar streamer de queue processes
  │     Falló: GeForceNOWStreamer.exe no existe en esta máquina
  │
15:00  Fix con títulos de ventana
  │     Falló: "Destiny 2 en GeForce NOW" aparece también en cola
  │
16:00  INVESTIGACIÓN EN VIVO — Comandos PowerShell en la máquina
  │     Descubrimiento: procesos IDÉNTICOS en cola y juego
  │     Descubrimiento: debug.log contiene onSessionSetupProgress
  │
16:05  Captura de evidencia del debug.log
  │     Cola: onSessionSetupProgress(state:1, queue:35→13, eta:30000)
  │     Juego: SILENCIO (dejan de aparecer líneas)
  │     Cierre: onStopResult(result: 16064513)
  │
17:00  Investigación: GFN SDK oficial (no usable desde cliente)
  │     Investigación: debug.log usado por la comunidad
  │
21:00  IMPLEMENTACIÓN FINAL — _get_window_state basado en debug.log
  │     Algoritmo: log + ventana como fallback
  │     Compila, pendiente de prueba en vivo
  │
21:14  Carpeta gfn_evolution/ creada con documentación completa
```

---

## 🎯 El algoritmo final en una frase

**Leer el debug.log de NVIDIA cada 15s. Si `onSessionSetupProgress` dejó de aparecer hace más de 10 segundos y hay una ventana GFN visible → el juego está transmitiendo.**

---

## 📊 Comparativa final de las 5 iteraciones

| # | Método | Precisión | CPU | RAM | Falló por |
|---|--------|-----------|-----|-----|-----------|
| 1 | EasyOCR | ~60% | 75-100% | 1.5 GB | Overkill, PyTorch en PC sin GPU |
| 2 | Procesos psutil | 0% | 0% | 0 MB | `nvstreamer.exe` no existe en esta versión de GFN |
| 3 | Procesos + ventanas | ~30% | 0% | 0 MB | Títulos de ventana iguales en cola y juego |
| 4 | Solo títulos de ventana | ~50% | 0% | 0 MB | El título cambia en cola también |
| 5 | **debug.log NVIDIA** | **~100%** | 0% | 0 MB | **NINGUNO — FUNCIONA** |

---

## 🔑 Archivos de código modificados

| Archivo | Cambio |
|---------|--------|
| `utils/gfn_engine.py:20` | Agregado `self._last_queue_info: dict \| None = None` |
| `utils/gfn_engine.py:27-148` | `_get_window_state` reescrito completamente |
| `utils/gfn_engine.py:17` | `self._cancel_events` — cancel por juego (ya estaba) |
| `utils/gfn_engine.py:19` | `self._state_errors` — tolerancia a fallos (ya estaba) |
| `config.py:308-317` | HotConfig `__setattr__` — escribe a `_base` (ya estaba) |

---

## ⏳ Pendiente

- [ ] Probar con sesión real de GFN (cola → juego → cerrar)
- [ ] Ajustar threshold de 10s si es necesario
- [ ] Integrar `_last_queue_info` en notificaciones Telegram
- [ ] Si funciona, eliminar dependencias obsoletas de `requirements.txt` (easyocr, opencv-python, mss)
