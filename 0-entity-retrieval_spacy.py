""" Overview
#       1) reads data from ./data/raw/Newsletters - Morning tech.json and
#                     from ./data/raw/Rapporteurs - AI act bill.json
#       2) searches for mentions of the provided rapporteurs that are
#                    AI related and generally
#       3) exports
#           the mention_counts (by date, mention type and rapporteur) and
#           the rapporteur names for later visualization
#
"""

#%% imports
import numpy as np
from bs4 import BeautifulSoup
import datetime as dt
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import spacy
from spacy.matcher import Matcher
import timeit

from helpers.spacy_pattern_from_list import spacy_pattern_from_list
from helpers.count_tup_first_values import count_tup_first_values
from helpers.tokenize_df_explode import tokenize_df_explode

# spacy.cli.download("en_core_web_lg")  # download spacy corpus
nlp = spacy.load('en_core_web_lg')  # load spacy corpus


#%% load data
newsletters: pd.DataFrame = pd.read_json("./data/raw/Newsletters - Morning tech.json")  # load data

#%% clean data
newsletters.set_index('id', inplace=True)  # set index
newsletters['date'] = pd.to_datetime(newsletters['date']).dt.date

newsletters = newsletters[['date', 'text']]

#%% split into paragraphs

print(f"The data frame 'newsletters' has {newsletters.shape[0]} rows and {newsletters.shape[1]} columns.")  # (1758, 2)
newsletter_paragraphs: pd.DataFrame = tokenize_df_explode(df=newsletters, textcol_in="text", split_on = "new_line", textcol_out="paragraph")
# The operation took 2.618 seconds.
print(f"The data frame 'newsletters' now has {newsletter_paragraphs.shape[0]} rows and {newsletter_paragraphs.shape[1]} columns.")  # (124519, 4)

newsletter_paragraphs.rename(columns={"date": "newsletter_date"}, inplace=True)
# newsletter_paragraphs.drop(columns="newsletter_index", inplace=True)  # contains errors

newsletter_paragraphs = newsletter_paragraphs[['newsletter_date', 'paragraph']]
newsletter_paragraphs['newsletter_date'] = pd.to_datetime(pd.to_datetime(newsletter_paragraphs['newsletter_date']).dt.date)

#%% convert paragraphs to spacy objects

starttime = timeit.default_timer()
newsletter_paragraphs['paragraph_spacy'] = [doc for doc in nlp.pipe(newsletter_paragraphs['paragraph'].tolist())]  # convert to spacy object
print(f"The creation of spaCy objects took {timeit.default_timer() - starttime:.3f} seconds.")
del starttime

type(newsletter_paragraphs.at[0, 'paragraph_spacy'])

#%% match topics (AI act & AI)
matcher_topic = Matcher(nlp.vocab)  # instantiate matcher for topic (AI act vs. AI vs. none)

# pattern to match artificial intelligence IF NOT followed by "act"
matcher_topic.add(100, [[{'LOWER': 'artificial'}, {'LOWER': 'intelligence'}, {'LOWER': 'act', 'OP': '!'}],
                          [{'LOWER': 'artificial'}, {'LOWER': 'intelligence'}, {'LOWER': 'act', 'OP': '!'}],
                          [{'LOWER': 'ai'}, {'LOWER': 'act', 'OP': '!'}]])

# pattern to match AI act
matcher_topic.add(101, [[{'LOWER': 'artificial'}, {'LOWER': 'intelligence'}, {'LOWER': 'act'}], [{'LOWER': 'ai'}, {'LOWER': 'act'}]])

topic_values: tuple = (100, 101)
topic_colmapper: dict = {100: "AIgen", 101: "AIact"}

