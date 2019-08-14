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

###########
# FUNCTIONS
###########

### clean_names()
# Get first and last names and assign them to new columns. This function takes in a column of names and returns a clean one.

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

### map_pairs()
# Scrape the FEC websites for more mapping pairs. This function takes in cleaned HTML tags and returns a dictionary of all the mapping pairs.

def map_pairs(url, type):
    
    raw = requests.get(url).text
    soup = BeautifulSoup(raw)
    clean_soup = soup.find_all('td')

    # Check whether the type is a report or transaction for determining which lines to copy.

    options = {'report':3, 'types':3, 'parties':3, 'expenditures':3, 'transaction':2}
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

### string_to_date()
# This function takes in a string argument of the format that appears in the FEC data. It returns a datetime object.

def string_to_date(s):

    # Convert the integer to a string.

    s = str(s)
    
    # Return a null if the date field is null.
    
    if s == 'nan':
        
        return None
    
    # The year is always the last four digits.

    year = re.search(r'(\d\d\d\d$)', s)[0]

    # If there are two digits for the month and day.

    if len(s) == 8:
        month = s[0:2]
        day = s[2:4]

    # If there's only one digit for the month or day.

    if len(s) == 7:
        if s[0] in ['2', '3'] or s[1] == '3' or s[2] == '0' or int(s[:2]) > 12:
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

### split_zips()
# This function takes in a column of zip codes and splits it into two (a main and extended one) to return a dataframe with both.

def split_zips(zips):
    
    # Make sure the list is of strings.
    
    zips = zips.astype('str')

    # Get only the valid numeric zip codes as a series. (I.e., only ones with repeating digits.) This ignores some cases that have invalid zip codes.
    # .loc[:,0] is used here because str.extract returns a dataframe, not series.

    zips = zips.str.extract(r'(\d+)').loc[:,0]

    # Make a separate list of just the extended zip codes.

    zips_long = zips.dropna()[zips.dropna().str.len() > 5]

    # Identify the main and secondary zip codes.

    zip1 = zips.str.extract(r'(\d\d\d\d\d)')
    zip2 = zips_long.str.extract(r'(\d\d\d\d$)')
    
    # Join the two results together by index, since some do not have a secondary zip.
    
    result = pd.concat([zip1, zip2], axis=1)
    
    # Rename them for clarity.
    
    result.columns = ['zip', 'zip2']

    return result

### remove_cancelled()
# This function takes in a dataframe and returns one without "cancelled" transactions (i.e., ones that have both negative and positive transaction amounts).
# This works for the df_individuals, df_expenditures, df_cc, and df_ccandidate dataframes.

def remove_cancelled(df):
    
    # Create a list of names with negative transactions.
    
    names = list(df[df.amount < 0].name)

    # Also create a pattern joined with 'or' to search for in the full list.
    
    pattern = '|'.join(names)
    
    # Create a dataframe with all of the transactions associated with the negative transactions.
    
    return df[df.name.str.contains(pattern)]


############
# COMMITTEES
############
### Import and clean all of the committee data.

# Read in the data from a saved location.
# Download the original file from https://www.fec.gov/data/browse-data/?tab=bulk-data.

raw_committee = pd.read_csv(
    'C:/Users/Gabriel/Desktop/FEC/2019-2020_committees/cm.txt', header=None, sep='|')

# Add a new header based on https://www.fec.gov/campaign-finance-data/committee-master-file-description/.

raw_committee.columns = ['id_committee', 'committee', 'treasurer', 'street1', 'street2', 'city', 'state',
                         'zip', 'designation', 'type', 'party', 'frequency', 'category', 'connection', 'id_candidate']

# Copy all of the information of interest (for display) into a new dataframe. The order is just more convenient for reading.

df_committee = raw_committee[['id_committee', 'committee', 'designation', 'type', 'party', 'category', 'frequency', 'connection', 'id_candidate', 'treasurer', 'street1', 'street2', 'city', 'state', 'zip']]

# Improve the capitalizations of a few of the variables.

df_committee = df_committee.assign(
    committee=df_committee.committee.str.title(), connection=df_committee.connection.str.title(),treasurer=df_committee.treasurer.str.title(),
    street1=df_committee.street1.str.title(),
    street2=df_committee.street2.str.title(),
    city=df_committee.city.str.title())

