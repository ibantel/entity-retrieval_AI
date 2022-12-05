# """ This file
#       1) reads data from ./data/raw/Newsletters - Morning tech.json and
#                     from ./data/raw/Rapporteurs - AI act bill.json
#       2) searches for mentions of the provided rapporteurs that are
#                    AI related and generally
#       3) exports
#           the mention_counts (by date, mention type and rapporteur) and
#           the rapporteur names for later visualization
# """

#%% imports
from bs4 import BeautifulSoup
import datetime as dt
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import spacy

from helpers.spacy_pattern_from_list import spacy_pattern_from_list
from helpers.count_tup_first_values import count_tup_first_values

# spacy.cli.download("en_core_web_lg")  # download spacy corpus
nlp = spacy.load('en_core_web_lg')  # load spacy corpus


#%% load data
newsletters: pd.DataFrame = pd.read_json("./data/raw/Newsletters - Morning tech.json")  # load data

#%% clean data
newsletters.set_index('id', inplace=True)  # set index
newsletters.drop(columns=['language', 'post_type', 'newsletter_type'], inplace=True)  # remove unneeded columns

newsletters[['date', 'created_at', 'updated_at']] = newsletters[['date', 'created_at', 'updated_at']].apply(pd.to_datetime)  # convert dates

newsletters['slug'] = newsletters['slug'].str.replace('^politico-pro(s)?-morning-tech-', '', regex=True)
newsletters.drop(columns=['slug','title', 'author_names',  'permalink'], inplace=True)

#%% dates: parse, inspect, compare, select date
dates_long: pd.DataFrame = pd.melt(newsletters, value_vars=['date', 'created_at', 'updated_at'],
                                   value_name='dt', ignore_index=False)
dates_long['dt'].hist(by=dates_long['variable'])
plt.show()

# result: discard 'created_at' and 'updated_at'
del dates_long, newsletters['created_at'], newsletters['updated_at']

newsletters = newsletters[['date', 'html']]

newsletters['date'] = pd.to_datetime(newsletters['date']).dt.date

#%% pre-processing text (extract information on AI): find anything related ARTIFICIAL INTELLIGENCE (in different spellings) in the HTML column

if False:  # attempt one: extract what's in the section entitled "ARTIFICIAL INTELLIGENCE"
    match_string_AI_section: str = r'(<table.+><tbody><tr><td.+><span .+>ARTIFICIAL INTELLIGENCE<\/span><\/td><\/tr><\/tbody><\/table>.+<table)'  # HTML tag matching
    newsletters['html_AI_section'] = newsletters['html'].str.extract(match_string_AI_section)

    # does this lose many things? benchmark against AI string matching
    match_string_AI_general: str = r'(ARTIFICIAL INTELLIGENCE)'  # inspect
    newsletters['html_AI_general'] = newsletters['html'].str.extract(match_string_AI_general)

    newsletters['html_AI1'].notna().sum()  # 285 matches
    newsletters['html_AI2'].notna().sum()  # 337 matches
    # inspect differences
    newsletters.loc[newsletters['html_AI1'].isna() & newsletters['html_AI2'].notna(), 'html'].to_csv('./test_csv_nonmatches.csv')

    # result: too many relevant losses; take AI section and fill nas with less sophisticated matching

if False:
    # attempt #2: extract the paragraphs containing "artificial intelligence" in different spellings:
    # (AI|artificial intelligence|ARTIFICIAL INTELLIGENCE)\.?

    matchstring_AI_paragraph: str = r'(<p>(?:(?!<p>).)*?(artificial intelligence|\sAI(\s|\.)|ARTIFICIAL INTELLIGENCE(?!\s*\<\/span\>)).+?<\/p>)'
    newsletters[['html_AI_par1', 'html_AI_par2', 'html_AI_par3']] = newsletters['html'].str.extract(matchstring_AI_paragraph)
    newsletters.loc[newsletters['html_AI_par2'].notna(), 'html_AI_par2'].value_counts()

    newsletters.loc[newsletters['html_AI_par1'].notna(), ['html', 'html_AI_par1', 'html_AI_par2', 'html_AI_par3']].to_csv("df_.csv")

    # problem: str.exctract gets only the first match!
    # use --> df['new_col'] =  df['old_col'].str.findall(r'>([A-Z][^<]+)<')

