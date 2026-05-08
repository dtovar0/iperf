# 🏗️ ARQUITECTURA TÉCNICA - NEXUS

## 🧩 Patrón de Diseño
NEXUS utiliza una arquitectura modular basada en **Flask Blueprints**. Cada módulo es independiente y maneja su propia lógica de negocio, modelos de base de datos y rutas, permitiendo un escalado horizontal del código.

## 💾 Modelado de Datos
El sistema utiliza SQLAlchemy para la persistencia de datos con un enfoque en la gestión de accesos:

1.  **Areas**: Define los departamentos u organizaciones lógicas.
2.  **Platforms**: Representa los sistemas o servicios finales a los que los usuarios acceden.
3.  **AccessRequests**: Gestiona el flujo de solicitudes de acceso entre usuarios y plataformas.
4.  **AuditLogs**: Registro histórico de acciones administrativas y de usuario.

## 🔐 Seguridad y Auditoría
*   **RBAC (Role Based Access Control)**: Control de acceso basado en roles (`administrador` y `usuario`).
*   **LDAP Integration**: Permite la sincronización de usuarios corporativos mapeando atributos CN y Mail.
*   **AuditLog**: Cada interacción de escritura o cambio de configuración se registra en la tabla `audit_logs`, capturando Usuario, IP, Acción y Timestamp.

## 📧 Motor de Notificaciones
Centralizado en el módulo `notifications`, permite:
*   Configuración dinámica de SMTP.
*   Uso de **Slugs** (ej: `inicio`, `terminado`, `error`) para llamar a plantillas preconfiguradas.
*   Inyección de contexto dinámico (Variables Jinja2 en los correos).
*   Notificaciones In-App para avisos en tiempo real dentro del portal.
