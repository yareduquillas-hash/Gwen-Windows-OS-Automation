# 📱 Gwen Android App — Arquitectura y Plan de Desarrollo

> **Proyecto:** App Android companion para Gwen (Jarvis Windows Pro)
> **Repositorio:** `jarvis_windows_pro/android_app/` (monorepo)
> **Stack:** Kotlin + Jetpack Compose + Material 3
> **Fecha:** 2026-08-02
> **Estado:** PLAN — Fase 0 (diseño completo)
> **Base existente:** Proyecto Gradle skeleton con Compose, Retrofit, OkHttp, Coil, Navigation

---

## 🎯 Visión

App Android nativa que se conecta a Gwen por **WiFi local o Internet** con auto-detección de modo. Chat estilo Gemini, panel de módulos con auto-descubrimiento desde la API de Gwen, terminal en tiempo real, y dashboard de estado. Si Gwen crece en la PC, la app se actualiza sola — cero deploy manual.

---

## 🔧 Decisiones de Arquitectura (ya tomadas)

### Kotlin/Compose vs Flutter

| Factor | Kotlin/Compose ✅ | Flutter |
|--------|------------------|---------|
| Proyecto base | ✅ Ya existe `android_app/` con Gradle listo | Empezar de cero |
| Material 3 / Gemini-like | ✅ Nativo, idéntico a apps Google | Bueno, no 100% nativo |
| WebSocket | ✅ OkHttp nativo | ⚠ Paquete externo |
| Conexión dual WiFi/remota | ✅ NetworkCallback nativo | ⚠ Plugin |
| Tamaño APK | ~8-12 MB | ~20-30 MB |
| iOS futuro | ❌ Solo Android | ✅ Un código |
| Rendimiento | ✅ Superior (sin bridge) | Bueno (bridge Dart→Native) |

**Veredicto: Kotlin/Compose.** El proyecto ya existe, es nativo, y para una app companion Android-only no hay razón para usar Flutter.

### Monorepo vs repo separado

| Factor | Monorepo (`android_app/`) ✅ | Repo separado |
|--------|------------------------------|---------------|
| Sincronización | ✅ Automática (misma rama) | Manual (versiones) |
| API de módulos | ✅ Comparte docs/tipos | Duplicación |
| CI/CD | ✅ Un pipeline | Dos pipelines |
| Independencia | Acoplado | ✅ Independiente |

**Veredicto: Monorepo.** `android_app/` ya existe dentro de Gwen. La app se conecta vía API — no lee archivos `.py` directamente. Esto funciona igual en local y remoto.

### Módulos: API vs leer archivos .py

| Factor | API (GET /api/v1/modules/detail) ✅ | Leer .py del filesystem |
|--------|--------------------------------------|-------------------------|
| Remoto | ✅ Funciona por Internet | ❌ Necesita acceso al disco |
| Latencia | 1 request HTTP (~50ms) | N lecturas de archivo (~N×10ms) |
| Metadata | Gwen la tiene en memoria | Parsear Python |
| Nuevo módulo | Automático (registry) | Detectar archivo nuevo |
| Seguridad | Token Bearer | Permisos filesystem |

**Veredicto: API.** Una llamada HTTP. Gwen ya tiene el `ModuleRegistry` en RAM — solo hay que serializarlo a JSON. Funciona local y remoto.

---

## 🌐 Arquitectura de Conexión Dual (Local + Remoto)

### Diagrama de flujo