# Create mappings to match abbreviations to full words to improve legibility. All according to https://www.fec.gov/campaign-finance-data/committee-master-file-description/.

designations = {'A':'Authorized by a candidate', 'B':'Lobbyist/Registrant PAC', 'D':'Leadership PAC', 'J':'Joint fundraiser', 'P':'Principal campaign committee', 'U':'Unauthorized'}
frequencies = {'A':'Administratively terminated', 'D':'Debt', 'M':'Monthly filer', 'T':'Terminated', 'W':'Waived'}
categories = {'C':'Corporation', 'L':'Labor organization', 'M':'Membership organization', 'T':'Trade organization', 'V':'Cooperative', 'W':'Corporation without capital stock'}

# Additionally, scrape the committee type and party information from the FEC website.
# This uses the map_pairs() function defined above.

type_mapping = map_pairs('https://www.fec.gov/campaign-finance-data/committee-type-code-descriptions/', 'types')

party_mapping = map_pairs('https://www.fec.gov/campaign-finance-data/party-code-descriptions/', 'parties')

# Apply all of the mapping schemes to the committee dataframe.

df_committee['designation'] = df_committee['designation'].map(designations)
df_committee['type'] = df_committee['type'].map(type_mapping)
df_committee['party'] = df_committee['party'].map(party_mapping)
df_committee['frequency'] = df_committee['frequency'].map(frequencies)
df_committee['category'] = df_committee['category'].map(categories)

# Split the zip codes with split_zips() and add them to the dataframe.

committee_zips = split_zips(df_committee.zip)

del df_committee['zip']

df_committee = pd.concat([df_committee, committee_zips], axis=1)


##########################
# INDIVIDUAL CONTRIBUTIONS
##########################
### Import and clean all of the data on individual contributions.

# Read the 2019-2020 individual contribution data.

raw_individuals = pd.read_csv('C:/Users/Gabriel/Desktop/FEC/2019-2020_individual-contributions/itcont.txt',
                  header=None, sep='|', nrows=10000)

# Fix the column names to something more legible based on the variable descriptions here: https://www.fec.gov/campaign-finance-data/contributions-individuals-file-description/.

raw_individuals.columns = ['id_committee', 'amendment', 'report', 'election', 'image', 'type', 'entity', 'name', 'city', 'state', 'zip', 'employer', 
               'occupation', 'date', 'amount', 'id_other', 'id_transaction', 'id_report', 'memo_code', 'memo_text', 'fec_record']

# Copy only some variables of interest.

df_individuals = raw_individuals[['name', 'amount', 'city', 'state', 'zip', 'date', 'employer', 'occupation', 'id_committee', 'amendment', 'report', 'election', 'type', 'entity', 'memo_text', 'image']]

# Improve look of employer, occupation, memo, and cities. Add the full URL to the original document image.

df_individuals = df_individuals.assign(
    city=df_individuals.city.str.title(), 
    employer=df_individuals.employer.str.title(), occupation=df_individuals.occupation.str.title(), memo_text=df_individuals.memo_text.str.capitalize())

# Clean up the formatting of the names with clean_names() defined above.

df_individuals = df_individuals.assign(name=clean_names(df_individuals.name))

# Split the zip codes into primary and secondary ones.

individual_zips = split_zips(df_individuals.zip)

del df_individuals['zip']

df_individuals = pd.concat([df_individuals, individual_zips], axis=1)

# Replace the date column with the function defined above.

df_individuals = df_individuals.assign(date = df_individuals.date.apply(string_to_date))

### Make some variable values more legible with full words.
# All according to the chart here: https://www.fec.gov/campaign-finance-data/contributions-individuals-file-description/.

amendments = {'N':'New', 'A':'Amendment', 'T':'Termination'}
elections = {'P':'Primary', 'G':'General', 'O':'Other', 'C':'Convention', 'R':'Runoff', 'S':'Special', 'E':'Recount'}
entities = {'CAN': 'Candidate', 'CCM':'Candidate Committee', 'COM':'Committee', 'IND':'Individual', 'ORG':'Organization', 'PAC':'Political Action Committee', 'PTY':'Party Organization'}

df_individuals['amendment'] = df_individuals['amendment'].map(amendments)
df_individuals['election'] = df_individuals['election'].map(elections)
df_individuals['entity'] = df_individuals['entity'].map(entities)

