import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
import json
# import earthpy as et
from bokeh.io import output_notebook, show, output_file
from bokeh.plotting import figure
from bokeh.models import GeoJSONDataSource, LinearColorMapper, ColorBar
from bokeh.palettes import brewer


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

# See the full extent of the polygons: sf.total_bounds
# See the CRS (coordinate reference system): sf.crs
# See which polygons are noncontiguous: sf.geom_type
# Plot some of the zips: sf.sample(200).plot()

# Select only the zip codes and their polygons.

zips = sf_zips[['geoid10', 'geometry']]

zips.columns = ['zip', 'geometry']

# Plot just the zip codes in the committee list.
# zips[zips.zip.isin(df_committee.zip.values)].plot()

#############
# INDIVIDUALS
#############

# Turn dates to strings.

df_individuals = df_individuals.assign(date=df_individuals.date.astype('str'))

# Merge the zips with the committee list to map the committee locations.

merged_individuals = zips.merge(df_individuals, on='zip')

# Turn the individual donations with associated areas to a json.

json_individuals = json.loads(merged_individuals.to_json())

json_data = json.dumps(json_individuals)

##########
# PLOTTING
##########

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
