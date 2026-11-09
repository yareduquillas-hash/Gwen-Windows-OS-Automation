# 🎨 Sistema de Diseño — Gwen Android App

> **Basado en:** `Diseño Estilo.md` — Plataforma de Inversión y Ahorro
> **Adaptado para:** Gwen Android App — Chat, Módulos, Terminal, Estado
> **Plataforma:** Jetpack Compose + Material 3
> **Temas:** Verde (principal) · Púrpura (variante) · Claro/Oscuro en ambos
> **Fecha:** 2026-08-02

---

## 1. 🟢 Tema Principal: Verde

### Modo Claro (Green Light)

| Token | Hex | Vista previa | Uso en Gwen |
|-------|-----|-------------|-------------|
| `Background` | `#F3F6F4` | ████████ | Fondo de pantallas |
| `Surface` | `#FFFFFF` | ████████ | Tarjetas, burbujas de Gwen, cards de módulos |
| `SurfaceVariant` | `#E3EDE6` | ████████ | Input de chat, chips, fondo terminal, filtros |
| `Primary` | `#1E5D3A` | ████████ | Botones CTA, toggle ON, iconos activos, burbuja usuario |
| `OnPrimary` | `#FFFFFF` | ████████ | Texto sobre Primary |
| `Secondary` | `#E3EDE6` | ████████ | Botones secundarios, chips inactivos |
| `OnSecondary` | `#1E5D3A` | ████████ | Texto sobre Secondary |
| `PrimaryText` | `#121A15` | ████████ | Títulos, cuerpo de texto, nombre de módulos |
| `SecondaryText` | `#6B7280` | ████████ | Subtítulos, timestamps, etiquetas, descripción |
| `Error` | `#DC2626` | ████████ | Errores, toast de fallo, módulo caído |
| `Success` | `#16A34A` | ████████ | Conexión OK, confirmaciones, juego en vivo |
| `SurfaceBorder` | `#D1D5DB` | ████████ | Bordes sutiles en dark mode fallback |

### Modo Oscuro (Green Dark)

| Token | Hex | Vista previa | Uso en Gwen |
|-------|-----|-------------|-------------|
| `Background` | `#090C0A` | ████████ | Fondo de pantallas — negro con matiz verde |
| `Surface` | `#151816` | ████████ | Tarjetas, burbujas de Gwen, cards de módulos |
| `SurfaceVariant` | `#1E221F` | ████████ | Input de chat, chips, fondo terminal |
| `Primary` | `#00D26A` | ████████ | Botones CTA, toggle ON, iconos activos, burbuja usuario (verde neón) |
| `OnPrimary` | `#090C0A` | ████████ | Texto sobre Primary (negro para contraste) |
| `Secondary` | `#2A332D` | ████████ | Botones secundarios, chips inactivos |
| `OnSecondary` | `#00D26A` | ████████ | Texto sobre Secondary |
| `PrimaryText` | `#FFFFFF` | ████████ | Títulos, cuerpo de texto — blanco puro |
| `SecondaryText` | `#88908B` | ████████ | Subtítulos, timestamps, etiquetas — gris claro |
| `Error` | `#FF4444` | ████████ | Errores — rojo vibrante (del diseño original) |
| `Success` | `#00D26A` | ████████ | Confirmaciones — mismo verde neón que Primary |
| `SurfaceBorder` | `#FFFFFF` (10%) | ████████ | Borde sutil 1dp con opacidad |

### Compose — Paleta Verde

