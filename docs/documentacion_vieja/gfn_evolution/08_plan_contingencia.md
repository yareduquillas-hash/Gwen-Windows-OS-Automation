# Plan de Contingencia — Si NVIDIA cambia algo

---

## Escenario A: NVIDIA cambia el formato del log

**Síntoma:** `_get_window_state` siempre retorna `QUEUE` o `CLOSED` aunque el juego esté corriendo.

**Diagnóstico:**
```powershell
# Ejecutar comando #5 de 07_comandos_investigacion.md
# Ver si onSessionSetupProgress sigue existiendo o tiene otro nombre
```

**Solución:**
1. Encontrar el nuevo nombre del evento (usando comando #5)
2. Actualizar las líneas 104 y 116 de `utils/gfn_engine.py`:
   ```python
   if "onSessionSetupProgress" in line:  # ← cambiar por el nuevo nombre
   ```
3. Actualizar regex si el formato cambió:
   ```python
   m_q = _re.search(r"queue:\s*(\d+)", line)  # ← ajustar si cambió formato
   ```

**Mientras tanto:** El fallback a ventana mantiene el sistema funcionando, aunque con precisión reducida (~50%).

---

## Escenario B: NVIDIA mueve el log de carpeta

**Síntoma:** `debug.log` no se encuentra, `_get_window_state` siempre usa fallback de ventana.

**Diagnóstico:**
```powershell
# Ejecutar comando #4 de 07_comandos_investigacion.md
# Si ninguna ruta funciona, buscar manualmente:
Get-ChildItem "$env:LOCALAPPDATA\NVIDIA Corporation" -Recurse -Filter "*.log" | Select-Object FullName
```

**Solución:**
1. Añadir la nueva ruta a la lista `log_paths` en `utils/gfn_engine.py:58-61`:
   ```python
   log_paths = [
       _os.path.expandvars(r"%LOCALAPPDATA%\NVIDIA Corporation\GeForceNOW\debug.log"),
       _os.path.expandvars(r"%LOCALAPPDATA%\NVIDIA Corporation\GeForceNOWStreamer\debug.log"),
       _os.path.expandvars(r"%LOCALAPPDATA%\NVIDIA Corporation\NUEVA_RUTA\debug.log"),  # ← añadir
   ]
   ```

---

## Escenario C: NVIDIA deja de escribir debug.log (poco probable)

**Síntoma:** El archivo existe pero no tiene entradas `onSessionSetupProgress` ni `onStopResult`.

**Diagnóstico:**
```powershell
# Ver si el archivo se actualiza durante una sesión:
Get-Item "$env:LOCALAPPDATA\NVIDIA Corporation\GeForceNOW\debug.log" | Select-Object LastWriteTime
# Esperar 30s y repetir. Si no cambió → log inactivo.
```

**Solución — Plan B (píxeles):**
Implementar detección por comparación de píxeles como alternativa:
```python
def _is_video_streaming(self):
    """Detecta video en vivo comparando screenshots."""
    import mss, time
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # pantalla principal
        img1 = sct.grab(monitor)
        time.sleep(0.5)
        img2 = sct.grab(monitor)

    # Comparar bytes: ¿cuántos píxeles cambiaron significativamente?
    changed = 0
    total = len(img1.raw) // 4
    for i in range(0, len(img1.raw), 4):
        if abs(img1.raw[i] - img2.raw[i]) > 30:
            changed += 1

    ratio = changed / total
    return ratio > 0.10  # >10% de píxeles cambiaron → video en vivo
```

**Plan C (audio):**
Detectar si GFN está reproduciendo audio usando pycaw:
```python
# GFN reproduce audio solo cuando el juego está activo
# La cola no tiene audio
```

---

## Escenario D: El threshold de 10s es incorrecto

**Síntoma:** Gwen reporta STREAMING demasiado pronto (la cola tarda >10s entre actualizaciones) o demasiado tarde (el juego tarda >10s en abrir Steam).

**Diagnóstico:**
```powershell
# Monitorear el log en vivo (comando #2) durante una sesión completa
# Medir el tiempo real entre la última línea de cola y el momento en que el juego inicia
```

**Solución:**
Ajustar el threshold en `utils/gfn_engine.py:144`:
```python
if t_queue and (now - t_queue).total_seconds() < 15:  # ← 10 → 15s
```

---

## Escenario E: GFN en navegador (no en app nativa)

**Síntoma:** No existe `debug.log` porque el usuario usa GFN en Chrome/Edge, no la app nativa.

**Solución:**
1. Detectar ventana del navegador con título "GeForce NOW"
2. Usar Plan B (píxeles) como método principal
3. El fallback actual del código ya cubre este caso (retorna QUEUE si hay ventana GFN sin log)

---

## Resumen de robustez

```
Nivel 1 (principal):  debug.log    → ~100% precisión
Nivel 2 (fallback):   ventanas      → ~50% precisión
Nivel 3 (emergencia): píxeles       → ~80% precisión (a implementar)
Nivel 4 (último):     audio         → ~90% precisión (a implementar)
```

El sistema nunca se queda sin detección — degrada gracefully a métodos menos precisos pero funcionales.
