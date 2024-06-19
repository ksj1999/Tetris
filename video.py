from flask import Blueprint, Response, current_app, jsonify
import cv2
import time
import math
from datetime import datetime
from config import model, camera
from db import get_db_connection

video_bp = Blueprint('video', __name__)

_app = None
last_prediction_data = {}

def set_app(application):
    global _app
    _app = application

@video_bp.route('/video_feed')
def video_feed():
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

def generate():
    global _app, last_prediction_data
    frame_count = 0
    with _app.app_context():
        while True:
            success, frame = camera.read()
            if not success:
                break
            frame_count += 1
            if _app.config.get('IS_PREDICTION_RUNNING'):
                frame, last_prediction_data = process_frame(frame)
            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(_app.config.get('LATENCY', 0) / 1000.0)

def process_frame(frame):
    results = model.track(frame, persist=True)
    boxes = results[0].boxes.xyxy.tolist()
    classes = results[0].boxes.cls.tolist()
    confidences = results[0].boxes.conf.tolist()
    names = results[0].names

    left_top_castings = []
    left_bottom_castings = []
    right_top_castings = []
    right_bottom_castings = []

    prediction_data = {}

    for i, (box, cls, conf) in enumerate(zip(boxes, classes, confidences)):
        if conf < 0.65:
            continue
        x1, y1, x2, y2 = box
        name = names[int(cls)]

        if name == 'corner-casting':
            box_color = (0, 0, 255)  # 코너 캐스팅 색상 (빨강)
            center_color = (255, 0, 0)  # 중심 좌표 색상 (파란색)
            center_radius = 2  # 코너 캐스팅 중심 좌표 원의 크기
            text_color = (0, 0, 255)  # 코너 캐스팅 텍스트 색상 (빨강)
            text_scale = 0.8  # 코너 캐스팅 텍스트 크기
            text_thickness = 1  # 코너 캐스팅 텍스트 두께
            box_thickness = 1  # 코너 캐스팅 박스 두께
            background_color = (255, 255, 255)  # 코너 캐스팅 텍스트 배경 색상 (흰색)

            x_center = (x1 + x2) / 2
            y_center = (y1 + y2) / 2

            # 코너 캐스팅을 위치에 따라 분류
            if x_center < frame.shape[1] / 2:
                if y_center < frame.shape[0] / 2:
                    left_top_castings.append((x_center, y_center))
                else:
                    left_bottom_castings.append((x_center, y_center))
            else:
                if y_center < frame.shape[0] / 2:
                    right_top_castings.append((x_center, y_center))
                else:
                    right_bottom_castings.append((x_center, y_center))

            # 바운딩 박스와 중앙 좌표를 그립니다.
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), box_color, box_thickness)
            cv2.circle(frame, (int(x_center), int(y_center)), center_radius, center_color, -1)
            cv2.putText(frame, f"({int(x_center)}, {int(y_center)})", (int(x_center), int(y_center) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, text_scale, center_color, text_thickness)

            # # 바운딩 박스 위에 텍스트 표시 (ID, 클래스 이름, 정확도)
            # label = f'id:{i} {name} {conf:.2f}'
            # label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, text_scale, text_thickness)[0]
            # label_x = int(x1)
            # label_y = int(y2) + label_size[1] + 10 if y2 < frame.shape[0] - 10 else int(y2) - 10

            # cv2.rectangle(frame, (label_x, label_y - label_size[1] - 2), (label_x + label_size[0], label_y + 2),
            #               background_color, cv2.FILLED)
            # cv2.putText(frame, label, (label_x, label_y), cv2.FONT_HERSHEY_SIMPLEX, text_scale, (0, 0, 0), text_thickness)

    # 정렬 여부 판단
    def check_alignment(castings):
        if len(castings) > 1:
            avg_x = sum(cc[0] for cc in castings) / len(castings)
            for cc in castings:
                if abs(cc[0] - avg_x) > 10:
                    return False
        return True

    is_aligned = (check_alignment(left_top_castings) and
                  check_alignment(left_bottom_castings) and
                  check_alignment(right_top_castings) and
                  check_alignment(right_bottom_castings))

    if is_aligned:
        alignment_text = "All Corner Castings Aligned"
        alignment_color = (0, 255, 0)
        prediction_data['stackResult'] = 1
    else:
        alignment_text = "Corner Castings Not Aligned"
        alignment_color = (0, 0, 255)
        prediction_data['stackResult'] = 0

    prediction_data['alignment'] = alignment_text

    # 주석이 달린 프레임에 정렬 여부 텍스트 추가
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1
    font_thickness = 1
    text_size = cv2.getTextSize(alignment_text, font, font_scale, font_thickness)[0]
    text_x = (frame.shape[1] - text_size[0]) // 2
    text_y = text_size[1] + 20

    cv2.putText(frame, alignment_text, (text_x, text_y), font, font_scale, alignment_color, font_thickness, cv2.LINE_AA)

    return frame, prediction_data

def save_prediction():
    global last_prediction_data
    current_stack_id = current_app.config.get('CURRENT_STACK_ID')
    if not current_stack_id:
        return jsonify(error="No active job found"), 400

    try:
        stack_result = last_prediction_data.get('stackResult', None)
        prediction_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO image (time, stackResult, stackId) VALUES (%s, %s, %s)",
                    (prediction_time, stack_result, current_stack_id)
                )
                connection.commit()
        return jsonify(status="Prediction saved successfully"), 200
    except Exception as e:
        return jsonify(error=str(e)), 500
