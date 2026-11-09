# Auditoria tecnica consolidada

Proyecto: Gwen / Jarvis Windows Pro  
Ruta: `C:\Users\admin\Desktop\jarvis_windows_pro`  
Revision: 2026-08-06  
Alcance: lectura de codigo Python, Android, scripts, configuracion, datos y
logs. No se iniciaron el bot ni la API durante la revision.

## Resumen ejecutivo

El proyecto tiene una base modular utilizable, pero no debe exponerse a una
red ni tratarse como un servicio confiable hasta resolver secretos expuestos,
ejecucion de comandos, descargas no verificadas, autenticacion de la API,
aislamiento de archivos y concurrencia.

La arquitectura actual mezcla cuatro responsabilidades en el mismo flujo:

```text
Entrada Telegram / REST / WebSocket / voz
    -> handlers y ModuleRegistry
    -> modulos con efectos directos
    -> adaptador Windows
    -> SQLite, proveedores IA y servicios externos
```

La primera correccion estructural ya comenzo: `adapters/` define una frontera
comun y Telegram, voz y WebSocket usan `InputRouter`. Tambien se aplicaron
mitigaciones iniciales de superficie remota, pero la rotacion de credenciales y
la politica completa de capacidades siguen pendientes.

## Calificacion orientativa

| Ambito | Nota | Evaluacion |
|---|---:|---|
| Arquitectura | 6/10 | Buena separacion inicial, pero con estado global y responsabilidades mezcladas. |
| Seguridad | 2/10 | RCE potencial, API expuesta, secretos en texto plano y descargas ejecutables. |
| Privacidad | 2/10 | Logs de conversaciones, memoria persistente y envio a multiples proveedores. |
| Funcionalidad | 4/10 | Varias funciones principales tienen fallos confirmados de runtime. |
| Concurrencia | 4/10 | Conexion SQLite y callbacks async/sync inseguros. |
| Rendimiento | 5/10 | Hay timeouts, pero tambien historial sin limite, hilos por accion y tareas bloqueantes. |
| Mantenibilidad | 5/10 | Modulos legibles, pero sin tests, lockfile ni contratos tipados de entrada. |
| Android / UX | 3/10 | Conexion falsa, WebSocket sin puente de estado y posible fallo de recursos. |
| Operaciones | 4/10 | Scripts practicos, pero instalan globalmente y abren firewall de forma amplia. |
| Autonomia segura | 3/10 | La IA puede proponer acciones, pero falta una politica central de permisos. |

## Fortalezas confirmadas

- `modules/registry.py` descubre modulos y aplica prioridades.
- `plat_adapter/` intenta aislar Windows y Linux.
- Las consultas SQL de los repositorios usan parametros.
- SQLite activa claves foraneas y WAL.
- Telegram valida `chat_id`, antiguedad y frecuencia en `modules/auth.py`.
- Varias operaciones externas tienen timeout.
- `utils/gfn_engine.py` tiene contador de errores consecutivos.
- El analisis sintactico de los archivos Python revisados no encontro errores de
  sintaxis.

## Hallazgos P0: detener exposicion y rotar secretos

### P0-01 - Credenciales reales almacenadas en el proyecto

Archivos afectados:

- `.env`
- `Gwen Key.txt`
- `data/credentials.json`
- `data/google_token.json`
- `data/jarvis.log`
- `data/jarvis_memoria.db`

Impacto: control del bot de Telegram, consumo de proveedores IA y acceso a
Google Drive si los tokens siguen vigentes. No se reproducen valores secretos
en esta documentacion.

Estado actual: las claves de entorno fueron migradas a Windows Credential
Manager, `.env` fue redactado, `Gwen Key.txt` fue eliminado y los archivos
OAuth, SQLite, logs y configuracion fueron copiados al runtime de
`%APPDATA%\GwenWindowsPro`. Las claves antiguas siguen necesitando revocacion
externa.

Acciones inmediatas:

1. Revocar y regenerar Telegram, Google OAuth, NVIDIA, OpenRouter y la clave de
   la API local.
2. Ejecutar `rotate_api_key.py` para crear la nueva clave local y configurarla
   en Android.
