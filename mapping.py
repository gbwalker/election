##############
# MAPPING DATA
##############

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
import requests
import re
from bs4 import BeautifulSoup
import json
import folium
from folium.plugins import MarkerCluster
import os
import webbrowser
# from bokeh.plotting import figure, show, output_file
# from bokeh.tile_providers import get_provider, Vendors

pd.set_option('expand_frame_repr', False)
pd.set_option('display.max_columns', 40)

# Read in the pickled dataframes from process_data.py.

df_committee = pd.read_pickle('C:/Users/Gabriel/Desktop/FEC/cleaned_data/df_committee')
df_individuals = pd.read_pickle('C:/Users/Gabriel/Desktop/FEC/cleaned_data/df_individuals')
df_expenditures = pd.read_pickle('C:/Users/Gabriel/Desktop/FEC/cleaned_data/df_expenditures')
df_candidate = pd.read_pickle('C:/Users/Gabriel/Desktop/FEC/cleaned_data/df_candidate')
df_cc = pd.read_pickle('C:/Users/Gabriel/Desktop/FEC/cleaned_data/df_cc')
zips = pd.read_pickle('C:/Users/Gabriel/Desktop/FEC/cleaned_data/zips')
zip_points = pd.read_pickle('C:/Users/Gabriel/Desktop/FEC/cleaned_data/zip_points')

############
# SHAPEFILES
############
# Details about how to use shapefiles here: https://www.earthdatascience.org/workshops/gis-open-source-python/intro-vector-data-python/.

# Read the full ZIP shapefile.

sf_zips = gpd.read_file('C:/Users/Gabriel/Desktop/FEC/2018-zips/tl_2018_us_zcta510.shp')

# Clean the column names for easier readings.

sf_zips.columns = sf_zips.columns.str.lower()

# Do the same for the state shapefiles: https://catalog.data.gov/dataset/tiger-line-shapefile-2017-nation-u-s-current-state-and-equivalent-national.

sf_states = gpd.read_file('C:/Users/Gabriel/Desktop/FEC/2017-states/tl_2017_us_state.shp')

sf_states.columns = sf_states.columns.str.lower()

sf_states = sf_states[['name', 'geometry']]

# Remove extra states that are not the contiguous 50 or Alaska/Hawaii.

sf_states = sf_states[~sf_states.name.isin(['United States Virgin Islands', 'Commonwealth of the Northern Mariana Islands', 'Guam', 'American Samoa', 'Puerto Rico'])]

# Scrape the list of state abbreviations from the web.

url = 'https://www.50states.com/abbreviations.htm'

raw_states = requests.get(url).text
soup_states = BeautifulSoup(raw_states)
clean_soup = soup_states.find_all('td')

# Save all the tags into a dataframe and turn them into readable strings.

state_abbvs = pd.DataFrame(pd.Series(clean_soup), columns=['tag'])

state_abbvs = state_abbvs.assign(tag=state_abbvs.tag.astype('str'))

# Iterate through all the tags and collect the corresponding abbreviations.

state_abbreviations = pd.DataFrame(index=range(len(state_abbvs)), columns=['abbreviation', 'state'])

for n in range(len(state_abbvs.values)):
        
    if n % 2 == 0:
        
        state_abbreviations.state[n] = re.search(r'>[\w\s]+<', state_abbvs.tag[n])[0].replace('>', '').replace('<', '')
        
    if n % 2 == 1:
        
        state_abbreviations.abbreviation[n - 1] = re.search(r'>[\w\s]+<', state_abbvs.tag[n])[0].replace('>', '').replace('<', '')

# Drop empty rows and save as a dictionary for mapping.

state_abbreviations = state_abbreviations.dropna()

state_mapping = dict(zip(state_abbreviations.abbreviation, state_abbreviations.state))

# Map state abbreviations to names in both df_cc and df_individuals.

df_cc = df_cc.assign(state_ab=df_cc.state)

df_individuals = df_individuals.assign(state_ab=df_individuals.state)

df_cc = df_cc.assign(state=df_cc['state'].map(state_mapping))

df_individuals = df_individuals.assign(state=df_individuals['state'].map(state_mapping))

# See the full extent of the polygons: sf.total_bounds
# See the CRS (coordinate reference system): sf.crs
# See which polygons are noncontiguous: sf.geom_type
# Plot some of the zips: zips.sample(200).plot()

# Select only the zip codes and their polygons.

zips = sf_zips[['geoid10', 'geometry']]

