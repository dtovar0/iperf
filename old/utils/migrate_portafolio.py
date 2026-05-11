import pymysql
import os
from dotenv import load_dotenv

# NEXUS DATA MIGRATOR v2.0: Portafolio -> MI_NUEVO_PROYECTO
# Migra Usuarios, Áreas, Plataformas y Solicitudes.

def migrate():
    # 1. Cargar Configuración de Destino
    load_dotenv()
    
    T_HOST = os.getenv('DB_HOST', 'localhost')
    T_USER = os.getenv('DB_USER')
    T_PASS = os.getenv('DB_PASS')
    T_NAME = os.getenv('DB_NAME')
    
    # 2. Configuración de Origen (Hardcoded de portafolio config.conf)
    S_HOST = 'localhost'
    S_USER = 'username'
    S_PASS = 'password'
    S_NAME = 'nexus'

    print(f"🔄 Iniciando migración extendida de {S_NAME} a {T_NAME}...")

    try:
        source_conn = pymysql.connect(host=S_HOST, user=S_USER, password=S_PASS, database=S_NAME)
        target_conn = pymysql.connect(host=T_HOST, user=T_USER, password=T_PASS, database=T_NAME)
        
        with source_conn.cursor(pymysql.cursors.DictCursor) as s_cursor, target_conn.cursor() as t_cursor:
            
            # --- SECCIÓN 1: ÁREAS ---
            print("📁 Migrando Áreas...")
            t_cursor.execute("""
                CREATE TABLE IF NOT EXISTS `areas` (
                  `id` int NOT NULL AUTO_INCREMENT,
                  `name` varchar(100) UNIQUE NOT NULL,
                  `description` text,
                  `icon` varchar(50) DEFAULT 'box',
                  `color` varchar(100) DEFAULT '#6366f1',
                  `status` varchar(20) DEFAULT 'Activo',
                  PRIMARY KEY (`id`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            
            s_cursor.execute("SELECT * FROM area")
            areas = s_cursor.fetchall()
            for a in areas:
                t_cursor.execute("""
                    INSERT IGNORE INTO areas (id, name, description, icon, color, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (a['id'], a['name'], a['description'], a['icon'], a['color'], a['status']))

            # --- SECCIÓN 2: USUARIOS ---
            print("👤 Migrando Usuarios...")
            s_cursor.execute("SELECT * FROM user")
            users = s_cursor.fetchall()
            user_id_to_email = {}
            for u in users:
                is_active = 1 if u['status'] == 'Activo' else 0
                role = u['role'].lower()
                if role == 'administrador': role = 'administrador'
                else: role = 'usuario'
                
                t_cursor.execute("""
                    INSERT INTO users (email, nombre, password_hash, role, is_active, created_at, auth_source)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                    nombre = VALUES(nombre), 
                    role = VALUES(role), 
                    is_active = VALUES(is_active)
                """, (u['email'], u['name'], u['password_hash'], role, is_active, u['created_at'], 'local'))
                user_id_to_email[u['id']] = u['email']

            # --- SECCIÓN 3: PLATAFORMAS ---
            print("💻 Migrando Plataformas...")
            t_cursor.execute("""
                CREATE TABLE IF NOT EXISTS `platforms` (
                  `id` int NOT NULL AUTO_INCREMENT,
                  `name` varchar(100) NOT NULL,
                  `description` text NOT NULL,
                  `area_id` int NOT NULL,
                  `direct_link` varchar(255) DEFAULT NULL,
                  `icon` varchar(50) DEFAULT 'box',
                  `status` varchar(20) DEFAULT 'Activo',
                  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
                  PRIMARY KEY (`id`),
                  KEY `area_id` (`area_id`),
                  CONSTRAINT `platforms_ibfk_1` FOREIGN KEY (`area_id`) REFERENCES `areas` (`id`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            
            s_cursor.execute("SELECT * FROM platform")
            platforms = s_cursor.fetchall()
            for p in platforms:
                t_cursor.execute("""
                    INSERT IGNORE INTO platforms (id, name, description, area_id, direct_link, icon, status, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (p['id'], p['name'], p['description'], p['area_id'], p['direct_link'], p['icon'], p['status'], p['created_at']))

            # --- SECCIÓN 4: SOLICITUDES ---
            print("📜 Migrando Solicitudes de Acceso...")
            t_cursor.execute("""
                CREATE TABLE IF NOT EXISTS `access_requests` (
                  `id` int NOT NULL AUTO_INCREMENT,
                  `platform_id` int NOT NULL,
                  `user_email` varchar(120) NOT NULL,
                  `status` varchar(20) DEFAULT 'Pendiente',
                  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
                  `processed_at` datetime DEFAULT NULL,
                  PRIMARY KEY (`id`),
                  KEY `platform_id` (`platform_id`),
                  CONSTRAINT `access_requests_ibfk_1` FOREIGN KEY (`platform_id`) REFERENCES `platforms` (`id`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            
            s_cursor.execute("SELECT * FROM access_request")
            requests = s_cursor.fetchall()
            for r in requests:
                u_email = user_id_to_email.get(r['user_id'])
                if u_email:
                    t_cursor.execute("""
                        INSERT IGNORE INTO access_requests (id, platform_id, user_email, status, created_at, processed_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (r['id'], r['platform_id'], u_email, r['status'], r['created_at'], r['processed_at']))

            target_conn.commit()
            print("\n✨ Migración extendida completada con éxito.")

    except Exception as e:
        print(f"\n❌ Error durante la migración: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'source_conn' in locals(): source_conn.close()
        if 'target_conn' in locals(): target_conn.close()

if __name__ == "__main__":
    migrate()
