import sys

try:
    from flask import Flask, render_template, redirect, request
except ImportError:
    sys.exit("failed to import flask")

from tinydb import where

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
        db_data = get_db_data()
        search = db_data.search(where("date") == f'{day}.{month}.{year}')
        if len(search) > 0:
            search = search[0]
        else:
            print("error")
            return None
        refactored_data = calc_proper_table(search)
        print(refactored_data)
        return render_template("table_view_of_data.html",
                                   year=year,
                                   month=month,
                                   day=day,
                                   table=refactored_data)

    def get_db_data():
        file_write_thread = parent.update()
        if file_write_thread:
            file_write_thread.join()
        return parent.database

    def construct_grid_table():
        dab_data = get_db_data().all()

        def extract_date_of_day(day_date):
            date = day_date.split(" ")[0].split(".")
            return int(date[0]), int(date[1]), int(date[2])

        def calc_len_changes(changes):
            result = 0
            for e in changes:
                if e["changed"]:
                    result = result + \
                             len(e["changed"]["content"]["additions"]) - \
                             len(e["changed"]["content"]["subtractions"])
            return result

        grid_tiles = []
        for whole_day in reversed(dab_data):
            day, month, year = extract_date_of_day(whole_day["date"])
            grid_tiles.append(
                {
                    "year": year,
                    "month": month,
                    "day": day,
                    "lenght_of_table": (len(whole_day["inital_content"]["content"]) +
                                        calc_len_changes(whole_day["changes"])),
                    "latest_status": whole_day["latest_status"],
                }
            )
        return grid_tiles


def run(data, parent, url, port):
    app = Flask(__name__)
    routes(app, data, parent)
    app.run(host=url, port=port, threaded=False, use_reloader=False, debug=True)
#     app.run(debug=True, host=url, port=port, threaded=True, use_reloader=True)


# run(data=None, parent=None, url="0.0.0.0", port="5000")
