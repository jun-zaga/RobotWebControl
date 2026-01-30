from flask import Flask, request, jsonify, send_from_directory
import time
import threading

import robotControl as rc

app = Flask(__name__, static_folder="static", static_url_path="")

# --- Safety / watchdog ---
LAST_CMD_TS = time.time()
CMD_TIMEOUT_SEC = 0.6          # if no drive cmd within this, stop
WATCHDOG_PERIOD_SEC = 0.1
_lock = threading.Lock()

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def is_number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)

def update_last_cmd_ts():
    global LAST_CMD_TS
    with _lock:
        LAST_CMD_TS = time.time()

def watchdog_loop():
    while True: 
        time.sleep(WATCHDOG_PERIOD_SEC)
        with _lock:
            age = time.time() - LAST_CMD_TS
        if age > CMD_TIMEOUT_SEC:
            rc.stop()

threading.Thread(target=watchdog_loop, daemon=True).start()

# --- Static site ---
@app.get("/")
def root():
    return send_from_directory(app.static_folder, "index.html")

@app.get("/health")
def health():
    return jsonify(ok=True, time=time.time())

# --- APIs ---
@app.post("/api/drive")
def api_drive():
    data = request.get_json(silent=True) or {}

    l = data.get("l")
    r = data.get("r")

    if not (is_number(l) and is_number(r)):
        return jsonify(ok=False, error="l and r must be numbers"), 400

    l = float(clamp(l, -1.0, 1.0))
    r = float(clamp(r, -1.0, 1.0))

    rc.drive(l, r)
    update_last_cmd_ts()
    return jsonify(ok=True, l=l, r=r)

@app.post("/api/head")
def api_head():
    data = request.get_json(silent=True) or {}
    pan = data.get("pan")
    tilt = data.get("tilt")

    # Allow sending one or both; validate only what's present
    if pan is not None:
        if not is_number(pan):
            return jsonify(ok=False, error="pan must be a number"), 400
        pan = float(clamp(pan, 0.0, 1.0))
        rc.head_pan(pan)

    if tilt is not None:
        if not is_number(tilt):
            return jsonify(ok=False, error="tilt must be a number"), 400
        tilt = float(clamp(tilt, 0.0, 1.0))
        rc.head_tilt(tilt)

    return jsonify(ok=True, pan=pan, tilt=tilt)

@app.post("/api/waist")
def api_waist():
    data = request.get_json(silent=True) or {}
    pos = data.get("pos")

    if not is_number(pos):
        return jsonify(ok=False, error="pos must be a number"), 400

    pos = float(clamp(pos, 0.0, 1.0))
    rc.waist(pos)
    return jsonify(ok=True, pos=pos)

@app.post("/api/say")
def api_say():
    data = request.get_json(silent=True) or {}
    phrase_id = data.get("phraseId")

    if not isinstance(phrase_id, int):
        return jsonify(ok=False, error="phraseId must be an int"), 400

    ok = rc.say(phrase_id)
    if not ok:
        return jsonify(ok=False, error="unknown phraseId"), 400
    return jsonify(ok=True, phraseId=phrase_id)

@app.post("/api/stop")
def api_stop():
    rc.stop()
    update_last_cmd_ts()
    return jsonify(ok=True)

if __name__ == "__main__":
    # IMPORTANT on Pi: host="0.0.0.0" so other devices can reach it
    # Pick your port number per project requirement
    rc.stop()  # stop on startup for safety
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
