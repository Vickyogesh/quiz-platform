# coding: utf-8
from sqlalchemy import Column, Date, DateTime, Float, Index, Integer, SmallInteger, String, Text, text
from sqlalchemy.dialects.mysql.enumerated import ENUM
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Answer(db.Model):
    __tablename__ = 'answers'

    user_id = Column(Integer, primary_key=True, nullable=False)
    quiz_type = Column(SmallInteger, primary_key=True, nullable=False)
    question_id = Column(Integer, primary_key=True, nullable=False)
    is_correct = Column(Integer, nullable=False, default=0)


class Application(db.Model):
    __tablename__ = 'applications'

    id = Column(SmallInteger, primary_key=True)
    appkey = Column(String(50), nullable=False, unique=True)
    description = Column(String(100))


class Blacklist(db.Model):
    __tablename__ = 'blacklist'

    id = Column(Integer, primary_key=True, nullable=False)
    quiz_type = Column(SmallInteger, primary_key=True, nullable=False)


class Chapter(db.Model):
    __tablename__ = 'chapters'

    id = Column(SmallInteger, primary_key=True, nullable=False)
    quiz_type = Column(SmallInteger, primary_key=True, nullable=False)
    priority = Column(Integer, nullable=False)
    text = Column(String(100), nullable=False)
    min_id = Column(Integer, nullable=False, default=0)
    max_id = Column(Integer, nullable=False, default=0)


class ExamAnswer(db.Model):
    __tablename__ = 'exam_answers'
    __table_args__ = (
        Index('ix_exam_answers', 'exam_id', 'question_id', 'quiz_type', unique=True),
    )

    add_id = Column(Integer, primary_key=True)
    exam_id = Column(Integer, nullable=False)
    question_id = Column(Integer, nullable=False)
    quiz_type = Column(SmallInteger, nullable=False)
    is_correct = Column(Integer, nullable=False, default=0)


class Exam(db.Model):
    __tablename__ = 'exams'

    id = Column(Integer, primary_key=True, nullable=False)
    quiz_type = Column(SmallInteger, primary_key=True, nullable=False)
    user_id = Column(Integer, nullable=False, index=True)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, index=True)
    err_count = Column(SmallInteger, nullable=False, default=0)


class GuestAcces(db.Model):
    __tablename__ = 'guest_access'

    id = Column(Integer, primary_key=True, nullable=False)
    quiz_type = Column(SmallInteger, primary_key=True, nullable=False)
    num_requests = Column(SmallInteger, nullable=False, default=0)
    period_end = Column(DateTime, nullable=False)


class GuestAccessSnapshot(db.Model):
    __tablename__ = 'guest_access_snapshot'

    guest_id = Column(Integer, primary_key=True, nullable=False)
    quiz_type = Column(SmallInteger, primary_key=True, nullable=False)
    now_date = Column(Date, primary_key=True, nullable=False)
    num_requests = Column(SmallInteger, nullable=False, default=0)


class LastSubquiz(db.Model):
    __tablename__ = 'last_subquiz'

    quiz_type = Column(SmallInteger, primary_key=True, nullable=False)
    user_id = Column(Integer, primary_key=True, nullable=False)
    user_type = Column(SmallInteger, primary_key=True, nullable=False)
    subquiz = Column(SmallInteger, nullable=False)


class Question(db.Model):
    __tablename__ = 'questions'

    id = Column(Integer, primary_key=True, nullable=False)
    quiz_type = Column(SmallInteger, primary_key=True, nullable=False)
    text = Column(String(500), nullable=False)
    text_fr = Column(String(500))
    text_de = Column(String(500))
    answer = Column(Integer, nullable=False)
    image = Column(String(10))
    image_part = Column(String(10))
    chapter_id = Column(SmallInteger, nullable=False, index=True)
    topic_id = Column(Integer, nullable=False, index=True)
    explanation = Column(String(500))


class QuizAnswer(db.Model):
    __tablename__ = 'quiz_answers'

    user_id = Column(Integer, primary_key=True, nullable=False)
    quiz_type = Column(SmallInteger, primary_key=True, nullable=False)
    question_id = Column(Integer, primary_key=True, nullable=False)
    is_correct = Column(Integer, nullable=False, default=0)


