
#%% imports

#%pip install bertopic
from bertopic import BERTopic
import spacy
import pandas as pd
spacy.cli.download("en_core_web_lg")
nlp = spacy.load('en_core_web_lg')  # load spacy corpus

#%% load topic data
quarterly_topics: pd.DataFrame = pd.read_csv('./data/preprocessed/quarterly-topics.csv')

quarterly_topics_overall = quarterly_topics.loc[quarterly_topics['rapporteur'] == 'any one or more', :]
quarterly_topics_rapporteurs = quarterly_topics.loc[quarterly_topics['rapporteur'] != 'any one or more', :]

del quarterly_topics

#%% transform to spaCy-object
quarterly_topics_overall['paragraph_spacy'] = [doc for doc in nlp.pipe(quarterly_topics_overall['paragraph'].tolist())]  # convert to spacy object

#%% clean text columns with spacy
del_pos= [# POS tags to remove (all POS tags listed; those to keep commented out from removal list)
          ##'ADJ', # adjective
          'ADP', # adposition
          'ADV', # adverb
          ##'AUX', # auxiliary
          'CCONJ', # coordinating conjunction
          'DET', # determiner
          #'INTJ', # interjection
          #'NOUN', # noun
          'NUM', # numeral
          'PART', # particle
          'PRON', # pronoun
          'PROPN', # proper noun
          'PUNCT', # punctuation
          'SPACE', # space
          #'SCONJ', # subordinating conjunction
          'SYM', # symbol
          #'VERB', # verb
    ]

keep_pos = ['NOUN'#, 'PROPN'
            ]


rapp_names_lower = ['solís pérez', 'cutajar', 'kolaja', 'maydell', 'benifei', 'tudorache', 'voss', 'clune', 'hahn', 
                    'van sparrentak', 'lacapelle', 'otowski', 'konečná', 'vitanov', 'lagodinsky', 'rooken', 'madison', 'ernst'
                    ]

exclude_toks = rapp_names_lower + ['datum', 'e', '-', '’s', 'rapporteur', '.&nbsp', 'politico']

tokens_rowwise = []
for row in nlp.pipe(quarterly_topics_overall['paragraph']):
  proj_tok = [token.lemma_.lower() for token in row if token.pos_ in keep_pos and token.lower_ not in exclude_toks]
  #proj_tok = [token.lemma_.lower() for token in row if token.pos_ not in del_pos and token.lower_ not in exclude_toks]

  #for tok in row:
    #if "datu" in tok.lower_:
      #print(tok.lower_)
  
  # remove tokens according to POS tag and if they're a rapporteur name

  tokens_rowwise.append(proj_tok)


# manually clean tokens
for row in tokens_rowwise:
  for i in row:
    if i in exclude_toks:
      row.remove(i)

quarterly_topics_overall['tokens'] = pd.Series(tokens_rowwise)

from gensim.corpora.dictionary import Dictionary
dictionary = Dictionary(quarterly_topics_overall['tokens']) # apply the Dictionary Object from Gensim, which maps each word to their unique ID. To inspect: print(dictionary.token2id)

trykey = 'politico' # '.&nbsp' # 'rapporteur'  # datum
try:
  dictionary.token2id[trykey]
except KeyError:
  print(f"No dictionary key '{trykey}'. This is desired")

dictionary.filter_extremes(no_below=5, no_above=0.5, keep_n=1000) # filter out low-frequency tokens (must appear in at least 5 documents, i.e. paragraphs) and high-frequency tokens (cannot appear in more than 50% of documens), also limit the vocabulary to a max of 1000 words:

corpus = [dictionary.doc2bow(doc) for doc in quarterly_topics_overall['tokens']]  # construct corpus using dictionary & doc2bow function (which counts each word's occurrences, converts word to its int id and returns the result as a sparse vector)

#%% Return most frequent words overall
quarterly_topics_overall['tokens'] = [' '.join(map(str, l)) for l in quarterly_topics_overall['tokens']]

from collections import Counter

term_counts = pd.DataFrame(Counter(" ".join(quarterly_topics_overall["tokens"]).split()).most_common(1000), columns=['term', 'counts'])

term_counts.to_csv(root_path + '/_term_counts_overall.csv')

#%% Return most frequent word by rapporteur

