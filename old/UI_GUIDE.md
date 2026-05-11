# 🧠 MEMORY UI - NEXUS DESIGN SYSTEM

## 🧱 Design Tokens Base

- **Checkbox Oficial**: `.nexus-checkbox` (Usar siempre con contenedor `flex items-center justify-center`).
- **Botón Simétrico**: `w-[180px] h-12 rounded-xl text-[10px] uppercase font-black`.
- **Selección de Fila**: `.nexus-row-selected` (Fondo transparente, solo indicador en checkbox).

## 📐 Estándar de Paneles y Contenedores
- **Borde**: `1px solid rgb(var(--color-panel-border))`
- **Redondeo (Radius)**: `12px` (Clase Tailwind: `rounded-xl`)
- **Fondo**: `rgb(var(--color-panel-fill))`
- **Aplicación**: Todos los paneles de KPIs, Gráficas, Tablas y Modales DEBEN usar este estándar para mantener la consistencia corporativa.

## 🧩 Componentes Reutilizables

### 1. Botón de Acción Gris
```html
<button class="w-[180px] h-12 bg-label/10 text-label/60 border border-panel-border ...">
    <!-- Icono + Texto -->
</button>
```

### 2. Tabla Administrativa (Layout)
- Header: `bg-slate-900/50 uppercase tracking-[0.2em]`.
- Fila: `border-spacing-y-1.5 transition-all duration-300`.

## 🎨 Authelia Premium Theme
- **Path**: `deployment/authelia/themes/nexus_premium.css`
- **Concept**: Futuristic Cyberpunk / Glassmorphism.
- **Accents**: Neon Blue (`#3b82f6`) & Electric Purple (`#8b5cf6`).
- **Nginx Injection**: Add `<link>` tag via `sub_filter`.


## 📏 Reglas de Modales (Footers)

- **Simetría Obligatoria**: Todos los botones de acción en el `modal-footer` DEBEN tener el mismo ancho.
- **Ancho Estándar**: `w-[160px]` o `flex-1` balanceado, pero NUNCA mezclar anchos diferentes en el mismo footer.
- **Comportamiento Must**: Ningún botón puede ser "más ancho" que el otro por su texto; se ajusta el contenedor o se usa un ancho fijo.
- **Acciones**: Atras (Secondary), Siguiente (Primary), Finalizar (Success), Cancelar (Outline/Danger).

## 🏗️ Estructura de Modal Footer (Symmetry + Alignment)

Para lograr que los botones sean simétricos pero estén pegados a los extremos, se debe usar la siguiente estructura:

```html
<footer class="modal-footer">
    <div class="footer-left">
        <!-- Botones: Cancelar, Regresar, Anterior -->
    </div>
    <div class="footer-right">
        <!-- Botones: Siguiente, Finalizar, Guardar -->
    </div>
</footer>
```

**Reglas de Estilo:**
- `modal-footer`: `justify-content: space-between`.
- `footer-left/right`: Contenedores flex para agrupar múltiples botones en un extremo.
- **Botones**: Deben mantener el `min-width: 160px` para preservar la simetría visual.

## 🔘 Regla Global de Botones

- **Simetría Universal**: TODOS los botones del sistema (fuera y dentro de modales) deben ser simétricos en altura y, preferiblemente, en anchura dentro de su contexto.
- **Simplificación de Texto**: Si el texto es demasiado largo para el botón estándar, se DEBE simplificar el copy y utilizar un icono descriptivo para mantener la estética limpia.
- **Dimensiones Estándar**: Usar clases `nexus-btn` que heredan el estilo premium del sistema.

## 📊 Estándar de Tablas (DataTables)

Todas las tablas del sistema deben implementarse bajo el motor DataTables con las siguientes características obligatorias:
- **Diseño Zebra**: Alternancia de colores en filas para facilitar la lectura.
- **Ghost Rows (Filas Fantasma)**: Uso de `renderGhostRows` en JS para rellenar el espacio vacío y mantener el tamaño de la tabla constante.
- **Paginación Premium**: Uso del layout de paginación de Nexus (controles en el footer de la tabla, no flotantes).
- **Consistencia Visual**: No se permiten tablas nativas de HTML sin el envoltorio y estilos de DataTables del proyecto.

## 📑 Patrón de Estructura de Modales

Para mantener la consistencia, todos los modales deben seguir esta jerarquía de clases y componentes:
- **Contenedor**: `.nexus-modal` (backdrop + blur).
- **Panel**: `.modal-panel` con `max-w-4xl` por defecto para asegurar legibilidad.
- **Header**: Icono representativo + Título (cursiva/black) + Subtítulo descriptivo.
- **Body**: Padding de `p-8` con scroll personalizado (`custom-scrollbar`).
- **Footer**: Uso estricto de `.footer-left` y `.footer-right` para botones simétricos.

