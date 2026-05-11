
from app import create_app, db
from app.modules.iperf.models import IperfSession, IperfMeasurement

app = create_app()
with app.app_context():
    session = IperfSession.query.order_by(IperfSession.id.desc()).first()
    print(f"Latest Session: ID={session.id}, Status={session.status}, User={session.user_id}")
    measurements = IperfMeasurement.query.filter_by(session_id=session.id).all()
    print(f"Measurements found: {len(measurements)}")
    for m in measurements[-5:]:
        print(f"  - M: {m.gbps} Gbps, Jitter: {m.jitter_ms} ms")
