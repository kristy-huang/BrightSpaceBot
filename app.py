from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

webapp = Flask(__name__)

webapp.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:''@localhost/brightspacebotdb'
webapp.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(webapp)
marshmallow = Marshmallow(webapp)


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    username = db.Column(db.String(50))
    password = db.Column(db.String(50))

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


@webapp.route("/getUsers", methods=['GET'])
def get_users():
    all_users = Users.query.all()
    results = users_schema.dump(all_users)
    return jsonify(results)


@webapp.route("/registerUser", methods=['POST'])
def register_user():
    first_name = request.json['first_name']
    last_name = request.json['last_name']
    username = request.json['username']
    password = request.json['password']
    user = Users(first_name, last_name, username, password)
    db.session.add(user)
    db.session.commit()
    return user_schema.jsonify(user)


if __name__ == "__main__":
    webapp.run(debug=True)