3. Revocar las claves antiguas en los paneles de cada proveedor.
4. Eliminar las copias antiguas de DB/logs despues de detener la instancia vieja.

### P0-02 - API expuesta y sin transporte seguro

Referencias:

- `config.py:56-58` usaba `0.0.0.0` como valor por defecto.
- `api_server.py:28-41` ahora usa CORS explicito sin credenciales cross-origin.
- `api_server.py:295-310` valida el token WebSocket por header.
- `api_server.py:333-336` inicia HTTP plano.
- `setup_firewall.ps1:12-14` abre el puerto para todos los perfiles.
- `android_app/app/src/main/AndroidManifest.xml:20-21` permite cleartext.

Mitigacion aplicada parcialmente: `127.0.0.1` por defecto, CORS explicito,
token WebSocket por header, rate limit basico y firewall privado. Sigue
pendiente TLS mediante VPN o proxy para acceso remoto y dejar de permitir
cleartext en Android.

### P0-03 - Ejecucion de comandos y binarios no confiables

Referencias:

- `modules/sistema.py:47-90`: la consola esta deshabilitada por defecto y, si se
  habilita, usa `shell=False` con allowlist de consultas.
- `utils/security.py:15-27`: blacklist y eliminacion de metacaracteres, no un
  control de seguridad suficiente.
- `modules/descargas.py:44-105`: HTTP(S), host publico, limites y archivo
  temporal atomico.
- `modules/descargas.py:108-212`: instaladores deshabilitados por defecto y
  extraccion canonica con limites.
- `utils/gfn_engine.py:219-225`: abre accesos directos sin fallback shell.

Mitigacion aplicada parcialmente: las rutas peligrosas estan cerradas por
defecto y hay validaciones de dominio, tamano y path traversal. Sigue pendiente
verificacion de hash/firma y una politica central de capacidades.

## Hallazgos P1: fallos funcionales y de control

### P1-01 - WebSocket Android rompe el puente de hilos

`api_server.py` ejecuta `registry.dispatch()` en un executor. El
`DummyBotSender` ahora usa `asyncio.run_coroutine_threadsafe()` contra el loop
propietario del WebSocket, por lo que el fallo de event loop esta corregido.

`ChatScreen.kt` ya conecta callbacks a estado Compose; aun falta migrar ese
estado a un `ViewModel`/`StateFlow` y probar reconexion.

### P1-02 - Android no valida conexion y contiene defaults inseguros

- `SessionPrefs.kt` ya no trae host ni token por defecto y migra preferencias a
  almacenamiento cifrado.
- `ConnectScreen.kt` ahora valida host, puerto y ejecuta `ping` antes de guardar.
- La referencia a `ic_launcher_round` fue eliminada.
- `SessionPrefs.kt` ya no expone el token en la URL; el WebSocket usa header.
- `SessionPrefs.kt` usa HTTP/WS solo en debug; release usa HTTPS/WSS.
- `AndroidManifest.xml` desactiva `allowBackup`; TLS/WSS sigue pendiente para
  acceso remoto.

### P1-03 - Busqueda de archivos con IA esta rota

La version anterior de `modules/archivos.py:215-249` llamaba al runner de IA
pero despues usaba `paths`, `split_files` y `_os` sin definirse. Ademas,
`ejecutar_ia_directa()` devolvia `bool`, no el texto con rutas.

El menu de archivos grandes tambien tenia una asignacion local incorrecta y
estado global compartido.

Correccion aplicada: se usa `pathlib`/`os.walk` bajo directorios permitidos,
aislando pendientes por `chat_id`; la IA no ejecuta busquedas de disco.

### P1-04 - Exfiltracion y escritura de archivos

- `modules/archivos.py:31-75` ahora usa rutas canonicas y raices permitidas.
- Se bloquean `credentials.json`, `google_token.json`, `Gwen Key.txt` y otros
  nombres sensibles.
- `modules/archivos.py:76-106` usa basename, limite de 50 MB y nombre aleatorio.
- Google Drive queda privado por defecto en `utils/file_uploader.py`.

### P1-05 - Politica de proveedores IA inconsistente

