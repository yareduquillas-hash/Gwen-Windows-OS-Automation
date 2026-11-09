# Iteración 2: Procesos psutil

> **Estado:** ❌ FALLÓ
> **Fecha:** 2026-08-02 (mañana)
> **CPU:** 0%
> **RAM:** 0 MB extra

---

## Método

Detectar procesos de GeForce NOW usando `psutil.process_iter()`.

```python
streamer_names = ("geforcenowstreamer.exe", "nvstreamer.exe", "gfnruntime.exe")
for p in psutil.process_iter(["name"]):
    if p.info.get("name", "").lower() in streamer_names:
        return "STREAMING"
```

## Por qué falló

**`GeForceNOWStreamer.exe` no existe en esta versión de GFN.**

Los procesos reales en esta máquina (Windows 11, GFN v2.x):

```
Durante la cola:     GeForceNOW.exe (×5) + GeForceNOWContainer.exe
Durante el juego:    GeForceNOW.exe (×5) + GeForceNOWContainer.exe
                     ↑ IDÉNTICOS ↑
```

No hay ningún proceso con "streamer" o "nvstream" en el nombre. Los nombres de procesos que el código buscaba eran de versiones antiguas de GFN o de otra arquitectura (posiblemente la versión de navegador).

## Evidencia (capturada 2026-08-02)

```powershell
Get-Process | Where-Object { $_.Name -match "geforce|nvidia|nvstream|gfn" }
```

Resultado (cola y juego: idéntico):
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

## Conclusión

La detección por nombre de proceso es frágil — NVIDIA cambia los nombres entre versiones. En esta versión simplemente no existen los procesos que el código buscaba.