```kotlin
// ui/theme/Color.kt
// ── Green Light ──
val GreenLightBg = Color(0xFFF3F6F4)
val GreenLightSurface = Color(0xFFFFFFFF)
val GreenLightSurfaceVariant = Color(0xFFE3EDE6)
val GreenLightPrimary = Color(0xFF1E5D3A)
val GreenLightOnPrimary = Color(0xFFFFFFFF)
val GreenLightSecondary = Color(0xFFE3EDE6)
val GreenLightOnSecondary = Color(0xFF1E5D3A)
val GreenLightPrimaryText = Color(0xFF121A15)
val GreenLightSecondaryText = Color(0xFF6B7280)
val GreenLightError = Color(0xFFDC2626)
val GreenLightSuccess = Color(0xFF16A34A)
val GreenLightBorder = Color(0xFFD1D5DB)

// ── Green Dark ──
val GreenDarkBg = Color(0xFF090C0A)
val GreenDarkSurface = Color(0xFF151816)
val GreenDarkSurfaceVariant = Color(0xFF1E221F)
val GreenDarkPrimary = Color(0xFF00D26A)
val GreenDarkOnPrimary = Color(0xFF090C0A)
val GreenDarkSecondary = Color(0xFF2A332D)
val GreenDarkOnSecondary = Color(0xFF00D26A)
val GreenDarkPrimaryText = Color(0xFFFFFFFF)
val GreenDarkSecondaryText = Color(0xFF88908B)
val GreenDarkError = Color(0xFFFF4444)
val GreenDarkSuccess = Color(0xFF00D26A)
```

---

## 2. 🟣 Tema Variante: Púrpura

### Modo Claro (Purple Light)

*Del diseño original: gradiente lavanda vibrante con glassmorphism.*

| Token | Hex | Vista previa | Uso en Gwen |
|-------|-----|-------------|-------------|
| `Background` | `#A385FF` → `#C0A9FF` | ████████ | Fondo con gradiente vertical |
| `Surface` | `#FFFFFF` | ████████ | Tarjetas sólidas o glassmorphism (`rgba(255,255,255,0.4)`) |
| `SurfaceVariant` | `#F4F0FF` | ████████ | Chips, fondo terminal, inputs |
| `Primary` | `#1A1A1A` | ████████ | Botones CTA, toggle ON — casi negro para contraste |
| `OnPrimary` | `#FFFFFF` | ████████ | Texto sobre botones oscuros |
| `Secondary` | `#6C38FF` | ████████ | Iconos activos, tags, acentos secundarios |
| `OnSecondary` | `#FFFFFF` | ████████ | Texto sobre Secondary |
| `PrimaryText` | `#121212` | ████████ | Títulos sobre tarjetas blancas |
| `SecondaryText` | `#7C6F9E` | ████████ | Subtítulos, timestamps — púrpura grisáceo |
| `Error` | `#DC2626` | ████████ | Errores |
| `Success` | `#6C38FF` | ████████ | Confirmaciones — púrpura eléctrico |
| `SurfaceBorder` | `rgba(255,255,255,0.6)` | ████████ | Borde glassmorphism |

### Modo Oscuro (Purple Dark)

*Complemento diseñado para completar el tema — no está en el archivo original.*

| Token | Hex | Vista previa | Uso en Gwen |
|-------|-----|-------------|-------------|
| `Background` | `#0D0A1A` | ████████ | Negro con matiz púrpura profundo |
| `Surface` | `#1A1528` | ████████ | Tarjetas — gris púrpura oscuro |
| `SurfaceVariant` | `#241F35` | ████████ | Chips, terminal, inputs |
| `Primary` | `#A78BFA` | ████████ | Botones CTA, toggle ON — lavanda brillante |
| `OnPrimary` | `#0D0A1A` | ████████ | Texto sobre Primary |
| `Secondary` | `#6C38FF` | ████████ | Iconos activos, acentos |
| `OnSecondary` | `#FFFFFF` | ████████ | Texto sobre Secondary |
| `PrimaryText` | `#FFFFFF` | ████████ | Títulos — blanco puro |
| `SecondaryText` | `#9B8EC4` | ████████ | Subtítulos — lavanda grisáceo |
| `Error` | `#FF4444` | ████████ | Errores — rojo vibrante |
| `Success` | `#A78BFA` | ████████ | Confirmaciones — lavanda |
| `SurfaceBorder` | `#FFFFFF` (8%) | ████████ | Borde sutil 1dp |

### Compose — Paleta Púrpura