if True:  # attempt #3: extract paragraphs (s. above) using findall to extract ALL paragraphs
    matchstring_AI_paragraph: str = r'(<p>(?:(?!<p>).)*?(artificial intelligence|\sAI(\s|\.)|ARTIFICIAL INTELLIGENCE(?!\s*\<\/span\>)).+?<\/p>)'
    newsletters['html_AI_p_matches'] = newsletters['html'].str.findall(matchstring_AI_paragraph)
    # find all occurences of "AI" (etc.; except in tables [i.e. headlines]) and get all surrounding paragraphs --> list of tuples (len: 3); first elemen is text

    newsletters['html_AI_p_raw'] = newsletters['html_AI_p_matches'].apply(lambda cell_list: [tup[0] for tup in cell_list])
    # get first element from each tuple --> list of strings, each containing the paragraph of interest

    newsletters['html_AI_p_raw'] = [' '.join(map(str, l)) for l in newsletters['html_AI_p_raw']]
    # transform each cell containing a list of strings to one string per cell

    newsletters['html_AI_p_raw'] = newsletters['html_AI_p_raw'].apply(BeautifulSoup)  # transform to bs object

    # FLAG FOR POTENTIAL EXTENSION (later): split here on </p><p> into paragraphs and make each paragraph one df row

    newsletters['AI_paragraphs'] = newsletters['html_AI_p_raw'].apply(BeautifulSoup.get_text)  # remove HTML tags

    # clean AI_paragraphs: replace (\sAI(\.|\s)|ARTIFICIAL INTELLIGENCE|artificial intelligence) with artificial_intelligence
    matchstring_AI_term = r"(\sAI(\.|\s)|ARTIFICIAL INTELLIGENCE|artificial intelligence)"
    newsletters['AI_paragraphs'] = newsletters['AI_paragraphs'].str.replace(matchstring_AI_term,
                                                                            " artificial_intelligence ", regex=True)

    del matchstring_AI_paragraph, matchstring_AI_term, newsletters['html_AI_p_raw']

# extract all text from HTML
newsletters['general_text'] = newsletters['html'].apply(BeautifulSoup, "lxml")  # transform to bs object
newsletters['general_text'] = newsletters['general_text'].apply(BeautifulSoup.get_text)  # remove HTML tags

newsletters = newsletters[['date', 'general_text',  'AI_paragraphs']]

#%% prepare entity recognition of rapporteurs: load & preprocess rapporteurs
rapporteurs: pd.DataFrame = pd.read_json("./data/raw/Rapporteurs - AI act bill.json")

# drop unneeded columns
rapporteurs.drop(columns=['id', 'bill_id', 'nimsp_id', 'date_of_birth', 'short_bio', 'bio', 'scraped_at', 'phone',
                          'facebook', 'twitter', 'email', 'image_hash', 'original_image', 'image', 'sponsor_types',
                          'organization', 'url', 'role', 'department_id', 'withdrawn', 'index', 'party', 'legislature',
                          'created_at', 'updated_at', 'legislator_session_id'], inplace=True)

# get the relevant entriies as dict
rapporteurs_dict: dict = rapporteurs.set_index("legislator_id")[['last_name', 'name', 'primary']].transpose().to_dict()

for k in rapporteurs_dict.keys():  # convdert names to lowercase
    rapporteurs_dict[k]['last_name'] = rapporteurs_dict[k]['last_name'].lower()
    rapporteurs_dict[k]['name'] = rapporteurs_dict[k]['name'].lower()

del rapporteurs, k

#%% entity recognition from the other json: how often are those entities mentioned? (i.e. the different people)

newsletters['AI_paragraphs_spacy'] = [doc for doc in nlp.pipe(newsletters['AI_paragraphs'].tolist())]  # convert to spacy object
newsletters['general_text_spacy'] = [doc for doc in nlp.pipe(newsletters['general_text'].tolist())]  # convert to spacy object

type(newsletters.at[157233, 'AI_paragraphs_spacy']) # check that cell contains a spaCy Doc object
type(newsletters.at[157233, 'general_text_spacy']) # check that cell contains a spaCy Doc object

# prepare patterns from rapporteur names
patterns: list = []  # list to hold spaCy patterns
mep_ids_raw: list = []  # list to hold MEP IDs
mep_column_mapper: dict = {}  # dict to hold MEP ID as key and last name as value

for k in rapporteurs_dict.keys():
    p_lastname = spacy_pattern_from_list([rapporteurs_dict[k]['last_name']])[0]
    p_name = spacy_pattern_from_list([rapporteurs_dict[k]['name']])[0]

    patterns.append({k: [p_name, p_lastname]})
    mep_ids_raw.append(k)
    mep_column_mapper[k] = "_".join(rapporteurs_dict[k]['last_name'].split(" "))

mep_ids: tuple = tuple(mep_ids_raw)  # tuple with values of mep_ids

# matcher
matcher_meps = spacy.matcher.Matcher(nlp.vocab)  # instantiate Matcher

# add patterns to matcher
for pat in patterns:
    k = list(pat.keys())[0]  # dictionary key
    matcher_meps.add(k, pat[k])
    # result in matcher with each pattern having
    #   id of the person as match_id and
    #   name & last_name of MEP as match patterns