zips.columns = ['zip', 'geometry']

zips = zips.assign(prefix=None)

# Add in a column of the prefixes (first three digits). Note that .apply() won't work because re.search() returns a list.

for n in range(len(zips.zip)):
    
    zips.prefix[n] = re.search(r'(\d\d\d)', zips.zip[n])[0]

# Plot just the zip codes in the committee list.
# zips[zips.zip.isin(df_committee.zip.values)].plot()

# Save the state shapes.

sf_states.to_pickle('C:/Users/Gabriel/Desktop/FEC/cleaned_data/sf_states')

###########
# ZIP CODES
###########
# Scrape zip code prefixes from Wikipedia to match zip shapefiles with states.

url = 'https://en.wikipedia.org/wiki/List_of_ZIP_Code_prefixes'

raw_wiki = requests.get(url).text
soup_wiki = BeautifulSoup(raw_wiki)
clean_soup = soup_wiki.find_all('td')

# Save all the tags into a dataframe and turn them into readable strings.

zips_wiki = pd.DataFrame(clean_soup, columns=['tag'])

zips_wiki = zips_wiki.assign(tag=zips_wiki.tag.astype('str'))

# Create a new dataframe for storing zip prefixes and locations.

zip_prefixes = pd.DataFrame(index=range(len(zips_wiki)), columns=['prefix', 'state', 'city'])

# Iterate through all of the captured tags and grab the prefix (three consecutive numbers) and location.

for n in range(len(zips_wiki.values)):

    # Capture the prefix first if there is a valid set of three numbers.

    if type(re.search(r'(>\d\d\d)', zips_wiki.tag[n])) != type(None):

        zip_prefixes.prefix[n] = re.search(r'(>\d\d\d)', zips_wiki.tag[n])[0].replace('>', '')
    
    # Capture the state associated with each zip prefix only if there is a valid state.
    
    if type(re.search(r'(title="\w+[\s-]?(\w+)?[\s-]?\w+?)', zips_wiki.tag[n])) != type(None):
        
        zip_prefixes.state[n] = re.search(r'(title="\w+[\s-]?(\w+)?[\s]?(\w+)?[\s]?(\w+)?)', zips_wiki.tag[n])[0].replace('title="', '').strip()

    # Capture a specific city if the state field is valid.
    
    if type(zip_prefixes.state[n]) != type(np.NaN):
        
        pattern = r'\w+(\s)?(\w+)?(\s)?(\w+)?, ' + zip_prefixes.state[n]
        
        delete_pattern = ', ' + zip_prefixes.state[n]
        
        # Make sure that there is a valid city.
        
        if type(re.search(r'(/a.+\n)', zips_wiki.tag[n])) != type(None):
            
            # Make an initial slice of the characters to remove the first link.
        
            initial_slice = re.search(r'(/a.+\n)', zips_wiki.tag[n])[0]
        
            # Make sure there is a valid city.
        
            if type(re.search(r'(title="\w+\s?(\w+)?\s?(\w+)?\s?(\w+)?)', initial_slice)) != type(None):
        
                zip_prefixes.city[n] = re.search(r'(title="\w+\s?(\w+)?\s?(\w+)?\s?(\w+)?)', initial_slice)[0].replace('title="', '')

# Merge in the state and city information based on the zip code prefix.
# First convert the prefixes to strings so they match in both dataframes.

zip_prefixes = zip_prefixes.assign(prefix=zip_prefixes.prefix.astype('str'))

zips = pd.merge(zips, zip_prefixes, how='left', on='prefix')

# Add a centroid to each zip code area.

zips = zips.assign(center=zips.geometry.centroid)

# Reclassify Washington, DC, areas and centers correctly (marked both 'city' and 'state' as 'Washington').

dc = zips[(zips.state == 'Washington') & (zips.city == 'Washington')]

dc = dc.assign(state='District of Columbia')

zips.loc[dc.index] = dc

# Make a separate list of just the center points.

zip_points = zips[['zip', 'state', 'city', 'center']]

# Save the zip shapefiles along with the cleaned data.

zips.to_pickle('C:/Users/Gabriel/Desktop/FEC/cleaned_data/zips')

zip_points.to_pickle('C:/Users/Gabriel/Desktop/FEC/cleaned_data/zip_points')

###########################
# TEST PLOTTING WITH FOLIUM
###########################

# Get donations and zip codes just for Pennsylvania.

pa_zips = zips[zips.state == 'Pennsylvania']

