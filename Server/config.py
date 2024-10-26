from flask import Flask, request, make_response, jsonify
from sqlalchemy import MetaData
from flask_migrate import Migrate
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.ext.hybrid import hybrid_property
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from datetime import datetime, timezone, timedelta
import os
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, current_user, get_jwt, set_access_cookies, get_jwt_identity

app = Flask(__name__)
metadata = MetaData()
db = SQLAlchemy(metadata=metadata)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///whimsy.db'
app.config['SECRET_KEY'] = '49b77a70efb919bcf7d37b1b05c7d149'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = b'\x9d~\xaejx\xfe\xc5\xa1\xf6\xaa\x31\xdb\xb0k\xf7\x9d'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=72)
app.config['JWT_COOKIE_SECURE'] = False

db.init_app(app)
migrate = Migrate(app,db)
jwt = JWTManager(app)
api = Api(app)
bcrypt = Bcrypt(app)
CORS(app)