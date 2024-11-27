from flask import Flask
import logging
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECURITY_API_KEY'] = '#' 

app.config.from_object('config.DevelopmentConfig')
db = SQLAlchemy(app)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

from . import views
