import sys
from dataclasses import dataclass
from os import path
from typing import List
import util
import yaml
import sqliteDB
from environs import Env
import os
import macaddress

@dataclass
class ConfSchedule:
    day: str
    time: str
    hour: int
    minute: int


@dataclass
class Config:
    url: str  ## example: http://syncthing:8384
    apiKey: str
    foldersToScan: List[str]
    allFolders: bool
    weeklySchedule: ConfSchedule
    dailySchedule: ConfSchedule
    lastDayOfMonthSchedule: ConfSchedule
    tz: str
    WOLImage: str
    WOLMacAddr: str


# can be found here: https://hub.docker.com/r/r0gger/docker-wake-on-lan/tags
# hidden env var to set the image of the wake on lan docker image
WOL_R0GGER_IMAGE = os.getenv("WOL_R0GGER_IMAGE", "r0gger/docker-wake-on-lan:latest")


conf = Config(None, None, None, None, None, None, None, None, WOL_R0GGER_IMAGE, None)


def checkMandatoryFields():
    if conf.url is None:
        errMsg = "ERROR: Url of the Syncthing GUI must be inputted!"
        print(f"{errMsg} Now exiting!")
        sqliteDB.update_db(500, errMsg, util.getCurrentDateTime())
        sys.exit()
    if conf.apiKey is None:
        errMsg = "ERROR: API KEY of the Syncthing service must be inputted!"
        print(f"{errMsg} Now exiting!")
        sqliteDB.update_db(500, errMsg, util.getCurrentDateTime())
        sys.exit()
    if conf.weeklySchedule is None and conf.dailySchedule is None and conf.lastDayOfMonthSchedule is None:
        errMsg = "ERROR: At least one backup schedule must be setup in order for the script to work!"
        print(f"{errMsg} Now exiting!")
        sqliteDB.update_db(500, errMsg, util.getCurrentDateTime())
        sys.exit()
    if conf.weeklySchedule is not None and (conf.weeklySchedule.time is None or conf.weeklySchedule.day is None):
        errMsg = "ERROR: Weekly Schedule must have TIME and DAY setup!"
        print(f"{errMsg} Now exiting!")
        sqliteDB.update_db(500, errMsg, util.getCurrentDateTime())
        sys.exit()
    if conf.lastDayOfMonthSchedule is not None and (
            conf.lastDayOfMonthSchedule.time is None or conf.lastDayOfMonthSchedule.day is None):
        errMsg = "ERROR: Last Day Of Month Schedule must have TIME and DAY setup!"
        print(f"{errMsg} Now exiting!")
        sqliteDB.update_db(500, errMsg, util.getCurrentDateTime())
        sys.exit()
    if conf.dailySchedule is not None and conf.dailySchedule.time is None:
        errMsg = "ERROR: Daily Schedule must have TIME field setup!"
        print(f"{errMsg} Now exiting!")
        sqliteDB.update_db(500, errMsg, util.getCurrentDateTime())
        sys.exit()


def printSetConfig():
    resultStr = "The following config params were set:\n"
    resultStr += f"- url = {conf.url}\n"
    resultStr += f"- api_key = {conf.apiKey}\n"
    if conf.allFolders is False:
        resultStr += f"- folders_to_scan = {conf.foldersToScan}\n"
    else:
        resultStr += f"- All folders will be rescanned\n"
    resultStr += f"- Timezone = {conf.tz}\n"

    resultStr += f"Backup Schedule:\n"
    if conf.weeklySchedule is not None:
        resultStr += f"- weekly.day = {conf.weeklySchedule.day}\n"
        resultStr += f"- weekly.time = {conf.weeklySchedule.time}\n"
    if conf.dailySchedule is not None:
        resultStr += f"- daily.time = {conf.dailySchedule.time}\n"
    if conf.lastDayOfMonthSchedule is not None:
        resultStr += f"- last_day_of_month.day = {conf.lastDayOfMonthSchedule.day}\n"
        resultStr += f"- last_day_of_month.time = {conf.lastDayOfMonthSchedule.time}\n"
    if conf.WOLMacAddr is not None:
        resultStr += f"Wake On Lan Settings:\n"
        resultStr += f"- wake_on_lan_settings.mac_address = {conf.WOLMacAddr}\n"

    print(resultStr)


