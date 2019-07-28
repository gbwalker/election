import numpy as np
import pandas as pd

#####################
# RAW DATA PROCESSING
#####################

### Import the contribution data.

# Read the 2019-2020 individual contribution data.

raw = pd.read_csv('C:/Users/Gabriel/Desktop/FEC individual contributions/2019-2020/itcont.txt', header=None, sep='|', nrows=10)

# Add the header from FEC.gov to the raw file.

# raw.columns = pd.read_csv('C:/Users/Gabriel/Desktop/FEC individual contributions/indiv_header_file.csv', nrows=1).columns.values

# Fix the column names to something more legible.
# See the variable descriptions here: https://www.fec.gov/campaign-finance-data/contributions-individuals-file-description/.

raw.columns = ['recipient', 'amendment', 'report', 'election', 'image', 'type', 'entity', 'name', 'city', 'state', 'zip', 'employer', 'occupation', 'date', 'amount', 'id_other', 'id_transaction', 'id_report', 'memo_code', 'memo_text', 'fec_record']

### Process the data.

# Fix NA values.

# Improve look of cities.

df = df.assign(city=df.city.str.title())

# Copy the raw dataframe.

df = raw[:]

# Get first and last names and assign them to new columns.

names = df['name'].str.split(' ', expand=True)

df = df.assign(lastname=names[0].str.replace(',', '').str.title())

df = df.assign(firstname=names[1].str.title())

del df['name']

# Remove other variables that don't add any predictive value, such as the image number, transaction ID, and FEC record (and possibly memo code).
# Delete 22Y entries, which are refunded donations?

del df['image'], df['id_transaction'], df['fec_record']

### Import the committee data.

# Read in the committee data.

raw_committee = pd.read_csv('C:/Users/Gabriel/Desktop/FEC individual contributions/2019-2020_committees/cm.txt', header=None, sep='|')

# Add a new header based on https://www.fec.gov/campaign-finance-data/committee-master-file-description/.

raw_committee.columns = ['recipient', 'name', 'treasurer', 'street1', 'street2', 'city', 'state', 'zip', 'designation', 'type', 'party', 'frequency', 'category', 'connection', 'id_candidate']

# Copy only the committee information of interest and match the names in the original dataframe.

# Count how many give outside their state.

# Find the numerical range, average, etc. (plot?) of the donation amounts. Also distribution of locations.

# Find candidate election results. Manipulate the date to determine how early/late donation is.

