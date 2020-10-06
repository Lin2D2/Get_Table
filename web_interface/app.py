import sys
import time
import flask
import json
from datetime import date
from flask_api import FlaskAPI
from flask_cors import CORS, cross_origin

try:
    import tinydb
except ImportError:
    sys.exit("Failed to import tinydb")

week_days_german = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]


def routes(app, cors, data, parent):
    @app.route("/api/days", methods=['GET'])
    def table_view():
        days = []
        for day in parent.database.all():
            days.append(day["date"])
        json_resp = json.dumps({"time": time.time(), "days": days})
        resp = flask.Response(json_resp, content_type='application/json; charset=utf-8')
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

    @app.route("/api/day/<date>", methods=['GET'])
    def table_view_day(date):
        day = parent.database.search(tinydb.where("date") == date)
        json_resp = json.dumps({"time": time.time(),
                                "day": {"header": [day[0]["inital_content"]["header"]["row"]],
                                        "content": [row["row"]
                                                    for row in day[0]["inital_content"]["content"]]}
                                })
        resp = flask.Response(json_resp, content_type='application/json; charset=utf-8')
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

    @app.route("/api/today", methods=['GET'])
    def table_today():
        today = date.today()
        week_day = week_days_german[today.weekday()]
        # title_today: "1.9.2020 Dienstag, Woche A"
        if week_day == parent.table_object.title_today.split(" ")[1].strip(","):
            table_today_data = {"title": parent.table_object.title_today,
                                "massage": parent.table_object.massage_today.strip("Nachrichten zum Tag\n"),
                                "header": [parent.table_object.table_header["row"]],
                                "content": [row["row"] for row in parent.table_object.content_today],
                                }
        elif week_day == parent.table_object.title_tomorow.split(" ")[1].strip(","):
            table_today_data = {"title": parent.table_object.title_tomorow,
                                "massage": parent.table_object.massage_tomorow.strip("Nachrichten zum Tag\n"),
                                "header": [parent.table_object.table_header],
                                "content": [row["row"] for row in parent.table_object.content_tomorow],
                                }
        else:
            print("weekend?")
            table_today_data = {}  # temp
            # table_today_data = {"title": parent.table_object}
        json_resp = json.dumps({"time": time.time(),
                                "day": table_today_data
                                })
        resp = flask.Response(json_resp, content_type='application/json; charset=utf-8')
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

    @app.route("/api/login", methods=["POST"])
    def login():
        data = flask.request.data
        # {username: <name>, password: <passwort>}
        # TODO for adding users: parent.database_users.insert(data)
        search = parent.database_users.search(tinydb.where("username") == data["username"])
        if 2 > len(search) > 0:
            search = search[0]
            print(search)
            if search["password"] == data["password"]:
                json_resp = json.dumps({
                    "state": "success",
                })
                # TODO add some cockie or key that this cant be faked
            else:
                json_resp = json.dumps({
                    "state": "wrong password",
                })
        else:
            if len(search) < 1:
                json_resp = json.dumps({
                    "state": "need to Sign in",
                })
            else:
                print("something not expected!!!")
                json_resp = json.dumps({
                    "state": "failed",
                })
        resp = flask.Response(json_resp, content_type='application/json; charset=utf-8')
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp


def run(data, parent, url, port):
    app = FlaskAPI(__name__)
    cors = CORS(app)
    app.config['CORS_HEADERS'] = 'Content-Type'
    routes(app, cors, data, parent)
    app.run(host=url, port=port, threaded=True, use_reloader=False, debug=True)
#     app.run(debug=True, host=url, port=port, threaded=True, use_reloader=True)


# run(data=None, parent=None, url="0.0.0.0", port="5000")