```kotlin
// ── Purple Light ──
val PurpleLightBgStart = Color(0xFFA385FF)
val PurpleLightBgEnd = Color(0xFFC0A9FF)
val PurpleLightSurface = Color(0xFFFFFFFF)
val PurpleLightSurfaceGlass = Color(0x66FFFFFF)  // rgba(255,255,255,0.4)
val PurpleLightSurfaceVariant = Color(0xFFF4F0FF)
val PurpleLightPrimary = Color(0xFF1A1A1A)
val PurpleLightOnPrimary = Color(0xFFFFFFFF)
val PurpleLightSecondary = Color(0xFF6C38FF)
val PurpleLightOnSecondary = Color(0xFFFFFFFF)
val PurpleLightPrimaryText = Color(0xFF121212)
val PurpleLightSecondaryText = Color(0xFF7C6F9E)
val PurpleLightError = Color(0xFFDC2626)
val PurpleLightSuccess = Color(0xFF6C38FF)
val PurpleLightBorder = Color(0x99FFFFFF)  // rgba(255,255,255,0.6)

// ── Purple Dark ──
val PurpleDarkBg = Color(0xFF0D0A1A)
val PurpleDarkSurface = Color(0xFF1A1528)
val PurpleDarkSurfaceVariant = Color(0xFF241F35)
val PurpleDarkPrimary = Color(0xFFA78BFA)
val PurpleDarkOnPrimary = Color(0xFF0D0A1A)
val PurpleDarkSecondary = Color(0xFF6C38FF)
val PurpleDarkOnSecondary = Color(0xFFFFFFFF)
val PurpleDarkPrimaryText = Color(0xFFFFFFFF)
val PurpleDarkSecondaryText = Color(0xFF9B8EC4)
val PurpleDarkError = Color(0xFFFF4444)
val PurpleDarkSuccess = Color(0xFFA78BFA)
```

### Efecto Glassmorphism (solo Purple Light)

```kotlin
// ui/theme/Glassmorphism.kt
@Composable
fun Modifier.glassmorphism(): Modifier = this
    .background(
        color = PurpleLightSurfaceGlass,
        shape = RoundedCornerShape(24.dp)
    )
    .border(
        width = 1.dp,
        color = PurpleLightBorder,
        shape = RoundedCornerShape(24.dp)
    )
    // backdrop-filter: blur(20px) — requiere API 31+
    // Alternativa: usar Modifier.blur(20.dp) en API 31+
```

---

## 3. 🔤 Tipografía (común a ambos temas)

*Del diseño original: Inter, SF Pro Display o Roboto.*

| Rol | Familia | Weight | Size | Uso en Gwen |
|-----|---------|--------|------|-------------|
| Display | Inter / SF Pro | Bold 700 | 32-40sp | No usado en Gwen (opcional splash) |
| Heading | Inter | SemiBold 600 | 20-24sp | Título de pantalla, nombre de módulo en detalle |
| Title | Inter | Medium 500 | 16-18sp | Nombre en ModuleCard, título de sección |
| Body | Inter | Regular 400 | 14-16sp | Mensajes del chat, cuerpo de texto |
| Caption | Inter | Regular 400 | 12sp | Timestamps, etiquetas, posición cola |
| Button | Inter | Medium 500 | 14sp | Botones, chips, tabs, bottom nav labels |
| Code | JetBrains Mono | Regular 400 | 13sp | Terminal output |

### Pesos (Weights) — del diseño original

| Weight | Uso específico |
|--------|---------------|
| Regular (400) | Cuerpo de texto, etiquetas secundarias, descripciones de módulos |
| Medium (500) | Botones, subtítulos, nombres de módulos en cards |
| SemiBold (600) / Bold (700) | Títulos de sección, hora en el chat, valor en GaugeCard |

### Escala — del diseño original

| Escala | Size | Uso en Gwen |
|--------|------|-------------|
| Display | 32-40sp | Nombre "Gwen" en splash screen |
| Heading | 20-24sp | "Chat", "Módulos", "Terminal" en TopBar |
| Body | 14-16sp | Mensajes, descripciones |
| Caption | 12sp | Timestamps, etiquetas |

