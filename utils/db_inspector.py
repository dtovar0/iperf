import sys
import os
from sqlalchemy import inspect

# Añadir el raíz del proyecto al path para importar la app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db

def inspect_database():
    """
    Inspección profunda de la base de datos: tablas, columnas, tipos, PKs, FKs e índices.
    """
    app = create_app()
    with app.app_context():
        engine = db.engine
        inspector = inspect(engine)
        
        print("\n" + "="*60)
        print("🔍 REPORTE TÉCNICO: INSPECTOR DE BASE DE DATOS NEXUS")
        print("="*60)
        
        tables = inspector.get_table_names()
        
        if not tables:
            print("⚠️ No se encontraron tablas en la base de datos.")
            return

        for table in tables:
            print(f"\n📂 TABLA: {table.upper()}")
            print("-" * (len(table) + 12))
            
            # --- COLUMNAS ---
            print("  |-- Columnas:")
            columns = inspector.get_columns(table)
            pks = inspector.get_pk_constraint(table).get('constrained_columns', [])
            
            for col in columns:
                name = col['name']
                type_ = col['type']
                nullable = "NULL" if col.get('nullable') else "NOT NULL"
                default = f" DEFAULT {col.get('default')}" if col.get('default') else ""
                pk_marker = " [PK]" if name in pks else ""
                print(f"      • {name:<20} | {str(type_):<15} | {nullable:<10}{default}{pk_marker}")

            # --- LLAVES FORÁNEAS (FK) ---
            fks = inspector.get_foreign_keys(table)
            if fks:
                print("  |-- Llaves Foráneas:")
                for fk in fks:
                    referred_table = fk['referred_table']
                    constrained_columns = ", ".join(fk['constrained_columns'])
                    referred_columns = ", ".join(fk['referred_columns'])
                    print(f"      🔗 {constrained_columns} -> {referred_table}({referred_columns})")

            # --- ÍNDICES ---
            indexes = inspector.get_indexes(table)
            if indexes:
                print("  |-- Índices:")
                for idx in indexes:
                    name = idx['name']
                    cols = ", ".join(idx['column_names'])
                    unique = " (UNIQUE)" if idx.get('unique') else ""
                    print(f"      📌 {name:<20} | Col: {cols}{unique}")

        print("\n" + "="*60)
        print(f"✅ Inspección finalizada. Total de tablas: {len(tables)}")
        print("="*60 + "\n")

if __name__ == '__main__':
    inspect_database()
