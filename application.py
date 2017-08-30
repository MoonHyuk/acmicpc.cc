import os
import urllib.request
import datetime

from bs4 import BeautifulSoup
from flask import Flask, render_template, request, abort
from flask_debugtoolbar import DebugToolbarExtension
from flask_sslify import SSLify

from models import db
from models import User, Submission, AcceptedSubmission

application = Flask(__name__)
sslify = SSLify(application)
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
        soup = get_soup_from_url(url)
        return soup.h1.string.strip()


def get_soup_from_url(url):
    req = urllib.request.Request(url, headers=hds)
    fp = urllib.request.urlopen(req)
    source = fp.read()
    fp.close()
    return BeautifulSoup(source, "html.parser")


def update_profile(user_id):
    user = User.query.filter_by(boj_id=user_id).first()
    soup = get_soup_from_url("https://www.acmicpc.net/user/" + user_id)
    intro = soup.blockquote.string
    solved_num = soup.tbody.find_all('tr')[1].td.string

    if user.intro != intro:
        user.intro = intro
    if user.solved_num != solved_num:
        user.solved_num = solved_num

    update_submission(user_id)
    user.update_time = datetime.datetime.utcnow()
    db.session.commit()
    return user


def update_submission(user_id):
    soup = get_soup_from_url("https://www.acmicpc.net/status/?user_id=" + user_id)
    table = soup.find(id="status-table")
    trs = table.tbody.find_all('tr')

    latest_submit_id = 0
    submissions = Submission.query.filter_by(boj_id=user_id)
    if submissions.first() is not None:
        latest_submit_id = submissions.order_by(Submission.submit_id.desc()).first().submit_id

    i = 0
    while 1:
        # If it's last submission
        try:
            tr = trs[i]
        except LookupError:
            break

        # Parse data
        tds = tr.find_all('td')
        submit_id = int(tds[0].string)
        date = tds[8].a.attrs['title']
        date = datetime.datetime.strptime(date, "%Y년 %m월 %d일 %H시 %M분 %S초")
        if submit_id == latest_submit_id or (datetime.datetime.utcnow() - date).days >= 14:
            break
        problem_id = int(tds[2].a.string)
        problem_name = tds[2].a.attrs['title']
        result = tds[3].span.span.string.replace("\n", "").replace("\t", "")
        try:
            result = RESULTS.index(result)

            # 틀렸을 경우 메모리와 시간은 0으로 한다.
            try:
                memory = int(tds[4].find(text=True, recursive=False))
            except TypeError:
                memory = 0
            try:
                time = int(tds[5].find(text=True, recursive=False))
            except TypeError:
                time = 0
            language = tds[6].string.replace("\n", "").replace("\t", "")

            # 코드 길이를 감추는 문제들이 있음. 그런 경우 code_length 를 0으로 해준다.
            try:
                code_length = int(tds[7].string[:-2].replace("\n", "").replace("\t", "").split(" ")[0])
            except ValueError:
                code_length = 0

            # Save data
            submit = Submission(submit_id=submit_id, datetime=date, problem_id=problem_id, problem_name=problem_name,
                                result=result, memory=memory, time=time, language=language, code_length=code_length,
                                boj_id=user_id)
            db.session.add(submit)

        except:
            pass

        # Load next submission page
        if tr == trs[-1]:
            soup = get_soup_from_url("https://www.acmicpc.net/status/?user_id=" + user_id + "&top=" + str(submit_id))
            table = soup.find(id="status-table")
            trs = table.tbody.find_all('tr')
            i = 0
        i += 1
    db.session.commit()


@application.route('/')
def render_index():
    return render_template("index.html")


@application.route('/user')
def get_user():
    user_id = request.args.get("id")
    acc_user_id = is_boj_user(user_id)
    if acc_user_id:
        if not User.query.filter_by(boj_id=acc_user_id).scalar():
            user = User(boj_id=acc_user_id)
            db.session.add(user)
            db.session.commit()
    else:
        return render_template("index.html", id=user_id, err=True)

    user = User.query.filter_by(boj_id=acc_user_id).first()
    submissions = []
    accepted_submissions = AcceptedSubmission.query.filter_by(boj_id=acc_user_id).order_by(
        AcceptedSubmission.datetime).all()
    if user.update_time is None or (datetime.datetime.utcnow() - user.update_time).seconds > 600:
        updated = False
    else:
        updated = True
        two_weeks_ago = datetime.date.today() - datetime.timedelta(days=14)
        submissions = Submission.query.filter_by(boj_id=acc_user_id).filter(Submission.datetime > two_weeks_ago)
    return render_template("user.html", user=user, updated=updated, submissions=submissions,
                           accepted_submissions=accepted_submissions)


@application.route('/update_user')
def update_user():
    if request.is_xhr:
        user_id = request.args.get('id')
        update_profile(user_id)
        return "OK"
    else:
        abort(404)


@application.route('/statistics')
def statistics():
    with open('ranking.txt', 'r') as f:
        data_list = []
        data_txt = f.readlines()
        for data in data_txt:
            data_list.append(data.strip('\n').split(' '))

        return render_template("statistics.html", data_list=data_list)


if __name__ == "__main__":
    application.run()