# Scrape the report and transaction types from the FEC website for mapping abbreviations to full words.

report_mapping = map_pairs('https://www.fec.gov/campaign-finance-data/report-type-code-descriptions/', 'report')

transaction_mapping = map_pairs('https://www.fec.gov/campaign-finance-data/transaction-type-code-descriptions/', 'transaction')

# Map all of the full words.

df_individuals['report'] = df_individuals['report'].map(report_mapping)
df_individuals['type'] = df_individuals['type'].map(transaction_mapping)


##############
### CANDIDATES
##############

# All candidate data from: https://www.fec.gov/data/browse-data/?tab=bulk-data

raw_candidate = pd.read_csv('C:/Users/Gabriel/Desktop/FEC/2019-2020_candidates/cn.txt', header=None, sep='|')

# Rename the columns and create a separate copy of it.

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
# Don't fix zip codes because many here are not the standard five-digit ones, but three-digit (or less) abbreviations.

df_candidate['district'] = df_candidate['district'].astype(str).str.replace('.0', '')
df_candidate['election_year'] = df_candidate['election_year'].astype(str)
df_candidate['zip'] = df_candidate['zip'].astype(str).str.replace('.0', '')
df_candidate['street'] = df_candidate['street'].astype(str).str.title()
df_candidate['street2'] = df_candidate['street2'].astype(str).str.title()
df_candidate['city'] = df_candidate['city'].astype(str).str.title()

########################
# COMMITTEE EXPENDITURES
########################
# Data on all expenditures by each committee.

# Load the data, downloaded from the FEC bulk data site (as above), and rename the variables.

raw_expenditures = pd.read_csv('C:/Users/Gabriel/Desktop/FEC/2019-2020_committee-expenditures/oppexp.txt', header=None, sep='|')

raw_expenditures.columns = ['id_committee', 'amendment', 'year', 'type', 'image', 'line', 'form', 'schedule', 'name', 'city', 'state', 'zip', 'date', 'amount', 'election', 'purpose', 'category', 'category_description', 'memo', 'memo_text', 'entity', 'record', 'file', 'transaction', 'transaction_backref', 'empty']

# Save only variables of interest for display and merging with other datasets.

df_expenditures = raw_expenditures[['id_committee', 'name', 'entity', 'date', 'amount', 'purpose', 'category_description', 'city', 'state', 'zip', 'type', 'election', 'memo_text', 'image']]

# Clean up the formatting of name, purpose, and city.

df_expenditures = df_expenditures.assign(
    name=df_expenditures.name.str.title(),
    purpose=df_expenditures.purpose.str.capitalize(),
    city=df_expenditures.city.str.title(),
    memo_text=df_expenditures.memo_text.str.capitalize())

# Split the zip code into primary and secondary.

expenditure_zips = split_zips(df_expenditures.zip)

del df_expenditures['zip']

df_expenditures = pd.concat([df_expenditures, committee_zips], axis=1)

# Scrape the FEC site for report expenditure type mapping.

expenditure_type_mapping = map_pairs('https://www.fec.gov/campaign-finance-data/report-type-code-descriptions/', 'expenditures')

# Turn abbreviations into full words for improved legibility.

df_expenditures['entity'] = df_expenditures['entity'].map(entities)
df_expenditures['election'] = df_expenditures['election'].map(elections)
df_expenditures['type'] = df_expenditures['type'].map(expenditure_type_mapping)

# Convert the date strings to real datetime objects.

expenditure_dates = df_expenditures.date.dropna().apply(datetime.strptime, args=['%M/%d/%Y']).apply(datetime.date)

df_expenditures = df_expenditures.assign(date=expenditure_dates)


#####################################
# COMMITTEE-TO-COMMITTEE TRANSACTIONS
#####################################
# Data that tracks all committee-to-committee transactions.

# Read in the downloaded file and assign column names: https://www.fec.gov/campaign-finance-data/any-transaction-one-committee-another-file-description/.

raw_cc = pd.read_csv('C:/Users/Gabriel/Desktop/FEC/2019-2020_committee-to-committee-transactions/itoth.txt', header=None, sep='|')

