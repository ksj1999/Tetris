from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
import os

index_bp = Blueprint('index', __name__)

MODELS_PATH = './models'

@index_bp.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['driver_id'] = request.form['driverId']
        session['crane_id'] = request.form['craneId']
        session['ship_id'] = request.form['shipId']
        return redirect(url_for('routes.index.main'))  # 'index'는 블루프린트 이름입니다.
    return render_template('login.html')

@index_bp.route('/main', methods=['GET'])
def main():
    if 'driver_id' not in session or 'crane_id' not in session or 'ship_id' not in session:
        return redirect(url_for('index.login'))  # 'index'는 블루프린트 이름입니다.
    return render_template('index.html', driverId=session['driver_id'], craneId=session['crane_id'], shipId=session['ship_id'])

@index_bp.route('/query')
def query():
    return render_template('query.html')

@index_bp.route('/sensor')
def sensor():
    return render_template('sensor.html')

@index_bp.route('/get_models', methods=['GET'])
def get_models():
    model_files = [f for f in os.listdir(MODELS_PATH) if f.endswith('.pt')]
    return jsonify(model_files)
