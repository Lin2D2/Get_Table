import copy


def calc(table_dont_change, changed_view=False):
    table = copy.deepcopy(table_dont_change)
    NDruck_was = []
    header_row = table["inital_content"]["header"]["row"]
    index_of_VertretungsText = header_row.index("Text")
    index_of_Mitbetreuung = header_row.index("Mitbetreuung")
    index_of_Entfall = header_row.index("Entfall")
    del header_row

    # TODO add join Vertretung and Info

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

