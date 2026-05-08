# 🧠 NEXUS - UNIFIED SYSTEM TERMINAL

NEXUS es una plataforma de gestión centralizada diseñada para el monitoreo y administración de identidades, áreas operativas y plataformas de servicios.

## 🚀 Características Principales

*   **Gestión de Áreas y Plataformas**: Control centralizado de departamentos y los sistemas vinculados a ellos.
*   **Portal de Catálogo**: Vista unificada para que los usuarios finales exploren y marquen sus sistemas favoritos.
*   **Sistema de Solicitudes**: Flujo de aprobación para el acceso a plataformas restringidas.
*   **Seguridad de Grado Empresarial**: Sistema de autenticación con soporte LDAP y control de acceso basado en roles (RBAC).
*   **Sistema de Notificaciones**: Motor de plantillas configurable para alertas por correo electrónico y notificaciones in-app.
*   **Auditoría Integral**: Registro detallado de cada acción realizada en el sistema.

## 🛠️ Stack Tecnológico

*   **Backend**: Python 3.x, Flask (Modular con Blueprints).
*   **Frontend**: Tailwind CSS, Vanilla JS, Design Tokens (Consistencia Visual).
*   **Base de Datos**: SQLAlchemy (Soporte para SQLite y MySQL).
*   **Entorno**: Soporte nativo para variables `.env`.

## 📂 Estructura del Proyecto

```text
/
├── app/                  # Núcleo de la aplicación Flask
│   ├── modules/          # Módulos independientes (Blueprints)
│   │   ├── auth/         # Autenticación y Usuarios
│   │   ├── areas/        # Gestión de Departamentos
│   │   ├── platforms/    # Gestión de Sistemas/Plataformas
│   │   ├── portal/       # Catálogo de Usuario Final
│   │   ├── notifications/# SMTP y Plantillas
│   │   ├── audit/        # Logs de Auditoría
│   │   └── settings/     # Configuración de Sistema
│   └── utils/            # Utilidades compartidas
├── static/               # Activos estáticos (CSS/JS/Design Tokens)
├── templates/            # Plantillas Jinja2
└── run.py                # Punto de entrada de la aplicación
```

## ⚙️ Configuración Rápida

1.  **Clonar y configurar entorno**:
    ```bash
    cp .env.example .env
    # Editar .env con tus credenciales
    ```
2.  **Instalar dependencias**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Iniciar Aplicación**:
    ```bash
    python run.py
    ```

## 📚 Documentación Adicional

*   [Reglas de Negocio](docs/business_rules.md): Lineamientos operativos y de diseño.
*   [Arquitectura Técnica](docs/ARCHITECTURE.md): Detalles sobre el flujo de datos y base de datos.
*   [Guía de Estilos](UI_GUIDE.md): Design tokens y componentes reutilizables.

## 🚧 Desarrollos Pendientes (Roadmap)

*   [ ] **Activación del Centro de Ayuda**: Habilitación visual de la documentación integrada para usuarios y administradores.

