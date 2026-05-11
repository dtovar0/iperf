from functools import wraps
from flask import abort, redirect, url_for, flash
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'administrador':
            flash('Acceso restringido. Se requieren permisos de administrador.', 'warning')
            return redirect(url_for('core.index'))
        return f(*args, **kwargs)
    return decorated_function
