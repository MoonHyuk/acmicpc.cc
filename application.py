import os
import urllib.request
import datetime

from bs4 import BeautifulSoup
from flask import Flask, render_template, request, abort
from flask_debugtoolbar import DebugToolbarExtension

from models import db
from models import User, Submission

application = Flask(__name__)
application.config.from_object(os.environ['APP_SETTINGS'])
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(application)

toolbar = DebugToolbarExtension(application)

# define header for urllib request
user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) ' \
             'Chrome/58.0.3029.110 Safari/537.36'
hds = {'User-Agent': user_agent}

# constants
RESULTS = ["기다리는 중", "재채점을 기다리는 중", "채점 준비중", "채점중", "맞았습니다!!", "출력 형식이 잘못되었습니다",
           "틀렸습니다", "시간 초과", "메모리 초과", "출력 초과", "런타임 에러", "컴파일 에러"]


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


def get_soup_from_url(url, user_id):
    url = url + user_id
    req = urllib.request.Request(url, headers=hds)
    fp = urllib.request.urlopen(req)
    source = fp.read()
    fp.close()
    return BeautifulSoup(source, "html.parser")


def update_profile(user_id):
    user = User.query.filter_by(boj_id=user_id).first()
    soup = get_soup_from_url("https://www.acmicpc.net/user/", user_id)
    intro = soup.blockquote.string
    solved_num = soup.tbody.find_all('tr')[1].td.string

    if user.intro != intro:
        user.intro = intro
    if user.solved_num != solved_num:
        user.solved_num = solved_num

    update_submission(user_id)
    user.update_time = datetime.datetime.now()
    db.session.commit()
    return user


def update_submission(user_id):
    soup = get_soup_from_url("https://www.acmicpc.net/status/?user_id=", user_id)
    table = soup.find(id="status-table")
    trs = table.tbody.find_all('tr')

    latest_submit_id = 0
    submissions = Submission.query.filter_by(boj_id=user_id)
    if submissions.scalar():
        latest_submit_id = submissions.first().submit_id

    for tr in trs:
        tds = tr.find_all('td')
        submit_id = tds[0].string
        if submit_id == latest_submit_id:
            break
        problem_id = tds[2].a.string
        problem_name = tds[2].a.attrs['title']
        result = tds[3].span.span.string.replace("\n", "").replace("\t", "")
        memory = tds[4].find(text=True, recursive=False)
        time = tds[5].find(text=True, recursive=False)
        language = tds[6].string.replace("\n", "").replace("\t", "")
        code_length = tds[7].string[:-2].replace("\n", "").replace("\t", "").split(" ")[0]
        date = tds[8].a.attrs['title']
        print(problem_id + " " + problem_name + " ")
        print(result)
        print(memory)
        print(time)
        print(language)
        print(code_length)
        print(date)

@application.route('/')
def render_index():
    return render_template("index.html")


@application.route('/user')
def get_user():
    user_id = request.args.get("id")
    if not User.query.filter_by(boj_id=user_id).scalar():
        if is_boj_user(user_id):
            user = User(boj_id=user_id)
            db.session.add(user)
            db.session.commit()
        else:
            return render_template("index.html", id=user_id, err=True)

    user = User.query.filter_by(boj_id=user_id).first()
    if user.update_time is None or (datetime.datetime.now() - user.update_time).seconds > 3600:
        updated = False
    else:
        updated = True
    return render_template("user.html", user=user, updated=updated)


@application.route('/update_user')
def update_user():
    if request.is_xhr:
        user_id = request.args.get('id')
        update_profile(user_id)
        return "OK"
    else:
        abort(404)


if __name__ == "__main__":
    application.run()
