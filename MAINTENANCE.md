# 🛠️ NEXUS MASTER MAINTENANCE GUIDE

Este documento detalla las reglas para mantener y actualizar el **Nexus Master Scaffolder**.

## 🧠 Reglas de Oro
1. **Inmutabilidad de Core**: Los módulos `auth`, `core`, `settings` y `audit` son el corazón del sistema. No deben ser opcionales ya que garantizan la estabilidad base.
2. **Convención de Nombres**: Para que un módulo sea "scaffoldable", debe seguir esta estructura:
   - **Backend**: `app/modules/<nombre>/`
   - **Estilos**: `assets/css/<nombre>.css`
   - **Lógica JS**: `assets/js/<nombre>.js`
   - **Template**: `templates/<nombre>.html`
3. **Registro en Scaffolder**: Si añades un nuevo módulo opcional, debes agregarlo a la lista `OPTIONAL_MODULES` en `nexus_cli.py`.
4. **UI_GUIDE**: Este archivo es el Single Source of Truth del diseño. Cualquier cambio en los tokens de `tokens.css` debe verse reflejado en la guía.

## 🔄 Cómo añadir un nuevo módulo al Scaffolder
1. Crea tu módulo en `app/modules/mi_modulo`.
2. Asegúrate de que en `app/__init__.py` la línea de registro sea: `app.register_blueprint(mi_modulo_bp)`.
3. En `sidebar.html`, envuelve tu enlace en una etiqueta `<a>` que use `url_for('mi_modulo_module.ruta')`.
4. Añade `'mi_modulo'` a la lista `OPTIONAL_MODULES` en `nexus_cli.py`.

---
*Nexus Master v4.0 - Generación Automática de Software de Alta Densidad.*
