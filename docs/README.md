# Gwen / Jarvis Windows Pro - Documentacion activa

Esta carpeta contiene la documentacion vigente del proyecto. La documentacion
anterior fue conservada sin cambios en `docs/documentacion_vieja/`.

## Documentos vigentes

1. `AUDITORIA_TECNICA.md`
   Diagnostico consolidado de seguridad, arquitectura, funcionalidad,
   concurrencia, rendimiento, Android y operaciones.
2. `PLAN_IMPLEMENTACION.md`
   Orden de trabajo, prioridades, criterios de aceptacion y estrategia de
   validacion.
3. `ARQUITECTURA_ADAPTADORES.md`
   Contratos y migracion de Telegram, REST, WebSocket y voz hacia una frontera
   de entrada comun.
4. `ROTACION_SECRETOS.md`
   Procedimiento de revocacion externa y migraciones locales sin exponer claves.

## Regla de mantenimiento

Los cambios de comportamiento deben actualizar primero el codigo y despues
esta documentacion activa. Los documentos historicos no son fuente de verdad;
solo sirven como contexto de decisiones anteriores.

## Estado de referencia

- Aplicacion principal: Python, Telegram, FastAPI y WebSocket.
- Cliente adicional: Android Jetpack Compose.
- Persistencia: SQLite singleton con WAL.
- Secretos y runtime privado: Windows Credential Manager y
  `%APPDATA%\GwenWindowsPro\`.
- Frontera de entradas: `adapters/` con contratos para Telegram, REST,
  WebSocket y voz; Telegram, voz y WebSocket ya usan el router comun.
- Puntos de entrada actuales: `main.py`, `jarvis.py`, `api_server.py` y voz de
  Telegram.
- Pruebas iniciales: `tests/` cubre adapters, registro, configuracion, base de
  datos y seguridad de archivos.
- La suite de pruebas aun no cubre todos los modulos ni la compilacion Android.
- La validacion inicial encontro errores de sintaxis no presentes, pero si
  errores de runtime, seguridad y contratos entre componentes.
