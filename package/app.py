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
try:
    import tinydb
except ImportError:
    sys.exit("Failed to import tinydb")

# web api
from web_interface import app as web_app

# create logger
logging_time = logging.getLogger("main")
logging_time.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter(
    '[%(asctime)s] %(levelname)s in %(threadName)s: %(message)s',
    "%Y-%m-%d %H:%M:%S"))

logging.root.handlers = [handler]

if not os.path.exists("vertretungsplan"):
    print("created vertretungsplan")
    os.mkdir("vertretungsplan")

if not os.path.exists("users"):
    print("created users")
    os.mkdir("users")


# TODO database instead of json file
class App:
    def __init__(self):
        logging_time.info("Start")
        time.sleep(0.01)
        self.table_object = TableUtil()
        self.Subjects = Subjects()
        self.database = tinydb.TinyDB("vertretungsplan/data_base.json")
        self.database_users = tinydb.TinyDB("users/data_base_users.json")
        self.now = datetime.datetime.now()
        self.update()
        threading.Thread(target=self.start_web_interface, name="web_threat").start()
        self.timing()

    def start_web_interface(self):
        logging_time.info("starting web-thread...")
        ip_adress = "192.168.0.146"
        web_app.run(parent=self, url=ip_adress, port="5000")

    def update(self):
        logging_time.info("performing update...")
        self.table_object.update()
        database_write = threading.Thread(
            target=self.write_file,
            args=[self.table_object],
            name="file_write").start()
        return database_write

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
            day, month, year = extract_date_of_day(title)
            return {
                "latest_status": status,
                "date": f'{day}.{month}.{year}',
                "title": title,
                "inital_content": {"header": header,
                                   "title": title,
                                   "massage": massage,
                                   "content": content},
                "changes": [
                    create_changes_structur(status)
                ]
            }

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
                    additions.append({"id": unique_id, "row": e["row"]})
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
                if not day["inital_content"]["content"] == table["inital_content"]["content"] \
                        and table["inital_content"]["content"] is not None:
                    content_changed = find_changes_in_table(day["inital_content"]["content"],
                                                            table["inital_content"]["content"])
                return create_changes_structur(table["latest_status"], massage_changed, content_changed)
            else:
                logging_time.info("nothing changed")
                return create_changes_structur(table["latest_status"])

        def write_to_db(date, content):
            search = self.database.search(tinydb.where("date") == date)
            if len(search) > 0:
                search = search[0]
                if not search["inital_content"] == content["inital_content"]:
                    # TODO dosent work right??? isnt added i think
                    search["changes"].append(add_changes_to_day(search, content))
                else:
                    logging_time.info("nothing changed")
            else:
                logging_time.debug("writeing to db")
                self.database.insert(content)

        def extract_date_of_day(day_date):
            date = day_date.split(" ")[0].split(".")
            return int(date[0]), int(date[1]), int(date[2])

        table_item_today = create_table_structur(object_of_table.status_today,
                                                 object_of_table.title_today,
                                                 object_of_table.table_header,
                                                 object_of_table.massage_today,
                                                 object_of_table.content_today)
        logging_time.info("writing today")
        write_to_db(table_item_today["date"], table_item_today)

        table_item_tomorow = create_table_structur(object_of_table.status_tomorow,
                                                   object_of_table.title_tomorow,
                                                   object_of_table.table_header,
                                                   object_of_table.massage_tomorow,
                                                   object_of_table.content_tomorow)
        logging_time.info("writing tomorow")
        write_to_db(table_item_tomorow["date"], table_item_tomorow)


