import torch
from ultralytics import YOLO
import cv2

# 장치 설정 (GPU 사용 가능 여부에 따라)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# 학습된 모델 가져오기 -> best.pt
model = YOLO("./models/best_v8_2.pt")

# 비디오 캡처

camera = cv2.VideoCapture(1)


# 전역 변수 초기화
latency = 0
is_prediction_running = False
current_stack_id = None
is_job_running = False