```kotlin
// ui/theme/Type.kt
val GwenTypography = Typography(
    displayLarge = TextStyle(  // Splash "GWEN"
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.Bold,
        fontSize = 36.sp
    ),
    headlineMedium = TextStyle(  // TopBar titles
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.SemiBold,
        fontSize = 22.sp
    ),
    titleMedium = TextStyle(  // ModuleCard name
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.Medium,
        fontSize = 16.sp
    ),
    bodyLarge = TextStyle(  // Chat messages
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.Normal,
        fontSize = 16.sp,
        lineHeight = 24.sp
    ),
    bodyMedium = TextStyle(  // Module descriptions
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.Normal,
        fontSize = 14.sp,
        lineHeight = 20.sp
    ),
    labelMedium = TextStyle(  // Buttons, chips, bottom nav
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.Medium,
        fontSize = 14.sp
    ),
    bodySmall = TextStyle(  // Timestamps, captions
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.Normal,
        fontSize = 12.sp,
        lineHeight = 16.sp
    )
)
```

---

## 4. 📐 Geometría — Border Radius (del diseño original)

| Elemento | Radio | Origen |
|----------|-------|--------|
| Tarjetas principales / Bottom Sheets | 24-32dp | Original: "24px a 32px — squircle amplio" |
| Tarjetas internas / Widgets | 16dp | Original: "16px" |
| Botones CTA | 999dp (pill) | Original: "Totalmente redondeados / píldora" |
| Chips de filtro | 8-12dp | Original: "8px a 12px" |

### Aplicado a componentes Gwen

| Componente | Border Radius |
|------------|--------------|
| ModuleCard | 24.dp |
| ModuleDetailSheet (top) | 24.dp |
| StatusCard, GaugeCard | 16.dp |
| MessageBubble (user) | 20.dp (topLeft = 4.dp) |
| MessageBubble (gwen) | 20.dp (topRight = 4.dp) |
| ChatInputBar | 28.dp (pill) |
| Botón "Enviar" | 999.dp (circle) |
| Botón "Conectar" | 999.dp (pill) |
| CategoryFilter chips | 12.dp |
| QuickActions chips | 12.dp |
| TriggerChip en ModuleCard | 8.dp |
| CommandInput (terminal) | 8.dp |
| Switch track | 999.dp |
| BottomSheet drag handle | 999.dp |

---

## 5. 🌑 Sombras y Profundidad (del diseño original)

### Modo Claro — ambos temas (Green + Purple)
*Del original: "Sombras muy suaves, amplias y difuminadas."*

| Elemento | Elevación | Efecto |
|----------|-----------|--------|
| Cards en grid | 2.dp | `shadow(0, 10, 30, rgba(0,0,0,0.05))` |
| TopBar | 0.dp | Plana, separada por color de fondo |
| BottomBar | 4.dp | `shadow(0, -4, 12, rgba(0,0,0,0.06))` |
| BottomSheet | 8.dp | `shadow(0, -8, 40, rgba(0,0,0,0.12))` |
| Burbujas chat | 0.dp | Sin sombra, separadas por color |

### Modo Oscuro — ambos temas (Green + Purple)
*Del original: "Uso nulo o casi nulo de sombras. La jerarquía se logra mediante cambios de tono y bordes sutiles."*

| Elemento | Elevación | Efecto |
|----------|-----------|--------|
| Cards | 0.dp | Borde 1dp `SurfaceBorder` al 10% opacidad |
| TopBar | 0.dp | Separada por tono `Background` → `Surface` |
| BottomBar | 0.dp | Borde superior 1dp `SurfaceBorder` al 10% |
| Burbujas chat | 0.dp | Sin sombra ni borde |

### Glassmorphism — solo Purple Light
*Del original: "Fondo translúcido, desenfoque de fondo, borde blanco fino."*

```
Fondo:  rgba(255, 255, 255, 0.4)
Blur:   backdrop-filter: blur(20px)    → Compose: Modifier.blur(20.dp) API 31+
Borde:  1px solid rgba(255, 255, 255, 0.6)
```

---

## 6. 📏 Espaciado — Grid 8dp (del diseño original)

*Del original: "Sistema de espaciado basado en una cuadrícula de 8 puntos."*

| Contexto | Valor | Origen |
|----------|-------|--------|
| Márgenes laterales de pantalla | 20-24dp | Original: "20px o 24px" |
| Espacio entre secciones mayores | 32dp | Original: "32px" |
| Espacio entre tarjetas | 16dp | Original: "16px" |
| Padding interno de tarjetas | 16-20dp | Original: "16px a 20px" |
| Espacio icono ↔ texto | 8dp | Original: "8px" |