## 🔔 Notificaciones y Alertas

Cualquier sistema de notificación (modales de éxito, error o advertencia) debe reutilizar el mismo diseño:
- **Reutilización Obligatoria**: Si se define un estilo para una alerta de "Guardado Exitoso", ese mismo diseño (iconografía, colores, animaciones) debe replicarse en todo el sistema.
- **SweetAlert2 Config**: Usar el tema de Nexus (Glassmorphism, Dark Mode, Tipografía Inter/Black) configurado globalmente.

## 📐 Paridad de Altura (Toolbar Standards)

- **Alineación Táctica**: Todos los elementos de la toolbar (inputs de búsqueda, selectores y botones) deben compartir exactamente la misma altura.
- **Altura Estándar**: Se establece **3rem (48px)** como la altura oficial para todos los controles interactivos de la toolbar.
- **Inputs**: Deben usar la misma altura que los botones `nexus-btn` para que la línea visual sea perfecta y profesional.

## ⚖️ Alineación de Columnas de Selección

- **Simetría Vertical**: En cualquier tabla con columnas de selección (checkboxes), tanto el encabezado (`<th>`) como las celdas (`<td>`) deben compartir la misma alineación.
- **Centrado Obligatorio**: Por estándar, las columnas de selección deben estar **centradas horizontalmente** (`text-center` + `justify-center`) para mantener el equilibrio visual de la tabla.

## 📐 Estándares de Orientación y Dimensionado (DataTables)

Para garantizar una lectura fluida y una estética equilibrada en las tablas, se deben seguir estos lineamientos de alineación y tamaño de columnas:

### 1. Orientación de Textos (Alignment)
- **Identidades y Nombres**: Siempre alineados a la **Izquierda** (`text-left`). Es la forma natural de lectura para nombres de usuario, correos y títulos de servicios.
- **Badges y Etiquetas de Estado**: Siempre **Centrados** (`text-center`). Los badges (Activo, Inactivo, Roles) deben flotar en el centro de su celda para evitar que la tabla se vea cargada hacia un lado.
- **Acciones y Selectores**: Siempre **Centrados** (`text-center`).
- **Datos Numéricos o Contadores**: Siempre **Centrados** (`text-center`) con tipografía `font-black` para resaltar el dato sobre el texto.

### 2. Dimensionado de Columnas (Sizing)
- **Columnas Tácticas (Checkbox, Icono, Estado)**: Usar anchos fijos o mínimos en píxeles (ej: `w-[40px]` o `w-[100px]`) para evitar que el motor de DataTables las deforme.
- **Columnas de Iconos y Badges**: Estas columnas no deben ser excesivamente grandes; su ancho debe estar ajustado al contenido y este debe estar estrictamente **centrado**.
- **Columnas de Datos (Nombre, Email, Descripción)**: Usar porcentajes para adaptabilidad. 
  - Las columnas de **Nombre/Descripción** deben tener una longitud mayor para acomodar la información.
  - Generalmente, la columna de **Descripción** debe ser más ancha que la de **Nombre** debido a la densidad de texto.
- **Truncado Inteligente**: Las columnas de texto largo deben usar `truncate` y `line-clamp` para evitar saltos de línea que rompan la simetría de las filas Zebra.

## 🛠️ Lógica de Interacción Administrativa

Para garantizar una experiencia de control robusta y evitar acciones accidentales, se establecen las siguientes reglas de interacción en tablas de gestión:

### 1. Estado Inicial de Botones
- **Desactivación por Defecto**: Todos los botones de acción global (Modificar, Eliminar, Suspender, etc.) deben iniciar en estado **deshabilitado**.
- **Estilo de Desactivación**: Se deben aplicar las clases `opacity-40` y `pointer-events-none` junto con el atributo `disabled` para proporcionar un feedback visual claro de que la acción no está disponible.

### 2. Habilitación Condicional
- **Acción Única (Modificar/Ver Detalles)**: Se habilita únicamente cuando hay **exactamente 1** registro seleccionado.
- **Acción Masiva (Eliminar/Exportar)**: Se habilita cuando hay **1 o más** registros seleccionados.

### 3. Patrón de Selección de Filas
- **Clic para Seleccionar**: Al hacer clic en cualquier parte de una fila de la tabla, el sistema debe conmutar la selección de dicha fila (marcar/desmarcar checkbox y resaltar fondo).
- **No Clic para Editar**: Se prohíbe que el clic simple en una fila abra directamente un modal de edición. El flujo oficial debe ser: **Seleccionar → Visualizar botón habilitado → Click en botón de acción**.
- **Retroalimentación Visual**: Las filas seleccionadas deben usar la clase `.bg-primary/5` y mostrar el indicador lateral de color de la marca para confirmar la selección.
