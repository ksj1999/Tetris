from flask import Blueprint, jsonify, request, current_app

prediction_bp = Blueprint('prediction', __name__)

@prediction_bp.route('/start_prediction', methods=['POST'])
def start_prediction():
    current_app.config['IS_PREDICTION_RUNNING'] = True
    print("Prediction started")
    return jsonify(status="Prediction started")

@prediction_bp.route('/stop_prediction', methods=['POST'])
def stop_prediction():
    current_app.config['IS_PREDICTION_RUNNING'] = False
    print("Prediction stopped")
    return jsonify(status="Prediction stopped")

@prediction_bp.route('/set_latency', methods=['POST'])
def set_latency():
    latency = int(request.form.get('latency', 0))
    current_app.config['LATENCY'] = latency
    print(f"Latency set to {latency} ms")
    return jsonify(status="Latency updated successfully")