if False:  # matcher testing:
    doc = nlp(
        "AI should match theAIpattern. gAIn not. Artificial Intelligence and AI and artificial intelligence should match theAIpattern. AID not. Atrificial intelligence not."
        "AI act, artificial intelligence act should match theAIACTpattern, not PArtificial intelligence act, not artificial intelligence.")

    matches = matcher_topic(doc)

    for match_id, start, end in matches:
        string_id = nlp.vocab.strings[match_id]  # Get string representation
        span = doc[start:end]  # The matched span
        print(f"match pattern: {string_id}, start match: {start}, end match: {end}, match text: {span.text}")

# apply matcher
newsletter_paragraphs['matches_topic'] = newsletter_paragraphs['paragraph_spacy'].apply(matcher_topic)  # match patterns

# manipulate emotion matches
newsletter_paragraphs = newsletter_paragraphs.join(newsletter_paragraphs['matches_topic'].apply(
    count_tup_first_values, args=(topic_values, )))  # aggregate matches: extract values & rejoin

# rename columns
newsletter_paragraphs = newsletter_paragraphs.rename(columns=topic_colmapper)  # optional columns renaming

#%% clean matched topics: each paragraph counted only once

newsletter_paragraphs.loc[:, ['AIgen', 'AIact']] = \
    newsletter_paragraphs.loc[:, ['AIgen', 'AIact']].replace(
        [i for i in range(1, (newsletter_paragraphs.loc[:, ['AIgen', 'AIact']].max().max() + 1))], 1)  # count each paragraph mentioning a topic only once


#%% match rapporteurs

matcher_rapps = spacy.matcher.Matcher(nlp.vocab)  # instantiate matcher for rapporteurs

rapporteur_patterns_spacy: dict = {}

with open("./data/preprocessed/rapporteur_patterns.txt", "r") as f:  # load rapporteur lastname patterns
    for line in f.readlines():
        rap_pat = [i.strip() for i in line.split(',')][0]  # only the all lower-case version is needed

        if len(rap_pat.split(" ")) == 2:
            name = rap_pat.replace(" ", "_")
            patt = [[{'LOWER': rap_pat.split(" ")[0]}, {'LOWER': rap_pat.split(" ")[1]}]]

        else:  # len(rap_pat.split(" ")) == 1
            name = rap_pat
            patt = [[{'LOWER': rap_pat}]]

        rapporteur_patterns_spacy[name] = patt

del f, line, rap_pat,  name, patt

int_id_pattern: int = 1001  # int number of rapporteurs
rapp_values: list = []  # to be transformed to tuple; holds int values of rapporteus
rapp_colmapper: dict = {}  # to rename columns after mapping; int to name of rapporteur pattern

for rapp in rapporteur_patterns_spacy.keys():

    print(f"int id: {int_id_pattern}, rapp patt: {rapporteur_patterns_spacy[rapp]}, rapp name: {rapp}")
    # pattern to match AI act
    matcher_rapps.add(int_id_pattern, rapporteur_patterns_spacy[rapp])

    rapp_values.append(int_id_pattern)
    rapp_colmapper[int_id_pattern] = rapp

    int_id_pattern += 1

del int_id_pattern, rapp, rapporteur_patterns_spacy

# apply matcher
newsletter_paragraphs['matches_rapp'] = newsletter_paragraphs['paragraph_spacy'].apply(matcher_rapps)  # match patterns

# manipulate rapporteur matches
newsletter_paragraphs = newsletter_paragraphs.join(newsletter_paragraphs['matches_rapp'].apply(
    count_tup_first_values, args=(tuple(rapp_values), )))  # aggregate matches: extract values & rejoin

# rename columns
newsletter_paragraphs = newsletter_paragraphs.rename(columns=rapp_colmapper)  # optional columns renaming

#%% inspect rapporteur matching results & save relevant info (quarterly data) in separate data frame

newsletter_paragraphs[[i for i in rapp_colmapper.values()]].sum()  # matching worked - matches found
# newsletter_paragraphs['newsletter_date'] = pd.to_datetime(pd.to_datetime(newsletter_paragraphs['newsletter_date']).dt.date)  # remove if no error thrown; if error thrown: remove "#" to make code functional

