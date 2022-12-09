"""
    This file reads rapporteurs from ./data/raw/Rapporteurs - AI act bill.json
    creates ./data/preprocessed/rapporteur_patterns.txt that contains for each rapporteur (one line per rapporteur)
        lastname, Lastname, LASTNAME
    two-word lastnames are handled such that:
        if the last name contains "von", "van", "vander" or "de", this word is not capitalized in the second entity
        otherwise, the second word is also capitalized in the second entity
                e.g.    de lastname, de Lastname DE LASTNAME
                        last name, Last Name, LAST NAME
"""

import pandas as pd

#%% load raw data to pandas data frame
rapporteurs: pd.DataFrame = pd.read_json("./data/raw/Rapporteurs - AI act bill.json")
rapporteurs = rapporteurs[['last_name', 'name']]
rapporteurs.insert(0, 'last_name_lo', rapporteurs['last_name'].str.lower())

#%% convert to dictionary
rapporteurs_dict: dict = rapporteurs.set_index("last_name_lo").transpose().to_dict()

#%%
patterns: list = []
for rapp_k in rapporteurs_dict.keys():
    if len(rapp_k.split()) == 1:  # if it's only one word
        pat = rapp_k.capitalize()

    if len(rapp_k.split()) == 2:  # if there are two words in the name
        if rapp_k.split()[0].lower() in ['von', 'van', 'vander', 'de']:
            pat = " ".join([rapp_k.split()[0], rapp_k.split()[1].capitalize()])
        else:
            pat = " ".join([rapp_k.split()[0].capitalize(), rapp_k.split()[1].capitalize()])
    patterns.append([pat.lower(), pat, pat.upper()])

with open("./data/preprocessed/rapporteur_patterns.txt", "w") as f:
    for patt in patterns:
        write_pat = ', '.join(patt)  # make list to string
        f.write(write_pat)
        f.write('\n')