```
App inicia
    │
    ▼
┌──────────────────────────────────────────────────────────┐
│  1. Leer preferencias guardadas                           │
│     - lastLocalIp, lastRemoteUrl, lastMode               │
│     - Si firstRun → mostrar pantalla de configuración    │
└──────────────────────────┬───────────────────────────────┘
                           │
              ┌────────────▼────────────┐
              │  lastMode == "local"?    │
              └────────────┬────────────┘
                   Sí      │      No
                           │
    ┌──────────────────────▼──────────────────────┐
    │  2a. Intentar conexión LOCAL                 │
    │      http://<savedIp>:8000/api/v1/ping       │
    │      timeout: 2 segundos                     │
    │      sin API key (red local confiable)       │
    └──────────────────────┬──────────────────────┘
                           │
              ┌────────────▼────────────┐
              │     ¿Responde?           │
              └────────────┬────────────┘
                   Sí      │      No
                           │
    ┌──────────────────────▼──────────────────────────┐
    │  2b. Intentar IPs locales alternativas           │
    │      192.168.1.x → 192.168.0.x → 10.0.0.x      │
    │      timeout: 1.5 segundos por IP               │
    └──────────────────────┬──────────────────────────┘
                           │
              ┌────────────▼────────────┐
              │     ¿Responde?           │
              └────────────┬────────────┘
                   Sí      │      No
                           │
    ┌──────────────────────▼──────────────────────────┐
    │  3. Intentar conexión REMOTA                     │
    │      https://<savedRemoteUrl>:8000/api/v1/ping  │
    │      timeout: 5 segundos                         │
    │      CON API key (Internet = inseguro sin auth)  │
    └──────────────────────┬──────────────────────────┘
                           │
              ┌────────────▼────────────┐
              │     ¿Responde?           │
              └────────────┬────────────┘
                   Sí      │      No
                           │
    ┌──────────────────────▼──────────────────────────┐
    │  4. Mostrar pantalla de CONFIGURACIÓN MANUAL     │
    │     El usuario ingresa IP/URL, puerto, API key  │
    │     "Probar conexión" → feedback visual         │
    └─────────────────────────────────────────────────┘
```

### Código: ConnectionManager.kt

```kotlin
// data/remote/ConnectionManager.kt
package com.gwen.android.data.remote

import kotlinx.coroutines.*
import java.util.concurrent.TimeUnit

enum class ConnectionMode { LOCAL, REMOTE, MANUAL }

data class ServerConfig(
    val baseUrl: String,
    val port: Int = 8000,
    val mode: ConnectionMode = ConnectionMode.LOCAL,
    val apiKey: String? = null,
    val useTls: Boolean = false
)

class ConnectionManager(private val prefs: SessionManager) {

    companion object {
        private val LOCAL_SUBNETS = listOf(
            "192.168.1", "192.168.0", "10.0.0", "10.0.1"
        )
        private const val LOCAL_TIMEOUT_SEC = 2L
        private const val REMOTE_TIMEOUT_SEC = 5L
        private const val LOCAL_IP_SCAN_RANGE = 100..150
    }

    suspend fun autoConnect(): Result<ServerConfig> {
        // 1. Intentar IP local guardada
        prefs.lastLocalIp?.let { ip ->
            val config = ServerConfig(
                baseUrl = "http://$ip:${prefs.port}",
                port = prefs.port,
                mode = ConnectionMode.LOCAL
            )
            if (tryPing(config, LOCAL_TIMEOUT_SEC)) {
                prefs.lastMode = "local"
                prefs.lastLocalIp = ip
                return Result.success(config)
            }
        }

        // 2. Escanear subnets locales
        for (subnet in LOCAL_SUBNETS) {
            for (host in LOCAL_IP_SCAN_RANGE) {
                val ip = "$subnet.$host"
                val config = ServerConfig(
                    baseUrl = "http://$ip:${prefs.port}",
                    port = prefs.port,
                    mode = ConnectionMode.LOCAL
                )
                if (tryPing(config, 1500L)) {
                    prefs.lastMode = "local"
                    prefs.lastLocalIp = ip
                    return Result.success(config)
                }
            }
        }

        // 3. Intentar URL remota guardada
        prefs.remoteUrl?.let { url ->
            val config = ServerConfig(
                baseUrl = url,
                port = prefs.port,
                mode = ConnectionMode.REMOTE,
                apiKey = prefs.apiKey,
                useTls = true
            )
            if (tryPing(config, REMOTE_TIMEOUT_SEC)) {
                prefs.lastMode = "remote"
                return Result.success(config)
            }
        }

        // 4. Fallback: el usuario configura manualmente
        return Result.failure(NoConnectionException(
            "No se pudo conectar. Configure manualmente."
        ))
    }

    private suspend fun tryPing(config: ServerConfig, timeoutMs: Long): Boolean {
        return withContext(Dispatchers.IO) {
            try {
                val url = "${config.baseUrl}/api/v1/ping"
                val client = OkHttpClient.Builder()
                    .connectTimeout(timeoutMs, TimeUnit.MILLISECONDS)
                    .readTimeout(timeoutMs, TimeUnit.MILLISECONDS)
                    .apply {
                        if (config.apiKey != null) {
                            addInterceptor { chain ->
                                val req = chain.request().newBuilder()
                                    .addHeader("Authorization", "Bearer ${config.apiKey}")
                                    .build()
                                chain.proceed(req)
                            }
                        }
                        if (!config.useTls) {
                            // Aceptar certificados self-signed en local
                            hostnameVerifier { _, _ -> true }
                        }
                    }
                    .build()

                val request = okhttp3.Request.Builder().url(url).get().build()
                val response = client.newCall(request).await()
                response.isSuccessful
            } catch (e: Exception) {
                false
            }
        }
    }
}
```

