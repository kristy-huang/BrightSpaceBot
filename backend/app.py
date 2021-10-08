from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import models

webapp = Flask(__name__)

webapp.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:''@localhost/brightspacebotdb'
webapp.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(webapp)
marshmallow = Marshmallow(webapp)


class UsersSchema(marshmallow.Schema):
    class Meta:
        fields = ('id', 'first_name', 'last_name', 'username', 'password')


user_schema = UsersSchema()
users_schema = UsersSchema(many=True)


@webapp.route("/registerUser", methods=['POST'])
def register_user():
    first_name = request.json['first_name']
    last_name = request.json['last_name']
    username = request.json['username']
    password = request.json['password']
    user = models.Users(first_name, last_name, username, password)
    db.session.add(user)
    db.session.commit()
    return user_schema.jsonify(user)


@webapp.route("/getUsers", methods=['GET'])
def get_users():
    all_users = models.Users.query.all()
    results = users_schema.dump(all_users)
    return jsonify(results)


if __name__ == "__main__":
    webapp.run(debug=True)
