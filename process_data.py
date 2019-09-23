import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import re
import requests
from bs4 import BeautifulSoup
import string
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

# Make dataframes appear as full tables, not wrapped.

pd.set_option('expand_frame_repr', False)
pd.set_option('display.max_columns', 40)

#####################
# RAW DATA PROCESSING
#####################

###########
# FUNCTIONS
###########

# clean_names()
# Get first, middle, and last names and assign them to new columns. This function takes in a column of names and returns an expanded version.

def clean_names(names):
    
    # Remove leading or trailing spaces.
    
    names = names.str.strip()
    
    # Fix names with a comma and no space after it or ampersand and no spaces.
    
    names = names.str.replace(',', ', ').str.replace('&', ' & ').str.replace('  ', ' ')
    
    # Initialize an empty list for storing the complete names.

    result = pd.DataFrame(columns=['name_full', 'first_last', 'first', 'middle', 'last'], index=names.index)
    
    # Split the names by comma.

    split_names = names.str.split(' ', expand=True)
    
    # Iterate through each row in the split names to identify first, middle, and last names.

    for index, row in split_names.iterrows():
                            
        # If the name is only one word long, use that.
        
        if row.count() == 1:
            
            result.loc[index] = {'name_full': row[0].title(),
                                 'first_last': row[0].title(),
                                 'first': row[0].title(),
                                 'middle': '',
                                 'last': ''}
            
            continue
        
        # If the name has an ampersand in it and no comma, it's likely a law firm or business.
        # If it has LLC or LP in the name, it's also a business.
        
        name_full = row.str.cat(sep=' ').title()
        
        if (('&' in name_full) & (not ',' in name_full)) | (' LLC' in name_full) | (' LP' in name_full):
            
            result.loc[index] = {'name_full': name_full,
                        'first_last': name_full,
                        'first': '',
                        'middle': '',
                        'last': ''}
            
            continue
        
        # If the name has a comma AND an ampersand, it's most likely a couple.
        
        if ('&' in name_full) & (',' in name_full):
            
            result.loc[index] = {'name_full': row[1:].str.cat(sep=' ').title() + ' ' + row[0].title(),
                        'first_last': row[1:].str.cat(sep=' ').title() + ' ' + row[0].title(),
                        'first': row[1:].str.cat(sep=' ').title(),
                        'middle': '',
                        'last': row[0].title()}
            
            continue
        
        # Iterate over each split.
        
        for n in range(row.count()):
                                                
            # If the element has a comma, it should be the last name.
                        
            if ',' in row[n]:
        
                # Save the identified last name and remove the comma after it.
        
                last = ' '.join(row[0:n+1])[0:-1]
                
                first = row[n+1]
                
                # If there is an additional name that does not contain a period (e.g., Mrs., Dr., etc.), then save it as the middle. This leaves out some middle initials, but should be good enought to identify most individuals.
                
                middle = ''
                
                if not n + 2 >= row.count():
                    
                    if ('.' not in row[n+2]) & ('MR' not in row[n+2]) & (row[n+2] not in ['OTHER', 'Other']):
                    
                        middle = row[n+2]
                
                result.loc[index] = {
                    'name_full': first.title() + ' ' + middle.title() + ' ' + last.title(), 
                    'first_last': first.title() + ' ' + last.title(),
                    'first': first.title(), 
                    'middle': middle.title(), 
                    'last': last.title()}
                                            
                break
                        
            # Catch edge cases that have no commas.
            
            if n + 1 == row.count():
                
                result.loc[index] = {
                    'name_full': row.str.cat(sep=' ').title(), 
                    'first_last': row[1].title() + ' ' + row[0].title(),
                    'first': row[1].title(), 
                    'middle': '', 
                    'last': row[0].title()}
                            
            # Make a specific exception for Dr. Michel Anissa Powell, whose name is listed wrong.
            
            if row[0] == 'MICHEL':
                
                result.loc[index] = {
                    'name_full': row.str.cat(sep=' ').title(), 
                    'first_last': row[0].title() + ' ' + row[2].title(),
                    'first': row[0].title(), 
                    'middle': row[1].title(), 
                    'last': row[2].title()}
    

    
    # Clean up formatting a bit.
    
    result = result.assign(name_full=result.name_full.str.replace(',', '').str.replace(' Ii', ''),
                           first_last=result.first_last.str.replace(',', '').str.replace(' Ii', ''),
                           middle=result.middle.str.replace(',', ''),
                           last=result['last'].str.replace(',', '').str.replace(' Ii', ''))
    
    return result


