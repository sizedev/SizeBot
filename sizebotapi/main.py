import json

import flask
from flask import abort

from sizebot.lib import userdb
from sizebot.lib.errors import UserNotFoundException

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
        return

    return json.dumps({"nickname": u.nickname})


def main():
    app.run()


if __name__ == "__main__":
    main()
