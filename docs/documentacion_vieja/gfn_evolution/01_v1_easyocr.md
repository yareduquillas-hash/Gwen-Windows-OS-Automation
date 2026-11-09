# Iteración 1: EasyOCR (v1 original)

> **Estado:** ❌ FALLÓ
> **Fecha:** Antes de 2026-08-02
> **CPU:** 75-100%
> **RAM:** +1.5 GB
> **Tiempo de verificación:** 8-10 segundos

---

## Método

Usar `EasyOCR` + `PyTorch` para leer texto en pantalla y detectar números de cola y estado del juego.

```python
import easyocr
reader = easyocr.Reader(['en'])
result = reader.readtext(screenshot)
```

## Por qué falló

1. **PC sin GPU dedicada** — PyTorch carga todo en RAM del sistema
2. **1.5 GB de RAM** — solo para tener el modelo cargado
3. **75-100% CPU** — el OCR corría cada 15 segundos, congelando el sistema
4. **8-10 segundos por verificación** — demasiado lento para detección en tiempo real
5. **Falsos positivos** — el OCR leía mal los números de cola o confundía UI con estado de juego

## Conclusión

EasyOCR es overkill para este problema. Se necesita un approach más ligero que no dependa de ML.
