from app import create_app, db
from app.modules.iperf.models import IperfTest

app = create_app()
with app.app_context():
    db.create_all()
    print("✅ Tablas sincronizadas (incluyendo iperf_tests)")
