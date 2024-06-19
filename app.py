from flask import Flask, session, redirect, url_for
from flask_cors import CORS
from routes import routes_bp
from apscheduler.schedulers.background import BackgroundScheduler
from sensor import fetch_sensor_data
import config

# Flask 애플리케이션 생성 및 설정
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 세션을 사용하기 위해 필요
CORS(app)
app.register_blueprint(routes_bp)

# 환경 변수 설정
app.config['CURRENT_STACK_ID'] = config.current_stack_id
app.config['IS_JOB_RUNNING'] = config.is_job_running
app.config['LATENCY'] = config.latency
app.config['IS_PREDICTION_RUNNING'] = config.is_prediction_running

# 백그라운드 작업 스케줄러 설정 및 시작
scheduler = BackgroundScheduler()
scheduler.add_job(fetch_sensor_data, 'interval', seconds=3)
scheduler.start()

# 비디오 블루프린트 설정
from video import set_app
set_app(app)

# 서버 실행
if __name__ == "__main__":
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
