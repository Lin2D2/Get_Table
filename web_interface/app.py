import sys
import time
import flask
import json
import logging
from datetime import date
from flask_api import FlaskAPI
from flask_cors import CORS
import package.util.table_merge_row as table_merge_row
from gevent.pywsgi import WSGIServer

try:
    import tinydb
except ImportError:
    sys.exit("Failed to import tinydb")

week_days_german = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]


def routes(app, parent):
    @app.route("/api/days", methods=['GET'])
    def table_view():
        days = []
        for day in parent.database.all():
            days.append(day["date"])
        days.reverse()
        json_resp = json.dumps({"time": time.time(), "days": days})
        resp = flask.Response(json_resp, content_type='application/json; charset=utf-8')
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

    @app.route("/api/subjects", methods=['GET'])
    def subjects():
        json_resp = json.dumps({"subjects": parent.Subjects.subject_list,
                                "subjects_short": parent.Subjects.subject_list_short})
        resp = flask.Response(json_resp, content_type='application/json; charset=utf-8')
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

    @app.route("/api/day/<date>", methods=['GET'])
    def table_view_day(date):
        day = parent.database.search(tinydb.where("date") == date)
        json_resp = json.dumps({"time": time.time(),
                                "day": {"massage": day[0]["inital_content"]["massage"].strip("Nachrichten zum Tag\n"),
                                        "header": None if day[0]["inital_content"]["header"] is None
                                        else [day[0]["inital_content"]["header"]["row"]],
                                        "content": None if day[0]["inital_content"]["content"] is None
                                        else [row["row"] for row in day[0]["inital_content"]["content"]],}
                                })
        resp = flask.Response(json_resp, content_type='application/json; charset=utf-8')
        # TODO temp for debug
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

    @app.route("/api/today-tomorrow/<today_tomorrow>", methods=['GET'])
    def table_today_tomorrow(today_tomorrow):
        logging.debug(today_tomorrow)
        today = date.today()
        if today_tomorrow == "today":
            header, content = table_merge_row.calc({
                "inital_content": {"header": parent.table_object.table_header,
                                   "content": parent.table_object.content_today},
            })
            table_today_data = {"title": parent.table_object.title_today,
                                "massage": parent.table_object.massage_today.strip("Nachrichten zum Tag\n"),
                                "header": (None if header is None else [header]),
                                "content": content,
                                }
        elif today_tomorrow == "tomorrow":
            header, content = table_merge_row.calc({
                "inital_content": {"header": parent.table_object.table_header,
                                   "content": parent.table_object.content_tomorow},
            })
            table_today_data = {"title": parent.table_object.title_tomorow,
                                "massage": parent.table_object.massage_tomorow.strip("Nachrichten zum Tag\n"),
                                "header": None if header is None else [header],
                                "content": content,
                                }
        else:
            table_today_data = {}  # temp
        json_resp = json.dumps({"time": time.time(),
                                "day": table_today_data
                                })
        resp = flask.Response(json_resp, content_type='application/json; charset=utf-8')
        resp.headers['Access-Control-Allow-Origin'] = '*'
        logging.debug(json_resp)
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
            logging.debug(search)
            if search["password"] == data["password"]:
                try:
                    json_resp = json.dumps({
                        "state": "success",
                        "timetable": search["timetable"],
                        "year": search["year"],
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
                logging.warning("something not expected!!!")
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
            logging.warning(f"something not expected!!! data:{data}")
            json_resp = json.dumps({
                "state": "failed",
            })
        resp = flask.Response(json_resp, content_type='application/json; charset=utf-8')
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

    # @app.route("/api/login", methods=['POST'])
    # def table_view_day():
    #     request = flask.request
    #     if request.is_secure():
    #         return
    #     return True


def run(parent, url, port):
    app = FlaskAPI(__name__)
    CORS(app)
    app.config['CORS_HEADERS'] = 'Content-Type'
    routes(app, parent)
    # app.run(host=url, port=port, threaded=True, use_reloader=False, debug=True)
    http_server = WSGIServer((url, int(port)), app)
    http_server.serve_forever()

# run(data=None, parent=None, url="0.0.0.0", port="5000")
