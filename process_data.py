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
pd.set_option('display.max_columns', 40)

#####################
# RAW DATA PROCESSING
#####################

### Import the contribution data.

# Read the 2019-2020 individual contribution data.

raw = pd.read_csv('C:/Users/Gabriel/Desktop/FEC/2019-2020/itcont.txt',
                  header=None, sep='|', nrows=1000)

# Fix the column names to something more legible.
# See the variable descriptions here: https://www.fec.gov/campaign-finance-data/contributions-individuals-file-description/.

raw.columns = ['id_committee', 'amendment', 'report', 'election', 'image', 'type', 'entity', 'name', 'city', 'state', 'zip', 'employer', 
               'occupation', 'date', 'amount', 'id_other', 'id_transaction', 'id_report', 'memo_code', 'memo_text', 'fec_record']

#####################
### Process the data.
#####################

# Copy the raw dataframe.

df = raw[:]

# Improve look of employer, occupation, memo, and cities.

df = df.assign(city=df.city.str.title(), employer=df.employer.str.title(), occupation=df.occupation.str.title(), memo_text=df.memo_text.str.title())

# Make sure ZIP codes are strings.

df['zip'] = df['zip'].astype('str')

### Get first and last names and assign them to new columns.
# This function takes in a column of names and returns a clean one.

def clean_names(names):
    
    # Initialize an empty list for storing the complete names.
    
    result = []
    
    # Split the names by spacing.
    
    names = names.str.split(' ', expand=True)
    
    # The last name always comes first.
    
    last = names[0].str.replace(',', '').str.title()
        
    # Go through every name to check for ones that aren't first or last.
    # Note this uses a numeric iterator in case there are null values.
    
    for n in range(len(names)):
    
        # Make sure the person is not 'II,' or 'Jr.'
        
        if ',' not in str(names[1][n]) and '.' not in str(names[1][n]):
        
            # Use the name as the first name.
            
            first = str(names[1][n]).title()
            
            # If the second column was empty, use the first column as the first name.
            
            if first == 'None':
                first = last[n]
                last[n] = ''
            
        # Otherwise use the next split on the same corresponding row as long as it's not null.
        
        elif str(names[2][n]) != 'None':
            
            first = str(names[2][n]).title()
        
        else:
            
            first = str(names[1][n]).title()
    
        result.append(first + ' ' + last[n])
    
    return pd.DataFrame(result, columns=['name'])

# Assign a new name column with the cleaned names using the function above.

df = df.assign(name=clean_names(df.name))

# Remove other variables that don't add any predictive value, such as the image number, transaction ID, and FEC record (and possibly memo code).
# Delete 22Y entries, which are refunded donations?

del df['image'], df['id_transaction'], df['fec_record']

### Split the zip code into a main and secondary (extra) code.

# Get only the valid numeric zip codes as a Series. (I.e., only ones with repeating digits.)

zips = df.zip.str.extract(r'(\d+)').loc[:,0]

# Make a separate list of just the extended zip codes.

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
entities = {'CAN': 'Candidate', 'CCM':'Candidate Committee', 'COM':'Committee', 'IND':'Individual', 'ORG':'Organization', 'PAC':'Political Action Committee', 'PTY':'Party Organization'}

df['amendment'] = df['amendment'].map(amendments)
df['election'] = df['election'].map(elections)
df['entity'] = df['entity'].map(entities)

### Scrape the FEC websites for more mapping pairs.

# This function takes in cleaned HTML tags and returns a dictionary of all the mapping pairs.

def map_pairs(url, type):
    
    raw = requests.get(url).text
    soup = BeautifulSoup(raw)
    clean_soup = soup.find_all('td')

    # Check whether the type is a report or transaction for determining which lines to copy.

    options = {'report':3, 'types':3, 'parties':3, 'transaction':2}
    position = options.get(type)

    # Initialize an empty dictionary to store values and a counter.

    mapping = {}
    counter = 0

    for tag in clean_soup:

        # Check if the element is in the right position in the text.

        if counter > 2 and counter % position == 0:

            # Clean the tag and get the next item in the list to use as the value.

            key = str(tag).replace('</td>', '').replace('<td>', '')
            val = str(clean_soup[counter + 1]).replace('</td>', '').replace('<td>', '')

            mapping.update({key:val})
        
        counter += 1

    return mapping


# Get the report types.

report_mapping = map_pairs('https://www.fec.gov/campaign-finance-data/report-type-code-descriptions/', 'report')

# Get the transaction types.

transaction_mapping = map_pairs('https://www.fec.gov/campaign-finance-data/transaction-type-code-descriptions/', 'transaction')

# Map all of the scraped values.

df['report'] = df['report'].map(report_mapping)
df['type'] = df['type'].map(transaction_mapping)

##############################
### Import the committee data.
##############################

# Read in the committee data.

raw_committee = pd.read_csv(
    'C:/Users/Gabriel/Desktop/FEC/2019-2020_committees/cm.txt', header=None, sep='|')

# Add a new header based on https://www.fec.gov/campaign-finance-data/committee-master-file-description/.