# apply mapper
newsletters['rapporteur_matches_AI_paragraphs'] = newsletters['AI_paragraphs_spacy'].apply(matcher_meps)  # match patterns
newsletters['rapporteur_matches_overall'] =       newsletters['general_text_spacy'].apply(matcher_meps)  # match patterns

del k, mep_ids_raw, p_lastname, p_name, nlp, matcher_meps, patterns, pat, rapporteurs_dict

#%% aggregate and validate entity matches

if True:  # option 1: one column per rapporteur, with counts of occurences
    # aggregate matches from AI paragraphs
    newsletters = newsletters.join(newsletters['rapporteur_matches_AI_paragraphs'].apply(
        count_tup_first_values, args=(mep_ids,)))  # extract values & rejoin

    # rename columns
    newsletters = newsletters.rename(columns={k: str(v) + "_AIpar" for k, v in mep_column_mapper.items()})

    # aggregate matches from general paragraphs
    newsletters = newsletters.join(newsletters['rapporteur_matches_overall'].apply(
        count_tup_first_values, args=(mep_ids,)))  # extract values & rejoin

    newsletters = newsletters.rename(columns={k: str(v) + "_total" for k, v in mep_column_mapper.items()})

    newsletters_pivoting = newsletters.drop(columns=['general_text', 'AI_paragraphs', 'AI_paragraphs_spacy',
                                                     'rapporteur_matches_overall', 'rapporteur_matches_AI_paragraphs',
                                                     'general_text_spacy'])

    for rapp in ['solís_pérez', 'cutajar', 'kolaja', 'maydell', 'benifei', 'tudorache', 'voss', 'clune', 'hahn', 'ernst',
                 'van_sparrentak', 'lacapelle', 'otowski', 'konečná', 'vitanov', 'lagodinsky', 'rooken', 'madison']:
        newsletters_pivoting[rapp + "_nonAIpar"] = \
            newsletters_pivoting[rapp + "_total"] - newsletters_pivoting[rapp + "_AIpar"]

    newsletters_pivoted: pd.DataFrame = pd.melt(newsletters_pivoting, id_vars=['date'],
                                                value_vars=[col for col in newsletters_pivoting.drop(columns='date').columns],
                                                var_name="rapporteur", value_name='mentioned', ignore_index=False
                                                ).sort_index().sort_values(by=['date'])

    newsletters_pivoted[['rapporteur', 'topic']] =\
        newsletters_pivoted['rapporteur']\
            .str.replace("_AIpar", " AI")\
            .str.replace("_nonAIpar", " nonAI")\
            .str.replace("_total", " total")\
            .str.split(expand=True)

    newsletters_pivoted = newsletters_pivoted[['date', 'topic', 'rapporteur', 'mentioned']]  # reorder columns

    newsletters_pivoted = newsletters_pivoted.loc[newsletters_pivoted['mentioned'] != 0, :]  # keep only non-zero rows

    newsletters_pivoted['topic'] = newsletters_pivoted['topic'].replace({'gen': 'total'})  # for better readability

if False:  # option 2: extract from tuples and keep one column
    newsletters['rapporteur_match_ids'] = newsletters['rapporteur_matches'].apply(
        lambda cell_list: [tup[0] for tup in cell_list])
    # get first element from each tuple --> list of ints, each containing the match_id of interest

    newsletters['rapporteur_match_ids'] = [', '.join(map(str, l)) for l in newsletters['rapporteur_match_ids']]
    # transform each cell containing a list of strings to one string per cell

    newsletters['rapporteur_match_names'] = newsletters['rapporteur_match_ids'].replace(
        {str(k): str(v) for k, v in mep_column_mapper.items()}, regex=True)

    newsletter_ai_matches = newsletters.loc[newsletters['rapporteur_match_names'] != ""]

#%% export summary data

newsletters_pivoted['mentioned'].sum()
newsletters_pivoted.groupby(['topic'])['mentioned'].sum()
newsletters_pivoted.groupby(['rapporteur', 'topic'])['mentioned'].sum()

newsletters_pivoted.to_csv("./data/preprocessed/newsletters_preprocessed.csv")

#%% make rapporteurs ready for export & export rapporteurs

rapporteurs_print_dict: dict = {}

for k in rapporteurs_dict.keys():
    lastname_key = rapporteurs_dict[k]['last_name'].replace(" ", "_")
    print_name = rapporteurs_dict[k]['name'].title().replace("Van", "van")

    rapporteurs_print_dict[k] = {"lastname": lastname_key,
                                 "printname": print_name,
                                 "primary": rapporteurs_dict[k]['primary']}

rapporteurs_df: pd.DataFrame = pd.DataFrame(rapporteurs_print_dict).transpose()

rapporteurs_df.to_csv("./data/preprocessed/rapporteurs_preprocessed.csv")
