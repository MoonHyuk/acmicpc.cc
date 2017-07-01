from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    boj_id = db.Column(db.String(20), unique=True, nullable=False)
    into = db.Column(db.String(100), default="")
    tobcoder_id = db.Column(db.String(20), default="")
    tobcoder_rating = db.Column(db.Integer, default=0)
    codeforce_id = db.Column(db.String(20), default="")
    codeforce_rating = db.Column(db.Integer, default=0)
    update_time = db.Column(db.DateTime)


class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    submit_id = db.Column(db.Integer, unique=True, nullable=False)
    number = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    result = db.Column(db.Integer, nullable=False)
    language = db.Column(db.Integer, nullable=False)
    datetime = db.Column(db.DateTime, nullable=False)


class Ranking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    rank = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=False)