class SchoolStatCache(db.Model):
    __tablename__ = 'school_stat_cache'

    school_id = Column(Integer, primary_key=True, nullable=False)
    quiz_type = Column(SmallInteger, primary_key=True, nullable=False)
    last_activity = Column(DateTime, nullable=False, default='0000-00-00 00:00:00')
    last_update = Column(DateTime, nullable=False, default='0000-00-00 00:00:00')
    stat_cache = Column(Text, nullable=False)


class SchoolTopicErr(db.Model):
    __tablename__ = 'school_topic_err'

    school_id = Column(Integer, primary_key=True, nullable=False)
    quiz_type = Column(SmallInteger, primary_key=True, nullable=False)
    topic_id = Column(Integer, primary_key=True, nullable=False)
    err_count = Column(SmallInteger, nullable=False, default=0)
    count = Column(SmallInteger, nullable=False, default=0)
    err_week = Column(Float, nullable=False, default=-1)
    err_week3 = Column(Float, nullable=False, default=-1)


class SchoolTopicErrSnapshot(db.Model):
    __tablename__ = 'school_topic_err_snapshot'

    school_id = Column(Integer, primary_key=True, nullable=False)
    quiz_type = Column(SmallInteger, primary_key=True, nullable=False)
    topic_id = Column(Integer, primary_key=True, nullable=False)
    now_date = Column(Date, primary_key=True, nullable=False)
    err_percent = Column(Float, nullable=False, default=-1)


class StatJson(db.Model):
    __tablename__ = 'stat_json'

    name = Column(String(80), primary_key=True)
    value = Column(Text, nullable=False)


class TopicErrCurrent(db.Model):
    __tablename__ = 'topic_err_current'

    user_id = Column(Integer, primary_key=True, nullable=False)
    quiz_type = Column(SmallInteger, primary_key=True, nullable=False)
    topic_id = Column(Integer, primary_key=True, nullable=False)
    err_count = Column(SmallInteger, nullable=False, default=0)
    count = Column(SmallInteger, nullable=False, default=0)


class TopicErrSnapshot(db.Model):
    __tablename__ = 'topic_err_snapshot'

    user_id = Column(Integer, primary_key=True, nullable=False)
    quiz_type = Column(SmallInteger, primary_key=True, nullable=False)
    topic_id = Column(Integer, primary_key=True, nullable=False)
    now_date = Column(Date, primary_key=True, nullable=False)
    err_percent = Column(Float, nullable=False, default=-1)


class Topic(db.Model):
    __tablename__ = 'topics'

    id = Column(Integer, primary_key=True, nullable=False)
    quiz_type = Column(SmallInteger, primary_key=True, nullable=False)
    text = Column(String(200), nullable=False)
    text_fr = Column(String(200))
    text_de = Column(String(200))
    chapter_id = Column(SmallInteger, index=True)
    min_id = Column(Integer, nullable=False, default=0)
    max_id = Column(Integer, nullable=False, default=0)


class TruckLastSublicense(db.Model):
    __tablename__ = 'truck_last_sublicense'

    user_id = Column(Integer, primary_key=True, nullable=False)
    user_type = Column(SmallInteger, primary_key=True, nullable=False)
    sublicense = Column(SmallInteger, nullable=False)


class UserProgressSnapshot(db.Model):
    __tablename__ = 'user_progress_snapshot'

    user_id = Column(Integer, primary_key=True, nullable=False)
    quiz_type = Column(SmallInteger, primary_key=True, nullable=False)
    now_date = Column(Date, primary_key=True, nullable=False)
    progress_coef = Column(Float, nullable=False, default=-1)


class User(db.Model):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, nullable=False)
    type = Column(ENUM(u'student', u'guest'), nullable=False)
    quiz_type = Column(SmallInteger, primary_key=True, nullable=False)
    school_id = Column(Integer, primary_key=True, nullable=False)
    last_visit = Column(DateTime, nullable=False, index=True, default='0000-00-00 00:00:00')
    progress_coef = Column(Float, nullable=False, default=-1)
