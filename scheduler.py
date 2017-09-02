import os
import datetime

from flask import Flask

from application import *
from models import db
from models import User, AcceptedSubmission

scheduler = Flask(__name__)
scheduler.config.from_object(os.environ['APP_SETTINGS'])
scheduler.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(scheduler)


def update_accepted():
    with scheduler.app_context():
        users = User.query.all()
        for user in users:
            print("user " + user.boj_id+ " start")
            user_id = user.boj_id
            url = "https://www.acmicpc.net/status/?user_id=" + user_id + "&result_id=4"
            soup = get_soup_from_url(url)
            table = soup.find(id="status-table")
            trs = table.tbody.find_all('tr')

            latest_submit_id = 0
            submissions = AcceptedSubmission.query.filter_by(boj_id=user_id)
            prev_accepted_ids = [submission.problem_id for submission in submissions]
            new_accepted_ids = []

            if submissions.first() is not None:
                latest_submit_id = submissions.order_by(AcceptedSubmission.submit_id.desc()).first().submit_id

            i = 0
            while 1:
                # If it's last submission
                try:
                    tr = trs[i]
                except LookupError:
                    break

                # Parse data
                tds = tr.find_all('td')
                problem_id = int(tds[2].a.string)
                submit_id = int(tds[0].string)
                if submit_id == latest_submit_id:
                    break

                if problem_id not in prev_accepted_ids:
                    date = tds[8].a.attrs['title']
                    date = datetime.datetime.strptime(date, "%Y년 %m월 %d일 %H시 %M분 %S초")
                    try:
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
                        if problem_id in new_accepted_ids:
                            db.session.query(AcceptedSubmission).filter_by(boj_id=user_id, problem_id=problem_id).update({
                                "memory": memory, "time": time, "language": language, "code_length": code_length,
                                "datetime": date
                            })
                        else:
                            accepted = AcceptedSubmission(submit_id=submit_id, problem_id=problem_id, datetime=date,
                                                          memory=memory, time=time, language=language,
                                                          code_length=code_length,
                                                          boj_id=user_id)
                            db.session.add(accepted)
                            new_accepted_ids.append(problem_id)

                    except:
                        pass

                # Load next submission page
                if tr == trs[-1]:
                    soup = get_soup_from_url(
                        "https://www.acmicpc.net/status/?user_id=" + user_id + "&result_id=4&top=" + str(submit_id))
                    table = soup.find(id="status-table")
                    trs = table.tbody.find_all('tr')
                    i = 0
                i += 1
            db.session.commit()
            print("user " + user_id + " done")
