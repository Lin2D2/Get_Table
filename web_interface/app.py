import sys
import time
import flask
import json
from flask_api import FlaskAPI

try:
    import tinydb
except ImportError:
    sys.exit("Failed to import tinydb")


def routes(app, data, parent):
    @app.route("/api/days", methods=['GET', 'POST'])
    def home():
        days = []
        for day in parent.database.all():
            days.append(day["date"])
        json_resp = json.dumps({"time": time.time(), "days": days})
        resp = flask.Response(json_resp, content_type='application/json; charset=utf-8')
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp


def run(data, parent, url, port):
    app = FlaskAPI(__name__)
    routes(app, data, parent)
    app.run(host=url, port=port, threaded=False, use_reloader=False, debug=True)
#     app.run(debug=True, host=url, port=port, threaded=True, use_reloader=True)


# run(data=None, parent=None, url="0.0.0.0", port="5000")