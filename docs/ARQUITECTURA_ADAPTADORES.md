# Arquitectura de adaptadores de entrada

## Objetivo

Separar el transporte de la intencion del usuario y de la ejecucion de
capacidades. Telegram, REST, WebSocket y voz deben entregar el mismo contrato
al nucleo.

La primera implementacion vive en `adapters/contracts.py` y
`adapters/router.py`. No es todavia la politica completa de capacidades; es la
frontera de normalizacion sobre la que se construira esa politica.

## Flujo objetivo

```text
TelegramAdapter ─┐
RestAdapter ──────┼─> InputRouter -> AuthPolicy -> CommandDispatcher
WebSocketAdapter ─┤                              -> CapabilityPolicy
VoiceAdapter ─────┘                              -> Module / Platform adapter
                                                        |
                                      ResponsePort <────┘
```

## Contrato de entrada

Cada adaptador debe producir un evento con:

```text
InboundMessage
  request_id: identificador unico de trazabilidad
  channel: telegram | rest | websocket | voice
  user_id: identidad normalizada del usuario
  text: texto ya limitado y normalizado
  metadata: chat_id, headers permitidos, idioma y timestamp
```

El dispatcher no debe conocer objetos de TeleBot, FastAPI o OkHttp. Solo debe
recibir `InboundMessage`, consultar una politica y ejecutar una capacidad.

## Contrato de salida

```text
ResponsePort
  send_text(text, format=None)
  send_image(content, media_type="image/png")
  send_file(content, name)
  request_confirmation(action, expires_at)
```

El adaptador convierte estas operaciones a Telegram, JSON REST, mensajes JSON
WebSocket o estado Compose. Las excepciones de transporte no deben llegar a los
modulos.

## Adaptadores actuales y migracion

### Telegram

Actualmente `JarvisBot` registra handlers y llama a `ModuleRegistry` directamente.
La migracion debe conservar `TeleBot` en el adaptador, pero convertir mensajes
de texto y voz a `InboundMessage` antes de entrar al router.

### REST

Actualmente `api_server.py` expone informacion de sistema, volumen, medios,
modelos y configuracion. Cada endpoint debe validar un esquema Pydantic y
convertirse en una capacidad tipada; no debe aceptar `dict` arbitrarios.

### WebSocket

El loop async es propietario del WebSocket. Los modulos existentes son
sincronicos, por lo que sus respuestas deben volver al loop con
`asyncio.run_coroutine_threadsafe()`. Nunca se debe llamar `create_task()` desde
un worker sin loop.

### Voz

La transcripcion es un adaptador de entrada encima de Telegram. El texto
transcrito debe pasar por el mismo router, autenticacion, rate limit y politica
de capacidades que el texto escrito.

## Reglas de seguridad de la frontera

- No confiar en `chat_id=999999` como autorizacion.
- No aceptar tokens en query strings cuando exista header o handshake seguro.
- No permitir que el modelo IA invoque directamente adaptadores.
- No guardar contenido completo de mensajes en logs de nivel INFO.
- Limitar texto, JSON, imagen, archivo, conexiones y tareas concurrentes.
- Emitir un `request_id` en logs para seguir una operacion sin guardar secretos.
- Asociar estado de sesion a `channel + user_id`, no a variables globales.

## Politica de capacidades

| Capacidad | Riesgo | Confirmacion |
|---|---|---|
| Leer bateria/sistema | read | no, si esta autorizado |
| Capturar pantalla | sensitive_read | si la politica lo exige |
| Controlar medios/volumen | write | no, con rate limit |
| Leer o enviar archivos | sensitive_read / external_upload | si, siempre para secretos o nube |
| Terminar procesos | destructive | si, proceso exacto |
| Reiniciar/apagar | destructive | confirmacion explicita y expiracion |
| Ejecutar shell | critical | deshabilitado por defecto |

## Criterios de aceptacion

1. Los cuatro canales generan el mismo tipo de evento.
2. La politica se ejecuta una sola vez en el nucleo.
3. Un canal no puede ejecutar una capacidad que otro canal no tenga autorizada.
4. Un fallo del transporte no deja un worker bloqueado ni una tarea sin limite.
5. Las respuestas WebSocket actualizan la UI Android mediante estado observable.