# map_pairs()
# Scrape the FEC websites for more mapping pairs. This function takes in cleaned HTML tags and returns a dictionary of all the mapping pairs.

def map_pairs(url, type):

    raw = requests.get(url).text
    soup = BeautifulSoup(raw)
    clean_soup = soup.find_all('td')

    # Check whether the type is a report or transaction for determining which lines to copy.

    options = {'report': 3, 'types': 3, 'parties': 3,
               'expenditures': 3, 'transaction': 2}
    position = options.get(type)

    # Initialize an empty dictionary to store values and a counter.

    mapping = {}
    counter = 0

    for tag in clean_soup:

        # Check if the element is in the right position in the text.

        if counter > 2 and counter % position == 0:

            # Clean the tag and get the next item in the list to use as the value.

            key = str(tag).replace('</td>', '').replace('<td>', '')
            val = str(clean_soup[counter + 1]
                      ).replace('</td>', '').replace('<td>', '')

            mapping.update({key: val})

        counter += 1

    return mapping

# string_to_date()
# This function takes in a string argument of the format that appears in the FEC data. It returns a datetime object.

def string_to_date(s):

    # Convert the float to a string.

    s = str(s)
    
    s = s.replace('.0', '')

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

# split_zips()
# This function takes in a column of zip codes and splits it into two (a main and extended one) to return a dataframe with both.

def split_zips(zips):

    # Make sure the list is of strings.

    zips = zips.astype('str')

    # Get only the valid numeric zip codes as a series. (I.e., only ones with repeating digits.) This ignores some cases that have invalid zip codes.
    # .loc[:,0] is used here because str.extract returns a dataframe, not series.

    zips = zips.str.extract(r'(\d+)').loc[:, 0]

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

# remove_invalid()
# This function takes in a dataframe and returns one without "invalid" transactions (i.e., ones that are negative OR are positive and correspond to a negative one).
# This works for the df_individuals, df_expenditures, and df_cc dataframes.
# It assumes that there are not duplicate name entries for negative transactions.

def remove_invalid(df):

    # Create a dictionary of only negative transactions with names as keys.
    # There must only be one negative transaction per name key.

    negatives = pd.Series(df[df.amount < 0].amount.values,
                          index=df[df.amount < 0].name_full).to_dict()

    # Make an initial list of invalid transactions to remove (negatives).

    delete_list = list(df[df.amount < 0].index)

    # Create a much shortened dataframe with just name matches.

    df_short = df[df.name_full.isin(negatives.keys())]

    # Find all entries that have a name in the negative list AND an amount that's the positive version of a negative transaction.

    for index, row in df_short.iterrows():

        # Match an amount that corresponds to a negative.

        if negatives[row['name_full']] == -1 * row['amount']:

            # Add the transactions to the list of ones to delete.

            delete_list.append(index)

    # Remove the entries that appear in the delete list.

    result = df[~df.index.isin(delete_list)]

    return result

# identify_party()
# This function takes in a dataframe of unique PAC recipients listed in df_cc, a dataframe of transactions between PACs, and matches the party affiliation for each transaction using the party affiliation of candidates and PACs (in df_candidates and df_committee). It uses fuzzy string matching, so is accurate but not necessarily perfect.

