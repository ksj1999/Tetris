# sensor.py
from flask import Blueprint, request, jsonify, current_app
import math
from datetime import datetime
import requests
from db import get_db_connection
import logging
from flask_socketio import SocketIO, emit

# Configure logging
logging.basicConfig(level=logging.DEBUG)

sensor_bp = Blueprint('sensor', __name__)
socketio = SocketIO()

sensor_data = {}

@sensor_bp.route('/sensor-data')
def get_sensor_data():
    global sensor_data  # 전역 변수로 선언
    logging.debug("GET /sensor-data called")
    print(f"Returning sensor data: {sensor_data}")
    return jsonify(sensor_data)

@sensor_bp.route('/sensor-data-receive', methods=['POST'])
def sensor_data_endpoint():
    global sensor_data  # 전역 변수로 선언
    data = request.json
    logging.debug(f"POST /sensor-data-receive called with data: {data}")
    print("Received sensor data:", data)
    sensor_data.update(data)

    # Roll, Pitch, Yaw 계산
    roll = math.atan2(sensor_data['accY'], sensor_data['accZ']) * 180 / math.pi
    pitch = math.atan2(-sensor_data['accX'], math.sqrt(sensor_data['accY']**2 + sensor_data['accZ']**2)) * 180 / math.pi
    yaw = math.atan2(sensor_data['gyroY'], sensor_data['gyroX']) * 180 / math.pi
    
    # 실시간으로 클라이언트에게 데이터 전송
    socketio.emit('sensor_update', {'roll': roll, 'pitch': pitch, 'yaw': yaw, 'distance': sensor_data.get('distance', 0)})

    process_and_insert_sensor_data(sensor_data)

    return jsonify(status="Data received successfully")

def process_and_insert_sensor_data(sensor_data):
    current_stack_id = current_app.config.get('CURRENT_STACK_ID')
    is_job_running = current_app.config.get('IS_JOB_RUNNING')

    if is_job_running and current_stack_id is not None:
        roll = math.atan2(sensor_data['accY'], sensor_data['accZ']) * 180 / math.pi
        pitch = math.atan2(-sensor_data['accX'], math.sqrt(sensor_data['accY']**2 + sensor_data['accZ']**2)) * 180 / math.pi
        yaw = math.atan2(sensor_data['gyroY'], sensor_data['gyroX']) * 180 / math.pi
        sensor_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        try:
            with get_db_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO sensor (time, roll, pitch, yaw, lidar, stackId) "
                        "VALUES (%s, %s, %s, %s, %s, %s)",
                        (sensor_time, roll, pitch, yaw, sensor_data['distance'], current_stack_id)
                    )
                    connection.commit()
            print(f"Sensor data inserted for stackId: {current_stack_id}")
        except Exception as e:
            logging.error(f"Failed to insert sensor data: {e}")
            print(f"Failed to insert sensor data: {e}")

def fetch_sensor_data():
    global sensor_data
    try:
        response = requests.get('http://172.20.10.5/')  # Arduino IP 주소로 변경
        sensor_data = response.json()
        logging.debug(f"Fetched sensor data: {sensor_data}")

        # 센서 데이터를 sensor_data_endpoint로 전송
        response = requests.post('http://127.0.0.1:5000/sensor/sensor-data-receive', json=sensor_data)
        if response.status_code != 200:
            logging.error(f"Failed to send sensor data: {response.status_code}")
            print(f"Failed to send sensor data: {response.status_code}")
    except Exception as e:
        logging.error(f"Error fetching sensor data: {e}")
        print(f"Error fetching sensor data: {e}")
