from flask import Flask
from flask import Response

flask_app = Flask("flaskapp")

@flask_app.route("/shark")
def shark():
  return Response("Welcome to the shark zone\n", mimetype = "text/plain")

app = flask_app.wsgi_app