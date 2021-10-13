from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required
import config
# import models

webapp = Flask(__name__)
CORS(webapp)
JWTManager(webapp)

webapp.config['SQLALCHEMY_DATABASE_URI'] = config.database_uri_dev
webapp.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config.track_modifications
webapp.config['SECRET_KEY'] = config.secret_key

db = SQLAlchemy(webapp)
marshmallow = Marshmallow(webapp)


# db schema for a user
class Users(db.Model):
    username = db.Column(db.String(50), primary_key=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    password = db.Column(db.String(255))
    major = db.Column(db.String(50))

    def __init__(self, username, first_name, last_name, password, major):
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.password = password
        self.major = major


class UsersSchema(marshmallow.Schema):
    class Meta:
        fields = ('username', 'first_name', 'last_name', 'password', 'major')


user_schema = UsersSchema()
users_schema = UsersSchema(many=True)


class Preferences(db.Model):
    username = db.Column(db.String(50), primary_key=True)
    storage_location = db.Column(db.String(100))
    notification_frequency = db.Column(db.String(50))

    def __init__(self, username, storage_location, notification_frequency):
        self.username = username
        self.storage_location = storage_location
        self.notification_frequency = notification_frequency


@webapp.route("/registerUser", methods=['POST'])
def register_user():
    # get user input from website
    print(request.get_json())
    username = request.json['username']
    first_name = request.json['firstName']
    last_name = request.json['lastName']
    password = request.json['password']
    major = request.json['major']
    storage_location = request.json['storageLocation']
    notification_frequency = request.json['notificationFrequency']

    hash_pass = generate_password_hash(password)

    # check if user is already signed up
    db_user = Users.query.filter_by(username=username).first()
    if db_user is not None:
        return jsonify({
            "status": 400,
            "message": "Username already exists!"
        })

    # add user to database
    user = Users(username, first_name, last_name, hash_pass, major)
    db.session.add(user)
    db.session.commit()

    # add user preferences to database
    user_preferences = Preferences(username, storage_location, notification_frequency)
    db.session.add(user_preferences)
    db.session.commit()

    return jsonify({
        "status": 200,
        "message": "User successfully registered"
    })


@webapp.route("/login", methods=['POST'])
def login_user():
    # get user input from website
    username = request.json['username']
    password = request.json['password']

    # find user in db by username
    user = Users.query.filter_by(username=username).first()

    # user exists and password is correct
    if user and check_password_hash(user.password, password):
        access_token = create_access_token(identity=user.username)
        refresh_token = create_refresh_token(identity=user.username)
        return jsonify({
            "access_token": access_token,
            "refresh_token": refresh_token
        })

    return jsonify({
        "message": "Error, could not login"
    })


@webapp.route("/getUsers", methods=['GET'])
def get_users():
    all_users = Users.query.all()
    results = users_schema.dump(all_users)
    return jsonify(results)


if __name__ == "__main__":
    webapp.run(debug=True)