### Código: SessionManager.kt

```kotlin
// data/repository/SessionManager.kt
package com.gwen.android.data.repository

import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

class SessionManager(context: Context) {

    private val masterKey = MasterKey.Builder(context)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
        .build()

    private val prefs = EncryptedSharedPreferences.create(
        context,
        "gwen_secure_prefs",
        masterKey,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )

    var lastLocalIp: String?
        get() = prefs.getString("last_local_ip", null)
        set(value) = prefs.edit().putString("last_local_ip", value).apply()

    var remoteUrl: String?
        get() = prefs.getString("remote_url", null)
        set(value) = prefs.edit().putString("remote_url", value).apply()

    var port: Int
        get() = prefs.getInt("port", 8000)
        set(value) = prefs.edit().putInt("port", value).apply()

    var lastMode: String
        get() = prefs.getString("last_mode", "auto")
        set(value) = prefs.edit().putString("last_mode", value).apply()

    var apiKey: String?
        get() = prefs.getString("api_key", null)
        set(value) = prefs.edit().putString("api_key", value).apply()

    var remoteSetup: String?
        get() = prefs.getString("remote_setup_type", null)
        set(value) = prefs.edit().putString("remote_setup_type", value).apply()

    val isFirstRun: Boolean
        get() = prefs.getBoolean("first_run", true)
}
```

### UI: Indicador de modo en TopBar

```
┌─────────────────────────────────────┐
│  🏠 Local   Gwen AI           ⚙️    │  ← WiFi, baja latencia
│  🌐 Remoto  Gwen AI           ⚙️    │  ← Internet, autenticado
│  ⚠ Offline  Gwen AI           ⚙️    │  ← Sin conexión
└─────────────────────────────────────┘
```

### UI: Pantalla de configuración

```
┌─────────────────────────────────────┐
│  ← Conexión                         │
├─────────────────────────────────────┤
│                                     │
│  Tipo de conexión                   │
│  ┌─────────────────────────────┐    │
│  │ ● Automático (recomendado)  │    │
│  │ ○ Solo Local (WiFi)         │    │
│  │ ○ Solo Remoto (Internet)    │    │
│  │ ○ Manual                    │    │
│  └─────────────────────────────┘    │
│                                     │
│  ─── Remoto ───                     │
│  URL                                │
│  ┌─────────────────────────────┐    │
│  │ mi-casa.duckdns.org        │    │
│  └─────────────────────────────┘    │
│                                     │
│  Puerto                             │
│  ┌─────────────────────────────┐    │
│  │ 8000                        │    │
│  └─────────────────────────────┘    │
│                                     │
│  API Key                            │
│  ┌─────────────────────────────┐    │
│  │ ••••••••••••••             │    │
│  └─────────────────────────────┘    │
│                                     │
│  ┌─────────────────────────────┐    │
│  │       PROBAR CONEXIÓN       │    │
│  └─────────────────────────────┘    │
│                                     │
│  ✅ Gwen v2.0 en línea              │
│  🏠 Conectado por WiFi local        │
│  Módulos: 22 activos | CPU: 15%     │
│                                     │
│  ┌─────────────────────────────┐    │
│  │  Ayuda: ¿Cómo exponer Gwen  │    │
│  │  a Internet de forma segura?│    │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
```

---

## ☁️ Conexión Remota: Cómo exponer Gwen a Internet

