import sys
import docker
import configInit
import sqliteDB
import util


def checkSyncthingValidity(container):
    if "syncthing" in container.attrs["Config"]["Image"]:
        return True
    else:
        return False


def checkSyncthingAvailability(dockerClient, config):
    try:
        container = dockerClient.containers.get(config.syncthingContainerName)
        if str(container.status).lower() == "running":
            return True, container
        else:
            return False, None
    except Exception as e:
        return False, None


def mainChecks():
    try:
        client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    except Exception as e:
        errMsg = "ERROR: Cannot find docker server!"
        sqliteDB.update_db(500, errMsg, util.getCurrentDateTime())
        print(f"{errMsg} Now exiting!")
        sys.exit()

    print("Reading the config from the YAML file...")
    config = configInit.initConfig()

    print("Checking the availability and validity of Syncthing container...")
    available, container = checkSyncthingAvailability(client, config)

    if not available:
        errMsg = f"ERROR: The container with name {config.syncthingContainerName} is not valid or the container is stopped! Please fix this!"
        errMsg = util.fixString(errMsg)
        print(f"${errMsg} Now Exiting!")
        sqliteDB.update_db(500, errMsg, util.getCurrentDateTime())
        sys.exit()

    if not checkSyncthingValidity(container):
        errMsg = f"ERROR: The container with name {config.syncthingContainerName} is not created from the syncthing image! Please use a container that it is the Syncthing!"
        errMsg = util.fixString(errMsg)
        print(f"${errMsg} Now exiting!")
        sqliteDB.update_db(500, errMsg, util.getCurrentDateTime())
        sys.exit()

    print("SUCCESS: The specified container is currently running and is in fact Syncthing container!")
    return config
