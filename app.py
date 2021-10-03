from flask import Flask, send_from_directory
from flask_restful import Api, Resource, reqparse
from flask_cors import CORS  # comment this out on deployment
from backendApi.HelloApiHandler import HelloApiHandler
from backendApi.registerApiHandler import RegisterApiHandler

webapp = Flask(__name__, static_url_path='', static_folder='web/public')
CORS(webapp)  # comment this out on deployment
api = Api(webapp)


@webapp.route("/", defaults={'path': ''})
def serve(path):
    return send_from_directory(webapp.static_folder, 'index.html')


api.add_resource(HelloApiHandler, '/flask/hello')
api.add_resource(RegisterApiHandler, '/register')
