# Comandos de Investigación — PowerShell

> **Propósito:** Validar, depurar y preparar para futuras versiones de GFN

---

## 1. Verificar la ruta del log en esta máquina

```powershell
Get-ChildItem "$env:LOCALAPPDATA\NVIDIA Corporation" -Recurse -Filter "debug.log" |
    Select-Object FullName, Length, LastWriteTime
```

**Cuándo usar:** Si la detección deja de funcionar, verificar que el archivo siga existiendo y en qué ruta.

---

## 2. Monitorear el log en tiempo real durante una sesión

```powershell
Get-Content "$env:LOCALAPPDATA\NVIDIA Corporation\GeForceNOW\debug.log" -Wait -Tail 5 |
    ForEach-Object {
        if ($_ -match "onSessionSetupProgress|onStopResult|session.*start|stream.*start") {
            Write-Host $_ -ForegroundColor Cyan
        }
    }
```

**Cuándo usar:** Para observar en vivo qué escribe NVIDIA durante cola → juego → cierre. Dejar corriendo mientras juegas una sesión completa.

---

## 3. Ver qué otras líneas aparecen cuando el juego inicia

```powershell
# Ejecutar DURANTE el juego (no en cola):
Get-Content "$env:LOCALAPPDATA\NVIDIA Corporation\GeForceNOW\debug.log" -Tail 100 |
    Select-String -Pattern "simple_grid_app|session|stream|game|launch|start|stop"
```

**Cuándo usar:** Si el threshold de 10s no es suficiente (el juego tarda más en arrancar), este comando muestra qué escribe NVIDIA durante la transición.

---

## 4. Probar si el log existe en otras rutas posibles

```powershell
@(
    "$env:LOCALAPPDATA\NVIDIA Corporation\GeForceNOW\debug.log",
    "$env:LOCALAPPDATA\NVIDIA Corporation\GeForceNOWStreamer\debug.log",
    "$env:LOCALAPPDATA\NVIDIA Corporation\GeForceNOW\logs\debug.log",
    "$env:APPDATA\NVIDIA Corporation\GeForceNOW\debug.log"
) | ForEach-Object { if (Test-Path $_) { Write-Host "✓ $_" } else { Write-Host "✗ $_" } }
```

**Cuándo usar:** Si NVIDIA mueve el log de carpeta en una actualización futura.

---

## 5. Extraer TODOS los eventos que emite NVIDIA

```powershell
Get-Content "$env:LOCALAPPDATA\NVIDIA Corporation\GeForceNOW\debug.log" |
    Select-String "simple_grid_app.cc\(\d+\)\]\s+(\w+)" |
    ForEach-Object { $_.Matches.Groups[1].Value } |
    Sort-Object -Unique
```

**Cuándo usar:** Si NVIDIA cambia el nombre de `onSessionSetupProgress` en una versión futura. Este comando te da la lista completa de eventos para encontrar el nuevo nombre.

Ejemplo de salida esperada:
```
Creating
Destroying
Executing
Initializing
Registering
onSessionSetupProgress    ← cola
onStopResult              ← cierre
setDecoderInfo
setDynamicStreamingMode
stopRecording
```

---

## 6. Ver tamaño y rotación del log

```powershell
Get-Item "$env:LOCALAPPDATA\NVIDIA Corporation\GeForceNOW\debug.log" |
    Select-Object Length, LastWriteTime, CreationTime
```

**Cuándo usar:** Para entender si el log rota (se vacía/renombra) entre sesiones o si crece indefinidamente.

---

## 7. Simular el parser manualmente

```powershell
python -c "
import os, re
log_path = os.path.expandvars(r'%LOCALAPPDATA%\NVIDIA Corporation\GeForceNOW\debug.log')
with open(log_path, 'rb') as f:
    f.seek(0, 2)
    f.seek(max(0, f.tell() - 16384))
    raw = f.read().decode('utf-8', errors='ignore')

found_queue = False
found_stop = False
for line in raw.splitlines():
    if 'onSessionSetupProgress' in line:
        m = re.search(r'(\d{2}:\d{2}:\d{2})', line)
        q = re.search(r'queue:\s*(\d+)', line)
        if m:
            print(f'QUEUE at {m.group(1)}, position {q.group(1) if q else \"?\"}')
            found_queue = True
    if 'onStopResult' in line:
        m = re.search(r'(\d{2}:\d{2}:\d{2})', line)
        if m:
            print(f'STOP at {m.group(1)}')
            found_stop = True

if not found_queue and not found_stop:
    print('No queue or stop entries in last 16KB')
elif not found_queue:
    print('No queue entries → game may be streaming')
"
```

**Cuándo usar:** Para probar el parser sin arrancar Gwen. Ejecutar durante cola y durante juego para verificar que el algoritmo funciona.
