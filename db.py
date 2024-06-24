from sshtunnel import SSHTunnelForwarder
import pymysql
from contextlib import contextmanager
from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

# 환경 변수 가져오기
SSH_HOST = os.getenv('SSH_HOST')
SSH_PORT = int(os.getenv('SSH_PORT'))
SSH_USER = os.getenv('SSH_USER')
SSH_PRIVATE_KEY = os.getenv('SSH_PRIVATE_KEY')

DB_HOST = os.getenv('DB_HOST')
DB_PORT = int(os.getenv('DB_PORT'))
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_DATABASE = os.getenv('DB_DATABASE')

@contextmanager
def create_ssh_tunnel():
    server = SSHTunnelForwarder(
        (SSH_HOST, SSH_PORT),
        ssh_username=SSH_USER,
        ssh_pkey=SSH_PRIVATE_KEY,
        remote_bind_address=(DB_HOST, DB_PORT)
    )
    server.start()
    try:
        yield server
    finally:
        server.stop()

@contextmanager
def get_db_connection():
    with create_ssh_tunnel() as server:
        connection = pymysql.connect(
            host='127.0.0.1',
            port=server.local_bind_port,
            user=DB_USER,
            password=DB_PASSWORD,
            db=DB_DATABASE,
            autocommit=False  # 명시적으로 커밋을 수행하기 위해 autocommit을 False로 설정
        )
        try:
            yield connection
        finally:
            connection.close()