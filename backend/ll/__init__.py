import logging
from flask import Flask
from flask_cors import CORS
from ll.api import api
from ll.model import db
import os

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

app = Flask(__name__)

def init_webapp(test=False):
    app.register_blueprint(api, url_prefix='/api')
    
    if test:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI', 'sqlite:///ll.db')

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "abc123")
    CORS(app, 
         supports_credentials=True,
         resources={r"/api/*": {"origins": "*"}})
    db.app = app
    db.init_app(app)
    return app