from flask import Blueprint
from sensor import sensor_bp
from database import database_bp
from video import video_bp
from index import index_bp
from prediction import prediction_bp

routes_bp = Blueprint('routes', __name__)
routes_bp.register_blueprint(sensor_bp, url_prefix='/sensor')
routes_bp.register_blueprint(database_bp, url_prefix='/database')
routes_bp.register_blueprint(video_bp, url_prefix='/video')
routes_bp.register_blueprint(index_bp, url_prefix='/')  # 'index_bp'를 루트 경로에 등록
routes_bp.register_blueprint(prediction_bp, url_prefix='/prediction')