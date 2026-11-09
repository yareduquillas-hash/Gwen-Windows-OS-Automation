# Iteración 4: Solo títulos de ventana

> **Estado:** ❌ FALLÓ
> **Fecha:** 2026-08-02 (tarde-noche)
> **CPU:** 0%
> **RAM:** 0 MB extra

---

## Método

Eliminar completamente la detección por procesos y usar **solo títulos de ventana**.

```python
for win in gw.getAllWindows():
    if not win.visible or win.isMinimized:
        continue
    w_title = win.title.lower()

    if "geforce now" in w_title:
        has_gfn_window = True

        # ¿El título contiene el nombre del juego?
        if game_keywords and any(k in w_title for k in game_keywords):
            has_game_streaming = True  # "Destiny 2 en GeForce NOW"
```

## Evidencia inicial (parecía prometedora)

```
Cola:   [NVIDIA GeForce NOW]   800x600   ← genérico
Juego:  [Destiny 2 en GeForce NOW]  1360x768  ← contiene "destiny"
```

**Parecía la señal perfecta.** El título cambia al entrar al juego.

## Por qué falló

El usuario reportó: *"me acabo de dar cuenta que en la cola cambia el titulo tambien"*

El título **también** cambia a "Destiny 2 en GeForce NOW" durante la cola de espera. GFN muestra el nombre del juego en el título desde que inicias la sesión, no solo cuando el juego arranca.

## Conclusión

La ventana de GFN cambia su título al iniciar la sesión (cola), no al iniciar el streaming. No hay diferencia de título entre cola y juego.
