from app import create_app, db
from app.modules.iperf.models import IperfMeasurement
app = create_app()
with app.app_context():
    count = IperfMeasurement.query.count()
    print(f"TOTAL_MEASUREMENTS: {count}")
