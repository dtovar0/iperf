import os
import subprocess
import threading
import time
import socket
import json
import re
from datetime import datetime
from flask import Flask, request, jsonify, Response
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Config
API_TOKEN = os.getenv('IPERF_API_TOKEN', 'nexus_secret_token_2024_v1')
SATELLITE_NAME = os.getenv('SATELLITE_NAME', socket.gethostname())

# State tracking
active_procs = {} # 'server' or 'client' -> subprocess.Popen
live_logs = []
live_measurements = []
lock = threading.Lock()

DATA_RE = re.compile(
    r'\[\s*(?P<id>\d+|SUM)\]\s+'
    r'(?P<t0>[\d.]+)-(?P<t1>[\d.]+)\s+sec\s+'
    r'[\d.]+\s+\w+Bytes\s+'
    r'(?P<rate>[\d.]+)\s+(?P<unit>[GkMK])bits/sec'
    r'(?:\s+(?P<jitter>[\d.]+)\s+ms)?'
    r'(?:\s+(?P<lost>\d+)/\s*(?P<total>\d+))?'
    r'(?:\s+(?P<retx>\d+))?'
    r'.*?(?:\s+(?P<role>sender|receiver))?\s*$'
)

def to_gbps(v, u):
    return {"G": v, "M": v / 1000, "K": v / 1000000}[u]

def port_is_listening(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0

def iperf_reader(proc, mode):
    global live_logs, live_measurements
    
    for raw in proc.stdout:
        line = raw.rstrip()
        if not line: continue
        
        with lock:
            live_logs.append(line)
            if len(live_logs) > 500: live_logs.pop(0)
            
            m = DATA_RE.search(line)
            if m:
                try:
                    t0, t1 = float(m.group("t0")), float(m.group("t1"))
                    # Interval check (1s)
                    if 0.5 <= (t1 - t0) <= 1.5:
                        gbps = to_gbps(float(m.group("rate")), m.group("unit"))
                        jitter = float(m.group("jitter")) if m.group("jitter") else 0.0
                        retx = int(m.group("retx") or m.group("lost") or 0)
                        
                        meas = {
                            "ts": time.strftime('%H:%M:%S'),
                            "gbps": gbps,
                            "mbps": round(gbps * 1000, 2),
                            "jitter": jitter,
                            "retx": retx,
                            "t1": t1
                        }
                        
                        # Only add SUM or individual lines depending on role to avoid double counting
                        role = m.group("role") or ""
                        is_sum = m.group("id").strip() == "SUM"
                        
                        if is_sum:
                            live_measurements.append(meas)
                        elif not any(x.get('t1') == t1 for x in live_measurements):
                            # Simple logic: if no sum yet for this second, add this line
                            # In a real satellite, we'd be more precise, but this works for live graphing
                            live_measurements.append(meas)
                        
                        if len(live_measurements) > 100: live_measurements.pop(0)
                except: pass

    with lock:
        if mode in active_procs:
            del active_procs[mode]

# Auth Decorator
def require_auth(f):
    def decorated(*args, **kwargs):
        token = request.headers.get('X-API-Token')
        if not token or token != API_TOKEN:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({
        "name": SATELLITE_NAME,
        "server_running": "server" in active_procs,
        "client_running": "client" in active_procs,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/server/start', methods=['POST'])
@require_auth
def start_server():
    port = request.json.get('port', 5201)
    
    if "server" in active_procs:
        return jsonify({"success": False, "message": "Server already running"}), 400
        
    # Cleanup port
    if port_is_listening(port):
        subprocess.run(["fuser", "-k", "-n", "tcp", str(port)], capture_output=True)
        time.sleep(1)

    cmd = ["iperf3", "-s", "-p", str(port), "--forceflush"]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        active_procs["server"] = proc
        threading.Thread(target=iperf_reader, args=(proc, "server"), daemon=True).start()
        
        # Wait for port
        for _ in range(5):
            time.sleep(0.5)
            if port_is_listening(port):
                return jsonify({"success": True, "message": f"Server started on {port}"})
        
        return jsonify({"success": False, "message": "Server failed to bind port"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/server/stop', methods=['POST'])
@require_auth
def stop_server():
    if "server" not in active_procs:
        return jsonify({"success": False, "message": "No server running"}), 400
        
    proc = active_procs["server"]
    proc.terminate()
    return jsonify({"success": True, "message": "Server stopped"})

@app.route('/api/client/run', methods=['POST'])
@require_auth
def run_client():
    data = request.json
    host = data.get('host')
    port = data.get('port', 5201)
    duration = data.get('duration', 10)
    protocol = data.get('protocol', 'TCP').lower()
    
    if "client" in active_procs:
        return jsonify({"success": False, "message": "Client test already in progress"}), 400
        
    if not host:
        return jsonify({"success": False, "message": "Host is required"}), 400

    cmd = ["iperf3", "-c", host, "-p", str(port), "-t", str(duration), "--forceflush", "-i", "1"]
    if protocol == 'udp':
        cmd += ["-u", "-b", data.get('bandwidth', '100M')]

    try:
        # Clear previous data
        with lock:
            live_measurements.clear()
            live_logs.clear()

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        active_procs["client"] = proc
        threading.Thread(target=iperf_reader, args=(proc, "client"), daemon=True).start()
        
        return jsonify({"success": True, "message": "Client test started"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/live-data', methods=['GET'])
@require_auth
def get_live_data():
    with lock:
        return jsonify({
            "logs": live_logs[-20:],
            "measurements": live_measurements[-20:]
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
