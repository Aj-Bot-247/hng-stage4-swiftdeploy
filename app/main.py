from flask import Flask, request, jsonify, Response
import os
import time
import random

app = Flask(__name__)
START_TIME = time.time()

# Global state to track chaos mode
chaos_state = {
    "mode": "recover", # Default state
    "duration": 0,
    "rate": 0.0
}

@app.before_request
def apply_chaos():
    """Intercepts requests to apply chaos behavior before routing."""
    # Skip chaos for the health check so Docker doesn't kill the container unnecessarily
    if request.path == '/healthz':
        return

    if chaos_state["mode"] == "slow":
        time.sleep(chaos_state["duration"])
    elif chaos_state["mode"] == "error":
        if random.random() < chaos_state["rate"]:
            return jsonify({"error": "Simulated chaos error"}), 500

@app.after_request
def apply_canary_header(response: Response):
    """Injects the Canary header into every response if in canary mode."""
    if os.environ.get("MODE") == "canary":
        response.headers["X-Mode"] = "canary"
    return response

@app.route('/', methods=['GET'])
def welcome():
    return jsonify({
        "message": "SwiftDeploy API running smoothly.",
        "mode": os.environ.get("MODE", "stable"),
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
        return jsonify({"message": "Recovered. Chaos disabled."})
    
    elif mode == "slow":
        chaos_state.update({"mode": "slow", "duration": data.get("duration", 2)})
        return jsonify({"message": f"Slow mode activated. Delay: {chaos_state['duration']}s"})
    
    elif mode == "error":
        chaos_state.update({"mode": "error", "rate": data.get("rate", 0.5)})
        return jsonify({"message": f"Error mode activated. Failure rate: {chaos_state['rate']}"})

    return jsonify({"error": "Unknown chaos mode"}), 400

if __name__ == '__main__':
    port = int(os.environ.get("APP_PORT", 3000))
    app.run(host='0.0.0.0', port=port)