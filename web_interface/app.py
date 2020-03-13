import sys

try:
    from flask import Flask
except ImportError:
    sys.exit("failed to import flask")


def routes(app, data):
    @app.route("/")
    def home():
        return "Test"
        # return render_template("control_panel.html")


def run(data, url, port):
    app = Flask(__name__)
    routes(app, data)
    app.run(host=url, port=port, threaded=True, use_reloader=False)
#     app.run(debug=True, host=url, port=port, threaded=True, use_reloader=True)


# run(data=None, url="0.0.0.0", port="5000")
