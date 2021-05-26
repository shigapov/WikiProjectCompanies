from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import difflib
import csv


"""
Match registration authorities in GLEIF and OpenCorporates
"""


# Get jurisdiction, url and registration authority from OpenCorporates
r = requests.get('https://opencorporates.com/registers?all_registers=true')
soup = BeautifulSoup(r.content, 'html.parser')
registers = []
for reg in soup.find_all('tr'):
    try:
        registers.append([reg.find('td').text.replace('\n',''), # jurisdiction
                          reg.find('a', class_='register').get('href'), # url
                          reg.find('a', class_='register').text ]) # register
    except Exception:
        pass
opencorporates = pd.DataFrame(registers, columns=['jurisdiction', 'url', 'register'])

# Get registration authorities from GLEIF
gleif = pd.read_csv('https://www.gleif.org/content/2-about-lei/7-code-lists/1-gleif-registration-authorities-list/2019-12-05_ra-list-v1.5.csv')
gleif.replace(np.nan, '', inplace=True)
gleif['aliases'] = gleif[['International name of Register',
                          'Local name of Register',
                          'International name of organisation responsible for the Register',
                          'Local name of organisation responsible for the Register']].values.tolist()
gleif['aliases'] = gleif['aliases'].apply(lambda x: [y for y in x if y != ''])

# Naive exact and inexact matching of registration authorities in GLEIF and OpenCorporates
opencorporates['gleif_racode_exact'] = '' # a column with GLEIF RA codes for exact matching
opencorporates['gleif_racode_inexact_90'] = '' # a column with GLEIF RA codes for inexact matching with cutoff=0.90
opencorporates['gleif_racode_inexact_80'] = '' # a column with GLEIF RA codes for inexact matching with cutoff=0.80
for j,orow in opencorporates.iterrows():
    subset = gleif[gleif['Country']==orow['jurisdiction']]
    if not subset.empty:
        for i,row in subset.iterrows():
            if orow['register'] in row['aliases']: # 29 exact matches
                opencorporates.loc[j]['gleif_racode_exact'] = gleif.loc[row.name]['Registration Authority Code']
            if len(difflib.get_close_matches(orow['register'], row['aliases'], cutoff=0.9))>0: # 45 inexact matches
                opencorporates.loc[j]['gleif_racode_inexact_90'] = gleif.loc[row.name]['Registration Authority Code']
            if len(difflib.get_close_matches(orow['register'], row['aliases'], cutoff=0.8))>0: # 64 inexact matches
                opencorporates.loc[j]['gleif_racode_inexact_80'] = gleif.loc[row.name]['Registration Authority Code']

del i, j, orow, r, registers, row, subset, soup

# Check statistics
statistics = opencorporates.describe()

# Save dataframe to a CSV-file
opencorporates.to_csv('ra_opencorporates_gleif.csv', quoting=csv.QUOTE_ALL)