def identify_party(df):
    
    # Initialize an empty storage dataframe.
    
    result = pd.DataFrame(index=range(len(df)), columns=['party', 'recipient', 'candidate_match', 'candidate_confidence', 'committee_match', 'committee_confidence'])
    
    # Loop through every row in the original transaction dataframe.

    for n in range(len(df)):
        
        # Print a simple counter.
        
        if n % 10 == 0:
            print(n)
        
        # Define the recipient entity and save it.
        
        recipient = df.recipient.iloc[n]
        
        result.recipient[n] = recipient
                
        # Find a match to the recipient in the candidate list.
        
        match_candidate = process.extract(recipient, df_candidate.committee, scorer=fuzz.token_sort_ratio, limit=1)
                
        # Save the candidate match if it's accurate enough.
        
        if match_candidate[0][1] >= 95:
                        
            result.candidate_match[n] = match_candidate[0][0]
            
            result.candidate_confidence[n] = match_candidate[0][1]
            
            # Get the party information from the candidate dataframe.
            
            location = match_candidate[0][2]
                        
            result.party[n] = df_candidate.party_candidate[location]
                
        # If the recipient is not likely a candidate, then check for a PAC.
        
        elif match_candidate[0][1] < 95:
            
            # Find a match to the recipient in the committee list.
            
            match_committee = process.extract(recipient, df_committee.committee, scorer=fuzz.token_sort_ratio, limit=1)
            
            # Save it to the storage dataframe with the confidence level and the location of the PAC in the full list.
            
            result.committee_match[n] = match_committee[0][0]
            
            result.committee_confidence[n] = match_committee[0][1]
            
            # Get the party information from the committee dataframe.
            
            location = match_committee[0][2]
            
            result.party[n] = df_committee.party[location]
        
    # Send back the full result.
    
    return result


### OLD NOTES

        # If the transaction party is still undetermined after checking the recipient, check the sender.
        #
        
        if result.party[n] in ['Unknown', 'None', 'No Party Affiliation']:
            
            sender = df.sender.iloc[n]
        
            result.sender[n] = sender
            
            # Find a match to the sender in the candidate list.
        
            match_candidate = process.extract(sender, df_candidate.first_last, scorer=fuzz.token_sort_ratio, limit=1)
                    
            # Save the candidate match if it's accurate enough.
            
            if match_candidate[0][1] >= 70:
                            
                result.candidate_match[n] = match_candidate[0][0]
                
                result.candidate_confidence[n] = match_candidate[0][1]
                
                # Get the party information from the candidate dataframe.
                
                location = match_candidate[0][2]
                            
                result.party[n] = df_candidate.party_candidate[location]
                    
            # If the sender is not likely a candidate, then check for a PAC.
            
            elif match_candidate[0][1] < 70:
                
                # Find a match to the sender in the committee list.
                
                match_committee = process.extract(sender, df_committee.committee, scorer=fuzz.token_sort_ratio, limit=1)
                
                # Save it to the storage dataframe with the confidence level and the location of the PAC in the full list.
                
                result.committee_match[n] = match_committee[0][0]
                
                result.committee_confidence[n] = match_committee[0][1]
                
                # Get the party information from the committee dataframe.
                
                location = match_committee[0][2]
                
                result.party[n] = df_committee.party[location]



############
# COMMITTEES
############
# Import and clean all of the committee data.

# Read in the data from a saved location.
# Download the original file from https://www.fec.gov/data/browse-data/?tab=bulk-data.


raw_committee = pd.read_csv(
    'C:/Users/Gabriel/Desktop/FEC/2019-2020_committees/cm.txt', header=None, sep='|')

# Add a new header based on https://www.fec.gov/campaign-finance-data/committee-master-file-description/.

raw_committee.columns = ['id_committee', 'committee', 'treasurer', 'street1', 'street2', 'city', 'state',
                         'zip', 'designation', 'type', 'party', 'frequency', 'category', 'connection', 'id_candidate']

