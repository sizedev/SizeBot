import asyncio
import json

import flask
from flask import abort, request

from sizebot.lib import userdb
from sizebot.lib.errors import InvalidSizeValue, UserNotFoundException

from sizebot.lib import units
from sizebot.lib.units import SV, WV, TV

asyncio.run(units.init())

app = flask.Flask(__name__)


@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found.</p>", 404


@app.route("/user/<int:guildid>/<int:userid>", methods=["GET"])
def user(guildid, userid):
    try:
        u = userdb.load(guildid, userid)
    except UserNotFoundException:
        abort(404)

    return json.dumps({"nickname": u.nickname})


@app.route("/unit/SV/parse", methods=["GET"])
def SV_parse():
    s = request.args.get("s")
    try:
        val = SV.parse(s)
    except InvalidSizeValue:
        abort(404)
    return json.dumps({"SV": str(val)})


@app.route("/unit/WV/parse", methods=["GET"])
def WV_parse():
    s = request.args.get("s")
    try:
        val = WV.parse(s)
    except InvalidSizeValue:
        abort(404)
    return json.dumps({"WV": str(val)})


@app.route("/unit/TV/parse", methods=["GET"])
def TV_parse():
    s = request.args.get("s")
    try:
        val = TV.parse(s)
    except InvalidSizeValue:
        abort(404)
    return json.dumps({"TV": str(val)})


def main():
    app.run()


if __name__ == "__main__":
    main()
