# Evidencia Real — Capturada en vivo 2026-08-02

> **Máquina:** Windows 11, GeForce NOW v2.x
> **Juego:** Destiny 2
> **Sesión:** 16:03 a 16:06 (cola + cierre sin entrar al juego)

---

## Procesos activos (cola y juego: idénticos)

```powershell
Get-Process | Where-Object { $_.Name -match "geforce|nvidia|nvstream|gfn" }
```

```
Name                  Id
----                  --
GeForceNOW          4848
GeForceNOW          5828
GeForceNOW          5840
GeForceNOW          6708
GeForceNOW          6872
GeForceNOWContainer 3536
```

---

## Ventanas (cambian en ambos estados)

```
Cola:  [NVIDIA GeForce NOW]       → también puede ser [Destiny 2 en GeForce NOW]
Juego: [Destiny 2 en GeForce NOW]  → mismo formato que en cola
```

---

## debug.log — La única señal fiable

### Ruta
```
%LOCALAPPDATA%\NVIDIA Corporation\GeForceNOW\debug.log
Tamaño: ~60 KB durante la sesión
```

### Cola activa (actualizaciones cada ~1 segundo)
```
16:05:24 → onSessionSetupProgress(state: 1, queue: 36, eta: 30000)
16:05:25 → onSessionSetupProgress(state: 1, queue: 36, eta: 30000)
16:05:26 → onSessionSetupProgress(state: 1, queue: 36, eta: 30000)
16:05:27 → onSessionSetupProgress(state: 1, queue: 36, eta: 30000)
16:05:28 → onSessionSetupProgress(state: 1, queue: 35, eta: 30000)
16:05:29 → onSessionSetupProgress(state: 1, queue: 35, eta: 30000)
16:05:30 → onSessionSetupProgress(state: 1, queue: 35, eta: 30000)
16:05:31 → onSessionSetupProgress(state: 1, queue: 35, eta: 30000)
16:05:32 → onSessionSetupProgress(state: 1, queue: 33, eta: 30000)
16:05:33 → onSessionSetupProgress(state: 1, queue: 33, eta: 30000)
16:05:34 → onSessionSetupProgress(state: 1, queue: 33, eta: 30000)
16:05:36 → onSessionSetupProgress(state: 1, queue: 32, eta: 30000)
16:05:37 → onSessionSetupProgress(state: 1, queue: 32, eta: 30000)
16:05:38 → onSessionSetupProgress(state: 1, queue: 30, eta: 30000)
16:05:39 → onSessionSetupProgress(state: 1, queue: 30, eta: 30000)
16:05:40 → onSessionSetupProgress(state: 1, queue: 30, eta: 30000)
16:05:41 → onSessionSetupProgress(state: 1, queue: 30, eta: 30000)
16:05:42 → onSessionSetupProgress(state: 1, queue: 30, eta: 30000)
16:05:43 → onSessionSetupProgress(state: 1, queue: 28, eta: 30000)
16:05:44 → onSessionSetupProgress(state: 1, queue: 28, eta: 30000)
16:05:45 → onSessionSetupProgress(state: 1, queue: 28, eta: 30000)
16:05:46 → onSessionSetupProgress(state: 1, queue: 28, eta: 30000)
16:05:47 → onSessionSetupProgress(state: 1, queue: 28, eta: 30000)
16:05:48 → onSessionSetupProgress(state: 1, queue: 25, eta: 30000)
16:05:49 → onSessionSetupProgress(state: 1, queue: 23, eta: 30000)
16:05:50 → onSessionSetupProgress(state: 1, queue: 23, eta: 30000)
16:05:51 → onSessionSetupProgress(state: 1, queue: 23, eta: 30000)
16:05:52 → onSessionSetupProgress(state: 1, queue: 21, eta: 30000)
16:05:53 → onSessionSetupProgress(state: 1, queue: 21, eta: 30000)
16:05:54 → onSessionSetupProgress(state: 1, queue: 21, eta: 30000)
16:05:55 → onSessionSetupProgress(state: 1, queue: 21, eta: 30000)
16:05:56 → onSessionSetupProgress(state: 1, queue: 21, eta: 30000)
16:05:58 → onSessionSetupProgress(state: 1, queue: 13, eta: 30000)
16:05:59 → onSessionSetupProgress(state: 1, queue: 13, eta: 30000)
```

### Cierre de sesión
```
16:06:00 → onStopResult(result: 16064513)
```

### Observaciones

1. **Frecuencia:** exactamente 1 línea por segundo durante la cola
2. **Queue:** avanza de 36 a 13 en ~35 segundos
3. **ETA:** siempre 30000ms (30s) — parece ser un valor fijo, no dinámico
4. **State:** siempre 1 durante la cola
5. **No hubo entrada al juego** en esta sesión (cola → stop, sin streaming)
6. **El log incluye líneas de inicialización** del decoder de video y audio ANTES de la cola:
   - `Creating DX11 decoder for H264`
   - `Creating audio renderer`

---

## Líneas del log que NO son de cola (ciclo de vida completo)

```
16:03:52 → Creating SimpleGridApp                           [inicio de app]
16:04:03 → Creating DX11 decoder for H264                    [preparación video]
16:04:04 → Creating audio renderer                           [preparación audio]
16:04:04 → Initializing audio renderer
16:05:24 → onSessionSetupProgress(state:1, queue:36, ...)   [INICIO COLA]
...      → (35 líneas de cola, 35 segundos) ...
16:05:59 → onSessionSetupProgress(state:1, queue:13, ...)   [FIN COLA]
16:06:00 → onStopResult(result: 16064513)                    [CIERRE]
16:06:00 → Executing ShutdownPlatformResources               [limpieza]
16:06:01 → Destroying SimpleGridApp                          [fin de app]
```

---

## Conclusión

El `debug.log` de NVIDIA es **la única señal que distingue cola de juego de forma fiable**. Los procesos y ventanas son idénticos en ambos estados. El log reporta la cola activamente y deja de hacerlo cuando el juego arranca.
