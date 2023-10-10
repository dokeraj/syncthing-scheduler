import calendar
import sys
from datetime import datetime

import docker
import requests
from apscheduler.schedulers.background import BackgroundScheduler

import configInit
import sqliteDB
import statusController
import util


def runPostRequest(config, dockerClient):
    header = {"X-API-Key": config.apiKey}
    urlToScan = f"{config.url}/rest/db/scan"
    tsDatetime = util.getCurrentDateTime()

    try:
        if config.allFolders:
            print(
                f"---------------\nNow running the post request on \'{urlToScan}\' for all folders in the Syncthing service")
            response = requests.post(urlToScan, headers=header)

            if response.status_code == 200:
                respMsg = "Successfully scanned all folders!"

                wolMsg = ""
                if config.WOLImage is not None and config.WOLMacAddr is not None:
                    wolMsg = f"\nNow waking up PC on mac address: {config.WOLMacAddr}, so it can receive the backup files.."
                    WOLEnvVars = {"MAC": config.WOLMacAddr}

                    dockerClient.containers.run(config.WOLImage, network_mode="host",
                                                name="WOL-syncthing-scheduler", remove=True,
                                                environment=WOLEnvVars)

                byeMsg = "\nSUCCESS: Backup will commence now! See you at the next scheduled time. ;)"
                print(respMsg + wolMsg + byeMsg)
                sqliteDB.update_db(response.status_code, respMsg, tsDatetime)
            else:
                respMsg = f"ERROR: While scanning all folders. Code = {response.status_code} with error message = {response.text}! Please rescan it manually!"
                respMsg = util.fixString(respMsg)
                print(respMsg)
                sqliteDB.update_db(response.status_code, respMsg, tsDatetime)

        else:
            print(
                f"---------------\nNow running the post request for scanning the following folders in syncthing service: {util.fixString(str(config.foldersToScan))}")
            responses = []
            for folder in config.foldersToScan:
                folderToScan = f"{urlToScan}/?folder={folder}"
                responses.append(requests.post(folderToScan, headers=header))

            hasFailed = any(resp.status_code != 200 for resp in responses)
            failedFolders = []
            if hasFailed:
                onlyFailed = (res for res in responses if res.status_code != 200)
                for res in onlyFailed:
                    failedFolders.append(res.request.url.split("=")[-1])
                    print("Error: The following requests have failed:")
                    print(
                        f"- Called URL: {res.request.url}. RESPONSE CODE: {res.status_code} and error msg: {res.text}")

                respMsg = f"ERROR: while scanning multiple folders {failedFolders}: Please rescan them manually!"
                respMsg = util.fixString(respMsg)
                print(respMsg)
                sqliteDB.update_db(500, respMsg, tsDatetime)
            else:
                respMsg = f"Successfully scanned all selected folders: {config.foldersToScan}."
                respMsg = util.fixString(respMsg)

                wolMsg = ""
                if config.WOLImage is not None and config.WOLMacAddr is not None:
                    wolMsg = f"\nNow waking up PC on mac address: {config.WOLMacAddr}, so it can receive the backup files.."
                    WOLEnvVars = {"MAC": config.WOLMacAddr}

                    dockerClient.containers.run(config.WOLImage, network_mode="host",
                                                name="WOL-syncthing-scheduler", remove=True,
                                                environment=WOLEnvVars)

                byeMsg = "\nSUCCESS: Backup will commence now! See you at the next scheduled time. ;)"
                print(respMsg + wolMsg + byeMsg)
                sqliteDB.update_db(200, respMsg, tsDatetime)

    except requests.exceptions.Timeout:
        strErr = f"ERROR: Timeout has occurred while calling scanning folder(s)! Please run the scan manually!"
        print(strErr)
        sqliteDB.update_db(408, strErr, tsDatetime)
        return None
    except Exception as e:
        strErr = f"ERROR: {str(e)} has occurred while calling folders to scan! Please run the scan manually!"
        respMsg = util.fixString(strErr)
        print(respMsg)
        sqliteDB.update_db(500, respMsg, tsDatetime)
        return None


def mainLastDayOfMonth(dockerClient):
    # check to see if it is in fact the last day of the month - and if so, then allow the schedule to take place
    today = datetime.today()
    curDay = today.day
    daysInCurMonth = calendar.monthrange(today.year, today.month)[1]

    if (daysInCurMonth - 7) < curDay:
        startMainProcess(dockerClient)


def startMainProcess(dockerClient):
    print("---------------\nCOMMENCING THE SCHEDULED TASK TO PING SYNCTHING FOR BACKUP..\n")
    config = configInit.initConfig()
    runPostRequest(config, dockerClient)


def main():
    print("STARTING SCRIPT!")

    # initialize the db
    print("Initializing sqlite database..")
    sqliteDB.init_db(r"/sqldb/nova.db")

    print("Connecting with docker server..")
    try:
        dockerClient = docker.DockerClient(base_url='unix://var/run/docker.sock')
    except Exception as e:
        print("ERROR: cannot find docker server! now exiting!")
        sys.exit(0)

    config = configInit.initConfig()

    scheduler = BackgroundScheduler({'apscheduler.timezone': config.tz})

    if config.dailySchedule is not None:
        scheduler.add_job(lambda: startMainProcess(dockerClient), trigger='cron', minute=config.dailySchedule.minute,
                          hour=config.dailySchedule.hour, day='*', month='*', day_of_week='*')
    if config.weeklySchedule is not None:
        scheduler.add_job(lambda: startMainProcess(dockerClient), trigger='cron', minute=config.weeklySchedule.minute,
                          hour=config.weeklySchedule.hour, day='*', month='*',
                          day_of_week=config.weeklySchedule.day.lower())
    if config.lastDayOfMonthSchedule is not None:
        scheduler.add_job(lambda: mainLastDayOfMonth(dockerClient), trigger='cron',
                          minute=config.lastDayOfMonthSchedule.minute,
                          hour=config.lastDayOfMonthSchedule.hour, day='*', month='*',
                          day_of_week=config.lastDayOfMonthSchedule.day.lower())

    scheduler.start()

    statusController.runApi()


main()
