import json

import flask
from flask import abort, request

from sizebot.lib import userdb
from sizebot.lib.errors import InvalidSizeValue, ParseError, UserNotFoundException

from sizebot.lib import units
from sizebot.lib.digidecimal import Decimal
from sizebot.lib.diff import Diff, Rate, LimitedRate
from sizebot.lib.units import SV, WV, TV

units.init()

app = flask.Flask(__name__)


@app.errorhandler(404)
def page_not_found(e: Exception | int) -> tuple[str, int]:
    return "<h1>404</h1><p>The resource could not be found.</p>", 404


@app.route("/user/<int:guildid>/<int:userid>", methods=["GET"])
def user(guildid: int, userid: int) -> str:
    try:
        u = userdb.load(guildid, userid)
    except UserNotFoundException:
        abort(404)

    return json.dumps({"nickname": u.nickname})


@app.route("/unit/SV/parse", methods=["GET"])
def sv_parse() -> str:
    s = request.args.get("s")
    try:
        val = SV.parse(s)
    except InvalidSizeValue:
        abort(404)
    return json.dumps({"SV": str(val)})


@app.route("/unit/SV/format", methods=["GET"])
def sv_format() -> str:
    value = Decimal(request.args.get("value"))
    system = request.args.get("system")
    try:
        val = SV(value)
    except InvalidSizeValue:
        abort(404)
    return json.dumps({"formatted": format(val, system)})


@app.route("/unit/WV/parse", methods=["GET"])
def wv_parse() -> str:
    s = request.args.get("s")
    try:
        val = WV.parse(s)
    except InvalidSizeValue:
        abort(404)
    return json.dumps({"WV": str(val)})


@app.route("/unit/WV/format", methods=["GET"])
def wv_format() -> str:
    value = Decimal(request.args.get("value"))
    system = request.args.get("system")
    try:
        val = WV(value)
    except InvalidSizeValue:
        abort(404)
    return json.dumps({"formatted": format(val, system)})


@app.route("/unit/TV/parse", methods=["GET"])
def tv_parse() -> str:
    s = request.args.get("s")
    try:
        val = TV.parse(s)
    except InvalidSizeValue:
        abort(404)
    return json.dumps({"TV": str(val)})


@app.route("/unit/TV/format", methods=["GET"])
def tv_format() -> str:
    value = Decimal(request.args.get("value"))
    system = request.args.get("system", "m")
    try:
        val = TV(value)
    except InvalidSizeValue:
        abort(404)
    return json.dumps({"formatted": format(val, system)})


@app.route("/unit/Diff/parse", methods=["GET"])
def diff_parse() -> str:
    s = request.args.get("s")
    try:
        val = Diff.parse(s)
    except (InvalidSizeValue, ParseError):
        abort(404)
    return json.dumps({"Diff": val.toJSON()})


@app.route("/unit/Rate/parse", methods=["GET"])
def rate_parse() -> str:
    s = request.args.get("s")
    try:
        val = Rate.parse(s)
    except (InvalidSizeValue, ParseError):
        abort(404)
    return json.dumps({"Rate": val.toJSON()})


@app.route("/unit/LimitedRate/parse", methods=["GET"])
def limitedrate_parse() -> str:
    s = request.args.get("s")
    try:
        val = LimitedRate.parse(s)
    except (InvalidSizeValue, ParseError):
        abort(404)
    return json.dumps({"LimitedRate": val.toJSON()})


def main():
    app.run()


if __name__ == "__main__":
    main()
