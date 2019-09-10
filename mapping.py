import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
import requests
import re
from bs4 import BeautifulSoup
import json
# import earthpy as et
import folium
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

######################
# PLOTTING WITH FOLIUM
######################

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

# The donation data has zip codes 15275 and 19421 but the shapefiles do not, so those records must be deleted.

df_pa = df_pa[~df_pa.zip.isin(['15275', '19421'])]

# Test plot the PA zip code areas as GeoJSONs, without any associated data.
# See the structure of the GeoJSON with: json_zips.get('features')[0]

json_zips = pa_zips.__geo_interface__

json_tiny = pa_zips[pa_zips.zip.isin(df_pa_tiny.zip)].__geo_interface__

# Create the map.

m = folium.Map(location=[48, -102],
               tiles='Mapbox Bright',
               zoom_start=3)

# Add a choropleth layer.

folium.Choropleth(
    geo_data=json_zips,
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


#######
# NOTES
#######

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