tokens_rowwise = []
for row in nlp.pipe(quarterly_topics_rapporteurs['paragraph']):
  proj_tok = [token.lemma_.lower() for token in row if token.pos_ in keep_pos and token.lower_ not in exclude_toks]
  #proj_tok = [token.lemma_.lower() for token in row if token.pos_ not in del_pos and token.lower_ not in exclude_toks]

  #for tok in row:
    #if "datu" in tok.lower_:
      #print(tok.lower_)
  
  # remove tokens according to POS tag and if they're a rapporteur name

  tokens_rowwise.append(proj_tok)


# manually clean tokens
for row in tokens_rowwise:
  for i in row:
    if i in exclude_toks:
      row.remove(i)

quarterly_topics_rapporteurs['tokens'] = pd.Series(tokens_rowwise)

quarterly_topics_rapporteurs_exploded=quarterly_topics_rapporteurs.explode('tokens').groupby('rapporteur')['tokens'].value_counts()  #Explode and count

top_terms_rapporteurs = pd.DataFrame(quarterly_topics_rapporteurs_exploded).rename(columns = {'tokens': 'count'}).reset_index().rename(columns={'tokens':'token'})


top_term_raps = top_terms_rapporteurs.loc[top_terms_rapporteurs.reset_index().groupby(['rapporteur'])['count'].idxmax(), :]  # what is the top term for each rapporteur?
top_term_raps.to_csv(root_path + '/_top_terms_rapporteurs.csv')


#%% topic models (LDA) model building

from gensim.models import LdaMulticore
# lda_model = LdaMulticore(corpus=corpus, id2word=dictionary, iterations=50, num_topics=10, workers = 4, passes=10)  # alternative: gensim.models.ldamodel.LdaModel

import matplotlib.pyplot as plt
from gensim.models import CoherenceModel
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

# inspect topic coherence across topic numbers

# performance based on https://www.baeldung.com/cs/topic-modeling-coherence-score
# 1) 'u_mass' scores (negative numbers; higher absolute numbers are better)
topics = []
score = []

for i in range(1, 55, 1):
    lda_model = LdaMulticore(corpus=corpus, id2word=dictionary, iterations=10, num_topics=i, workers=4, passes=10,
                             random_state=100)
    cm = CoherenceModel(model=lda_model, corpus=corpus, dictionary=dictionary, coherence='u_mass')
    topics.append(i)
    score.append(cm.get_coherence())

_ = plt.plot(topics, score)
_ = plt.xlabel('Number of Topics')
_ = plt.ylabel('UMass Coherence Score (lower is better)')
plt.show()

print("1st local minimum:", dict(zip(score[:10], topics[:10]))[min(score[:10])])  # 1st local minimum
print("2nd local minimum:", dict(zip(score[10:20], topics[10:20]))[min(score[10:20])])  # 2nd local minimum
print("2nd local minimum:", dict(zip(score[20:30], topics[20:30]))[min(score[20:30])])  # 2nd local minimum
print("2nd local minimum:", dict(zip(score[30:40], topics[30:40]))[min(score[30:40])])  # 2nd local minimum
print("Overall minimum in measured area:", dict(zip(score, topics))[min(score)])  # minimum at 49 topics
# dict(zip(topics, score))

topic_n = 10  # ..

lda_model = LdaMulticore(corpus=corpus, id2word=dictionary, iterations=100, num_topics=topic_n, workers=4, passes=100)

# %% print and visualize topics

# lda_model.print_topics(-1)  # print all topics
# print one document
# quarterly_topics['paragraph'][0]  # first document
# lda_model[corpus][0]  # belongs to topic 38 (index 37)

# visualize the topics and the words in each topic
# %pip install pyLDAvis -qq
import pyLDAvis.gensim_models

pyLDAvis.enable_notebook()  # visualise inside a notebook

lda_display = pyLDAvis.gensim_models.prepare(lda_model, corpus, dictionary)
pyLDAvis.display(lda_display)

# add topics to df
quarterly_topics_overall['topic'] = [" ".join(["topic", str(sorted(lda_model[corpus][text])[0][0])]) for text in
                                     range(len(quarterly_topics_overall['paragraph']))]
# quarterly_topics['topic'].value_counts()

pyLDAvis.save_html(lda_display, root_path + '/_topics.html')
quarterly_topics_overall.to_csv(root_path + '/_quarterly-topics_overall_LDA.csv')