raw_cc.columns = ['id_committee', 'amendment', 'report', 'election', 'image', 'transaction', 'entity', 'name', 'city', 'state', 'zip', 'employer', 'occupation', 'date', 'amount', 'id_other', 'id_transaction', 'file', 'memo', 'memo_text', 'fec_record']

# Save only variables of interest for display and merging with other datasets.

df_cc = raw_cc[['id_committee', 'name', 'entity', 'date', 'amount', 'city', 'state', 'zip', 'employer', 'election', 'report', 'memo_text', 'image']]

# Clean up the formatting of name, city, date, etc.

df_cc = df_cc.assign(
    name=df_cc.name.str.title(),
    city=df_cc.city.str.title(),
    date=df_cc.date.astype('str').str.replace('\.0', ''),
    zip=df_cc.zip.astype('str'),
    memo_text=df_cc.memo_text.str.capitalize())

# Split the zip code into primary and secondary.

cc_zips = split_zips(df_cc.zip)

del df_cc['zip']

df_cc = pd.concat([df_cc, cc_zips], axis=1)

# Turn abbreviations into full words for improved legibility.

df_cc['entity'] = df_cc['entity'].map(entities)
df_cc['election'] = df_cc['election'].map(elections)
df_cc['report'] = df_cc['report'].map(report_mapping)

# Replace the date with datetime objects.

df_cc = df_cc.assign(date = df_cc.date.apply(string_to_date))


######################################
# COMMITTEE-TO-CANDIDATE CONTRIBUTIONS
######################################
# Data that tracks all committee-to-candidate transactions and independent expenditures.

# Read in the downloaded file and assign column names: https://www.fec.gov/campaign-finance-data/any-transaction-one-committee-another-file-description/.

raw_ccandidate = pd.read_csv('C:/Users/Gabriel/Desktop/FEC/2019-2020_committee-to-candidate-transactions/itpas2.txt', header=None, sep='|')

raw_ccandidate.columns = ['id_committee', 'amendment', 'report', 'election', 'image', 'transaction', 'entity', 'name', 'city', 'state', 'zip', 'employer', 'occupation', 'date', 'amount', 'id_other', 'id_candidate', 'id_transaction', 'file', 'memo', 'memo_text', 'fec_record']

# Save only variables of interest for display and merging with other datasets.

df_ccandidate = raw_ccandidate[['id_committee', 'id_candidate', 'name', 'entity', 'date', 'amount', 'city', 'state', 'zip', 'employer', 'election', 'report', 'memo_text', 'image']]

# Clean up the formatting of name, city, date, etc.

df_ccandidate = df_ccandidate.assign(
    name=df_ccandidate.name.str.title(),
    city=df_ccandidate.city.str.title(),
    date=df_ccandidate.date.astype('str').str.replace('\.0', ''),
    zip=df_ccandidate.zip.astype('str'),
    memo_text=df_ccandidate.memo_text.str.capitalize())

# Split the zip code into primary and secondary.

ccandidate_zips = split_zips(df_ccandidate.zip)

del df_ccandidate['zip']

df_ccandidate = pd.concat([df_ccandidate, ccandidate_zips], axis=1)

# Turn abbreviations into full words for improved legibility.

df_ccandidate['entity'] = df_ccandidate['entity'].map(entities)
df_ccandidate['election'] = df_ccandidate['election'].map(elections)
df_ccandidate['report'] = df_ccandidate['report'].map(report_mapping)

# Replace the date with datetime objects.

df_ccandidate = df_ccandidate.assign(date = df_ccandidate.date.apply(string_to_date))


###########################
# DATA CLEANING AND MERGING
###########################

# The six semi-finalized dataframes:
# df_committee
# df_individuals
# df_expenditures
# df_candidate
# df_cc
# df_ccandidate



######################### NEXT STEPS
# Remove negative donations.
# Join the 6 datasets into two (inflows/outflows).
# Exploratory plots (donation amounts and distribution of locations).

# https: // www.fec.gov/campaign-finance-data/contributions-individuals-file-description/
# https://www.fec.gov/campaign-finance-data/committee-master-file-description/
# ZIP shapefiles: https://catalog.data.gov/dataset/tiger-line-shapefile-2015-2010-nation-u-s-2010-census-5-digit-zip-code-tabulation-area-zcta5-na

### Use this URL to find original images AND committee pages. Just append the image number or committee ID: https://docquery.fec.gov/cgi-bin/fecimg/?