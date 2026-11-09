# Historial de Contexto y Decisiones del Proyecto (GeForce NOW Refactor)

Este archivo sirve como registro completo de la conversación y las entrevistas `/grill-me` realizadas para llegar al diseño v3 final.

---

## 📝 Resumen del Diálogo y Decisiones del Usuario

1. **Priorización de Problemas**:
   - El usuario reportó que el error más molesto era la afirmación prematura *"¡Ya estás jugando!"* cuando aún estaba en la cola.
   - Ocurría con todos los juegos de GeForce NOW (*Destiny 2*, *Genshin Impact*, *Honkai Star Rail*, etc.).

2. **Entrevista /Grill-Me #1 (Estrategia OCR vs Proceso)**:
   - Se acordó inicialmente probar OCR con preprocesamiento OpenCV para leer el número exacto.

3. **Prueba en Vivo y Falla de Rendimiento**:
   - Al probar en vivo, el usuario reportó que la PC (modesta) sufrió un **75% de uso de CPU y 1.5 GB de RAM** debido a PyTorch/EasyOCR.
   - El juego (Destiny 2) inició y se cerró, pero Gwen nunca notificó y el proceso en segundo plano continuó colgado.

4. **Entrevista /Grill-Me #2 (Rediseño Radical Ultra-Liviano)**:
   - El usuario aprobó la **eliminación total 100% de EasyOCR y PyTorch**.
   - Se adoptó la detección por capa de ventanas de Windows (`win32gui`/`pygetwindow`).
   - Se configuró la autodestrucción inmediata de los hilos de monitoreo en cuanto el usuario cierra el juego o la app.
   - Se estableció la respuesta instantánea en 0ms para las consultas *"cómo va la cola"*.

---

## 📌 Guía para OpenCode

Si vas a realizar modificaciones o sugerencias adicionales en este módulo utilizando **OpenCode** u otros modelos:

1. **NO** reimportar `easyocr`, `torch`, `torchvision` ni librerías de visión pesadas dentro del proceso principal de Python.
2. Mantener la lógica de `_get_window_state()` en `utils/gfn_engine.py` de respuesta instantánea en < 300 ms.
3. Asegurar que cualquier nuevo hilo de monitoreo mantenga el patrón de autodestrucción al detectar `state == 'CLOSED'`.
