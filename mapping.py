import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
import os
# import earthpy as et

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

sf = gpd.read_file('C:/Users/Gabriel/Desktop/FEC/2018-zips/tl_2018_us_zcta510.shp')

# Clean the column names for easier readings.

sf.columns = sf.columns.str.lower()

# Do the same for the state shapefiles: https://catalog.data.gov/dataset/tiger-line-shapefile-2017-nation-u-s-current-state-and-equivalent-national.

sf_states = gpd.read_file('C:/Users/Gabriel/Desktop/FEC/2017-states/tl_2017_us_state.shp')

sf_states.columns = sf_states.columns.str.lower()

sf_states = sf_states[['name', 'geometry']]

# See the full extent of the polygons: sf.total_bounds
# See the CRS (coordinate reference system): sf.crs
# See which polygons are noncontiguous: sf.geom_type
# Plot some of the zips: sf.sample(200).plot()

# Select only the zip codes and their polygons.

zips = sf[['geoid10', 'geometry']]

zips.columns = ['zip', 'geometry']

# Plot just the zip codes in the committee list.
# zips[zips.zip.isin(df_committee.zip.values)].plot()

# Merge the zips with the committee list to map the committee locations.

test = zips.merge(df_individuals, on='zip')

# Make sure the polygons are plottable.

test = test.assign(geometry=gpd.GeoSeries(test.geometry))


# ZIP shapefiles: https://catalog.data.gov/dataset/tiger-line-shapefile-2015-2010-nation-u-s-2010-census-5-digit-zip-code-tabulation-area-zcta5-na
# City and zip shapes: https://www.census.gov/cgi-bin/geo/shapefiles/index.php.