La version anterior de `ai/direct_ai_runner.py:180-297` intentaba proveedores
adicionales solo porque existia una clave, aunque el proveedor seleccionado
fuera otro.

La API ahora restringe alias y actualiza el campo de modelo correspondiente;
los proveedores no implementados ya no aparecen como alias activos.

### P1-06 - Acciones peligrosas sin confirmacion uniforme

- `modules/reconfig.py:118-121` y `jarvis.py` ahora exigen confirmacion explicita
  antes de reiniciar.
- `plat_adapter/windows.py:171-181` mata procesos por coincidencia parcial.
- `direct_ai_runner.py:73-77` limpia etiquetas de IA y no ejecuta acciones por
  defecto.

Toda accion debe tener una capacidad, nivel de riesgo, auditoria y confirmacion
independiente del canal.

## Hallazgos P2: arquitectura, datos y operaciones

- `database/connection.py` comparte una conexion SQLite, ahora serializada; una
  futura migracion puede separar conexiones por hilo.
- `ai/direct_ai_runner.py:19-22` limita el historial con `deque`, pero aun mezcla
  canales y no es una sesion por usuario.
- `modules/secciones.py` y `modules/wizard.py` ahora aislan estado por chat;
  falta extraerlo a un store persistente.
- `utils/scheduler.py` ya usa `TIMEZONE`, notifica nuevas tareas y limita la
  espera sin tareas; falta probar DST y persistencia de zona en Windows.
- `main.py` ya ejecuta purga de datos al iniciar; falta una politica de retencion
  configurable.
- `requirements.txt` usa rangos `>=` y aun no tiene lockfile, pero declara
  directamente `requests` y `requests_toolbelt`.
- `setup.ps1` sigue instalando globalmente; ahora detiene errores y los scripts
  PowerShell pasan el parser de Windows PowerShell 5.1.
- Hay tests iniciales, pero falta pipeline de lint, tipos y auditoria de
  dependencias.
- Los logs antiguos confirmaban errores de `HotConfig` y `AudioDevice.Activate`;
  el codigo actual corrige la ruta de `pycaw` y los logs se copian fuera del
  proyecto.

## Mitigaciones implementadas en esta iteracion

- `adapters/` define `InboundMessage`, canales y `InputRouter`; Telegram, voz y
  WebSocket ya lo utilizan.
- WebSocket usa `Authorization: Bearer`, rate limit por conexion y
  `run_coroutine_threadsafe()` para responder desde workers.
- REST usa CORS explicito, rate limit, esquemas Pydantic, rangos y allowlists.
- `/sh`, instaladores automaticos y acciones implicitas de IA quedan
  deshabilitados por defecto.
- Descargas usan HTTP(S), validacion de host publico, limites, temporales
  atomicos y extraccion segura.
- Busqueda y envio de archivos usan rutas canonicas, raices permitidas,
  nombres sensibles bloqueados, limites y estado por usuario.
- SQLite serializa conexion y escrituras; configuracion usa escritura atomica y
  backups con identificador unico.
- Android elimina defaults de credenciales, migra preferencias cifradas, valida
  `ping`, usa header WebSocket y conecta respuestas al estado de Compose.
- Android permite cleartext solo en debug y exige HTTPS/WSS en release; el
  servidor ya acepta certificados TLS configurables.
- Windows usa `EndpointVolume` con fallback compatible y no afirma silenciar el
  microfono cuando no tiene implementado el endpoint de captura.
- Secretos y runtime privado se migran a Credential Manager y `%APPDATA%`.
- Se anadio `.gitignore` raiz y se conservaron documentos antiguos en
  `docs/documentacion_vieja/`.
- Las pruebas unitarias iniciales pasan: 14 tests; 73 archivos Python pasan
  analisis sintactico.

## Consciencia y autonomia

El proyecto implementa identidad, prompt, memoria, contexto, metricas en vivo y
automatizacion. Eso produce una experiencia de autoconciencia operativa, pero
no demuestra consciencia subjetiva. Tecnologicamente debe tratarse como un
agente con estado, herramientas y una politica de permisos verificable.