### Aplicado a componentes Gwen

| Componente | Espaciado |
|------------|-----------|
| Padding lateral en Chat/Modules/Terminal | 20.dp |
| Espacio entre ModuleCards en grid | 16.dp |
| Padding interno ModuleCard | 16.dp |
| Espacio entre burbujas de chat | 8.dp |
| Espacio mensaje ↔ timestamp | 4.dp |
| Padding interno MessageBubble | 12dp horz, 8dp vert |
| Espacio icono ↔ nombre en ModuleCard | 8.dp |
| Espacio entre secciones en DetailSheet | 32.dp |
| Padding BottomSheet | 20.dp lateral, 16.dp vertical |
| Altura ChatInputBar | 52.dp |
| Altura BottomNav | 64.dp |
| Tamaño icono en ModuleCard | 32.dp |
| Tamaño icono en BottomNav | 24.dp |

---

## 7. 🧩 Theme System — Implementación en Compose

```kotlin
// ui/theme/Theme.kt
enum class GwenTheme { GREEN, PURPLE }
enum class GwenMode { LIGHT, DARK, SYSTEM }

@Composable
fun GwenTheme(
    theme: GwenTheme = GwenTheme.GREEN,
    mode: GwenMode = GwenMode.SYSTEM,
    content: @Composable () -> Unit
) {
    val isDark = when (mode) {
        GwenMode.LIGHT -> false
        GwenMode.DARK -> true
        GwenMode.SYSTEM -> isSystemInDarkTheme()
    }

    val colorScheme = when {
        theme == GwenTheme.GREEN && !isDark -> greenLightScheme()
        theme == GwenTheme.GREEN && isDark  -> greenDarkScheme()
        theme == GwenTheme.PURPLE && !isDark -> purpleLightScheme()
        theme == GwenTheme.PURPLE && isDark  -> purpleDarkScheme()
        else -> greenLightScheme()
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = GwenTypography,
        content = content
    )
}
```

### Color Schemes para Material 3

```kotlin
// ui/theme/Scheme.kt
import androidx.compose.material3.lightColorScheme
import androidx.compose.material3.darkColorScheme

fun greenLightScheme() = lightColorScheme(
    background = GreenLightBg,
    surface = GreenLightSurface,
    surfaceVariant = GreenLightSurfaceVariant,
    primary = GreenLightPrimary,
    onPrimary = GreenLightOnPrimary,
    secondary = GreenLightSecondary,
    onSecondary = GreenLightOnSecondary,
    onBackground = GreenLightPrimaryText,
    onSurface = GreenLightPrimaryText,
    onSurfaceVariant = GreenLightSecondaryText,
    error = GreenLightError,
    outline = GreenLightBorder,
)

fun greenDarkScheme() = darkColorScheme(
    background = GreenDarkBg,
    surface = GreenDarkSurface,
    surfaceVariant = GreenDarkSurfaceVariant,
    primary = GreenDarkPrimary,
    onPrimary = GreenDarkOnPrimary,
    secondary = GreenDarkSecondary,
    onSecondary = GreenDarkOnSecondary,
    onBackground = GreenDarkPrimaryText,
    onSurface = GreenDarkPrimaryText,
    onSurfaceVariant = GreenDarkSecondaryText,
    error = GreenDarkError,
)

fun purpleLightScheme() = lightColorScheme(
    primary = PurpleLightPrimary,
    onPrimary = PurpleLightOnPrimary,
    secondary = PurpleLightSecondary,
    onSecondary = PurpleLightOnSecondary,
    background = PurpleLightBgStart,  // cuidado: gradiente no es un color sólido
    surface = PurpleLightSurface,
    surfaceVariant = PurpleLightSurfaceVariant,
    onBackground = PurpleLightPrimaryText,
    onSurface = PurpleLightPrimaryText,
    onSurfaceVariant = PurpleLightSecondaryText,
    error = PurpleLightError,
    outline = PurpleLightBorder,
)

fun purpleDarkScheme() = darkColorScheme(
    primary = PurpleDarkPrimary,
    onPrimary = PurpleDarkOnPrimary,
    secondary = PurpleDarkSecondary,
    onSecondary = PurpleDarkOnSecondary,
    background = PurpleDarkBg,
    surface = PurpleDarkSurface,
    surfaceVariant = PurpleDarkSurfaceVariant,
    onBackground = PurpleDarkPrimaryText,
    onSurface = PurpleDarkPrimaryText,
    onSurfaceVariant = PurpleDarkSecondaryText,
    error = PurpleDarkError,
)
```

