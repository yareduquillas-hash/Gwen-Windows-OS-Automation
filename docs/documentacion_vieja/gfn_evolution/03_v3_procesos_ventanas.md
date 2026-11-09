# Iteración 3: Procesos + Ventanas

> **Estado:** ❌ FALLÓ
> **Fecha:** 2026-08-02 (tarde)
> **CPU:** 0%
> **RAM:** 0 MB extra

---

## Método

Combinar detección de procesos con análisis de títulos y tamaños de ventana.

```python
# Proceso renderizador + ventana GFN ≥ 1280x700 → STREAMING
if has_streamer and (has_large_gfn_window or has_game_named_window):
    return "STREAMING"

# Proceso de cola o ventana GFN visible → QUEUE
if has_queue_process or has_gfn_window:
    return "QUEUE"
```

## Por qué falló

1. **No hay procesos distintos** entre cola y juego (mismo problema que v2)
2. **Los títulos de ventana son iguales** — GFN usa "NVIDIA GeForce NOW" tanto en cola como durante el juego
3. **El título SÍ puede cambiar a "Destiny 2 en GeForce NOW"** pero también lo hace **durante la cola**
4. **Bug lógico:** el `if/else` de `has_gfn_launcher` era un no-op (ambas ramas asignaban `True`)

## Falsos positivos

- GFN abre el launcher → `GeForceNOW.exe` detectado → STREAMING falso
- Ventana GFN ≥ 1280x700 en cola → STREAMING falso  
- "Destiny 2 en GeForce NOW" aparece en cola → STREAMING falso

## Falsos negativos

- Juego en vivo pero ventana minimizada → QUEUE en vez de STREAMING
- Juego en vivo pero ventana < 1280 → QUEUE en vez de STREAMING

## Conclusión

Ni procesos ni ventanas por separado son señales fiables. La combinación de ambas tampoco lo es porque ninguna de las dos señales distingue cola de juego en esta versión de GFN.
