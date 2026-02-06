import datetime
from PyQt5 import QtCore

"""Преобразование даты/времени из формата python в формат Qt и обратно"""

def date_to_QDate(d:datetime.date)->QtCore.QDate:
    return QtCore.QDate(d.year,d.month,d.day)

def QDate_to_date(q:QtCore.QDate)->datetime.date:
    return datetime.date(q.year(),q.month(),q.day())

def time_to_QTime(t:datetime.time)->QtCore.QTime:
    return QtCore.QTime(t.hour, t.minute, t.second, round(t.microsecond / 1000))

def QTime_to_time(qtime:QtCore.QTime):
    return datetime.time(qtime.hour(), qtime.minute(), qtime.second(), qtime.msec() * 1000)

def datetime_to_QDateTime(dt:datetime.datetime)->QtCore.QDateTime:
    return QtCore.QDateTime(dt.date(),dt.time())

def QDateTime_to_datetime(qdt:QtCore.QDateTime)->datetime.datetime:
    return datetime.datetime(qdt.date().year(),qdt.date().month(), qdt.date().day(),
                             qdt.time().hour(), qdt.time().minute(), qdt.time().second(),
                             qdt.time().msec()*1000)