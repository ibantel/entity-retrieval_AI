#%% Define function for aggregation of patterns


def count_tup_first_values(lst, values):
    """ Takes in list of tuples. Returns count of occurences of different values at position 0 of the tuples
        Example:
            lst: list = [(101, 0, 2), (102, 4, 6), (101, 8, 10)]
            values: [101, 102, 103]
            return: pd.Series(index=[0,1], data={0: 2, 1: 1})
    :param lst: list of tuples
    :param values: list of values to be aggregated
    :return: pd.Series
    """

    from collections import Counter
    import pandas as pd

    counts = Counter({n: 0 for n in values})  # initialize the counts to zero for every element of values

    if len(lst) == 0:
        return pd.Series(counts)  # if value is NaN: return zero counts

    # lst = ast.literal_eval(lst_str)  # convert string to list if input is

    counts.update(x for x, *_ in lst if x in values)  # update counts based on 1st element of each tuple

    return pd.Series(counts) # return series of counts

