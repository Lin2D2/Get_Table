import copy
from operator import is_not
from functools import partial
from pprint import pprint


def calc(table_dont_change):
    empty_row = "\u00a0"
    table = copy.deepcopy(table_dont_change)
    header_row = table["inital_content"]["header"]["row"]
    content_rows = [row["row"] for row in table["inital_content"]["content"]]

    index_of_VertretungsText = header_row.index("Text")
    index_of_Vertretenvon = header_row.index("Vertr. von")
    index_of_Mitbetreuung = header_row.index("Mitbetreuung")
    index_of_Entfall = header_row.index("Entfall")
    index_of_NDruck = header_row.index("N.Druck. (N)")
    to_exclude = [index_of_VertretungsText, index_of_Vertretenvon, index_of_Mitbetreuung, index_of_Entfall,
                  index_of_NDruck]

    content = []
    header = list(filter(partial(is_not, None),
                         [(e if header_row.index(e) not in to_exclude else None) for e in header_row] + ["Info"]))
    for row in content_rows:
        index = -1
        counter = 0
        new_row = []
        for e in row:
            index += 1
            if index not in to_exclude:
                new_row.append(e)
            else:
                if e != empty_row and counter < 1:
                    counter += 1
                    if index == index_of_VertretungsText or index == index_of_Vertretenvon or index == index_of_NDruck:
                        new_row.append(e)
                    elif index == index_of_Mitbetreuung:
                        new_row.append("Mitbetreuung")
                    elif index == index_of_Entfall:
                        new_row.append("Entfall")
                elif counter > 1:
                    print("more then one set")
        content.append(new_row if len(new_row) == 9 else new_row + [empty_row])
    return header, content
