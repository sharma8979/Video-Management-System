from flask import Flask, request, jsonify
from flask_cors import CORS
from threading import Thread
import cv2
import time

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

streams = {}
results = {}
alerts = {}

def asset_detection(frame):
    # Dummy asset detection model
    return {"assets": 3}

def defect_analysis(frame):
    # Dummy defect analysis model
    return {"defects": 1 if int(time.time()) % 10 == 0 else 0}

MODEL_MAP = {
    "asset_detection": asset_detection,
    "defect_analysis": defect_analysis
}

def process_stream(stream_id, path, models):
    cap = cv2.VideoCapture(path)
    while cap.isOpened() and streams[stream_id]['status'] == 'running':
        ret, frame = cap.read()
        if not ret:
            break
        stream_results = {}
        stream_alerts = []
        for model in models:
            output = MODEL_MAP.get(model, lambda x: {})(frame)
            stream_results[model] = output
            if model == "defect_analysis" and output.get("defects", 0) > 0:
                stream_alerts.append(f"Defect detected in {stream_id}!")
        results[stream_id] = stream_results
        alerts[stream_id] = stream_alerts
        time.sleep(1)
    cap.release()
    streams[stream_id]['status'] = 'stopped'

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

@app.route('/add_stream', methods=['POST'])
def add_stream():
    data = request.json
    # Validate input
    if not all(k in data for k in ("stream_id", "path", "models")):
        return jsonify({"error": "Missing required keys"}), 400
    stream_id = data['stream_id']
    path = data['path']
    models = data['models']
    if stream_id in streams:
        return jsonify({"error": "Stream ID already exists"}), 400
    streams[stream_id] = {'path': path, 'models': models, 'status': 'running'}
    t = Thread(target=process_stream, args=(stream_id, path, models))
    t.daemon = True
    t.start()
    return jsonify({"message": "Stream added", "id": stream_id})

@app.route('/streams', methods=['GET'])
def get_streams():
    return jsonify(streams)

@app.route('/results', methods=['GET'])
def get_results():
    return jsonify(results)

@app.route('/alerts', methods=['GET'])
def get_alerts():
    return jsonify(alerts)

@app.route('/stop_stream/<stream_id>', methods=['POST'])
def stop_stream(stream_id):
    if stream_id in streams:
        streams[stream_id]['status'] = 'stopped'
        return jsonify({"message": f"Stream {stream_id} stopped"})
    return jsonify({"error": "Stream not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)