La app se conecta por HTTP/WebSocket al puerto 8000 de Gwen. Para acceso desde fuera de casa, necesitas que ese puerto sea accesible desde Internet. Aquí están las opciones, ordenadas por facilidad:

### Opción 1: Tailscale Funnel ⭐ (RECOMENDADO)

```bash
# En la PC donde corre Gwen:
winget install tailscale
tailscale up
tailscale serve --bg --https=443 http://localhost:8000
# Obtiene URL tipo: https://mi-pc.tailnet-name.ts.net
```

| Pros | Contras |
|------|---------|
| ✅ Sin abrir puertos del router | ⚠ Requiere Tailscale instalado |
| ✅ TLS automático (HTTPS) | |
| ✅ Gratis (personal) | |
| ✅ End-to-end encriptado | |
| ✅ No expone otros servicios | |

**URL que configuras en la app:** `https://mi-pc.tailnet-name.ts.net` (sin puerto, Tailscale hace proxy)

---

### Opción 2: Cloudflare Tunnel

```bash
# En la PC donde corre Gwen:
winget install cloudflare.cloudflared
cloudflared tunnel login
cloudflared tunnel create gwen
cloudflared tunnel route dns gwen gwen.mi-dominio.com
cloudflared tunnel run --url http://localhost:8000 gwen
```

| Pros | Contras |
|------|---------|
| ✅ Sin abrir puertos | ⚠ Necesitas dominio (o usar trycloudflare.com) |
| ✅ TLS automático | ⚠ trycloudflare URLs son temporales |
| ✅ Gratis | |
| ✅ Dashboard web | |

**URL que configuras en la app:**
- Con dominio propio: `https://gwen.mi-dominio.com`
- Con quick tunnel: `https://random-name.trycloudflare.com`

---

### Opción 3: DDNS + Port Forwarding (tradicional)

```bash
# 1. Registrar DDNS gratuito (duckdns.org, no-ip.com)
# 2. Configurar router: forward puerto 8000 → IP de la PC
# 3. En la PC, verificar que el firewall permite el puerto:
netsh advfirewall firewall add rule name="Gwen API" dir=in action=allow protocol=TCP localport=8000
```

| Pros | Contras |
|------|---------|
| ✅ Sin software extra | ⚠ Expones el puerto a Internet |
| ✅ Funciona con cualquier dominio | ⚠ Necesitas configurar router |
| ✅ URLs persistentes | ⚠ Sin TLS por defecto (necesitas nginx/certbot) |

**URL que configuras en la app:** `http://mi-casa.duckdns.org:8000`

---

### Opción 4: ngrok (pruebas rápidas)

```bash
ngrok http 8000
# Obtiene URL tipo: https://abc123.ngrok.io
```

| Pros | Contras |
|------|---------|
| ✅ Cero configuración | ⚠ URLs cambian cada reinicio (free tier) |
| ✅ TLS automático | ⚠ Límite de conexiones (free tier) |
| ✅ Ideal para development | ⚠ No recomendado para producción |

**URL que configuras en la app:** `https://abc123.ngrok.io`

---

### Comparativa final

| | Tailscale | Cloudflare | DDNS+Port | ngrok |
|---|---|---|---|---|
| Dificultad setup | ⭐ Fácil | ⭐⭐ Medio | ⭐⭐⭐ Difícil | ⭐ Fácil |
| Sin abrir router | ✅ | ✅ | ❌ | ✅ |
| TLS/HTTPS | ✅ Auto | ✅ Auto | ❌ Manual | ✅ Auto |
| URL persistente | ✅ | ✅ (con dominio) | ✅ | ❌ Free tier |
| Gratis | ✅ | ✅ | ✅ | ✅ (limitado) |
| Seguridad | Alta | Alta | Media | Media |
| Recomendado para | **Uso diario** | Dominio propio | Sin software extra | Pruebas |

---

## 🏗️ Stack Tecnológico

| Capa | Tecnología | Razón |
|------|-----------|-------|
| Lenguaje | Kotlin | Nativo Android, moderno, conciso |
| UI | Jetpack Compose + Material 3 | Gemini-like, animaciones fluidas |
| HTTP | Retrofit + OkHttp | REST API + WebSocket |
| Tiempo real | OkHttp WebSocket | Chat en vivo |
| Estado | ViewModel + StateFlow | Reactividad, lifecycle-aware |
| Async | Kotlin Coroutines + Flow | Async sin callbacks |
| Imágenes | Coil | Iconos, screenshots |
| Navegación | Navigation Compose | Bottom nav + deep linking |
| Seguridad | EncryptedSharedPreferences | Token, URL remota |
| DI | Hilt | Inyección limpia |

