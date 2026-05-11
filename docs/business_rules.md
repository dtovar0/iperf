# Nexus Project: iperf

## Módulo General

### Regla: Estructura Nexus
El proyecto debe seguir la estructura de Nexus Scaffolder v5.1, utilizando Flask con Blueprints.

### Impacto
Arquitectura del sistema, mantenibilidad.

---

# 📚 MOTOR DE REGLAS DE NEGOCIO — NEXUS PLATFORM


## Áreas y Plataformas

### Regla: Integridad Referencial
No se permite la eliminación de un área si existen plataformas o sistemas vinculados a ella. El sistema debe bloquear la operación y mostrar un error detallado.

### Ejemplo
Si el área "Infraestructura" tiene vinculada la plataforma "AWS", el administrador recibirá un mensaje: "No se pueden eliminar las siguientes áreas porque tienen plataformas vinculadas: Infraestructura".

### Impacto
Backend (API de Áreas), UI (Módulo de Áreas).

---

## Seguridad y Autenticación

### Regla: Gestión de Contraseñas Locales
Los usuarios creados mediante el flujo Local DEBEN tener una contraseña establecida en el momento del registro. Los usuarios LDAP no requieren este campo ya que la autenticación es externa.

### Ejemplo
Al registrar un usuario local, los campos "Password" y "Confirm Password" son obligatorios y deben coincidir. Al importar de LDAP, estos campos se ocultan automáticamente.

### Impacto
Frontend (Registration Modal), Backend (User Model).

---

## Interfaz de Usuario (UI)

### Regla: Paginación Maestra
La paginación en todos los módulos de gestión debe seguir el estándar de Auditoría (DataTables style), mostrando "Mostrando X-Y de Z registros" y controles simplificados.

### Ejemplo
El módulo de Áreas utiliza `dt-layout-row` para su footer de paginación, logrando paridad 1:1 con Auditoría.

### Impacto
Módulos de Usuarios, Áreas y Plataformas.
---

## Gestión de Ciclo de Vida del Sistema

### Regla: Desacoplamiento de Componentes Legados
Queda terminantemente prohibida la reintroducción de módulos relacionados con PSX5K, Worker Daemons o APIs tácticas v1. El sistema debe operar exclusivamente bajo la arquitectura de portal de gestión de identidades y accesos.

### Ejemplo
Cualquier intento de crear una ruta `/api/v1` o de importar servicios de ejecución de comandos remotos (SSH/Task Engines) será rechazado en la revisión arquitectónica.

### Impacto
Arquitectura Global, Documentación Técnica, Estructura de Base de Datos.

---

## Gestión de Pruebas de Red (iperf3)

### Regla: Ejecución Asíncrona
Todas las pruebas de iperf3 deben ejecutarse de forma asíncrona o mediante un proceso en segundo plano para evitar el bloqueo del hilo principal de Flask. Se debe informar al usuario sobre el estado de la prueba (Pendiente, En curso, Completado).

### Ejemplo
Cuando un usuario inicia un test a 192.168.1.1, la UI muestra un spinner y el estado cambia a "Running". Al finalizar, se guarda el JSON de salida y se muestra en un modal de resultados.

### Regla: Orquestación de Servidor (iperf3)
El botón principal de la interfaz de iperf3 garantiza un inicio limpio mediante la limpieza agresiva del entorno. Antes de lanzar el servidor, el sistema DEBE finalizar cualquier proceso `iperf3` existente (SIGKILL) y liberar forzosamente el puerto `5201/tcp` mediante `fuser`.

### Ejemplo
Al presionar "Start iperf3 Server", el backend ejecuta `pkill -9 iperf3` seguido de `fuser -k 5201/tcp` y una pausa de 1 segundo antes del `iperf3 -s -D`. Esto previene el error "Address already in use".

### Regla: Telemetría en Tiempo Real (iperf3)
Para garantizar la monitorización en vivo en el dashboard (gráficas y terminal), el sistema debe utilizar `subprocess.Popen` con el flag `--forceflush` en lugar de la librería `iperf3-python` (la cual es bloqueante). Esto permite capturar y parsear cada intervalo de 1 segundo mediante hilos lectores dedicados.

### Regla: Persistencia Detallada y Reportes
Cada sesión de prueba (cliente o servidor) debe persistir sus puntos de medición (Throughput, Jitter, Retx) en una base de datos relacional. Al finalizar, el sistema debe generar automáticamente un resumen estadístico (Average, Max, Min) y permitir la exportación a un reporte PDF con el diseño Nexus Premium.

### Regla: REST API de Monitoreo
El módulo iperf debe exponer una API REST protegida por un Token (`X-API-Token`) para permitir la integración con sistemas externos (Zabbix, dashboards externos). Los endpoints deben devolver la paridad de datos con el sistema de base de datos relacional (sesiones, mediciones y resúmenes).

### Regla: Legibilidad de Log (iperf3)
Para mejorar la legibilidad en sesiones de larga duración, el visor de logs del dashboard debe repetir la cabecera de las columnas (Intervalo, Bitrate, etc.) automáticamente cada 10 pasos de medición. Esta inyección debe ocurrir en tiempo real tanto para el buffer global del servidor como para el historial de sesión del cliente.

### Ejemplo
Después de 10 líneas de datos (ej. 9.00-10.00 sec), el sistema inserta nuevamente `[ ID] Interval Transfer Bitrate Retr Cwnd` antes de mostrar el siguiente intervalo (10.00-11.00 sec).

### Impacto
UX/UI Dashboard (Log Panel).