pa_zips = pa_zips[['zip', 'geometry']]

df_pa = df_individuals[df_individuals['state'] == 'PA'][['amount', 'zip']]

# Find total donation amounts by zip code in order to plot a choropleth.

df_pa = df_pa.groupby('zip').sum()

df_pa.reset_index(level=0, inplace=True)

# Add donation amounts of zero to each zip code where no donation history exists in a new dataframe.

zero_zips = pa_zips.zip[~pa_zips.zip.isin(df_pa.zip)]

df_zeros = pd.DataFrame(data=zero_zips, columns=['zip'])

df_zeros = df_zeros.assign(amount=0)

# Combine the zeros with the original donation data.

df_pa = pd.concat([df_pa, df_zeros])

# Just get a few zip codes to test.

df_pa_tiny = df_pa.sample(100)

# Delete zip codes that are not in both the shapefiles and donation records.

common_zips = set(df_pa.zip).intersection(set(pa_zips.zip))

df_pa = df_pa[df_pa.zip.isin(common_zips)]

pa_zips = pa_zips[pa_zips.zip.isin(common_zips)]

# Test plot the PA zip code areas as GeoJSONs, without any associated data.
# See the structure of the GeoJSON with: json_zips.get('features')[0]

json_zips = pa_zips.__geo_interface__

json_tiny = pa_zips[pa_zips.zip.isin(df_pa_tiny.zip)].__geo_interface__

# Create the map.

m = folium.Map(location=[48, -102],
               tiles='cartodbpositron',
               zoom_start=3)

# Add a choropleth layer.

folium.Choropleth(
    geo_data=json_tiny,
    name='Donations',
    data=df_pa,
    columns=['zip', 'amount'],
    key_on='feature.properties.zip',
    fill_color='BuPu',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='Donation amount ($)'
    ).add_to(m)

folium.LayerControl().add_to(m)

m.save('C:/Users/Gabriel/Desktop/map.html')

webbrowser.open('C:/Users/Gabriel/Desktop/map.html')

############################
# TEST PLOTTING CERTAIN PACS
############################

# This function selects a PAC at random and displays all the donation data associated with it. Similar to what the real app should do to see if the zip code areas are too tiny to display...

