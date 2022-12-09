"""
    This file: provide function to explode data set based on delimiter
"""

import nltk
import pandas as pd
import timeit


def tokenize_df_explode(df: pd.DataFrame, split_on:str = "new_line", textcol_in: str = "text", textcol_out: str = "text_out"):
    """ explode data set by sentencizing one column (textcol_in)
        takes in
            'df' (pd.DataFrame)
            'textcol_in' (str) where df['textcol_in'] contains text
            'split_on' (str) which must be "sent_break" or "new_line" or "empty_line";
                indicates whether text should be split into sentences (on sentence breaks) or into paragraphs
                (denoted by a line break (\n) or an empty line (\n\n)
        returns data frame with a new column (df['sentencecol_out']) where each sentence in df['textcol_in'] is a row
    """
    starttime = timeit.default_timer()

    indexname: str = df.index.name  # save to reset later
    df.index.rename("index", inplace=True)  # for later melting when index becomes colum

    # instantiate needed tokenizer
    if split_on == "sent_break":  # sentence tokenizer
        tmp_tokenizer = nltk.tokenize.sent_tokenize
        out_series_list = df[textcol_in].apply(tmp_tokenizer)

    elif split_on == "new_line":  # line tokenizer
        tmp_tokenizer = nltk.tokenize.LineTokenizer(blanklines="discard")
        out_series_list = df[textcol_in].apply(tmp_tokenizer.tokenize)

    elif split_on == "empty_line":  # blank line tokenizer
        tmp_tokenizer = nltk.tokenize.BlanklineTokenizer()
        out_series_list = df[textcol_in].apply(tmp_tokenizer.tokenize)

    else:  # if split_on is another value
        raise ValueError("Value of split_on is invalid. Must be sent_break, new_line or empty_line")
        return -1


    out_series: pd.Series = pd.Series(data=out_series_list.apply(pd.Series).reset_index().melt(
        id_vars="index").dropna()[['index', 'value']].set_index('index')['value'], name=textcol_out)

    df: pd.DataFrame = pd.merge(df, out_series, left_index=True, right_index=True)

    df.reset_index(inplace=True)  # reset index to unique indices

    if "index" in df.columns: # delete old index column
        df.rename(columns={"index": "old_" + indexname}, inplace=True)

    print(f"The splitting took {timeit.default_timer() - starttime:.3f} seconds.")

    del out_series_list, out_series, starttime, indexname, tmp_tokenizer

    return df