class TableUtil:
    def __init__(self):
        self.new_url_today = "https://gymherderschule.de/iserv/public/infodisplay/file/22/infodisplay/e2005c52fea9317b5c110d5ab103fede/SchuelerOnline/subst_001.htm"
        self.new_url_tomorow = "https://gymherderschule.de/iserv/public/infodisplay/file/23/infodisplay/60d69d2be100b647e7bc0cc949431bf6/SchuelerOnline/subst_002.htm"
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

    def formatting(self, source, contentBool):
        unique_id = 0
        raw_list = self.soup(source).find(class_="mon_list")
        if contentBool:
            contents = self.soup(str(raw_list)).get_text(separator="|")
        raw_title = self.soup(source).find(class_="mon_title")
        title = self.soup(str(raw_title)).get_text(separator="|")
        raw_massage = self.soup(source).find(class_="info")
        massage = self.soup(str(raw_massage)).get_text(separator="")
        if contentBool:
            contents = re.split("\n", contents)
        raw_status = self.soup(source).find(class_="mon_head")
        raw_status = self.soup(str(raw_status)).find_all("p")
        status = None
        for e in raw_status:
            if e.find("Stand:") != -1:
                status = self.soup(str(raw_status)).get_text(separator="").strip("[").strip("]").split("Stand: ")[-1]
        if contentBool:
            table = []
            for row in contents:
                colums = row.split("|")
                if len(row) > 2:
                    for item in colums:
                        if item == "":
                            del colums[colums.index(item)]
                    table.append({"id": unique_id,
                                  "row": colums})
                    unique_id += 1
        # TODO header is deleted here some how
        if contentBool:
            self.table_header = table[1]
            del table[:2]
        massage = re.sub("\n", "", massage, 1)
        if massage == "None":
            massage = "Es gibt keine Nachrichten zum Tag"
        if contentBool:
            return title, massage, table, status
        else:
            return title, massage, None, status

    def get_page(self):
        sess = requests.Session()
        request_data_today = sess.get(self.new_url_today, headers=self.headers)
        request_data_tomorow = sess.get(self.new_url_tomorow, headers=self.headers)
        if str(request_data_tomorow.content).find("Keine Vertretungen") == -1:
            self.title_today, \
            self.massage_today, \
            self.content_today, \
            self.status_today = self.formatting(request_data_today.content, True)
        else:
            self.title_today, \
            self.massage_today, \
            self.content_today, \
            self.status_today = self.formatting(request_data_today.content, False)
        if str(request_data_tomorow.content).find("Keine Vertretungen") == -1:
            self.title_tomorow, \
            self.massage_tomorow, \
            self.content_tomorow, \
            self.status_tomorow = self.formatting(request_data_tomorow.content, True)
        else:
            self.title_tomorow, \
            self.massage_tomorow, \
            self.content_tomorow, \
            self.status_tomorow = self.formatting(request_data_tomorow.content, False)


class Subjects:
    def __init__(self):
        url = "https://www.herderschule-lueneburg.de/lernen/faecher/biologie/"
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:12.0) Gecko/20100101 Firefox/12.0'}
        source = requests.get(url, headers=headers).content
        raw_subject_list = self.soup(source).find("ul", {"id": "menu-faecher-menue"}).find_all("li")
        self.subject_list = [e.get_text(separator=",") for e in raw_subject_list]
        self.subject_list_short = []
        for e in self.subject_list:
            e = e.upper()
            e_split_und = e.split(" UND ")
            e_split_leer = e.split(" ")
            e_split_line = e.split("-")
            if len(e_split_und) > 1:
                short = e_split_und[0][0] + e_split_und[1][0]
                if short not in self.subject_list_short:
                    self.subject_list_short.append(short)
                else:
                    self.subject_list_short.append(e_split_und[0][0] + "u" + e_split_und[1][0])
            elif len(e_split_leer) > 1:
                short = e_split_leer[0][0] + e_split_leer[1][0]
                if short not in self.subject_list_short:
                    self.subject_list_short.append(short)
                else:
                    self.subject_list_short.append(e_split_leer[0][0] + e_split_leer[0][1] + e_split_leer[1][0])
            elif len(e_split_line) > 1:
                short = e_split_line[0][0] + e_split_line[1][0]
                if short not in self.subject_list_short:
                    self.subject_list_short.append(short)
                else:
                    self.subject_list_short.append(e_split_line[0][0] + "-" + e_split_line[1][0])
            else:
                short = e[0] + e[1]
                if short not in self.subject_list_short:
                    self.subject_list_short.append(short)
                else:
                    self.subject_list_short.append(e[0] + e[1] + e[2])

    @staticmethod
    def soup(file):
        return BeautifulSoup(file, "html.parser")