def initConfig():
    try:
        if path.exists('/yaml/config.yml'):
            with open('/yaml/config.yml') as f:
                docs = yaml.load_all(f, Loader=yaml.FullLoader)

                for doc in docs:
                    for k, v in doc.items():
                        if k == "general_settings" and v is not None:
                            for generalKey, generalVal in v.items():
                                if generalKey == "url" and generalVal != "<INSERT YOUR SYNCTHING GUI URL>":
                                    conf.url = generalVal
                                if generalKey == "api_key" and generalVal != "<INSERT YOUR SYNCTHING API KEY>":
                                    conf.apiKey = generalVal
                                if generalKey == "folders_to_scan":
                                    conf.foldersToScan = generalVal

                        # Backup Schedule
                        if k == "backup_schedule" and v is not None:
                            for backupKey, backupVal in v.items():
                                if backupKey == "weekly" and backupVal is not None:
                                    weeklySchedule = ConfSchedule(None, None, None, None)
                                    for weeklyKey, weeklyVal in backupVal.items():
                                        if weeklyKey == "day":
                                            if weeklyVal in ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]:
                                                weeklySchedule.day = weeklyVal
                                            else:
                                                errMsg = "ERROR: Weekly schedule's day is not set properly - Please use MON, TUE, WED, THU, FRI, SAT or SUN to specify the day."
                                                print(f"{errMsg} Now exiting!")
                                                sqliteDB.update_db(500, errMsg, util.getCurrentDateTime())
                                                sys.exit()
                                        if weeklyKey == "time":
                                            if util.isTimeFormat(weeklyVal):
                                                weeklySchedule.time = weeklyVal
                                                hour, minute = util.extractHourAndMinute(weeklyVal)
                                                weeklySchedule.hour = hour
                                                weeklySchedule.minute = minute
                                            else:
                                                errMsg = "ERROR: Weekly time format is not valid! Please use HH:mm format!"
                                                print(f"{errMsg} Now exiting!")
                                                sqliteDB.update_db(500, errMsg, util.getCurrentDateTime())
                                                sys.exit()

                                    conf.weeklySchedule = weeklySchedule

                                if backupKey == "daily" and backupVal is not None:
                                    dailySchedule = ConfSchedule(None, None, None, None)
                                    for dailyKey, dailyVal in backupVal.items():
                                        if dailyKey == "time":
                                            if util.isTimeFormat(dailyVal):
                                                dailySchedule.time = dailyVal
                                                hour, minute = util.extractHourAndMinute(dailyVal)
                                                dailySchedule.hour = hour
                                                dailySchedule.minute = minute
                                            else:
                                                errMsg = "ERROR: Daily time format is not valid! Please use HH:mm format!"
                                                print(f"{errMsg} Now exiting!")
                                                sqliteDB.update_db(500, errMsg, util.getCurrentDateTime())
                                                sys.exit()

                                    conf.dailySchedule = dailySchedule

                                if backupKey == "last_day_of_month" and backupVal is not None:
                                    lastDaySchedule = ConfSchedule(None, None, None, None)
                                    for lastDayKey, lastDayVal in backupVal.items():
                                        if lastDayKey == "day":
                                            if lastDayVal.upper() in ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]:
                                                lastDaySchedule.day = lastDayVal
                                            else:
                                                errMsg = "ERROR: Last Day Of Month schedule's day is not set properly - Please use MON, TUE, WED, THU, FRI, SAT or SUN to specify the day."
                                                print(f"{errMsg} Now exiting!")
                                                sqliteDB.update_db(500, errMsg, util.getCurrentDateTime())
                                                sys.exit()
                                        if lastDayKey == "time":
                                            if util.isTimeFormat(lastDayVal):
                                                lastDaySchedule.time = lastDayVal
                                                hour, minute = util.extractHourAndMinute(lastDayVal)
                                                lastDaySchedule.hour = hour
                                                lastDaySchedule.minute = minute
                                            else:
                                                errMsg = "ERROR: Last Day Of Month time format is not valid! Please use HH:mm format!"
                                                print(f"{errMsg} Now exiting!")
                                                sqliteDB.update_db(500, errMsg, util.getCurrentDateTime())
                                                sys.exit()

                                    conf.lastDayOfMonthSchedule = lastDaySchedule

                        if k == "wake_on_lan_settings" and v is not None:
                            for wolKey, wolVal in v.items():
                                if wolKey == "mac_address" and wolVal != "<INSERT YOUR BACKUP PC MAC ADDRESS>":
                                    macAddr = None
                                    try:
                                        macAddr = macaddress.EUI48(wolVal)
                                        macAddr = str(macAddr).replace('-', ':')
                                    except ValueError as error:
                                        print(f"MAC address: {macAddr} is not a valid MAC address! Now exiting!")
                                        sys.exit()
                                    conf.WOLMacAddr = macAddr

            env = Env()
            try:
                conf.tz = env('TZ')
            except Exception as e:
                errMsg = "ERROR: Timezone is not set in the docker run command/compose. You need to have it set in order for the sync to be executed on time."
                print(f"{errMsg} Now exiting!")
                sqliteDB.update_db(500, errMsg, util.getCurrentDateTime())
                sys.exit()

            if not conf.foldersToScan:
                conf.allFolders = True
            else:
                conf.allFolders = False

            checkMandatoryFields()
            printSetConfig()
            return conf

        else:
            errMsg = "ERROR: config.yml file not found (please bind the volume that contains the config.yml file)"
            print(f"{errMsg} - now exiting!")
            sqliteDB.update_db(500, errMsg, util.getCurrentDateTime())
            sys.exit()

    except Exception as e:
        errMsg = "ERROR: config.yml file is not a valid yml file"
        print(f"{errMsg} - now exiting!", e)
        sqliteDB.update_db(500, errMsg, util.getCurrentDateTime())
        sys.exit()