# Copy all of the information of interest (for display) into a new dataframe. The order is just more convenient for reading.

df_committee = raw_committee[['id_committee', 'committee', 'designation', 'type', 'party', 'category',
                              'frequency', 'connection', 'id_candidate', 'treasurer', 'street1', 'street2', 'city', 'state', 'zip']]

# Improve the capitalizations of a few of the variables.

df_committee = df_committee.assign(
    committee=df_committee.committee.str.title().str.replace('\'S', '\'s'), 
    connection=df_committee.connection.str.title(), 
    treasurer=df_committee.treasurer.str.title(),
    street1=df_committee.street1.str.title(),
    street2=df_committee.street2.str.title(),
    city=df_committee.city.str.title())

# Create mappings to match abbreviations to full words to improve legibility. All according to https://www.fec.gov/campaign-finance-data/committee-master-file-description/.

designations = {'A': 'Authorized by a candidate', 'B': 'Lobbyist/Registrant PAC', 'D': 'Leadership PAC',
                'J': 'Joint fundraiser', 'P': 'Principal campaign committee', 'U': 'Unauthorized'}
frequencies = {'A': 'Administratively terminated', 'D': 'Debt',
               'M': 'Monthly filer', 'T': 'Terminated', 'W': 'Waived'}
categories = {'C': 'Corporation', 'L': 'Labor organization', 'M': 'Membership organization',
              'T': 'Trade organization', 'V': 'Cooperative', 'W': 'Corporation without capital stock'}

# Additionally, scrape the committee type and party information from the FEC website.
# This uses the map_pairs() function defined above.

type_mapping = map_pairs(
    'https://www.fec.gov/campaign-finance-data/committee-type-code-descriptions/', 'types')

party_mapping = map_pairs(
    'https://www.fec.gov/campaign-finance-data/party-code-descriptions/', 'parties')

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

# Drop any committees without names.

df_committee = df_committee[df_committee.committee.notna()]

##########################
# INDIVIDUAL CONTRIBUTIONS
##########################
# Import and clean all of the data on individual contributions.

# Read the 2019-2020 individual contribution data.

raw_individuals = pd.read_csv('C:/Users/Gabriel/Desktop/FEC/2019-2020_individual-contributions/itcont.txt',
                              header=None, sep='|')

# Fix the column names to something more legible based on the variable descriptions here: https://www.fec.gov/campaign-finance-data/contributions-individuals-file-description/.

raw_individuals.columns = ['id_committee', 'amendment', 'report', 'election', 'image', 'type', 'entity', 'name_full', 'city', 'state', 'zip', 'employer',
                           'occupation', 'date', 'amount', 'id_other', 'id_transaction', 'id_report', 'memo_code', 'memo_text', 'fec_record']

# Copy only some variables of interest.

df_individuals = raw_individuals[['name_full', 'amount', 'city', 'state', 'zip', 'date', 'employer',
                                  'occupation', 'id_committee', 'amendment', 'report', 'election', 'type', 'entity', 'memo_text', 'image']]

# Improve look of employer, occupation, memo, and cities. Add the full URL to the original document image.

df_individuals = df_individuals.assign(
    city=df_individuals.city.str.title(),
    employer=df_individuals.employer.str.title(), occupation=df_individuals.occupation.str.title(), memo_text=df_individuals.memo_text.str.capitalize())

# Split the zip codes into primary and secondary ones.

individual_zips = split_zips(df_individuals.zip)

del df_individuals['zip']

df_individuals = pd.concat([df_individuals, individual_zips], axis=1)

# Replace the date column with the function defined above.

df_individuals = df_individuals.assign(
    date=df_individuals.date.apply(string_to_date))

# Make some variable values more legible with full words.
# All according to the chart here: https://www.fec.gov/campaign-finance-data/contributions-individuals-file-description/.