---

## 📐 Arquitectura de la App

```
┌─────────────────────────────────────────────────────────┐
│                     UI LAYER (Compose)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │  Chat    │  │ Módulos  │  │ Terminal │  │ Estado  │ │
│  │ Screen   │  │ Screen   │  │ Screen   │  │ Screen  │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘ │
│       │             │             │             │       │
│  ┌────▼─────┐  ┌────▼─────┐  ┌────▼─────┐  ┌────▼────┐ │
│  │  ChatVM  │  │ ModuleVM │  │  TermVM  │  │StatusVM │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘ │
├───────┼─────────────┼─────────────┼─────────────┼───────┤
│       │       DOMAIN LAYER        │             │       │
│  ┌────▼─────┐  ┌────▼─────┐  ┌────▼─────────────▼────┐ │
│  │ SendMsg  │  │GetModules│  │   ExecuteCommand      │ │
│  │ UseCase  │  │ UseCase  │  │   UseCase             │ │
│  └────┬─────┘  └────┬─────┘  └──────────┬────────────┘ │
├───────┼─────────────┼───────────────────┼───────────────┤
│       │         DATA LAYER             │               │
│  ┌────▼─────────────▼───────────────────▼────────────┐ │
│  │              GwenRepository                        │ │
│  │  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │ │
│  │  │ REST API │  │WebSocket │  │ConnectionManager│  │ │
│  │  │(Retrofit)│  │ (OkHttp) │  │(auto-detect)   │  │ │
│  │  └────┬─────┘  └────┬─────┘  └────────┬───────┘  │ │
│  └───────┼─────────────┼──────────────────┼───────────┘ │
└──────────┼─────────────┼──────────────────┼─────────────┘
           │             │                  │
     ┌─────▼─────────────▼──────────────────▼──────────┐
     │              GWEN PC (api_server.py)              │
     │  FastAPI :8000  +  SQLite  +  ModuleRegistry      │
     │  🏠 Red local: http://192.168.x.x:8000            │
     │  🌐 Internet: via Tailscale/Cloudflare/DDNS       │
     └──────────────────────────────────────────────────┘
```

---

## 🧭 Navegación (3+1 tabs)

```
┌──────────────────────────────────────────────────────┐
│  [💬 Chat]   [🧩 Módulos]   [⬛ Terminal]   [📊]    │
└──────────────────────────────────────────────────────┘

Chat:      Conversación con Gwen, WebSocket tiempo real
           Burbujas estilo Gemini, markdown, typing dots

Módulos:   Grid auto-descubierto desde API de Gwen
           Toggle enable/disable, triggers, categorías

Terminal:  Consola en vivo con historial
           Ejecutar comandos, output coloreado

Estado:    (Fase 6) Dashboard: CPU, RAM, batería, uptime
```

---

## 🔌 API de Gwen — Endpoints

### Existentes (sin cambios)
```
GET  /api/v1/ping              → health check
GET  /api/v1/system            → CPU, RAM, disco
GET  /api/v1/battery           → batería
GET  /api/v1/processes         → procesos
GET  /api/v1/windows           → ventanas
GET  /api/v1/volume            → volumen
POST /api/v1/volume            → cambiar volumen
POST /api/v1/media             → media keys
GET  /api/v1/screenshot        → captura PNG
GET  /api/v1/models            → modelos IA
POST /api/v1/model             → cambiar modelo
GET  /api/v1/config            → configuración
PATCH /api/v1/config           → cambiar configuración
GET  /api/v1/modules           → lista simple
WS   /ws/chat                  → chat tiempo real
```

### NUEVOS — implementar en api_server.py

