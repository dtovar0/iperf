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
El botón principal de la interfaz de iperf3 está destinado exclusivamente a la activación del servidor local (`iperf3 -s`). El sistema debe garantizar un inicio limpio; si ya existe una instancia de iperf3 en ejecución, esta debe ser finalizada antes de lanzar el nuevo proceso.

### Ejemplo
Cuando el usuario presiona "Start iperf3 Server", el backend ejecuta un `pkill` preventivo sobre procesos iperf3 previos y luego lanza `iperf3 -s -D`. Esto asegura la disponibilidad del puerto 5201.

### Impacto
Disponibilidad del servicio de pruebas, Módulo iperf, UX.
