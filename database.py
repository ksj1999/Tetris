from flask import Blueprint, request, jsonify, current_app
import time
from db import get_db_connection
import logging

database_bp = Blueprint('database', __name__)

@database_bp.route('/start_job', methods=['POST'])
def start_job():
    data = request.json
    driver_id = data.get('driverId')
    crane_id = data.get('craneId')
    ship_id = data.get('shipId')
    start_time = time.strftime('%Y-%m-%d %H:%M:%S')

    print(f"Received start_job request with driverId={driver_id}, craneId={crane_id}, shipId={ship_id}")

    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM ship WHERE shipId = %s", (ship_id,))
                if cursor.fetchone()[0] == 0:
                    print("Invalid shipId")
                    return jsonify(error="Invalid shipId", status="Job start failed")

                cursor.execute(
                    "INSERT INTO stack (startTime, shipId, driverId, craneId) VALUES (%s, %s, %s, %s)",
                    (start_time, ship_id, driver_id, crane_id)
                )
                connection.commit()
                cursor.execute("SELECT LAST_INSERT_ID()")
                current_stack_id = cursor.fetchone()[0]
                print(f"Newly created stack ID: {current_stack_id}")

        current_app.config['CURRENT_STACK_ID'] = current_stack_id
        current_app.config['IS_JOB_RUNNING'] = True
        current_app.config['IS_PREDICTION_RUNNING'] = True
        print(f"Job started successfully with stackId: {current_stack_id}")
        return jsonify(status="Job started successfully", stackId=current_stack_id)
    except Exception as e:
        print(f"Job start failed: {e}")
        return jsonify(error=str(e), status="Job start failed")