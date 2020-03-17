import copy


def calc(table_dont_change, changed_view=False):
    table = copy.deepcopy(table_dont_change)
    NDruck_was = []
    header_row = table["inital_content"]["header"]["row"]
    index_of_VertretungsText = header_row.index("Vertretungs-Text")
    index_of_Mitbetreuung = header_row.index("Mitbetreuung")
    index_of_Entfall = header_row.index("Entfall")
    index_of_NDruck = header_row.index("N.Druck. (N)")
    del header_row

    for row in table["inital_content"]["content"]:
        if row["row"][index_of_NDruck] != "\u00a0":
            NDruck_was.append(row)
    for changes in table["changes"]:
        if changes["changed"]:
            for addition in changes["changed"]["content"]["additions"]:
                if addition["row"][index_of_NDruck] != "\u00a0":
                    NDruck_was.append(addition)
    if not changed_view:
        for changes in table["changes"]:
            if changes["changed"]:
                for addition in changes["changed"]["content"]["subtractions"]:
                    for detected in NDruck_was:
                        if addition["id"] == detected:
                            del detected
    if len(NDruck_was) == 0:
        del table["inital_content"]["header"]["row"][index_of_NDruck]
        for row in table["inital_content"]["content"]:
            del row["row"][index_of_NDruck]
        if changed_view:
            for changes in table["changes"]:
                if changes["changed"]:
                    for addition in changes["changed"]["content"]["additions"]:
                        del addition["row"][index_of_NDruck]
                    for addition in changes["changed"]["content"]["subtractions"]:
                        del addition["row"][index_of_NDruck]

    # joining Entfall and Mitbetreuung
    for row in table["inital_content"]["content"]:
        value_of_VertretungsText = row["row"][index_of_VertretungsText]
        value_of_Mitbetreuung = row["row"][index_of_Mitbetreuung]
        value_of_Entfall = row["row"][index_of_Entfall]
        if value_of_Entfall == "x":
            row["row"][index_of_Mitbetreuung] = "Entfall"
        elif value_of_Mitbetreuung == "x":
            row["row"][index_of_Mitbetreuung] = "Mitbetreuung"
        elif value_of_VertretungsText != "\u00a0":
            row["row"][index_of_Mitbetreuung] = value_of_VertretungsText
    for row in table["inital_content"]["content"]:
        del row["row"][index_of_Entfall]
        del row["row"][index_of_VertretungsText]
    table["inital_content"]["header"]["row"][index_of_Mitbetreuung] = "Info"
    del table["inital_content"]["header"]["row"][index_of_Entfall]
    del table["inital_content"]["header"]["row"][index_of_VertretungsText]
    # TODO merge place holder lines to one
    return table