---

## 8. 💬 Chat — Aplicación de colores por tema

| Elemento | Green Light | Green Dark | Purple Light | Purple Dark |
|----------|-------------|------------|--------------|-------------|
| Fondo pantalla | `#F3F6F4` | `#090C0A` | Gradiente `#A385FF→#C0A9FF` | `#0D0A1A` |
| Burbuja usuario | `#1E5D3A` | `#00D26A` | `#1A1A1A` | `#A78BFA` |
| Texto burbuja user | `#FFFFFF` | `#090C0A` | `#FFFFFF` | `#0D0A1A` |
| Burbuja Gwen | `#FFFFFF` | `#151816` | Glass `rgba(255,255,255,0.4)` | `#1A1528` |
| Texto burbuja Gwen | `#121A15` | `#FFFFFF` | `#121212` | `#FFFFFF` |
| Input bar fondo | `#E3EDE6` | `#1E221F` | `#F4F0FF` | `#241F35` |
| Botón enviar | `#1E5D3A` | `#00D26A` | `#1A1A1A` | `#A78BFA` |
| Timestamp | `#6B7280` | `#88908B` | `#7C6F9E` | `#9B8EC4` |
| QuickAction chip | `#E3EDE6` | `#2A332D` | `#F4F0FF` | `#241F35` |
| QuickAction texto | `#1E5D3A` | `#00D26A` | `#6C38FF` | `#A78BFA` |
| Typing dots | `#6B7280` | `#88908B` | `#7C6F9E` | `#9B8EC4` |

---

## 9. 🧩 Módulos — Aplicación de colores por tema

| Elemento | Green Light | Green Dark | Purple Light | Purple Dark |
|----------|-------------|------------|--------------|-------------|
| Card fondo | `#FFFFFF` | `#151816` | `#FFFFFF` | `#1A1528` |
| Card sombra | Suave | Borde 1dp 10% blanco | Suave | Borde 1dp 10% blanco |
| Icono módulo | `#1E5D3A` | `#00D26A` | `#6C38FF` | `#A78BFA` |
| Nombre módulo | `#121A15` | `#FFFFFF` | `#121212` | `#FFFFFF` |
| Descripción | `#6B7280` | `#88908B` | `#7C6F9E` | `#9B8EC4` |
| Toggle ON track | `#1E5D3A` | `#00D26A` | `#1A1A1A` | `#A78BFA` |
| Toggle OFF track | `#E3EDE6` | `#2A332D` | `#F4F0FF` | `#241F35` |
| TriggerChip fondo | `#E3EDE6` | `#2A332D` | `#F4F0FF` | `#241F35` |
| TriggerChip texto | `#1E5D3A` | `#00D26A` | `#6C38FF` | `#A78BFA` |
| FilterChip select | `#1E5D3A` | `#00D26A` | `#1A1A1A` | `#A78BFA` |
| FilterChip unselect | `#E3EDE6` | `#2A332D` | `#F4F0FF` | `#241F35` |
| DetailSheet fondo | `#FFFFFF` | `#151816` | `#FFFFFF` | `#1A1528` |

---

## 10. ⬛ Terminal — Aplicación de colores por tema

