import os
import urllib.request

from bs4 import BeautifulSoup
from flask import Flask, render_template, request
from models import db


application = Flask(__name__)
application.config.from_object(os.environ['APP_SETTINGS'])
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(application)


from models import User


user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) ' \
             'Chrome/58.0.3029.110 Safari/537.36'
hds = {'User-Agent': user_agent}


def is_boj_user(user_id):
    url = "https://www.acmicpc.net/user/" + user_id
    try:
        req = urllib.request.Request(url, headers=hds)
        urllib.request.urlopen(req)
    except urllib.error.HTTPError:
        return False
    else:
        return True


@application.route('/')
def render_index():
    return render_template("index.html")


@application.route('/user')
def search_user():
    user_id = request.args.get("id")
    if not is_boj_user(user_id):
        return render_template("index.html", id=user_id, err=True)
    else:
        return render_template("user.html")

if __name__ == "__main__":
    application.run()