# 1) overall mentions (mere name count; one paragraph can be multiple counts)
rapp_overall_q_mentions_tmp =\
    newsletter_paragraphs.groupby(newsletter_paragraphs['newsletter_date'].dt.to_period("Q"))\
        [[i for i in rapp_colmapper.values()]].sum().reset_index()  # mentions overall (one paragraph can give two mentions)

rapp_q_mentions = pd.melt(rapp_overall_q_mentions_tmp, id_vars='newsletter_date',
                          value_vars=[i for i in rapp_colmapper.values()],
                          value_name='mentions_overall_total', var_name='rapporteur')

# 2) paragraph mentions (each paragraph counts once, no matter if mentioning the name once or more often)
newsletter_paragraphs.loc[:, [i for i in rapp_colmapper.values()]] =\
    newsletter_paragraphs.loc[:, [i for i in rapp_colmapper.values()]].replace(
        [i for i in range(1, (newsletter_paragraphs.loc[:, [i for i in rapp_colmapper.values()]].max().max()+1))], 1)
    # across all columns _counting_ the number of rapporteur matches, replace
    # any number between 1 and [the maximum of the numbers in these columns] + 1 with 1

rapp_overall_q_mentions_tmp =\
    newsletter_paragraphs.groupby(newsletter_paragraphs['newsletter_date'].dt.to_period("Q"))\
        [[i for i in rapp_colmapper.values()]].sum().reset_index()  # paragraph mentions (1 paragraph = max 1 mention)

rapp_q_mentions_para = pd.melt(rapp_overall_q_mentions_tmp, id_vars='newsletter_date',
                               value_vars=[i for i in rapp_colmapper.values()],
                               value_name='mentions_overall_paragraph', var_name='rapporteur')

rapp_q_mentions = pd.merge(rapp_q_mentions, rapp_q_mentions_para, how='outer', on=['newsletter_date', 'rapporteur'])

#3) AIact & AIgen mentions

for rapp in rapp_colmapper.values():
    # create a new column rapporteur_AIxxx that is one for each paragraph containing both the rapporteur and AIxxx
    newsletter_paragraphs.loc[:, rapp + "_AIact"] = \
        np.where((newsletter_paragraphs[rapp] > 0) & (newsletter_paragraphs["AIact"] > 0), 1, 0)

    newsletter_paragraphs.loc[:, rapp + "_AIgen"] = \
        np.where((newsletter_paragraphs[rapp] > 0) & (newsletter_paragraphs["AIgen"] > 0), 1, 0)

rapp_AIact = newsletter_paragraphs[['newsletter_date'] + [i for i in newsletter_paragraphs.columns if i.endswith("_AIact")]]  # date & _AIact columns
rapp_AIgen = newsletter_paragraphs[['newsletter_date'] + [i for i in newsletter_paragraphs.columns if i.endswith("_AIgen")]]  # date & _AIgen columns

rapp_AIact_q_raw = rapp_AIact.groupby(rapp_AIact['newsletter_date'].dt.to_period("Q")).sum().reset_index()  # quarterly AIact mentions (1 paragraph = max 1 mention)
rapp_AIgen_q_raw = rapp_AIgen.groupby(rapp_AIgen['newsletter_date'].dt.to_period("Q")).sum().reset_index()  # quarterly AIgen mentions (1 paragraph = max 1 mention)

rapp_AIact_q = pd.melt(rapp_AIact_q_raw, id_vars='newsletter_date', value_vars=[i for i in rapp_AIact_q_raw.columns if not 'newsletter_dat' in i], value_name='mentions_AIact', var_name='rapporteur')  # transform wide to long
rapp_AIgen_q = pd.melt(rapp_AIgen_q_raw, id_vars='newsletter_date', value_vars=[i for i in rapp_AIgen_q_raw.columns if not 'newsletter_dat' in i], value_name='mentions_AIgen', var_name='rapporteur')  # transform wide to long

