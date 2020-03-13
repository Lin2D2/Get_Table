try:
    import sys
    import os
    import requests
    import time
    import datetime
    import re
    import logging
    import json
    import threading
except ImportError:
    sys.exit("failed failed please check if you install all needed packages")
try:
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("failed because bs4 is not installed, do pip install bs4 to fix this")


from web_interface import app as web_app

# create logger
logging_time = logging.getLogger("main")
logging_time.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter(
    '[%(asctime)s] %(levelname)s in %(threadName)s: %(message)s',
    "%Y-%m-%d %H:%M:%S"))

logging.root.handlers = [handler]


class App:
    def __init__(self):
        logging_time.info("Start")
        time.sleep(0.01)
        username = input("enter the username: ")
        password = input("enter the password: ")
        self.table_object = TableUtil({'_username': username, '_password': password})
        self.save_location = "vertretungsplan/vertretungsplan.json"
        try:
            with open(self.save_location, "r") as file:
                self.vertretungsplan_json = json.load(file)
        except FileNotFoundError:
            logging_time.warning("couldnt find file")
        self.now = datetime.datetime.now()
        self.update()
        threading.Thread(target=self.start_web_interface, name="web_threat").start()
        self.timing()

    @staticmethod
    def start_web_interface():
        logging_time.info("starting web-thread...")
        web_app.run(data=None, url="0.0.0.0", port="5000")

    def update(self):
        logging_time.info("performing update...")
        self.table_object.update()
        threading.Thread(target=self.write_file, args=[self.table_object], name="file_write").start()

    def timing(self, timing=None):

        if timing is None:
            timing = [{"hour": 7, "minute": 30},
                      {"hour": 8, "minute": 20},
                      {"hour": 12, "minute": 30},
                      {"hour": 16, "minute": 30},
                      {"hour": 22, "minute": 0}]

        real_timings = []
        for e in timing:
            real_timings.append(e["hour"] * 60 * 60 + e["minute"] * 60)

        def check_time():
            time.sleep(0.1)
            now = datetime.datetime.now()
            real_now = now.hour * 60 * 60 + now.minute * 60 + now.second
            del now
            real_last_update = self.table_object.last_update.hour * 60 * 60 \
                               + self.table_object.last_update.minute * 60 \
                               + self.table_object.last_update.second

            smaller = []
            for real_timing in real_timings:
                if real_timing - real_now >= 0:
                    smaller.append({"index": real_timings.index(real_timing), "difference": real_timing - real_now})
            if real_now - real_last_update >= 10 * 60:
                if datetime.datetime.today().weekday() in range(0, 4):
                    if len(smaller) == 0:
                        sleep_time = (24*60*60 - real_now) + real_timings[0]
                        if sleep_time >= 10 * 60:
                            logging_time.info("sleeping for: " + str(sleep_time / 60) + " minutes")
                            time.sleep(0.0001)
                            time.sleep(sleep_time)
                    else:
                        if real_timings[smaller[0]["index"]] == real_now:
                            self.update()
                        else:
                            logging_time.info("sleeping for: " + str(smaller[0]["difference"] / 60) + " minutes")
                            time.sleep(0.0001)
                            time.sleep(smaller[0]["difference"])
                else:
                    sleep_time = (24*60*60 - real_now)
                    logging_time.info("sleeping for: " + str(sleep_time / 60) + " minutes")
                    time.sleep(0.0001)
                    time.sleep(sleep_time)
            else:
                logging_time.info("sleeping " + str(10 * 60 - (real_now - real_last_update)) + " sec...")
                time.sleep(0.0001)
                time.sleep(10 * 60 - (real_now - real_last_update))

        while True:
            logging_time.info("checking time...")
            check_time()

    def write_file(self, object_of_table):
        start_time = time.time()

        def create_changes_structur(status, massage=None, content=None):
            if not massage and not content:
                return {
                    "status": status,
                    "changed": None
                }
            elif not massage:
                return {
                    "status": status,
                    "changed": {
                        "content": content
                    }
                }
            elif not content:
                return {
                    "status": status,
                    "changed": {
                        "massage": massage
                    }
                }
            else:
                return {
                    "status": status,
                    "changed": {
                        "massage": massage,
                        "content": content
                    }
                }

        def create_table_structur(status, title, header, massage, content):
            return {
                "latest_status": status,
                "day": title,
                "inital_content": {"header": header,
                                   "title": title,
                                   "massage": massage,
                                   "content": content},
                "changes": [
                    create_changes_structur(status)
                ]
            }

        table_item_today = create_table_structur(object_of_table.status_today,
                                                 object_of_table.title_today,
                                                 object_of_table.table_header,
                                                 object_of_table.massage_today,
                                                 object_of_table.content_today)

        table_item_tomorow = create_table_structur(object_of_table.status_tomorow,
                                                   object_of_table.title_tomorow,
                                                   object_of_table.table_header,
                                                   object_of_table.massage_tomorow,
                                                   object_of_table.content_tomorow)

        def find_changes_in_table(old_table, new_table):
            logging_time.info("looking for changes in table")
            unique_id = old_table[-1]["id"] + 1

            def extract_row(row):
                data = []
                for other_row in row:
                    data.append(other_row["row"])
                return data

            additions = []
            for e in new_table:
                if not e["row"] in extract_row(old_table):
                    additions.append({"unique_id": unique_id, "row": e["row"]})
                    unique_id += 1

            subtractions = []
            for e in old_table:
                if not e["row"] in extract_row(new_table):
                    subtractions.append(e)
            logging_time.debug(["additions: ", additions])
            logging_time.debug(["subtractions: ", subtractions])
            return {"additions": additions, "subtractions": subtractions}

        def add_changes_to_day(day, table):
            logging_time.debug(["day: ", day])
            logging_time.debug(["table: ", table])
            if not day["inital_content"] == table["inital_content"]:
                logging_time.debug(["add_changes_to_day day =", day])
                day["latest_status"] = table["latest_status"]
                massage_changed = None
                content_changed = None
                if not day["inital_content"]["massage"] == table["inital_content"]["massage"]:
                    massage_changed = table["inital_content"]["massage"]
                if not day["inital_content"]["content"] == table["inital_content"]["content"]:
                    content_changed = find_changes_in_table(day["inital_content"]["content"],
                                                            table["inital_content"]["content"])
                return create_changes_structur(table["latest_status"], massage_changed, content_changed)
            else:
                logging_time.info("nothing changed")
                return create_changes_structur(table["latest_status"])

        def calc_file(table_item, date_of_table):
            found_year = False
            for year in self.vertretungsplan_json:
                if year["year"] == date_of_table["year"]:
                    found_year = True
                    found_month = False
                    for month in year["months"]:
                        if month["month"] == date_of_table["month"]:
                            found_month = True
                            found_day = False
                            for day in month["days"]:
                                if day["day"] == date_of_table["day"]:
                                    found_day = True
                                    table_object_json = self.vertretungsplan_json[
                                        self.vertretungsplan_json.index(year)]["months"][
                                        year["months"].index(month)]["days"][month["days"].index(day)]["day_object"]
                                    if not table_object_json["latest_status"] == table_item["latest_status"]:
                                        changes = add_changes_to_day(table_object_json, table_item)
                                        table_object_json["changes"].append(changes)
                                    else:
                                        logging_time.info("The Status didn't changed")

                            if not found_day:
                                self.vertretungsplan_json[
                                    self.vertretungsplan_json.index(year)]["months"][
                                    year["months"].index(month)]["days"].append(
                                    {"day": date_of_table["day"], "day_object": table_item}
                                )
                    if not found_month:
                        self.vertretungsplan_json[
                            self.vertretungsplan_json.index(year)]["months"].append(
                            {"month": date_of_table["month"], "days": [
                                {"day": date_of_table["day"], "day_object": table_item}
                            ]}
                        )
            if not found_year:
                self.vertretungsplan_json.append(
                    {"year": date_of_table["year"], "months":
                        [{"month": date_of_table["month"], "days": [
                            {"day": date_of_table["day"], "day_object": table_item}
                        ]}
                         ]}
                )

        def extract_date_of_table(title):
            date = title.split(" ")[0].split(".")
            return {"day": int(date[0]), "month": int(date[1]), "year": int(date[2])}

        try:
            calc_file(table_item_today, extract_date_of_table(object_of_table.title_today))
            calc_file(table_item_tomorow, extract_date_of_table(object_of_table.title_tomorow))
        except AttributeError:
            logging_time.warning("failed to calculate and construct json file")

        try:
            with open(self.save_location, "w") as file:
                logging_time.info("writing file...")
                json.dump(self.vertretungsplan_json, file, indent=2)

        except FileNotFoundError or AttributeError:
            try:
                os.mkdir("vertretungsplan")
            except ValueError:
                pass
            with open(self.save_location, "w+") as file:
                logging_time.info("rewriting file")
                json.dump([
                    {"year": self.now.year, "months":
                        [{"month": self.now.month, "days": [
                            {"day": self.now.day, "day_object": table_item_today}
                        ]}
                         ]}
                ], file, indent=2)

        end_time = time.time()
        logging_time.info("time taken to write file: " + str(end_time - start_time))


