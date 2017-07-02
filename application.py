import os
import urllib.request
import datetime

from bs4 import BeautifulSoup
from flask import Flask, render_template, request
from flask_debugtoolbar import DebugToolbarExtension

from models import db
from models import User

application = Flask(__name__)
application.config.from_object(os.environ['APP_SETTINGS'])
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(application)

toolbar = DebugToolbarExtension(application)

# define header for urllib request
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
    except UnicodeEncodeError:
        return False
    else:
        return True


def update_profile(user):
    url = "https://www.acmicpc.net/user/" + user.boj_id
    req = urllib.request.Request(url, headers=hds)
    fp = urllib.request.urlopen(req)
    source = fp.read()
    fp.close()

    soup = BeautifulSoup(source, "html.parser")
    intro = soup.blockquote.string
    solved_num = soup.tbody.find_all('tr')[1].td.string

    if user.intro != intro:
        user.intro = intro
    if user.solved_num != solved_num:
        user.solved_num = solved_num
    db.session.commit()


@application.route('/')
def render_index():
    return render_template("index.html")


@application.route('/user')
def search_user():
    user_id = request.args.get("id")
    if not User.query.filter_by(boj_id=user_id).scalar():
        if is_boj_user(user_id):
            user = User(boj_id=user_id)
            db.session.add(user)
            db.session.commit()
        else:
            return render_template("index.html", id=user_id, err=True)

    user = User.query.filter_by(boj_id=user_id).first()
    return render_template("user.html", user=user)

if __name__ == "__main__":
    application.run()