amendments = {'N': 'New', 'A': 'Amendment', 'T': 'Termination'}
elections = {'P': 'Primary', 'G': 'General', 'O': 'Other',
             'C': 'Convention', 'R': 'Runoff', 'S': 'Special', 'E': 'Recount'}
entities = {'CAN': 'Candidate', 'CCM': 'Candidate Committee', 'COM': 'Committee', 'IND': 'Individual',
            'ORG': 'Organization', 'PAC': 'Political Action Committee', 'PTY': 'Party Organization'}

df_individuals['amendment'] = df_individuals['amendment'].map(amendments)
df_individuals['election'] = df_individuals['election'].map(elections)
df_individuals['entity'] = df_individuals['entity'].map(entities)

# Scrape the report and transaction types from the FEC website for mapping abbreviations to full words.

report_mapping = map_pairs(
    'https://www.fec.gov/campaign-finance-data/report-type-code-descriptions/', 'report')

transaction_mapping = map_pairs(
    'https://www.fec.gov/campaign-finance-data/transaction-type-code-descriptions/', 'transaction')

# Map all of the full words.

df_individuals['report'] = df_individuals['report'].map(report_mapping)
df_individuals['type'] = df_individuals['type'].map(transaction_mapping)

# Remove invalid transactions that are either negative or positive AND correspond to a negative transaction. Use remove_invalid() as defined above.

df_individuals = remove_invalid(df_individuals)

# Clean up and expand the formatting of the names with clean_names() defined above.
# Then add it to the original dataframe and delete the name column.
# Note this will take about 45 minutes to run for all the individual donations (1.5M+ names).

individual_names = clean_names(df_individuals.name_full)

# Rename the original name column to 'name' to avoid confusing it with the cleaned names.

df_individuals = df_individuals.rename(columns={'name_full': 'name'})

df_individuals = pd.concat([df_individuals, individual_names], axis=1)

del df_individuals['name']


##############
# CANDIDATES
##############

# All candidate data from: https://www.fec.gov/data/browse-data/?tab=bulk-data

raw_candidate = pd.read_csv(
    'C:/Users/Gabriel/Desktop/FEC/2019-2020_candidates/cn.txt', header=None, sep='|')

# Rename the columns and create a separate copy of it.

raw_candidate.columns = ['id_candidate', 'candidate', 'party_candidate', 'election_year', 'election_state',
                         'race', 'district', 'incumbent', 'status', 'id_committee', 'street', 'street2', 'city', 'state', 'zip']

df_candidate = raw_candidate[:]

# Expand and improve the look of candidate names using the function clean_names() defined above.

candidate_names = clean_names(raw_candidate.candidate)

df_candidate = pd.concat([df_candidate, candidate_names], axis=1, )

del df_candidate['candidate']

# Use mappings to expand a few of the variables into full words.
# Find the corresponding info here: https://www.fec.gov/campaign-finance-data/candidate-master-file-description/

race_mapping = {'H': 'House', 'P': 'President', 'S': 'Senate'}
incumbent_mapping = {'I': 'Incumbent', 'C': 'Challenger', 'O': 'Open seat'}
status_mapping = {'C': 'Statutory candidate', 'F': 'Statutory candidate for future election',
                  'N': 'Not yet a statutory candidate', 'P': 'Statutory candidate in prior cycle'}

df_candidate['party_candidate'] = df_candidate['party_candidate'].map(
    party_mapping)
df_candidate['race'] = df_candidate['race'].map(race_mapping)
df_candidate['incumbent'] = df_candidate['incumbent'].map(incumbent_mapping)
df_candidate['status'] = df_candidate['status'].map(status_mapping)

# Redefine districts, streets, cities, and zip codes as strings.
# Don't fix zip codes because many here are not the standard five-digit ones, but three-digit (or less) abbreviations.

df_candidate['district'] = df_candidate['district'].astype(
    str).str.replace('.0', '')
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