```python
# ═══ MÓDULOS — Metadata completa ═══
GET /api/v1/modules/detail
# → { modules: [{ name, display_name, icon, description,
#      category, triggers, priority, enabled, has_config }],
#     total: 22, active: 18 }

POST /api/v1/modules/{name}/toggle
# Body: {"enabled": true/false}

# ═══ CHAT — REST (fallback cuando WS no disponible) ═══
POST /api/v1/chat
# Body: {"text": "lanza destiny 2"}
# → {"ok": true, "response": "🎮 Lanzando...", "module": "geforcenow"}

# ═══ TERMINAL ═══
GET  /api/v1/terminal/history?limit=50
POST /api/v1/terminal/execute
# Body: {"command": "dir"} → {"ok": true, "output": "...", "error": ""}

# ═══ ESTADO ═══
GET /api/v1/status
# → { uptime_seconds, active_modules, total_modules,
#     api_version, connected_clients, gwen_version }
```

---

## 🧩 Auto-Descubrimiento de Módulos

### En Gwen: metadatos en BaseModule

```python
# modules/base.py — NUEVOS atributos
class BaseModule(ABC):
    nombre: str = "base"
    prioridad: int = 100
    enabled: bool = True

    # ── Metadata para la app Android ──
    icon: str = "extension"           # Material Design icon name
    display_name: str = ""            # Nombre legible
    description: str = ""             # Descripción corta
    category: str = "general"         # gaming, system, media, files, tools
    triggers_display: list[str] = []  # Ej: ["lanza <juego>", "cómo va la cola"]
    has_config: bool = False
    config_keys: list[str] = []
```

### En la App: polling cada 30s

```
App inicia → GET /api/v1/modules/detail → 22 módulos → renderizar
Cada 30s   → GET /api/v1/modules/detail → si cambió → actualizar UI
Pull-down  → refresh manual instantáneo
Nuevo módulo en PC → siguiente poll (≤30s) → aparece en app
```

---

## 📁 Estructura del proyecto

```
android_app/                              ← YA EXISTE
├── build.gradle.kts                      ← YA EXISTE
├── settings.gradle.kts                   ← YA EXISTE (rootProject.name = "GwenAndroidApp")
│
├── app/
│   ├── build.gradle.kts                  ← YA EXISTE (Retrofit, OkHttp, Coil, Compose, Navigation)
│   │
│   └── src/main/java/com/gwen/android/
│       │
│       ├── GwenApplication.kt            # Hilt app class
│       ├── MainActivity.kt               # Single Activity
│       │
│       ├── data/
│       │   ├── remote/
│       │   │   ├── GwenApiService.kt     # Retrofit (todos los endpoints)
│       │   │   ├── GwenWebSocket.kt      # OkHttp WS manager
│       │   │   ├── ConnectionManager.kt  # ⭐ NUEVO — auto-detect local/remoto
│       │   │   └── dto/
│       │   │       ├── ModuleDto.kt
│       │   │       ├── ChatMessageDto.kt
│       │   │       ├── SystemInfoDto.kt
│       │   │       ├── TerminalLineDto.kt
│       │   │       └── StatusDto.kt
│       │   ├── repository/
│       │   │   ├── GwenRepository.kt
│       │   │   └── SessionManager.kt     # ⭐ NUEVO — EncryptedSharedPreferences
│       │   └── di/
│       │       └── NetworkModule.kt      # Hilt: Retrofit, OkHttp
│       │
│       ├── domain/
│       │   ├── model/
│       │   │   ├── Module.kt
│       │   │   ├── GwenMessage.kt
│       │   │   ├── TerminalOutput.kt
│       │   │   ├── SystemStatus.kt
│       │   │   └── ConnectionState.kt    # ⭐ NUEVO
│       │   └── usecase/
│       │       ├── SendMessageUseCase.kt
│       │       ├── GetModulesUseCase.kt
│       │       ├── ToggleModuleUseCase.kt
│       │       ├── ExecuteCommandUseCase.kt
│       │       └── GetStatusUseCase.kt
│       │
│       └── ui/
│           ├── theme/
│           │   ├── Theme.kt
│           │   ├── Color.kt
│           │   └── Type.kt
│           ├── navigation/
│           │   ├── GwenNavHost.kt
│           │   └── Screen.kt
│           ├── connection/               # ⭐ NUEVA sección
│           │   ├── ConnectionScreen.kt   # Configuración manual
│           │   └── ConnectionViewModel.kt
│           ├── chat/
│           │   ├── ChatScreen.kt
│           │   ├── ChatViewModel.kt
│           │   └── components/
│           │       ├── MessageBubble.kt
│           │       ├── ChatInputBar.kt
│           │       ├── QuickActions.kt
│           │       └── TypingDots.kt
│           ├── modules/
│           │   ├── ModulesScreen.kt
│           │   ├── ModulesViewModel.kt
│           │   ├── ModuleDetailSheet.kt
│           │   └── components/
│           │       ├── ModuleCard.kt
│           │       ├── ModuleIcon.kt
│           │       ├── CategoryFilter.kt
│           │       └── TriggerChip.kt
│           ├── terminal/
│           │   ├── TerminalScreen.kt
│           │   ├── TerminalViewModel.kt
│           │   └── components/
│           │       ├── TerminalOutput.kt
│           │       └── CommandInput.kt
│           └── status/                   # Fase 6 (futuro)
│               ├── StatusScreen.kt
│               ├── StatusViewModel.kt
│               └── components/
│                   ├── GaugeCard.kt
│                   └── ModuleHealth.kt
```

