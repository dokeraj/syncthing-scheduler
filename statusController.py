import dataclasses
import json
from flask import Flask, abort, Response
import sqliteDB

app = Flask("FlaskApp")


@app.route("/status")
def get_status():
    resp = sqliteDB.get_from_db()

    if resp is not None:
        respDict = dataclasses.asdict(resp)
    else:
        respDict = {"Error": "Cannot find response record. Maybe too soon?!"}

    jsonResponse = json.dumps({"Response": respDict})

    if resp is None:
        abort(Response(jsonResponse, status=400, content_type='application/json'))
    elif resp.code != 200:
        abort(Response(jsonResponse, status=resp.code, content_type='application/json'))

    return Response(jsonResponse, mimetype='application/json')


def runApi():
    from waitress import serve
    serve(app, host='0.0.0.0', port=1050)