class TableUtil:
    def __init__(self, payload):
        self.payload = payload
        self.url_s = 'https://gymherderschule.de/iserv/login_check'
        self.url_today = 'https://gymherderschule.de/iserv' \
                         '/infodisplay/file/23/infodisplay/0/SchuelerOnline/subst_001.htm'
        self.url_tomorow = 'https://gymherderschule.de/iserv' \
                           '/infodisplay/file/23/infodisplay/0/SchuelerOnline/subst_002.htm'
        self.headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:12.0) Gecko/20100101 Firefox/12.0'}
        self.table_header = None
        self.title_today = None
        self.massage_today = None
        self.content_today = None
        self.status_today = None
        self.title_tomorow = None
        self.massage_tomorow = None
        self.content_tomorow = None
        self.status_tomorow = None
        self.last_update = None

    def update(self):
        self.get_page()
        self.last_update = datetime.datetime.now()
        logging_time.info("last update at: " +
                     str(self.last_update.hour) + ":" +
                     str(self.last_update.minute) + ":" +
                     str(self.last_update.second))

    @staticmethod
    def soup(file):
        return BeautifulSoup(file, "html.parser")

    def formatting(self, source):
        unique_id = 0
        raw_list = self.soup(source).find(class_="mon_list")
        contents = self.soup(str(raw_list)).get_text(separator="|")
        raw_title = self.soup(source).find(class_="mon_title")
        title = self.soup(str(raw_title)).get_text(separator="|")
        raw_massage = self.soup(source).find(class_="info")
        massage = self.soup(str(raw_massage)).get_text(separator="")
        contents = re.split("\n", contents)
        raw_status = self.soup(source).find(class_="mon_head")
        raw_status = self.soup(str(raw_status)).find_all("p")
        status = None
        for e in raw_status:
            if e.find("Stand:") != -1:
                status = self.soup(str(raw_status)).get_text(separator="").strip("[").strip("]").split("Stand: ")[-1]
        table = []
        for row in contents:
            colums = row.split("|")
            del colums[0]
            table.append({"id": unique_id,
                          "row": colums})
            unique_id += 1
        i = 0
        while i < 3:
            i += 1
            del table[0]
            if i == 2:
                self.table_header = table[0]
        del table[-1]
        massage = re.sub("\n", "", massage, 1)
        if massage == "None":
            massage = "Es gibt keine Nachrichten zum Tag"
        return title, massage, table, status

    def get_page(self):
        sess = requests.Session()
        sess.post(self.url_s, data=self.payload, headers=self.headers)
        time.sleep(0.1)
        request_data_today = sess.get(self.url_today, headers=self.headers)
        request_data_tomorow = sess.get(self.url_tomorow, headers=self.headers)
        if not str(request_data_tomorow.content).find("Keine Vertretusngen") == -1:
            self.title_today, \
            self.massage_today, \
            self.content_today, \
            self.status_today = self.formatting(request_data_today.content)
        if not str(request_data_tomorow.content).find("Keine Vertretusngen") == -1:
            self.title_tomorow, \
            self.massage_tomorow, \
            self.content_tomorow, \
            self.status_tomorow = self.formatting(request_data_tomorow.content)
