import sys
import time
import flask
import json
from datetime import date
from flask_api import FlaskAPI
from flask_cors import CORS, cross_origin
import package.util.table_merge_row as table_merge_row

try:
    import tinydb
except ImportError:
    sys.exit("Failed to import tinydb")

week_days_german = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]


def routes(app, cors, parent):
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

    @app.route("/api/<today_tomorrow>", methods=['GET'])
    def table_today_tomorrow(today_tomorrow):
        print(today_tomorrow)
        today = date.today()
        # title_today: "1.9.2020 Dienstag, Woche A"
        if (week_days_german[today.weekday()] if today_tomorrow == "today" else week_days_german[
            today.weekday() + 1]) == parent.table_object.title_today.split(" ")[1].strip(","):
            header, content = table_merge_row.calc({
                "inital_content": {"header": parent.table_object.table_header,
                                   "content": parent.table_object.content_today},
            })
            table_today_data = {"title": parent.table_object.title_today,
                                "massage": parent.table_object.massage_today.strip("Nachrichten zum Tag\n"),
                                "header": [header],
                                "content": content,
                                }
        elif (week_days_german[today.weekday()] if today_tomorrow == "today" else week_days_german[
            today.weekday() + 1]) == parent.table_object.title_tomorow.split(" ")[1].strip(","):
            header, content = table_merge_row.calc({
                "inital_content": {"header": parent.table_object.table_header,
                                   "content": parent.table_object.content_tomorow},
            })
            table_today_data = {"title": parent.table_object.title_tomorow,
                                "massage": parent.table_object.massage_tomorow.strip("Nachrichten zum Tag\n"),
                                "header": [header],
                                "content": content,
                                }
        # TODO check for the weekend not with else
        else:
            print("weekend?")
            table_today_data = {}  # temp
            # table_today_data = {"title": parent.table_object}
        json_resp = json.dumps({"time": time.time(),
                                "day": table_today_data
                                })
        resp = flask.Response(json_resp, content_type='application/json; charset=utf-8')
        resp.headers['Access-Control-Allow-Origin'] = '*'
        print(json_resp)
        return resp

    @app.route("/api/login", methods=["POST"])
    def login():
        data = flask.request.data
        # {username: <name>, password: <passwort>}
        # parent.database_users.insert({"username": "root", "password": "12345678"})
        # TODO for adding users: parent.database_users.insert(data)
        search = parent.database_users.search(tinydb.where("username") == data["username"])
        if 2 > len(search) > 0:
            search = search[0]
            print(search)
            if search["password"] == data["password"]:
                try:
                    json_resp = json.dumps({
                        "state": "success",
                        "timetable": search["timetable"],
                    })
                except KeyError:
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

    @app.route("/api/timetable/push", methods=["POST"])
    def post_timetable():
        # TODO handle it over cookies don't send password twice
        data = flask.request.data
        User = tinydb.Query()
        search = parent.database_users.search(User.username == data["login"]["username"])
        if 2 > len(search) > 0:
            search = search[0]
            if search["password"] == data["login"]["password"]:
                parent.database_users.update(
                    {"timetable": {"monday": data["monday"], "tuesday": data["tuesday"], "wednesday": data["wednesday"],
                                   "thursday": data["thursday"], "friday": data["friday"]}},
                    User.username == data["login"]["username"])
                json_resp = json.dumps({
                    "state": "success",
                })
            else:
                json_resp = json.dumps({
                    "state": "failed login",
                })
        else:
            print("something not expected!!!")
            print(data)
            json_resp = json.dumps({
                "state": "failed",
            })
        resp = flask.Response(json_resp, content_type='application/json; charset=utf-8')
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp


def run(parent, url, port):
    app = FlaskAPI(__name__)
    cors = CORS(app)
    app.config['CORS_HEADERS'] = 'Content-Type'
    routes(app, cors, parent)
    app.run(host=url, port=port, threaded=True, use_reloader=False, debug=True)
#     app.run(debug=True, host=url, port=port, threaded=True, use_reloader=True)


# run(data=None, parent=None, url="0.0.0.0", port="5000")
