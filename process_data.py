import numpy as np
import pandas as pd

### Import the data.

# Read the 2019-2020 individual contribution data.

raw = pd.read_csv('C:/Users/Gabriel/Desktop/FEC individual contributions/2019-2020/itcont.txt', header=None, sep='|', nrows=10)

# Add the header from FEC.gov to the raw file.

# raw.columns = pd.read_csv('C:/Users/Gabriel/Desktop/FEC individual contributions/indiv_header_file.csv', nrows=1).columns.values

# Fix the column names to something more legible.
# See the variable descriptions here: https://www.fec.gov/campaign-finance-data/contributions-individuals-file-description/.

raw.columns = ['id_filer', 'amendment', 'report', 'election', 'image', 'type', 'entity', 'name', 'city', 'state', 'zip', 'employer', 'occupation', 'date', 'amount', 'id_other', 'id_transaction', 'id_report', 'memo_code', 'memo_text', 'fec_record']

### Process the data.

# Fix NA values.

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