def map_pac():
    
    # Select a PAC at random.
    
    # pac = df_cc[df_cc.entity != 'Individual']
    
    pac = df_individuals.drop_duplicates(subset='recipient').recipient.sample(1).iloc[0]
    
    # Some example PACs that are more challenging.
    # pac = 'Nextera Energy, Inc. Political Action Committee'
    # pac = 'Pac To The Future'
    
    print(pac)
    
    # Filter transactions for just the ones that the PAC sent.
    
    df = df_individuals[df_individuals.recipient == pac][['state', 'zip', 'amount']]
    
    # Get the total by each zip code to determine the marker size on the map.
    
    zip_totals = df.groupby('zip').sum().reset_index()
    
    # Get the zip codes and states from which individuals have contributed OR where the PAC has sent funds.
    
    pac_zip_points = zip_points[zip_points.zip.astype('int').isin(list(df.zip.values.astype('int')))]
    
    states = df_individuals[df_individuals.recipient == pac].state.drop_duplicates()
    
    # Merge in the zip code amounts that determine circle size.
    
    if not pac_zip_points.zip.empty:
    
        pac_zip_points = pd.merge(pac_zip_points, zip_totals, how='left', on='zip')
        
        # Fill null donation amounts with a 1.
        
        pac_zip_points = pac_zip_points.fillna(value={'amount': 1})
        
    # If no zip code points exist, use the centroids of each of the states.
    
    if pac_zip_points.zip.empty:
        
        pac_zip_points = sf_states[sf_states.name.isin(states)].assign(geometry=sf_states.geometry.centroid)
        
        # Also add in a set contribution amount for the zip code.
        
        pac_zip_points = pac_zip_points.assign(amount=1)
    
        pac_zip_points.columns = ['name', 'center', 'amount']
    
    # Sum donations by state for creating a choropleth.
    
    df = df.groupby('state').sum().reset_index()
    
    print(df)
    
    # Also get state polygons for the relevant transactions.
    
    pac_states = sf_states[sf_states.name.isin(df.state)]
    
    # Map the state areas with a choropleth.
    
    json_states = pac_states.__geo_interface__

    # Create the map.

    m = folium.Map(location=[39.5, -98.35],
                tiles='cartodbpositron',
                zoom_start=5,
                min_zoom=4)

    # Add a choropleth layer for the state.

    folium.Choropleth(
        geo_data=json_states,
        name='Donations',
        data=df,
        columns=['state', 'amount'],
        key_on='feature.properties.name',
        fill_color='YlGn',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='State-wide donation amount ($)'
    ).add_to(m)
    
    # Add transparent popup donation amounts for each state.
        
    donation_overlay = pd.merge(pac_states, df, how='left', left_on='name', right_on='state')[['name', 'geometry', 'amount']]
    
    # Make sure the amounts display as formatted strings rather than just integers.
    
    donation_overlay = donation_overlay.assign(amount='$' + donation_overlay.apply(lambda x: "{:,}".format(x['amount']), axis=1))
    
    folium.GeoJson(
        data=donation_overlay.to_json(),
        name='State donations',
        show=True,
        style_function=lambda feature: {
            # 'fillColor': 'green',
            'color': 'black',
            'weight': 0.25,
            'fillOpacity': 0
        },   
        # highlight_function=lambda x: {'weight': 3, 
        #                               'color': 'white',
        #                               'fillOpacity': 0.5},
        tooltip=folium.features.GeoJsonTooltip(
            fields=['name', 'amount'],
            aliases=['State:', 'Contributions:'],
            style=''
        )
    ).add_to(m)

    # Add points to the map representing where donations are from.
    # Start with a marker cluster.
    
    cluster = MarkerCluster(
        options={'maxClusterRadius': 10, 'circleFootSeparation': 60}
        ).add_to(m)
    
    for n in range(len(pac_zip_points)):
        
        # Check for a blank city.
                
        if str(pac_zip_points.city.iloc[n]) == 'nan':
        
            city = ''
            
        else:
            
            city = pac_zip_points.city.iloc[n] + ', '
        
        # Plot the points.
        
        folium.CircleMarker(
            location=(pac_zip_points.center.iloc[n].y, pac_zip_points.center.iloc[n].x),
            tooltip=('$' + ('{:,}'.format(pac_zip_points.amount.iloc[n])) + ' of contributions' + '<br/>' + city + pac_zip_points.state.iloc[n] + '<br/>' + 'Zip: ' + pac_zip_points.zip.iloc[n]),
            radius=np.log(pac_zip_points.amount.iloc[n])*4,
            color='green',
            fill=True,
            fill_color='green'
        ).add_to(cluster)

    # Add different colored marks for transactions sent by the PAC, not received.

    # Identify transactions of interest based on recipient zip codes.
    
    df_sent = df_cc[df_cc.sender == pac][['city', 'state', 'zip', 'amount', 'date', 'recipient', 'image']]

    # If there are transactions, proceed.
    
    if not df_sent.zip.empty:

        pac_zip_sent = zip_points[zip_points.zip.astype('int').isin(list(df_sent.zip.values.astype('int')))]

        # Add the center point to the information about the received transaction.
        
        df_sent = pd.merge(df_sent, pac_zip_sent[['zip', 'center']], how='left', on='zip')

        # Plot all the sent transactions.
        
        for n in range(len(df_sent)):
            
            # If no center point exists, assign it one based on the city and state.
            
            if str(df_sent.center.iloc[n]) == 'nan':
                
                df_sent.center.iloc[n] = zip_points[(zip_points.state == df_sent.state.iloc[n]) & (zip_points.city == df_sent.city.iloc[n])].center.iloc[0]
            
            # Also check for a blank city.
            
            if str(df_sent.city.iloc[n]) == 'nan':
            
                city = ''
                
            else:
                
                city = df_sent.city.iloc[n] + ', '
            
            # Then add the marker.
            
            folium.CircleMarker(
                location=(df_sent.center.iloc[n].y, df_sent.center.iloc[n].x),
                tooltip=('$' + ('{:,}'.format(df_sent.amount.iloc[n])) + ' transferred to' + '<br/>' + df_sent.recipient.iloc[n] + '<br/>' + city + df_sent.state.iloc[n] + '<br/>' + 'Zip: ' + df_sent.zip.iloc[n]),
                radius=np.log(df_sent.amount.iloc[n])*4,
                color='red',
                fill=True,
                fill_color='red'
            ).add_to(cluster)

    return m

# For saving the map output.

m.save('C:/Users/Gabriel/Desktop/map.html')

###############
# FULL PLOTTING
###############
# Plotting all 3,000 zip codes with associated donations. Don't plot any tracts with no donations.

