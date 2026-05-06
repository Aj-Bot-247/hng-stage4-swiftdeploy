from flask import Flask, request, jsonify, Response
import os
import time
import random
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)
START_TIME = time.time()

# ==========================================
# 1. PROMETHEUS METRICS SETUP
# ==========================================
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'path', 'status_code'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'Latency of HTTP requests in seconds', ['method', 'path', 'status_code'])
APP_UPTIME = Gauge('app_uptime_seconds', 'Uptime of the application in seconds')
APP_MODE = Gauge('app_mode', '0=stable, 1=canary')
CHAOS_ACTIVE = Gauge('chaos_active', '0=none, 1=slow, 2=error')

# Initialize static metrics
current_mode = os.environ.get("MODE", "stable")
APP_MODE.set(1 if current_mode == "canary" else 0)
CHAOS_ACTIVE.set(0) # Default to 0 (none)

# Global state to track chaos mode
chaos_state = {
    "mode": "recover", # Default state
    "duration": 0,
    "rate": 0.0
}

@app.before_request
def apply_chaos_and_start_timer():
    """Intercepts requests to apply chaos behavior and start metrics timer."""
    # Start the timer for Prometheus
    request.start_time = time.time()

    # Skip chaos for health check & metrics so Docker/Prometheus don't fail unnecessarily
    if request.path in ['/healthz', '/metrics']:
        return

    if chaos_state["mode"] == "slow":
        time.sleep(chaos_state["duration"])
    elif chaos_state["mode"] == "error":
        if random.random() < chaos_state["rate"]:
            # We must return early to trigger the error, but we still need 
            # to record this 500 error in Prometheus before we return it!
            duration = time.time() - request.start_time
            REQUEST_COUNT.labels(method=request.method, path=request.path, status_code=500).inc()
            REQUEST_LATENCY.labels(method=request.method, path=request.path, status_code=500).observe(duration)
            return jsonify({"error": "Simulated chaos error"}), 500

@app.after_request
def apply_canary_header_and_record_metrics(response: Response):
    """Injects Canary header and records Prometheus metrics after routing."""
    # 1. Inject Canary Header (Your original logic)
    if os.environ.get("MODE") == "canary":
        response.headers["X-Mode"] = "canary"
        
    # 2. Record Prometheus Metrics
    APP_UPTIME.set(time.time() - START_TIME)
    
    # We do not track the /metrics endpoint itself to avoid polluting our data
    # (And we skip 500 errors from chaos because they are already recorded in before_request)
    if request.path != '/metrics' and response.status_code != 500:
        duration = time.time() - request.start_time
        REQUEST_COUNT.labels(
            method=request.method, 
            path=request.path, 
            status_code=response.status_code
        ).inc()
        REQUEST_LATENCY.labels(
            method=request.method, 
            path=request.path, 
            status_code=response.status_code
        ).observe(duration)

    return response

# ==========================================
# 2. ROUTES
# ==========================================

@app.route('/metrics', methods=['GET'])
def metrics():
    """Exposes the Prometheus metrics."""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

@app.route('/', methods=['GET'])
def welcome():
    return jsonify({
        "message": "SwiftDeploy API running smoothly.",
        "mode": current_mode,
        "version": os.environ.get("APP_VERSION", "1.0.0"),
        "timestamp": time.time()
    })

@app.route('/healthz', methods=['GET'])
def healthz():
    return jsonify({
        "status": "ok",
        "uptime": int(time.time() - START_TIME)
    })

@app.route('/chaos', methods=['POST'])
def chaos():
    if os.environ.get("MODE") != "canary":
        return jsonify({"error": "Chaos endpoint is only available in canary mode"}), 403

    data = request.get_json()
    if not data or "mode" not in data:
        return jsonify({"error": "Invalid payload"}), 400

    mode = data["mode"]
    if mode == "recover":
        chaos_state.update({"mode": "recover", "duration": 0, "rate": 0.0})
        CHAOS_ACTIVE.set(0) # Update Prometheus
        return jsonify({"message": "Recovered. Chaos disabled."})
    
    elif mode == "slow":
        chaos_state.update({"mode": "slow", "duration": data.get("duration", 2)})
        CHAOS_ACTIVE.set(1) # Update Prometheus
        return jsonify({"message": f"Slow mode activated. Delay: {chaos_state['duration']}s"})
    
    elif mode == "error":
        chaos_state.update({"mode": "error", "rate": data.get("rate", 0.5)})
        CHAOS_ACTIVE.set(2) # Update Prometheus
        return jsonify({"message": f"Error mode activated. Failure rate: {chaos_state['rate']}"})

    return jsonify({"error": "Unknown chaos mode"}), 400

if __name__ == '__main__':
    port = int(os.environ.get("APP_PORT", 3000))
    app.run(host='0.0.0.0', port=port)