from flask import Blueprint, render_template, current_app
from flask_login import login_required, current_user
from app.modules.core.models import Area, Platform
from app.modules.auth.models import User

catalogo_bp = Blueprint('catalogo', __name__, url_prefix='/catalogo')

@catalogo_bp.route('/')
@login_required
def index():
    # Fresh query to avoid cache issues
    user = User.query.get(current_user.id)
    
    # User's assigned areas vs Admin All Areas
    if user.role == 'administrador':
        user_areas = Area.query.all()
        all_platforms = Platform.query.filter_by(status='Activo').order_by(Platform.visits.desc()).all()
    else:
        user_areas = user.areas
        user_area_ids = [a.id for a in user_areas]
        
        # STRICT FILTER: Only platforms within assigned areas
        if user_area_ids:
            all_platforms = Platform.query.filter(
                Platform.status == 'Activo',
                Platform.area_id.in_(user_area_ids)
            ).order_by(Platform.visits.desc()).all()
        else:
            all_platforms = []
    
    # Favorite platform IDs
    user_favorites_ids = [int(p.id) for p in user.favorites]
    
    # CRITICAL DEBUG LOG
    current_app.logger.info(f"--- PORTAL ACCESS DEBUG ---")
    current_app.logger.info(f"USER: {user.email}")
    current_app.logger.info(f"ROLE: {user.role}")
    current_app.logger.info(f"ASSIGNED AREAS: {[a.name for a in user_areas]}")
    current_app.logger.info(f"PLATFORMS FOUND: {len(all_platforms)}")
    current_app.logger.info(f"---------------------------")
    
    # Fetch ALL requests for this user with absolute normalization
    from app.modules.core.models import AccessRequest
    from sqlalchemy import func
    
    clean_email = current_user.email.strip().lower()
    user_requests = AccessRequest.query.filter(
        func.lower(func.trim(AccessRequest.user_email)) == clean_email
    ).all()
    
    # Create status map: { platform_id_str: status }
    user_request_statuses = {str(r.platform_id): r.status for r in user_requests}
    current_app.logger.info(f"FINAL STATUS MAP FOR {clean_email}: {user_request_statuses}")

    return render_template('catalogo.html', 
                         user_areas=user_areas, 
                         platforms=all_platforms,
                         user_favorites_ids=user_favorites_ids,
                         user_request_statuses=user_request_statuses)

@catalogo_bp.route('/favorite/toggle', methods=['POST'])
@login_required
def toggle_favorite():
    from flask import request, jsonify
    from app import db
    
    data = request.get_json()
    platform_id = data.get('platform_id')
    
    if not platform_id:
        return jsonify({'status': 'error', 'message': 'Falta platform_id'}), 400
        
    platform = Platform.query.get(platform_id)
    if not platform:
        return jsonify({'status': 'error', 'message': 'Plataforma no encontrada'}), 404
        
    if platform in current_user.favorites:
        current_user.favorites.remove(platform)
        message = f"{platform.name} eliminada de favoritos"
        current_app.logger.info(f"Portal: Removed platform {platform_id} from favorites for {current_user.email}")
    else:
        current_user.favorites.append(platform)
        message = f"{platform.name} añadida a favoritos"
        is_favorite = True
        current_app.logger.info(f"Portal: Added platform {platform_id} to favorites for {current_user.email}")
        
    db.session.add(current_user)
    db.session.commit()
    return jsonify({
        'status': 'success', 
        'message': message,
        'is_favorite': is_favorite
    })
