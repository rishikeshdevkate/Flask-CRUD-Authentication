from flask import Flask, request, jsonify
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, ForeignKey

import jwt
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:postgres@localhost/flask-demo'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class UserData(db.Model):
    __tablename__ = 'user_data'
    id = Column(Integer, primary_key = True)
    public_id = Column(String(50), unique = True)
    name = Column(String(100))
    email = Column(String(70), unique = True)
    password = Column(String())


class UserProduct(db.Model):
    __tablename__ = 'user_product'
    id = Column(Integer, primary_key=True)
    product_name = Column(String(150), unique=True, nullable=False)
    type = Column(String(150), nullable=True)
    price = Column(Integer)
    description = Column(String(150),  nullable=True)
    user = Column(Integer, ForeignKey('user_data.id'))

    def __repr__(self):
      return "<UserProduct %r>" % self.product_name



def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # jwt is passed in the request header
        auth_header =  request.environ.get('HTTP_AUTHORIZATION')
        if auth_header:
            key, token = auth_header.split(' ')
        # return 401 if token is not passed
        if not token:
            return jsonify({'message': 'Token is missing !!'}), 401

        try:
            # decoding the payload to fetch the stored details
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = UserData.query \
                .filter_by(public_id=data['public_id']) \
                .first()
        except:
            return jsonify({
                'message': 'Token is invalid !!'
            }), 401
        # returns the current logged in users contex to the routes
        return f( *args, **kwargs)

    return decorated
