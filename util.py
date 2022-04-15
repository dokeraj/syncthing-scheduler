import time
from datetime import datetime


def extractHourAndMinute(inputTime):
    datetime = time.strptime(str(inputTime), '%H:%M')
    return datetime.tm_hour.real, datetime.tm_min.real


def isTimeFormat(inputTime):
    try:
        time.strptime(str(inputTime), '%H:%M')
        return True
    except Exception as e:
        return False


def safeCastBool(val, default=False):
    try:
        return str(val).lower() in ['true', '1', 'y', 'yes']
    except Exception as e:
        return default


def getCurrentDateTime():
    timestamp = int(round(time.time()))
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')


def fixString(inStr: str):
    filtered_characters = list(s for s in inStr if s.isprintable())
    fixed = ''.join(filtered_characters)
    return fixed.replace("'", "\"")
