import sys
import os

# Asegurar que el contexto de la app se pueda cargar
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import inspect, text

def check_database_schema(auto_fix=True):
    app = create_app()
    with app.app_context():
        print("\n" + "="*60)
        print("🔍 NEXUS DB-SYNC: REVISIÓN DE INTEGRIDAD DE ESQUEMA")
        print("="*60)
        
        inspector = inspect(db.engine)
        db_tables = set(inspector.get_table_names())
        model_tables = set(db.Model.metadata.tables.keys())
        
        # --- ANÁLISIS DE TABLAS ---
        missing_in_db = model_tables - db_tables
        extra_in_db = db_tables - model_tables
        
        if missing_in_db:
            print(f"❌ Tablas FALTANTES en DB: {', '.join(missing_in_db)}")
            if auto_fix:
                print("🛠️  Creando tablas faltantes...")
                db.create_all()
                print("✅ Tablas sincronizadas.")
        else:
            print("✅ Estructura de tablas: OK")
            
        # --- ANÁLISIS DE COLUMNAS ---
        common_tables = db_tables.intersection(model_tables)
        issues = 0
        
        for table_name in common_tables:
            real_cols = {col['name']: col for col in inspector.get_columns(table_name)}
            model_cols = {col.name: col for col in db.Model.metadata.tables[table_name].columns}
            
            missing_cols = set(model_cols.keys()) - set(real_cols.keys())
            
            if missing_cols:
                issues += 1
                print(f"\n🔔 Discrepancia en `{table_name}`:")
                for col_name in missing_cols:
                    print(f"   ❌ Columna `{col_name}` no existe en DB.")
                    if auto_fix:
                        col_obj = model_cols[col_name]
                        try:
                            compiled_type = col_obj.type.compile(db.engine.dialect)
                            alter_sql = f"ALTER TABLE `{table_name}` ADD COLUMN `{col_name}` {compiled_type}"
                            db.session.execute(text(alter_sql))
                            db.session.commit()
                            print(f"      🔨 Columna `{col_name}` añadida exitosamente.")
                        except Exception as e:
                            print(f"      ⚠️ Error al añadir columna: {e}")
            
        if issues == 0 and not missing_in_db:
            print("✅ Columnas y Tipos: OK")
            print("\n✨ BASE DE DATOS EN SINCRONÍA TOTAL")
        
        print("="*60 + "\n")

if __name__ == '__main__':
    # Fix por defecto si no se especifica --check
    do_fix = '--check' not in sys.argv
    check_database_schema(auto_fix=do_fix)