# Get every zip code.

all_zips = zips[['zip', 'geometry']]

# Find total donations by zip code.

df_donations = df_individuals[['zip', 'amount']]

df_donations = df_donations.groupby('zip').sum()

df_donations.reset_index(level=0, inplace=True)

# Add donation amounts of zero to each zip code where no donation history exists in a new dataframe.
# zero_all_zips = all_zips.zip[~all_zips.zip.isin(df_donations.zip)]
# df_zeros = pd.DataFrame(data=zero_all_zips, columns=['zip'])
# df_zeros = df_zeros.assign(amount=0)
# Combine the zeros with the original donation data.
# df_donations = pd.concat([df_donations, df_zeros])

# Delete zip codes that are not in both the shapefiles and donation records.

common_zips = set(df_donations.zip).intersection(set(all_zips.zip))

df_donations = df_donations[df_donations.zip.isin(common_zips)]

all_zips = all_zips[all_zips.zip.isin(common_zips)]

# Define percentile bins for donation amounts.

bins = list(df_donations.amount.quantile([0, 0.25, 0.5, 0.75, 1]))

# Create a GeoJSON with all the zip code polygons.

json_zips_all = all_zips.__geo_interface__

# Create the map.

m = folium.Map(location=[48, -102],
               tiles='cartodbpositron',
               zoom_start=3)

# Add a choropleth layer.

folium.Choropleth(
    geo_data=json_zips_all,
    name='Donations',
    data=df_donations,
    columns=['zip', 'amount'],
    key_on='feature.properties.zip',
    fill_color='BuPu',
    fill_opacity=0.7,
    line_opacity=0.3,
    legend_name='Donation amount ($)',
    bins=bins,
    smooth_factor=1.0,
    highlight=True
    ).add_to(m)

folium.LayerControl().add_to(m)

m.save('C:/Users/Gabriel/Desktop/full_map.html')


#######
# NOTES
#######

# Test formatting for a GeoJSON dictionary.

test = {"type":"FeatureCollection","features":[{"type":"Feature","id":"AL","properties":{"name":"Alabama"},"geometry":{"type":"Polygon","coordinates":[[[-87.359296, 35.00118],[-85.606675,34.984749],[-85.431413,34.124869]]]}}]}

### Template below.

url = 'https://raw.githubusercontent.com/python-visualization/folium/master/examples/data'
state_geo = f'{url}/us-states.json'
state_unemployment = f'{url}/US_Unemployment_Oct2012.csv'
state_data = pd.read_csv(state_unemployment)

folium.Choropleth(
    geo_data=state_geo,
    name='choropleth',
    data=state_data,
    columns=['State', 'Unemployment'],
    key_on='feature.id',
    fill_color='YlGn',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='Unemployment Rate (%)'
).add_to(m)

# Turn dates to strings.

df_individuals = df_individuals.assign(date=df_individuals.date.astype('str'))

# Merge the zips with the committee list to map the committee locations.

merged_individuals = zips.merge(df_individuals, on='zip')

# Turn the individual donations with associated areas to a json.

json_individuals = json.loads(merged_individuals.to_json())

json_data = json.dumps(json_individuals)

# Input GeoJSON source that contains features for plotting.

geosource = GeoJSONDataSource(geojson = json_data)

# Define a hue palette and reverse the order.

palette = brewer['YlGnBu'][8]

palette = palette[::-1]

color_mapper = LinearColorMapper(palette = palette, low = 0, high = 40)

# Try patches.

p = figure(title = 'Test plot', plot_height = 600 , plot_width = 600, toolbar_location = None)

p.patches('xs','ys',
          source = geosource, 
          fill_color = {'field' :'per_cent_obesity', 'transform' : color_mapper}, 
          line_color = 'black', 
          line_width = 0.25, 
          fill_alpha = 1)

# Show the plot.

show(p)

# Make sure the polygons are plottable.
# test = test.assign(geometry=gpd.GeoSeries(test.geometry))

# ZIP shapefiles: https://catalog.data.gov/dataset/tiger-line-shapefile-2015-2010-nation-u-s-2010-census-5-digit-zip-code-tabulation-area-zcta5-na
# City and zip shapes: https://www.census.gov/cgi-bin/geo/shapefiles/index.php.

# Use this URL to find original images AND committee pages. Just append the image number or committee ID: https://docquery.fec.gov/cgi-bin/fecimg/?