---

## 🎨 Diseño de UI

### Chat Screen

```
┌─────────────────────────────────┐
│  🏠 Local  Gwen AI        ⚙️    │
├─────────────────────────────────┤
│                                 │
│  ┌───────────────────────────┐  │
│  │ Buenos días, Señor.       │  │  ← Gwen (izquierda, gris)
│  │ ¿En qué puedo ayudarle?   │  │
│  └───────────────────────────┘  │
│                                 │
│            ┌─────────────────┐ │
│            │ Abre Destiny 2  │ │  ← Usuario (derecha, azul)
│            └─────────────────┘ │
│                                 │
│  ┌───────────────────────────┐  │
│  │ 🎮 Lanzando Destiny 2    │  │
│  │ acceso directo escritorio │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐  │
│  │ ○ ○ ○  Gwen escribiendo  │  │  ← Typing dots
│  └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘  │
│                                 │
│  [lanza] [volumen] [cola] [sys]│  ← Quick actions
│                                 │
├─────────────────────────────────┤
│  🎤 ┌────────────────────┐  📎 │
│     │ Escribe un mensaje │  ➤ │
│     └────────────────────┘     │
└─────────────────────────────────┘
```

### Modules Screen

```
┌─────────────────────────────────┐
│  Módulos                  🔄    │
│  [Todo][Gaming][Sistema][Media] │  ← Category filter
├─────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐    │
│  │ 🎮       │  │ 🔊       │    │
│  │GeForceNOW│  │ Volumen   │    │
│  │Lanza y   │  │Ajusta el  │    │
│  │monitorea │  │volumen    │    │
│  │[lanza]   │  │[vol 50]   │    │
│  │     ⬤───│  │     ⬤───  │    │
│  └──────────┘  └──────────┘    │
│  ┌──────────┐  ┌──────────┐    │
│  │ ⬛       │  │ 📸       │    │
│  │Terminal  │  │Capturas   │    │
│  │[sh dir]  │  │[captura]  │    │
│  │     ⬤───│  │     ○────  │    │
│  └──────────┘  └──────────┘    │
└─────────────────────────────────┘
```

### Terminal Screen

```
┌─────────────────────────────────┐
│  Terminal                 🗑️    │
├─────────────────────────────────┤
│  [16:05:01] Gwen iniciada       │
│  [16:05:02] 22 módulos cargados │
│  [16:05:30] Usuario: lanza d2   │
│  [16:05:31] GFN: Lanzando...    │
│  [16:05:59] ⚠ GPU: 78°C        │
│  [16:06:15] ✅ Juego en vivo    │
├─────────────────────────────────┤
│  > ▌                             │
└─────────────────────────────────┘
```

---

## 🔄 Flujo de Datos

### Inicio de la app
```
1. ConnectionManager.autoConnect()
2. ¿Local? → http://192.168.1.x:8000/api/v1/ping
3. ¿Remoto? → https://mi-casa.duckdns.org:8000/api/v1/ping
4. Si falla → ConnectionScreen (manual)
5. GET /api/v1/modules/detail
6. GET /api/v1/status
7. WS /ws/chat → conectar
8. GET /api/v1/terminal/history
9. UI lista → Chat screen
```