| Elemento | Green Light | Green Dark | Purple Light | Purple Dark |
|----------|-------------|------------|--------------|-------------|
| Fondo terminal | `#E3EDE6` | `#1E221F` | `#F4F0FF` | `#241F35` |
| Output normal | `#6B7280` | `#88908B` | `#7C6F9E` | `#9B8EC4` |
| Output comando | `#1E5D3A` | `#00D26A` | `#1A1A1A` | `#A78BFA` |
| Output warning | `#DC2626` | `#FF4444` | `#DC2626` | `#FF4444` |
| Output success | `#16A34A` | `#00D26A` | `#6C38FF` | `#A78BFA` |
| Input fondo | `#FFFFFF` | `#151816` | `#FFFFFF` | `#1A1528` |
| Input texto | `#121A15` | `#FFFFFF` | `#121212` | `#FFFFFF` |
| Prompt ">" | `#1E5D3A` | `#00D26A` | `#6C38FF` | `#A78BFA` |

---

## 11. 🧭 Navegación y Conexión — Colores por tema

### Bottom Navigation

| Elemento | Green Light | Green Dark | Purple Light | Purple Dark |
|----------|-------------|------------|--------------|-------------|
| Fondo | `#FFFFFF` | `#151816` | `#FFFFFF` | `#1A1528` |
| Ícono activo | `#1E5D3A` | `#00D26A` | `#1A1A1A` | `#A78BFA` |
| Ícono inactivo | `#6B7280` | `#88908B` | `#7C6F9E` | `#9B8EC4` |
| Label activo | `#1E5D3A` | `#00D26A` | `#1A1A1A` | `#A78BFA` |
| Label inactivo | `#6B7280` | `#88908B` | `#7C6F9E` | `#9B8EC4` |
| Indicador activo | `#1E5D3A` (15% opac) | `#00D26A` (15% opac) | `#1A1A1A` (15% opac) | `#A78BFA` (15% opac) |

### TopBar

| Elemento | Green Light | Green Dark | Purple Light | Purple Dark |
|----------|-------------|------------|--------------|-------------|
| Fondo | `#F3F6F4` | `#090C0A` | Gradiente | `#0D0A1A` |
| Título | `#121A15` | `#FFFFFF` | `#121212` | `#FFFFFF` |
| Iconos | `#1E5D3A` | `#00D26A` | `#1A1A1A` | `#A78BFA` |

### Conexión (modo en TopBar)

| Modo | Green/Purple Light | Green/Purple Dark | Emoji |
|------|-------------------|-------------------|-------|
| Local WiFi | `#16A34A` / `#6C38FF` | `#00D26A` / `#A78BFA` | 🏠 |
| Remoto Internet | `#1E5D3A` / `#1A1A1A` | `#00D26A` / `#A78BFA` | 🌐 |
| Offline | `#DC2626` | `#FF4444` | ⚠ |

### Status Dashboard (futuro)

| Elemento | Green Light | Green Dark | Purple Light | Purple Dark |
|----------|-------------|------------|--------------|-------------|
| GaugeCard fondo | `#FFFFFF` | `#151816` | `#FFFFFF` | `#1A1528` |
| Gauge valor | `#121A15` | `#FFFFFF` | `#121212` | `#FFFFFF` |
| Gauge etiqueta | `#6B7280` | `#88908B` | `#7C6F9E` | `#9B8EC4` |
| Gauge progreso | `#1E5D3A` | `#00D26A` | `#1A1A1A` | `#A78BFA` |
| Gauge track | `#E3EDE6` | `#2A332D` | `#F4F0FF` | `#241F35` |
| Módulo ON | `#16A34A` | `#00D26A` | `#6C38FF` | `#A78BFA` |
| Módulo OFF | `#DC2626` | `#FF4444` | `#DC2626` | `#FF4444` |

---

## 12. 🎯 Mapeo de Iconos de Módulos

