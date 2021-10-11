from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required
# import models

webapp = Flask(__name__)
CORS(webapp)
JWTManager(webapp)

webapp.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:''@localhost/brightspacebotdb'
webapp.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
webapp.config['SECRET_KEY'] = 'the random string'

db = SQLAlchemy(webapp)
marshmallow = Marshmallow(webapp)


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    username = db.Column(db.String(50))
    password = db.Column(db.String(255))

    def __init__(self, first_name, last_name, username, password):
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.password = password


class UsersSchema(marshmallow.Schema):
    class Meta:
        fields = ('id', 'first_name', 'last_name', 'username', 'password')


user_schema = UsersSchema()
users_schema = UsersSchema(many=True)


@webapp.route("/registerUser", methods=['POST'])
def register_user():
    # get user input from website
    first_name = request.json['first_name']
    last_name = request.json['last_name']
    username = request.json['username']
    password = request.json['password']

    hash_pass = generate_password_hash(password)

    # check if user is already signed up
    db_user = Users.query.filter_by(username=username).first()
    if db_user is not None:
        return jsonify({"message": "Username already exists!"})

    # add user to database
    user = Users(first_name, last_name, username, hash_pass)
    db.session.add(user)
    db.session.commit()
    return user_schema.jsonify(user)


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
