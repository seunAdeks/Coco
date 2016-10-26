from flask import Flask
from flask_bcrypt import Bcrypt
import os

app = Flask(__name__)
bcrypt = Bcrypt(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "coco.db")
# Configurations
app.config.update(dict(
    DATABASE=db_path,
    DEBUG=True,
    SECRET_KEY='coco2015',
    USERNAME='admin',
    PASSWORD='default',
    SERVER_NAME='localhost:5000',
    # email server
    MAIL_SERVER='smtp.uni-saarland.de',
    MAIL_PORT=465,
    MAIL_USE_TLS=False,
    MAIL_USE_SSL=True,
    MAIL_DEBUG=True,
    MAIL_USERNAME=os.environ.get('MAIL_USER'),
    MAIL_PASSWORD=os.environ.get('MAIL_PASS'),
    #celery
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_RESULT_BACKEND='redis://localhost:6379'
))