```kotlin
// ui/modules/components/ModuleIcon.kt
fun moduleIcon(name: String): ImageVector = when (name) {
    "sports_esports"   -> Icons.Rounded.SportsEsports       // GeForce NOW
    "volume_up"        -> Icons.Rounded.VolumeUp            // Volumen
    "terminal"         -> Icons.Rounded.Terminal            // Terminal (módulo)
    "camera_alt"       -> Icons.Rounded.CameraAlt           // Capturas
    "battery_charging" -> Icons.Rounded.BatteryChargingFull // Batería
    "description"      -> Icons.Rounded.Description         // Archivos
    "download"         -> Icons.Rounded.Download            // Descargas
    "psychology"       -> Icons.Rounded.Psychology          // Memoria
    "schedule"         -> Icons.Rounded.Schedule            // Tareas
    "power"            -> Icons.Rounded.PowerSettingsNew    // Sistema
    "mic"              -> Icons.Rounded.Mic                 // Voz
    "chat"             -> Icons.Rounded.Chat                // Conversación
    "settings"         -> Icons.Rounded.Settings            // Reconfig
    "laptop"           -> Icons.Rounded.Laptop              // Sistema Info
    "window"           -> Icons.Rounded.Window              // Ventanas
    "list_alt"         -> Icons.Rounded.ListAlt             // Procesos
    "notifications"    -> Icons.Rounded.Notifications       // Notificaciones
    "content_copy"     -> Icons.Rounded.ContentCopy         // Portapapeles
    "play_arrow"       -> Icons.Rounded.PlayArrow           // Medios
    "auto_awesome"     -> Icons.Rounded.AutoAwesome         // Protocolos
    "topic"            -> Icons.Rounded.Topic               // Secciones
    "person"           -> Icons.Rounded.Person              // Wizard
    "security"         -> Icons.Rounded.Security            // Auth
    "extension"        -> Icons.Rounded.Extension           // Default / desconocido
    else               -> Icons.Rounded.Extension
}
```

---

## 13. 🎬 Animaciones

| Elemento | Tipo | Duración | Easing |
|----------|------|----------|--------|
| Cambio de tema | `animateColorAsState` | 400ms | `FastOutSlowInEasing` |
| Transición tabs | `fadeIn` + `slideIn` horizontal | 250ms | `FastOutSlowInEasing` |
| ModuleDetailSheet | `slideIn` bottom + `fadeIn` | 300ms | `FastOutSlowInEasing` |
| Nuevo mensaje chat | `scaleIn` + `fadeIn` | 200ms | `LinearOutSlowInEasing` |
| Typing dots (3) | Opacidad secuencial | 1200ms loop | — |
| Shimmer skeleton | Gradiente animado | 1500ms loop | — |
| Toggle switch | `animateColorAsState` | 300ms | `FastOutSlowInEasing` |
| Conexión OK | Icono `scaleIn` con overshoot | 400ms | `OvershootInterpolator` |
| Pull-to-refresh | Indicator circular estándar | — | Default Material |

---

## 14. 📊 Resumen de Temas

| Característica | Verde Claro | Verde Oscuro | Púrpura Claro | Púrpura Oscuro |
|----------------|-------------|-------------|---------------|----------------|
| **Personalidad** | Natural, confiable | Nocturno, intenso | Creativo, moderno | Elegante, premium |
| **Fondo** | Gris-verde suave | Negro-verde | Gradiente lavanda | Negro-púrpura |
| **Acento** | Verde bosque | Verde neón | Casi negro | Lavanda brillante |
| **Superficies** | Blanco puro | Gris oscuro | Blanco / Glass | Gris-púrpura oscuro |
| **Efecto especial** | Sombras suaves | Capas tonales | Glassmorphism | Capas tonales |
| **Recomendado para** | Uso diario | Batería / noche | Modo creativo | Noche premium |

### Origen de cada color en el diseño original

| Color | Fuente en `Diseño Estilo.md` |
|-------|------------------------------|
| Green Light | §1 "Modo Claro" — Background, Surface, Primary, Secondary, Text |
| Green Dark | §1 "Modo Oscuro" — Background, Surface, SurfaceVariant, Primary, Secondary, Text, Danger |
| Purple Light | §2 "Variante Púrpura" — Background gradiente, Surface, SurfaceSecondary, Primary, Secondary, Text |
| Purple Dark | **Complemento diseñado** — no existe en el original, creado para completitud |
| Tipografía | §3 — Inter, pesos 400/500/600/700, escala 12-40px |
| Border Radius | §4 — 24-32px cards, 16px widgets, 999px botones, 8-12px filtros |
| Sombras | §4 — Light suaves, Dark por tonos, Glassmorphism en Púrpura |
| Espaciado | §5 — Grid 8px, 20-24px márgenes, 32px secciones, 16px cards, 8px iconos |
