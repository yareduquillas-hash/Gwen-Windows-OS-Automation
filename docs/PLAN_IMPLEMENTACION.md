# Plan de implementacion

Este documento es la lista de trabajo activa. Cada fase debe terminar con
pruebas y criterios de aceptacion antes de pasar a la siguiente.

## Fase 0 - Contencion y secretos

Estado actual: almacenamiento local migrado; la revocacion externa sigue siendo
manual por el propietario.

- [ ] Revocar y regenerar todos los tokens y API keys existentes.
- [x] Migrar claves de entorno a Windows Credential Manager; `.env` queda sin
      valores secretos.
- [x] Mover OAuth de Google, SQLite, logs y configuracion runtime a
      `%APPDATA%\\GwenWindowsPro\\` mediante scripts de migracion.
- [x] Crear `.gitignore` raiz para `.env`, `data/`, logs, bases, caches y claves.
- [x] Cambiar API a `127.0.0.1` por defecto y actualizar el `.env` local.
- [x] Limitar la regla de firewall a perfil privado y subred local.
- [x] Deshabilitar `/sh`, instaladores automaticos y ejecucion implicita de IA
      hasta completar la politica de capacidades.

Criterio: ninguna credencial funcional queda en el arbol del proyecto y la API
no es accesible desde una red no confiable.

## Fase 1 - Frontera de entradas

Estado: en implementacion. Contratos base y router ya creados en `adapters/`.

- [x] Normalizar Telegram, REST, WebSocket y voz a un contrato comun.
- [x] Asociar cada entrada con `channel`, `user_id`, `request_id` y metadata.
- [x] Centralizar limites basicos de tamano y rate limit; falta la politica
      completa de capacidades y auditoria.
- [x] Mantener los modulos independientes del transporte mediante `InputRouter`.
- [x] Corregir el puente async/sync del WebSocket con el loop propietario.

Criterio: el mismo comando valido produce el mismo `CommandContext` sin duplicar
logica por canal; las respuestas del WebSocket llegan a Android.

## Fase 2 - Politica de capacidades

- [x] Definir capacidades: `system.read`, `screen.capture`, `media.control`,
      `process.terminate`, `file.read`, `file.upload`, `system.restart` y
      `shell.execute`.
- [x] Asignar riesgo `read`, `write`, `destructive` y `external_upload`.
- [x] Implementar `CapabilityPolicy` centralizada en `adapters/policy.py`.
- [x] Reemplazar blacklist de shell por allowlist o eliminar shell remota.
- [x] Exigir confirmacion temporal para reinicio, procesos, uploads y acciones
      destructivas.

Criterio: ni Telegram, ni Android ni la IA pueden saltarse la misma politica.

## Fase 3 - Correctitud funcional

- [x] Reescribir busqueda de archivos con `pathlib.Path.resolve()` y allowlist de
      directorios.
- [x] Corregir estado global de archivos pendientes y aislarlo por usuario.
- [x] Corregir respuesta de bateria del backend y modelos Kotlin.
- [x] Corregir referencia al icono Android.
- [x] Implementar `ChatViewModel` con `StateFlow` y reconexión automática en Android.
- [x] Corregir colisión de disparadores en `GeForceNowModule`.
- [x] Corregir terminación multi-instancia en `plat_adapter`.
- [x] Corregir registro de contexto de sección en base de datos.
- [x] Corregir selector de proveedor/modelo y eliminar alias OpenCode no conectado.
- [x] Corregir pycaw para API `EndpointVolume` y fallback `Activate`.
- [ ] Probar volumen en el Windows real; el mute de microfono queda no
      disponible hasta implementar el endpoint de captura.

## Fase 4 - Persistencia y rendimiento

- [x] Serializar conexion SQLite compartida y commits de escritura.
- [ ] Introducir migraciones versionadas y completar politica de retencion.
- [x] Usar `deque(maxlen=...)` para historial de sesion.
- [x] Aplicar timezone configurable al scheduler y notificacion inmediata.
- [ ] Ejecutar voz, IA, capturas y subidas en workers con limites.
- [ ] Añadir limites de memoria, mensaje, imagen, descarga y WebSocket.

## Fase 5 - Calidad y entrega

- [x] Añadir pruebas para adapters, registry, rutas, scheduler, sesiones,
      secretos y seguridad de archivos.
- [ ] Añadir pruebas para auth, IA y GFN.
- [x] Añadir pruebas de seguridad para path traversal, ZIP/TAR y hosts privados.
- [ ] Ejecutar Ruff, MyPy, Bandit y pip-audit en CI.
- [ ] Crear lockfile de dependencias con hashes y versionar Python soportado.
- [ ] Añadir health checks, logs redactados y politica de retencion.
- [ ] Documentar backup y recuperacion sin incluir secretos.

## Orden recomendado de commits

1. Contencion, `.gitignore`, configuracion segura y documentacion.
2. Contratos y adaptadores de entrada.
3. Politica de capacidades y confirmaciones.
4. Correcciones Android y WebSocket.
5. Archivos, descargas y proveedores IA.
6. Persistencia, scheduler, pruebas y operaciones.