### Enviar mensaje
```
Usuario: "lanza destiny 2"
  → WS → {"type":"message","text":"lanza destiny 2"}
  → Gwen: ModuleRegistry.dispatch()
  → Gwen: WS → {"type":"response","text":"🎮 Lanzando..."}
  → ChatVM: agrega MessageBubble(gwen, "🎮 Lanzando...")
```

### Toggle módulo
```
Usuario: desactiva GeForceNOW
  → POST /api/v1/modules/geforcenow/toggle {"enabled":false}
  → Gwen desactiva en caliente
  → App refresca lista
```

---

## 📋 Plan de Fases

### Fase 0 — Decisiones ✅ (completado)
- [x] Stack: Kotlin/Compose
- [x] Monorepo: `android_app/`
- [x] Módulos: API-based
- [x] Conexión: Dual auto-detect
- [x] Remoto: Tailscale + Cloudflare + DDNS
- [x] Diseño de arquitectura (este documento)

### Fase 1 — Gwen Backend (nuevos endpoints)
- [ ] `GET /api/v1/modules/detail`
- [ ] `POST /api/v1/modules/{name}/toggle`
- [ ] `POST /api/v1/chat` (REST fallback)
- [ ] `GET /api/v1/terminal/history`
- [ ] `POST /api/v1/terminal/execute`
- [ ] `GET /api/v1/status`
- [ ] Metadata en `BaseModule` (icon, display_name, description, category, triggers)
- [ ] Metadata en cada uno de los 22 módulos

### Fase 2 — Android: Conexión + Base
- [ ] `ConnectionManager.kt` — auto-detect local/remoto
- [ ] `SessionManager.kt` — EncryptedSharedPreferences
- [ ] `ConnectionScreen.kt` + `ConnectionViewModel.kt`
- [ ] `GwenApiService.kt` — Retrofit interface completa
- [ ] `NetworkModule.kt` — Hilt DI
- [ ] Tema Material 3 (colores Gwen, dark/light)
- [ ] Navigation host + bottom bar + splash

### Fase 3 — Chat
- [ ] `GwenWebSocket.kt` — OkHttp WS
- [ ] `ChatViewModel.kt` + `ChatScreen.kt`
- [ ] `MessageBubble.kt` — markdown, user/gwen styles
- [ ] `ChatInputBar.kt` — texto + voz + adjuntar
- [ ] `QuickActions.kt` — chips de triggers frecuentes
- [ ] `TypingDots.kt` — animación escribiendo

### Fase 4 — Módulos
- [ ] `ModulesViewModel.kt` — auto-refresh 30s
- [ ] `ModulesScreen.kt` — grid LazyVerticalStaggeredGrid
- [ ] `ModuleCard.kt` — icono, nombre, desc, triggers, toggle
- [ ] `CategoryFilter.kt` — chips de categoría
- [ ] `ModuleDetailSheet.kt` — bottom sheet
- [ ] `TriggerChip.kt` — tap → envía al chat

### Fase 5 — Terminal
- [ ] `TerminalViewModel.kt` — polling + execute
- [ ] `TerminalScreen.kt` — output scrollable + input
- [ ] `TerminalOutput.kt` — líneas coloreadas
- [ ] `CommandInput.kt` — input con historial

### Fase 6 — Estado (futuro)
- [ ] Dashboard CPU/RAM/Disco/Batería
- [ ] Gráficos circulares
- [ ] Lista de salud de módulos
- [ ] Uptime y versión

### Fase 7 — Pulido
- [ ] Animaciones (shimmer, transiciones)
- [ ] Manejo de errores (offline, timeout, auth)
- [ ] Notificaciones push (cuando Gwen responde)
- [ ] Widget Android
- [ ] Wear OS companion (opcional)

---

## 📊 Resumen

| Categoría | Total |
|-----------|-------|
| Endpoints nuevos en Gwen | 6 |
| Atributos nuevos en BaseModule | 7 |
| Archivos Kotlin (total) | ~50 |
| Fases | 7 (0-6) + pulido |
| Métodos de conexión remota documentados | 4 (Tailscale, Cloudflare, DDNS, ngrok) |