raw_expenditures = pd.read_csv(
    'C:/Users/Gabriel/Desktop/FEC/2019-2020_committee-expenditures/oppexp.txt', header=None, sep='|')

raw_expenditures.columns = ['id_committee', 'amendment', 'year', 'type', 'image', 'line', 'form', 'schedule', 'name_full', 'city', 'state', 'zip', 'date', 'amount',
                            'election', 'purpose', 'category', 'category_description', 'memo', 'memo_text', 'entity', 'record', 'file', 'transaction', 'transaction_backref', 'empty']

# Save only variables of interest for display and merging with other datasets.

df_expenditures = raw_expenditures[['id_committee', 'name_full', 'entity', 'date', 'amount', 'purpose',
                                    'category_description', 'city', 'state', 'zip', 'type', 'election', 'memo_text', 'image']]

# Clean up the formatting of name, purpose, and city.

df_expenditures = df_expenditures.assign(
    name_full=df_expenditures.name_full.str.title(),
    purpose=df_expenditures.purpose.str.capitalize(),
    city=df_expenditures.city.str.title(),
    memo_text=df_expenditures.memo_text.str.capitalize())

# Split the zip code into primary and secondary.

expenditure_zips = split_zips(df_expenditures.zip)

del df_expenditures['zip']

df_expenditures = pd.concat([df_expenditures, committee_zips], axis=1)

# Scrape the FEC site for report expenditure type mapping.

expenditure_type_mapping = map_pairs(
    'https://www.fec.gov/campaign-finance-data/report-type-code-descriptions/', 'expenditures')

# Turn abbreviations into full words for improved legibility.

df_expenditures['entity'] = df_expenditures['entity'].map(entities)
df_expenditures['election'] = df_expenditures['election'].map(elections)
df_expenditures['type'] = df_expenditures['type'].map(expenditure_type_mapping)

# Convert the date strings to real datetime objects.

expenditure_dates = df_expenditures.date.dropna().apply(
    datetime.strptime, args=['%M/%d/%Y']).apply(datetime.date)

df_expenditures = df_expenditures.assign(date=expenditure_dates)

# Remove invalid transactions that are either negative or positive AND correspond to a negative transaction. Use remove_invalid() as defined above.

df_expenditures = remove_invalid(df_expenditures)


#####################################
# COMMITTEE-TO-COMMITTEE TRANSACTIONS
#####################################
# Data that tracks all committee-to-committee transactions.

# Read in the downloaded file and assign column names: https://www.fec.gov/campaign-finance-data/any-transaction-one-committee-another-file-description/.

raw_cc = pd.read_csv(
    'C:/Users/Gabriel/Desktop/FEC/2019-2020_committee-to-committee-transactions/itoth.txt', header=None, sep='|')

raw_cc.columns = ['id_recipient', 'amendment', 'report', 'election', 'image', 'transaction', 'entity', 'name_full', 'city', 'state',
                  'zip', 'employer', 'occupation', 'date', 'amount', 'id_other', 'id_transaction', 'file', 'memo', 'memo_text', 'fec_record']

# Save only variables of interest for display and merging with other datasets.

df_cc = raw_cc[['id_recipient', 'name_full', 'entity', 'date', 'amount', 'city',
                'state', 'zip', 'employer', 'election', 'report', 'memo_text', 'image']]

# Clean up the formatting of name, city, date, etc.

