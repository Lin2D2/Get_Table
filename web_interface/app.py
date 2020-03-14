import sys

try:
    from flask import Flask, render_template, redirect, request
except ImportError:
    sys.exit("failed to import flask")

# TODO dont use global var
# TODO need some kind of cokkie instead of this shit
loged_in = False


def routes(app, data):
    @app.route("/")
    def home():
        if not loged_in:
            return redirect("/login")
        return render_template("home.html")

    @app.route("/login")
    def login():
        return render_template("login.html")

    @app.route("/login_check", methods=['POST'])
    def login_check():
        _username = request.form["_username"]
        _password = request.form["_password"]
        # TODO get a proper validator here
        if len(_password) >= 6 and len(_username) >= 4:
            global loged_in
            loged_in = True
            return redirect("/")
        else:
            return str(["data", _username, _password])

    @app.route("/table_view_of_dat/<year>/<month>/<day>")
    def table_view_of_dat(year, month, day):
        return str([year, month, day])


def run(data, url, port):
    app = Flask(__name__)
    routes(app, data)
    app.run(host=url, port=port, threaded=True, use_reloader=False)
#     app.run(debug=True, host=url, port=port, threaded=True, use_reloader=True)


# run(data=None, url="0.0.0.0", port="5000")