rapp_AIact_q["rapporteur"] = rapp_AIact_q["rapporteur"].str.replace("_AIact", "")  # remove superfluous trainling description
rapp_AIgen_q["rapporteur"] = rapp_AIgen_q["rapporteur"].str.replace("_AIgen", "")  # remove superfluous trainling description

rapp_q_mentions = pd.merge(rapp_q_mentions, rapp_AIact_q, how='outer', on=['newsletter_date', 'rapporteur'])
rapp_q_mentions = pd.merge(rapp_q_mentions, rapp_AIgen_q, how='outer', on=['newsletter_date', 'rapporteur'])
del rapp_AIact, rapp_AIgen, rapp_AIact_q_raw, rapp_AIgen_q_raw, rapp_AIact_q, rapp_AIgen_q

# transform to long (one row: time/rapporteur/mention type)
rapp_q_mentions_long = pd.melt(rapp_q_mentions, id_vars=['newsletter_date', 'rapporteur'],
                               value_vars=['mentions_overall_total', 'mentions_overall_paragraph',
                                           'mentions_AIact', 'mentions_AIgen'],
                               value_name='mentions', var_name='mention_type')
rapp_q_mentions_long['mention_type'] = rapp_q_mentions_long['mention_type'].str.replace("mentions_", "")  # remove supervluous description

rapp_q_mentions_long['mentions'].sum()
rapp_q_mentions_long.groupby(['mention_type'])['mentions'].sum()
rapp_q_mentions_long.groupby(['rapporteur', 'mention_type'])['mentions'].sum()

rapp_q_mentions_long.to_csv("./data/output_ready/mentions_qrtr_rapp_type.csv")

#%% prepare analysis of non-AI related topics
newsletter_paragraphs_topic =\
    newsletter_paragraphs.loc[
        ((newsletter_paragraphs['matches_rapp'].apply(len) > 0) &
         (newsletter_paragraphs['matches_topic'].apply(len) < 1)), :]  # keep row with a rapporteur but not AI(act)

newsletter_paragraphs_topic = \
    newsletter_paragraphs_topic[[i for i in newsletter_paragraphs.columns if
                                 ('AIact' not in i) and ('AI' not in i) and
                                 ('paragraph_spacy' not in i) and ('matches_' not in i)]]  # drop unneeded columns

# create data frame with quarterly documents of paragraphs mentioning rapporteurs (1 line = all par.s in that quarter with non-AI(act) related rapporteur mentions)
quarterly_overall_topics =\
    newsletter_paragraphs_topic.groupby(newsletter_paragraphs_topic['newsletter_date'].dt.to_period("Q"))['paragraph'].apply('\n'.join).reset_index()

# create rapporteur-specific data
date_rapporteur_topics = pd.melt(newsletter_paragraphs_topic,
                                 id_vars=['newsletter_date', 'paragraph'],
                                 value_vars=[i for i in rapp_colmapper.values()],
                                 value_name='mentioned', var_name='rapporteur')
date_rapporteur_topics =\
    date_rapporteur_topics.loc[date_rapporteur_topics['mentioned']!=0, ['newsletter_date', 'rapporteur', 'paragraph']]
    # drop date/rapporteurs combinations with 0 mentions of that rapporteur

date_rapporteur_topics['newsletter_date'] = date_rapporteur_topics['newsletter_date'].dt.to_period("Q")  # new column for grouping

quarterly_rapporteur_topics =\
    date_rapporteur_topics.groupby(['newsletter_date', 'rapporteur'])['paragraph'].apply('\n'.join).reset_index()

# export data
quarterly_overall_topics['rapporteur'] = 'any one or more'
quarterly_topics = pd.concat([quarterly_overall_topics, quarterly_rapporteur_topics])
del quarterly_overall_topics, quarterly_rapporteur_topics

quarterly_topics.to_csv('./data/preprocessed/quarterly-topics.csv')

