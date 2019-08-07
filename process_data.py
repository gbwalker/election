import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import re
import requests
from bs4 import BeautifulSoup

# Make dataframes appear as full tables, not wrapped.

pd.set_option('expand_frame_repr', False)

#####################
# RAW DATA PROCESSING
#####################

### Import the contribution data.

# Read the 2019-2020 individual contribution data.

raw = pd.read_csv('C:/Users/Gabriel/Desktop/FEC individual contributions/2019-2020/itcont.txt',
                  header=None, sep='|', nrows=10000)

# Add the header from FEC.gov to the raw file.

# raw.columns = pd.read_csv('C:/Users/Gabriel/Desktop/FEC individual contributions/indiv_header_file.csv', nrows=1).columns.values

# Fix the column names to something more legible.
# See the variable descriptions here: https://www.fec.gov/campaign-finance-data/contributions-individuals-file-description/.

raw.columns = ['id_committee', 'amendment', 'report', 'election', 'image', 'type', 'entity', 'name', 'city', 'state', 'zip',
               'employer', 'occupation', 'date', 'amount', 'id_other', 'id_transaction', 'id_report', 'memo_code', 'memo_text', 'fec_record']

### Process the data.

# Fix NA values.

# Copy the raw dataframe.

df = raw[:]

# Improve look of cities.

df = df.assign(city=df.city.str.title())

## Get first and last names and assign them to new columns.

names = df['name'].str.split(' ', expand=True)

# First name without the comma.

df = df.assign(lastname=names[0].str.replace(',', '').str.title())

# Last name.

df = df.assign(firstname=names[1].str.title())

del df['name']

# Remove other variables that don't add any predictive value, such as the image number, transaction ID, and FEC record (and possibly memo code).
# Delete 22Y entries, which are refunded donations?

del df['image'], df['id_transaction'], df['fec_record'], df['report']

## Split the zip code.

zips = df['zip']

# Make a separate list of just the very long zip codes.

zips_long = zips.dropna()[zips.dropna().str.len() > 5]

# Identify the first and second parts of the zip codes.
# Append .loc[:,0] to turn them into Series.
# Indices 783 and 1961 (among others) should be null, just for reference.

zip1 = zips.str.extract(r'(\d\d\d\d\d)')
zip2 = zips_long.str.extract(r'(\d\d\d\d$)')

# Join the two zip codes and name them appropriately.

zips_final = pd.merge(zip1, zip2, how='outer', left_index=True, right_index=True)
zips_final.columns = ['zip', 'zip2']

# Delete the original zip code column and merge in the split one.

del df['zip']
df = df.join(zips_final)

### Format the date column.

# This function takes in a string argument of the format that appears in the FEC data.
# It returns a datetime object.

def string_to_date(s):

    # Convert the integer to a string.

    s = str(s)

    # The year is always the last four digits.

    year = re.search(r'(\d\d\d\d$)', s)[0]

    # If there are two digits for the month and day.

    if len(s) == 8:
        month = s[0:2]
        day = s[2:4]

    # If there's only one digit for the month or day.

    if len(s) == 7:
        if s[0] in ['2', '3'] or s[1] == '3' or s[2] == '0':
            month = s[0]
            day = s[1:3]
        else:
            month = s[0:2]
            day = s[2]

    # If there's only one digit for the month AND day.
    
    if len(s) == 6:
        month = s[0]
        day = s[1]
    
    date = month + '-' + day + '-' + year

    return(datetime.strptime(date, '%m-%d-%Y').date())

# Replace the date column in the original dataframe.

df = df.assign(date = df.date.apply(string_to_date))

### Make some variable values more legible with full words.
# All according to the chart here: https://www.fec.gov/campaign-finance-data/contributions-individuals-file-description/.

amendments = {'N':'New', 'A':'Amendment', 'T':'Termination'}
elections = {'P':'Primary', 'G':'General', 'O':'Other', 'C':'Convention', 'R':'Runoff', 'S':'Special', 'E':'Recount'}

df['amendment'] = df['amendment'].map(amendments)
df['election'] = df['election'].map(elections)

### Scrape the FEC websites for more mapping pairs.



##############################
### Import the committee data.
##############################

# Read in the committee data.

raw_committee = pd.read_csv(
    'C:/Users/Gabriel/Desktop/FEC individual contributions/2019-2020_committees/cm.txt', header=None, sep='|')

# Add a new header based on https://www.fec.gov/campaign-finance-data/committee-master-file-description/.

raw_committee.columns = ['id_committee', 'name', 'treasurer', 'street1', 'street2', 'city', 'state',
                         'zip', 'designation', 'type', 'party', 'frequency', 'category', 'connection', 'id_candidate']

# Copy only the committee information of interest.

df_committee = raw_committee[['id_committee', 'name', 'designation', 'type', 'party', 'frequency', 'category', 'connection', 'id_candidate']]

# Join the committee info with the original donation data.

df = pd.merge(df, df_committee, how='left', on='id_committee', suffixes=['_donation', '_committee'])

##############################
### Import the candidate data.
##############################




# Count how many give outside their state.

# Find the numerical range, average, etc. (plot?) of the donation amounts. Also distribution of locations.

# Find candidate election results. Manipulate the date to determine how early/late donation is.


# https: // www.fec.gov/campaign-finance-data/contributions-individuals-file-description/
# https://www.fec.gov/campaign-finance-data/committee-master-file-description/
# https: // github.com/clintval/gender-predictor