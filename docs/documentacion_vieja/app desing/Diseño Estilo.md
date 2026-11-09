# Sistema de Diseño: Plataforma de Inversión y Ahorro

Este documento define las directrices visuales extraídas de los diseños de referencia, abarcando las paletas de colores para Modo Claro, Modo Oscuro (Tema Verde) y una variante adicional (Tema Púrpura), así como tipografía y geometría de la interfaz.

## 1. Paleta de Colores: Tema Principal (Verde)

### Modo Claro (Light Mode)
*   **Background (Fondo Principal):** `#F3F6F4` - Gris muy claro con un toque sutil de verde.
*   **Surface (Tarjetas y Contenedores):** `#FFFFFF` - Blanco puro.
*   **Primary Accent (Botones principales, Iconos activos):** `#1E5D3A` - Verde bosque oscuro.
*   **Secondary Accent (Fondos de botones secundarios):** `#E3EDE6` - Verde claro translúcido/pastel.
*   **Primary Text (Títulos, Valores principales):** `#121A15` - Casi negro.
*   **Secondary Text (Subtítulos, Etiquetas):** `#6B7280` - Gris neutro medio.

### Modo Oscuro (Dark Mode)
*   **Background (Fondo Principal):** `#090C0A` - Negro con un matiz extremadamente oscuro de verde.
*   **Surface (Tarjetas y Contenedores):** `#151816` - Gris oscuro ahumado.
*   **Surface Variant (Fondos de inputs o gráficas):** `#1E221F` - Gris oscuro ligeramente más claro.
*   **Primary Accent (Botones principales, Gráficas positivas):** `#00D26A` - Verde neón brillante (Alto contraste).
*   **Secondary Accent (Botones secundarios inactivos):** `#2A332D` - Gris verdoso oscuro.
*   **Primary Text (Títulos, Valores principales):** `#FFFFFF` - Blanco puro.
*   **Secondary Text (Subtítulos, Ejes de gráficas):** `#88908B` - Gris claro.
*   **Danger/Negative (Gráficas en bajada):** `#FF4444` - Rojo vibrante.

---

## 2. Paleta de Colores: Variante (Púrpura / Smart Saving)

Basado en la segunda propuesta del Modo Claro de la primera imagen.
*   **Background (Fondo Principal):** `#A385FF` (Base) a `#C0A9FF` (Gradiente) - Púrpura lavanda vibrante.
*   **Surface (Tarjetas):** `#FFFFFF` (Blanco sólido o con opacidad para efecto Glassmorphism).
*   **Surface Secondary (Tarjetas internas):** `#F4F0FF` - Púrpura muy pálido.
*   **Primary Accent (Botones oscuros):** `#1A1A1A` - Casi negro para contraste sobre el fondo púrpura.
*   **Secondary Accent (Iconos, tags):** `#6C38FF` - Púrpura eléctrico.
*   **Primary Text:** `#121212` (En tarjetas blancas).

---

## 3. Tipografía

Se sugiere una fuente Sans-serif moderna, geométrica y altamente legible para interfaces financieras.
*   **Familia Tipográfica:** Inter, SF Pro Display, o Roboto.
*   **Pesos (Weights):**
    *   *Regular (400):* Cuerpo de texto, etiquetas secundarias.
    *   *Medium (500):* Botones, subtítulos.
    *   *SemiBold (600) / Bold (700):* Balances de cuenta (`$5,440.17`), Títulos de sección.
*   **Escala sugerida:**
    *   Display/Balance: `32px` - `40px`
    *   Heading: `20px` - `24px`
    *   Body/Botones: `14px` - `16px`
    *   Caption/Small text: `12px`

---

## 4. Geometría y Estilos de Interfaz (UI)

### Border Radius (Redondeo de bordes)
*   **Tarjetas principales (Cards / Bottom Sheets):** `24px` a `32px` - Redondeo amplio y amigable (Squircle).
*   **Tarjetas internas (Widgets, Gráficos):** `16px`.
*   **Botones principales (Call to Action):** `999px` (Totalmente redondeados / Forma de píldora).
*   **Botones de selección (Filtros 1D, 1W, 1M):** `8px` a `12px`.

### Sombras (Shadows) y Profundidad
*   **Modo Claro:** Sombras muy suaves, amplias y difuminadas. Ejemplo: `0px 10px 30px rgba(0, 0, 0, 0.05)`.
*   **Modo Oscuro:** Uso nulo o casi nulo de sombras. La jerarquía se logra mediante los cambios de tono en los fondos (`#090C0A` vs `#151816`) y bordes sutiles (Stroke) de `1px` con opacidad del `10%` en blanco.
*   **Efecto Glassmorphism (Variante Púrpura):** Tarjetas con fondo translúcido (`rgba(255, 255, 255, 0.4)`), desenfoque de fondo (`backdrop-filter: blur(20px)`) y un borde blanco fino (`border: 1px solid rgba(255, 255, 255, 0.6)`).

---

## 5. Espaciado (Spacing)

Sistema de espaciado basado en una cuadrícula de 8 puntos.
*   **Márgenes de pantalla (Paddings laterales):** `20px` o `24px`.
*   **Espacio entre secciones mayores:** `32px`.
*   **Espacio entre tarjetas:** `16px`.
*   **Espacio interno de tarjetas (Padding):** `16px` a `20px`.
*   **Espacio entre elementos agrupados (ej. Icono y Texto):** `8px`.
