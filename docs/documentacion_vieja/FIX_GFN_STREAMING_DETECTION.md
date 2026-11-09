# Fix: GFN no detecta transición cola → juego

> **Bug:** Gwen dice "estás en cola" cuando Destiny 2 YA está transmitiendo
> **Causa:** `_get_window_state` exige que el título de ventana contenga el nombre del juego. GFN mantiene "NVIDIA GeForce NOW" como título al entrar al juego.
> **Archivo a modificar:** `utils/gfn_engine.py`

---

## Reemplazar completo `_get_window_state` (líneas ~27-91)

Buscar el método `_get_window_state` y reemplazarlo COMPLETO por esto:

```python
    # ── Detección Ultra-Liviana por Capa de Ventana y Proceso (0% CPU / 0 MB RAM) ──

    # Procesos que indican renderizado REAL del juego (solo activos cuando el juego transmite)
    _STREAMER_PROCESSES = ("geforcenowstreamer.exe",)
    # Procesos que NVIDIA levanta durante la cola/preparación (NO indican que el juego esté listo)
    _QUEUE_PROCESSES = ("nvstreamer.exe", "gfnruntime.exe", "gfncontainer.exe", "nvcontainer.exe")

    def _get_window_state(self, game_name: str | None = None) -> str:
        """Determina el estado real de la sesión GFN.
        Retorna: 'STREAMING', 'QUEUE', o 'CLOSED'."""
        key = (game_name or "__global__").lower()
        try:
            import pygetwindow as gw
            import psutil

            has_streamer = False
            has_queue_process = False

            for p in psutil.process_iter(["name"]):
                try:
                    name = (p.info.get("name") or "").lower()
                    if name in self._STREAMER_PROCESSES:
                        has_streamer = True
                    elif name in self._QUEUE_PROCESSES:
                        has_queue_process = True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            game_keywords = []
            if game_name:
                game_keywords = [w.lower() for w in game_name.split() if len(w) > 2]

            has_large_gfn_window = False
            has_small_gfn_window = False
            has_game_named_window = False

            for win in gw.getAllWindows():
                if not win.visible or win.isMinimized:
                    continue
                w_title = win.title.lower()

                is_gfn = ("geforce now" in w_title or "nvidia geforce now" in w_title
                          or "nvidia games" in w_title)

                if is_gfn:
                    if win.width >= 1280 and win.height >= 700:
                        has_large_gfn_window = True
                    else:
                        has_small_gfn_window = True

                if game_keywords and any(k in w_title for k in game_keywords):
                    if win.width >= 1280 and win.height >= 700:
                        has_game_named_window = True

            self._state_errors[key] = 0

            # STREAMING = renderizador + ventana GFN grande (con o sin nombre del juego)
            if has_streamer and (has_large_gfn_window or has_game_named_window):
                return "STREAMING"

            # Si hay ventana con nombre del juego a fullscreen, también es streaming
            if has_game_named_window:
                return "STREAMING"

            # QUEUE = proceso de preparación o ventana GFN visible
            if has_queue_process or has_small_gfn_window or has_large_gfn_window:
                return "QUEUE"

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

## Qué cambió y por qué

| Situación real | Fix anterior (roto) | Fix nuevo |
|---|---|---|
| Ventana GFN 1920x1080 + streamer.exe | QUEUE (exigía nombre del juego en título) | STREAMING ✓ |
| Ventana GFN 800x600 + streamer.exe | QUEUE | QUEUE ✓ |
| Ventana GFN 800x600 + nvstreamer.exe | QUEUE | QUEUE ✓ |
| Ninguna ventana + nvstreamer.exe | QUEUE | QUEUE ✓ |
| Sin procesos ni ventanas | CLOSED | CLOSED ✓ |

**Razón:** GFN no cambia el título de la ventana al pasar de cola a juego. "NVIDIA GeForce NOW" es el mismo título en ambos estados. Lo único que cambia es: (a) el tamaño de la ventana pasa a pantalla completa, (b) aparece `GeForceNOWStreamer.exe`. El fix ahora detecta **cualquier ventana GFN grande + streamer = STREAMING**, sin exigir que el título contenga el nombre del juego.
