import os

from bs4 import BeautifulSoup
from flask import Flask, render_template
from models import db


application = Flask(__name__)
application.config.from_object(os.environ['APP_SETTINGS'])
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(application)


from models import User


@application.route('/')
def render_index():
    return render_template("index.html")

if __name__ == "__main__":
    application.run()