raw_committee.columns = ['id_committee', 'committee', 'treasurer', 'street1', 'street2', 'city', 'state',
                         'zip', 'designation', 'type', 'party', 'frequency', 'category', 'connection', 'id_candidate']

# Copy only the committee information of interest.

df_committee = raw_committee[['id_committee', 'committee', 'designation', 'type', 'party', 'frequency', 'category', 'connection', 'id_candidate']]

# Improve the look of the organizations.

df_committee = df_committee.assign(committee=df_committee.committee.str.title(), connection=df_committee.connection.str.title())

# Map full words to abbreviations, as with the donations dataframe.

designations = {'A':'Authorized by a candidate', 'B':'Lobbyist/Registrant PAC', 'D':'Leadership PAC', 'J':'Joint fundraiser', 'P':'Principal campaign committee', 'U':'Unauthorized'}
frequencies = {'A':'Administratively terminated', 'D':'Debt', 'M':'Monthly filer', 'T':'Terminated', 'W':'Waived'}
categories = {'C':'Corporation', 'L':'Labor organization', 'M':'Membership organization', 'T':'Trade organization', 'V':'Cooperative', 'W':'Corporation without capital stock'}

### Scrape the type and party information, as with the donations.

# Committee type mapping.

type_mapping = map_pairs('https://www.fec.gov/campaign-finance-data/committee-type-code-descriptions/', 'types')

# Party type mapping.

party_mapping = map_pairs('https://www.fec.gov/campaign-finance-data/party-code-descriptions/', 'parties')

# Apply all of the mapping to the committee dataframe.

df_committee['designation'] = df_committee['designation'].map(designations)
df_committee['type'] = df_committee['type'].map(type_mapping)
df_committee['party'] = df_committee['party'].map(party_mapping)
df_committee['frequency'] = df_committee['frequency'].map(frequencies)
df_committee['category'] = df_committee['category'].map(categories)

# Join the committee info with the original donation data.

df = pd.merge(df, df_committee, how='left', on='id_committee', suffixes=['_donation', '_committee'])

##############################
### Import the candidate data.
##############################

# All candidate data from: https://www.fec.gov/data/browse-data/?tab=bulk-data

raw_candidate = pd.read_csv('C:/Users/Gabriel/Desktop/FEC/2019-2020_candidates/cn.txt', header=None, sep='|')

# Rename the columns and create a separate df.

raw_candidate.columns = ['id_candidate', 'candidate', 'party_candidate', 'election_year', 'election_state', 'race', 'district', 'incumbent', 'status', 'id_committee', 'street', 'street2', 'city', 'state', 'zip']

df_candidate = raw_candidate[:]

# Improve the look of candidate names.

df_candidate = df_candidate.assign(candidate=clean_names(df_candidate.candidate))

# Use mappings to expand a few of the variables into full words.
# Find the corresponding info here: https://www.fec.gov/campaign-finance-data/candidate-master-file-description/

race_mapping = {'H':'House', 'P':'President', 'S':'Senate'}
incumbent_mapping = {'I':'Incumbent', 'C':'Challenger', 'O':'Open seat'}
status_mapping = {'C':'Statutory candidate', 'F':'Statutory candidate for future election', 'N':'Not yet a statutory candidate', 'P':'Statutory candidate in prior cycle'}

df_candidate['party_candidate'] = df_candidate['party_candidate'].map(party_mapping)
df_candidate['race'] = df_candidate['race'].map(race_mapping)
df_candidate['incumbent'] = df_candidate['incumbent'].map(incumbent_mapping)
df_candidate['status'] = df_candidate['status'].map(status_mapping)

# Redefine districts, streets, cities, and zip codes as strings.

df_candidate['district'] = df_candidate['district'].astype(str).str.replace('.0', '')
df_candidate['election_year'] = df_candidate['election_year'].astype(str)
df_candidate['zip'] = df_candidate['zip'].astype(str).str.replace('.0', '')
df_candidate['street'] = df_candidate['street'].astype(str).str.title()
df_candidate['street2'] = df_candidate['street2'].astype(str).str.title()
df_candidate['city'] = df_candidate['city'].astype(str).str.title()

# Only select variables of interest. Ignore things like mailing address and primary committee because we're focusing on donations.

df_candidate_subset = df_candidate[['id_candidate', 'candidate', 'party_candidate', 'election_year', 'election_state', 'race', 'district', 'incumbent']]

# Merge the candidate dataset into the full one.

df = df.merge(df_candidate_subset, how='left', on='id_candidate')

#####
# Take care of NAs.
# Change certain columns to factors.
# Add in voting data.

######################### NEXT STEP IDEAS...

# Count how many give outside their state.

# Find the numerical range, average, etc. (plot?) of the donation amounts. Also distribution of locations.

# Find candidate election results. Manipulate the date to determine how early/late donation is.

# https: // www.fec.gov/campaign-finance-data/contributions-individuals-file-description/
# https://www.fec.gov/campaign-finance-data/committee-master-file-description/
# https: // github.com/clintval/gender-predictor