df_cc = df_cc.assign(
    city=df_cc.city.str.title(),
    date=df_cc.date.astype('str').str.replace('\.0', ''),
    zip=df_cc.zip.astype('str'),
    employer=df_cc.employer.str.title(),
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

df_cc = df_cc.assign(date=df_cc.date.apply(string_to_date))

# Remove invalid transactions that are either negative or positive AND correspond to a negative transaction. Use remove_invalid() as defined above.

df_cc = remove_invalid(df_cc)

# Rename the 'name_full' column to 'recipient' (since only the former works in remove_invalid()).

df_cc = df_cc.rename(columns={'name_full': 'sender'})

df_cc = df_cc.assign(sender=df_cc.sender.str.title())

# Turn candidate and individual names in the 'sender' column into a usable format.

cc_people = df_cc[df_cc.entity.isin(['Individual', 'Candidate'])]

# Filter out one listing that's for a PAC, not for an individual (Donald J. Trump For President, Inc.).

cc_people = cc_people[~cc_people.sender.str.contains('Inc\.', na=False)]

# Clean the names of the candidate and individual entities in the candidate transaction list.
# Note that this takes a few minutes to run.

cc_names = clean_names(cc_people.sender)

df_cc = pd.merge(df_cc, cc_names, how='left', left_index=True, right_index=True)

# Drop any transactions without a sender name.

df_cc = df_cc[df_cc.sender.notna()]

###########################
# DATA CLEANING AND MERGING
###########################

# Merge in the committee and individual names instead of using just ids.

committees = df_committee[['id_committee', 'committee']]

candidates = df_candidate[['id_candidate', 'first_last']]

# Add in the name of the sending committee.

df_cc = pd.merge(df_cc, committees, how='left', left_on='sender', right_on='committee')

del df_cc['committee']

df_cc = df_cc.rename(columns={'id_committee': 'id_sender'})

# Add in the name of the recipient committee.

df_cc = pd.merge(df_cc, committees, how='left', left_on='id_recipient', right_on='id_committee')

del df_cc['id_committee']

df_cc = df_cc.rename(columns={'committee': 'recipient'})

# Add in the candidate id for transactions from individuals.

df_cc = pd.merge(df_cc, candidates, how='left', left_on='first_last', right_on='first_last')

# Add in the recipient committee name to the individual donations.

df_individuals = pd.merge(df_individuals, committees, how='left', on='id_committee')

df_individuals = df_individuals.rename(columns={'committee': 'recipient'})

# Add in the committee name to the expenditures.

df_expenditures = pd.merge(df_expenditures, committees, how='left', on='id_committee')

# Add the corresponding committee name to the candidate list.

df_candidate = pd.merge(df_candidate, committees, how='left', on='id_committee')


###################
# PARTY AFFILIATION
###################
# Determine the party affiliation of committee-to-committee transactions (based on candidate names or PAC affiliations).
# Determine PAC affiliation "scores" based on the number of transactions in different party categories.

# Fill all party affiliations with "Uknown" if the field is blank.

df_committee = df_committee.assign(party=df_committee.party.fillna(value='Unknown'))
df_candidate = df_candidate.assign(party_candidate=df_candidate.party_candidate.fillna(value='Unknown'))

# Determine the party affiliations of specific transfers based on only unique recipients (4,244 total, to save time).

party_recipients = identify_party(df_cc.drop_duplicates(subset='recipient'))

parties = party_recipients[['party', 'recipient']]

# Map party affiliation onto every PAC transaction (in df_cc) based on recipient.

df_cc = pd.merge(df_cc, parties, how='left', on='recipient')

# Turn no party listed into 'Unknown,' just for consistency.

df_cc['party'] = df_cc['party'].replace(to_replace='None', value='Unknown')



# Save the five finalized dataframes.

df_committee.to_pickle('C:/Users/Gabriel/Desktop/FEC/cleaned_data/df_committee')
df_individuals.to_pickle('C:/Users/Gabriel/Desktop/FEC/cleaned_data/df_individuals')
df_expenditures.to_pickle('C:/Users/Gabriel/Desktop/FEC/cleaned_data/df_expenditures')
df_candidate.to_pickle('C:/Users/Gabriel/Desktop/FEC/cleaned_data/df_candidate')
df_cc.to_pickle('C:/Users/Gabriel/Desktop/FEC/cleaned_data/df_cc')
