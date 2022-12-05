

def spacy_pattern_from_list(list_in):
    """
        Takes in a list of multi-word strings, returns a pattern to be passed to spacy matcher.
        The resulting pattern will match that exact string
        E.g.:
            list_in = ["Barack Hussein Obama", "George Walker Bush", "George Bush"]
                ==> [[{'LOWER': 'barack'}, {'LOWER': 'hussein'}, {'LOWER': 'obama'}],
                     [{'LOWER': 'george'}, {'LOWER': 'walker'}, {'LOWER': 'bush'}],
                     [{'LOWER': 'george'}, {'LOWER': 'bush'}]]
    :param list_in: list
    :return: list (conforming to spacy matcher pattern architecture)
    """

    list_out: list = []  # list to hold patterns

    for name in list_in:  # gives entire name (2-x tokens)
        pattern_name = []
        for word in name.split():  # gives individual tokens of name
            pattern_name.append({"LOWER": word.lower()})

        list_out.append(pattern_name)

    return list_out

