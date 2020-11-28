import copy
from operator import is_not
from functools import partial
from pprint import pprint


# TODO maybe this should be client side
def calc(table_dont_change):
    empty_row = "\u00a0"
    table = copy.deepcopy(table_dont_change)
    header_row = table["inital_content"]["header"]["row"]
    content_rows = []

    index_of_VertretungsText = header_row.index("Text")
    index_of_Vertretenvon = header_row.index("Vertr. von")
    index_of_Mitbetreuung = header_row.index("Mitbetreuung")
    index_of_Entfall = header_row.index("Entfall")
    index_of_NDruck = header_row.index("N.Druck. (N)")
    to_exclude = [index_of_VertretungsText, index_of_Vertretenvon, index_of_Mitbetreuung, index_of_Entfall,
                  index_of_NDruck]

    content = []
    del header_row[index_of_NDruck], header_row[index_of_Entfall], header_row[index_of_Mitbetreuung], header_row[
        index_of_Vertretenvon], header_row[index_of_VertretungsText]
    header_row.insert(2, "Info")
    header = header_row
    for row in table["inital_content"]["content"]:
        value_of_VertretungsText = row["row"][index_of_VertretungsText]
        value_of_Vertretenvon = row["row"][index_of_Vertretenvon]
        value_of_Mitbetreuung = row["row"][index_of_Mitbetreuung]
        value_of_Entfall = row["row"][index_of_Entfall]
        value_of_NDruck = row["row"][index_of_NDruck]
        _info = []
        entfall = False
        if value_of_Mitbetreuung == "x":
            _info.append("Mitbetreuung")
        if value_of_Entfall == "x":
            _info.append("Entfall")
            entfall = True
        if value_of_NDruck != empty_row:
            _info.append(value_of_NDruck)
        if value_of_VertretungsText != empty_row:
            _info.append(value_of_VertretungsText)
        if value_of_Vertretenvon != empty_row:
            _info.append(value_of_Vertretenvon)
        del row["row"][index_of_NDruck], row["row"][index_of_Entfall], row["row"][index_of_Mitbetreuung], row["row"][
            index_of_Vertretenvon], row["row"][index_of_VertretungsText]

        if not entfall:
            if row["row"][4] != row["row"][7]:
                _info.insert(0, f'Raumwechsel')
            if row["row"][2] != row["row"][5]:
                _info.insert(0, f'Vertretung')
            elif row["row"][3] != row["row"][6]:
                _info.insert(0, f'Fachwechsel')
        info = ""
        for e in _info:
            info = (f"{info}, {e}" if info != "" else e)

        if row["row"][1] != empty_row:
            row["row"].insert(2, info)
        elif row["row"][0] != empty_row:
            row["row"].insert(2, "AG")
        else:
            row["row"].insert(2, info)
        content_rows.append(row["row"])
    return header, content_rows
