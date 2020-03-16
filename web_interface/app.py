import sys

try:
    from flask import Flask, render_template, redirect, request
except ImportError:
    sys.exit("failed to import flask")

from package.util.calc_proper_table import calc as calc_proper_table

# TODO dont use global var
# TODO need some kind of cokkie instead of this shit
loged_in = False


def routes(app, data, parent):
    @app.route("/")
    def home():
        if not loged_in:
            return redirect("/login")
        return render_template("home.html",
                               grid_tiles=construct_grid_table())

    @app.route("/exit")
    def _quit():
        # TODO find a way to check out or remove
        return ""

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

    @app.route("/table")
    def table():
        # TODO build proper page for Vertretungsplan Today and Tomoorow
        return ""

    @app.route("/table_view_of_data/<year>/<month>/<day>")
    def table_view_of_data(year, month, day):
        table_data = get_table()
        for _year in table_data:
            if str(_year["year"]) == str(year):
                for _month in _year["months"]:
                    if str(_month["month"]) == str(month):
                        for _day in _month["days"]:
                            if str(_day["day"]) == str(day):
                                # table_data = _day["day_object"]
                                table_data = calc_proper_table(_day["day_object"])
                                print(table_data)
                                return render_template("table_view_of_data.html",
                                                       year=year,
                                                       month=month,
                                                       day=day,
                                                       table=table_data)

    def get_table():
        file_write_thread = parent.update()
        if file_write_thread:
            file_write_thread.join()
        return parent.vertretungsplan_json

    def construct_grid_table():
        table_data = get_table()

        def calc_len_changes(changes):
            result = 0
            for e in changes:
                if e["changed"]:
                    result = result + \
                             len(e["changed"]["content"]["additions"]) - \
                             len(e["changed"]["content"]["subtractions"])
            return result

        grid_tiles = []
        for year in reversed(table_data):
            for month in reversed(year["months"]):
                for day in reversed(month["days"]):
                    grid_tiles.append(
                        {
                            "year": year["year"],
                            "month": month["month"],
                            "day": day["day"],
                            "lenght_of_table": (len(day["day_object"]["inital_content"]["content"]) +
                                                calc_len_changes(day["day_object"]["changes"])),
                            "latest_status": day["day_object"]["latest_status"],
                        }
                    )
        return grid_tiles


def run(data, parent,  url, port):
    app = Flask(__name__)
    routes(app, data, parent)
    app.run(host=url, port=port, threaded=False, use_reloader=False, debug=True)
#     app.run(debug=True, host=url, port=port, threaded=True, use_reloader=True)


# run(data=None, parent=None, url="0.0.0.0", port="5000")
