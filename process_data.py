import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re

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

raw.columns = ['recipient', 'amendment', 'report', 'election', 'image', 'type', 'entity', 'name', 'city', 'state', 'zip',
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

del df['image'], df['id_transaction'], df['fec_record']

## Split the zip code.

zips = df['zip']

# Make a separate list of just the very long zip codes.

zips_long = zips[zips.dropna().str.len() > 5]

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


### Import the committee data.

# Read in the committee data.

raw_committee = pd.read_csv(
    'C:/Users/Gabriel/Desktop/FEC individual contributions/2019-2020_committees/cm.txt', header=None, sep='|')

# Add a new header based on https://www.fec.gov/campaign-finance-data/committee-master-file-description/.

raw_committee.columns = ['recipient', 'name', 'treasurer', 'street1', 'street2', 'city', 'state',
                         'zip', 'designation', 'type', 'party', 'frequency', 'category', 'connection', 'id_candidate']

# Copy only the committee information of interest and match the names in the original dataframe.

# Count how many give outside their state.

# Find the numerical range, average, etc. (plot?) of the donation amounts. Also distribution of locations.

# Find candidate election results. Manipulate the date to determine how early/late donation is.

# https: // www.fec.gov/data/receipts /?data_type = processed & two_year_transaction_period = 2020 & min_date = 01 % 2F01 % 2F2019 & max_date = 12 % 2F31 % 2F2020
# https: // www.fec.gov/campaign-finance-data/contributions-individuals-file-description/
# https://www.fec.gov/campaign-finance-data/committee-master-file-description/
# https: // github.com/clintval/gender-predictor
