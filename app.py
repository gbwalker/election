##########
# DASH APP
##########
# See https://dash.plot.ly/ for details.
# Great examples for mapping: https://github.com/plotly/dash-sample-apps/tree/master/apps/dash-opioid-epidemic
# https://github.com/plotly/dash-sample-apps/tree/master/apps/dash-oil-and-gas

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import numpy as np
import pandas as pd
import folium
import json
import pathlib
from map_pac import map_pac

######
# DATA
######

# Identify the data folder and relative paths to it.
# PATH = pathlib.Path(__file__).parent
# DATA_PATH = PATH.joinpath('data').resolve()

# Load the pickled data.
# zips = pickle.load(open(DATA_PATH.joinpath('zips'), 'rb'))

df_committee = pd.read_pickle('data/df_committee')
df_individuals = pd.read_pickle('C:/Users/Gabriel/Desktop/FEC/cleaned_data/df_individuals')
df_cc = pd.read_pickle('C:/Users/Gabriel/Desktop/FEC/cleaned_data/df_cc')
zip_points = pd.read_pickle('C:/Users/Gabriel/Desktop/FEC/cleaned_data/zip_points')
state_abbreviations = pd.read_pickle('C:/Users/Gabriel/Desktop/FEC/cleaned_data/state_abbreviations')
sf_states = pd.read_pickle('C:/Users/Gabriel/Desktop/FEC/cleaned_data/sf_states')

# df_expenditures = pd.read_pickle('C:/Users/Gabriel/Desktop/FEC/cleaned_data/df_expenditures')
# df_candidate = pd.read_pickle('C:/Users/Gabriel/Desktop/FEC/cleaned_data/df_candidate')
# zips = pd.read_pickle('C:/Users/Gabriel/Desktop/FEC/cleaned_data/zips')

# Create a dictionary list of choices to use in the dropdown menu.

pac_choices = list(df_individuals.drop_duplicates(subset='recipient').sort_values(by='recipient').apply(lambda x: {'label': x['recipient'], 'value': x['recipient']}, axis='columns'))

markdown_text = '''
### Dash and Markdown!!

Dash apps can be written in Markdown.
Dash uses the [CommonMark](http://commonmark.org/)
specification of Markdown.
Check out their [60 Second Markdown Tutorial](http://commonmark.org/help/)
if this is your first introduction to Markdown!
'''

#######
# STYLE
#######
# Use CSS from an external source. See details here about customization: https://dash.plot.ly/external-resources.
# See HTML components: https://dash.plot.ly/dash-html-components.

style = ['C:/Users/Gabriel/Documents/Code/Python/repos/election/style.css']

# Custom colors.

colors = {
    'background': '#ffffff',
    'text': '#7FDBFF'
}

###########
# FUNCTIONS
###########

# generate_table() displays an HTML table from a Pandas dataframe.

def generate_table(dataframe, max_rows=5):
    return html.Table(
        
        # Header.
        
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        # Body.
        
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )

################
# USER INTERFACE
################

# See the core components gallery for input features... https://dash.plot.ly/dash-core-components.

app = dash.Dash(__name__, external_stylesheets=style)

app.layout = html.Div(
    id='root',
    children=[
        
        html.Div(id='output-container'),
    
        html.Div(
            id='header',
            children=[
                html.Hr(),
                dcc.Dropdown(
                    id='pac-input-box',
                    options=pac_choices,
                    multi=False,
                    clearable=False,
                    value="Hallmark Cards Pac"
                )
            ],
        ),
        
        html.Hr(),
                                        
        html.Div(
            id='app-container',
            children=[
                html.Div(
                    id='left-column',
                    children=[
                        
                        html.P('Here is another paragraph description.', id='map-title'),
                        
                        # Map container using an iFrame.
                        
                        html.Div(id='pac-map'),
                    ],
                ),
                html.Div(
                    id='graph-container',
                    children=[
                        html.P(id='chart-selector', children='Select chart:'),
                        dcc.Dropdown(
                            options=[
                                {
                                    'label': 'Histogram of total number of deaths (single year)',
                                    'value': 'show_absolute_deaths_single_year',
                                }
                            ],
                            value='show_death_rate_single_year',
                            id='chart-dropdown',
                        ),
                        dcc.Graph(
                            id='selected-data',
                            figure=dict(
                                data=[dict(x=0, y=0)],
                                layout=dict(
                                    paper_bgcolor='#F4F4F8',
                                    plot_bgcolor='#F4F4F8',
                                    autofill=True,
                                    margin=dict(t=75, r=50, b=100, l=50),
                                ),
                            ),
                        ),
                    ],
                ),
            ],
        ),
    ],
)
                
#                 html.H4(children='US Agriculture Exports (2011)'), 
                
#                 generate_table(df_candidate),
                
#                 html.Hr(),
                
#                 # Sample Markdown text.
                
#                 dcc.Markdown(children=markdown_text),
                
#                 html.Hr(),
                
#                 # A reactive text box.
                
#                 dcc.Input(id='my-id', value='initial value', type='text'),
                
#                 html.Div(id='my-div')
#             ]
#         ) 
#     ])

###################
# REACTIVE ELEMENTS
###################

# A reactive text box. The functional component (i.e., function) that translates the input property into the output property is directly below.

@app.callback(
    Output(component_id='output-container', component_property='children'),
    [Input(component_id='pac-input-box', component_property='value')]
)
def update_output_div(input_value):
    
    return html.H1(children=input_value.upper())

@app.callback(
    Output(component_id='pac-map', component_property='children'),
    [Input(component_id='pac-input-box', component_property='value')]
)
def update_map(input_value):
    
    map_pac(input_value, df_individuals, zip_points, sf_states, state_abbreviations, df_cc)
    
    return html.Iframe(srcDoc=open('map.html', 'r').read(), width='60%', height='600')

# def update_map(input_value):
    
#     # Use the PAC the user has selected.
    
#     pac = input_value

#     ###############
#     # PAC DONATIONS
#     ###############
    
#     # Filter transactions for just the ones that the PAC sent.
#     # Also delete any null values.
    
#     df = df_individuals[df_individuals.recipient == pac][['first_last', 'city', 'state', 'zip', 'amount', 'date', 'image']].dropna(axis='rows')
     
#     # Get the zip codes and states from which individuals have contributed OR where the PAC has sent funds.
    
#     pac_zip_points = zip_points[zip_points.zip.astype('int').isin(list(df.zip.values.astype('int')))].dropna(axis='rows')[['zip', 'center']]
    
#     states = df_individuals[df_individuals.recipient == pac].state.drop_duplicates().dropna(axis='rows')
    
#     # Merge the full donation data with the zip code center points.
    
#     if not pac_zip_points.zip.empty:
    
#         df = pd.merge(df, pac_zip_points, how='left', on='zip')
        
#         # Delete null donation amounts.
        
#         df = df.dropna(axis='rows')
        
#     # If no zip code points exist, use the centroids of each of the states.
    
#     if pac_zip_points.zip.empty:
        
#         pac_zip_points = sf_states[sf_states.name.isin(states)].assign(geometry=sf_states.geometry.centroid)
        
#         # Merge in the center points by state.
        
#         df = pd.merge(df, pac_zip_points, how='left', on='state')
    
#     # Sum donations by state for creating a choropleth.
    
#     df_state_totals = df.groupby('state').sum().reset_index()[['state', 'amount']]
    
#     # Also get state polygons for the relevant transactions.
    
#     pac_states = sf_states[sf_states.name.isin(df.state)]
    
#     # Map the state areas with a choropleth.
    
#     json_states = pac_states.__geo_interface__

#     # Create a state mapping for abbreviations.
    
#     state_mapping = dict(zip(state_abbreviations.state, state_abbreviations.abbreviation))

#     ### Create the map.

#     m = folium.Map(
#         location=[39.5, -98.35],
#         tiles=None,
#         zoom_start=5,
#         min_zoom=4,
#         prefer_canvas=True
#         )
    
#     folium.TileLayer(
#         tiles='cartodbpositron',
#         min_zoom=4,
#         name='PAC donations by state'
#     ).add_to(m)

#     # Add a choropleth layer for the state.

#     folium.Choropleth(
#         geo_data=json_states,
#         name='Donations',
#         data=df_state_totals,
#         columns=['state', 'amount'],
#         key_on='feature.properties.name',
#         fill_color='YlGn',
#         fill_opacity=0.7,
#         line_opacity=0.2,
#         legend_name='State-wide donations ($)',
#         control=False
#     ).add_to(m)
    
#     # Add transparent popup donation amounts for each state.
        
#     donation_overlay = pd.merge(pac_states, df_state_totals, how='left', left_on='name', right_on='state')[['name', 'geometry', 'amount']]
    
#     # Make sure the amounts display as formatted strings (dollar sign + comma) rather than just integers.
    
#     donation_overlay = donation_overlay.assign(amount='$' + donation_overlay.apply(lambda x: "{:,}".format(x['amount']), axis=1))
    
#     folium.GeoJson(
#         data=donation_overlay.to_json(),
#         name='State donations',
#         show=True,
#         control=False,
#         style_function=lambda feature: {
#             'color': 'black',
#             'weight': 0.25,
#             'fillOpacity': 0
#         },   
#         tooltip=folium.features.GeoJsonTooltip(
#             fields=['name', 'amount'],
#             aliases=['State:', 'Contributions:'],
#             style=''
#         )
#     ).add_to(m)

#     # Add points to the map representing where donations are from.
#     # Start with a layer for contributions.
    
#     contribution_layer = folium.FeatureGroup(name='Contributions').add_to(m)
    
#     # Format the donation amounts with a dollar sign and comma.
    
#     df = df.assign(amount='$' + df.apply(lambda x: "{:,}".format(x['amount']), axis=1))
    
#     # Make a custom jitter function for the coordinates of the points.
    
#     def jitter(n):
        
#         return n * (1 + np.random.rand() * .001)
    
#     for n in range(len(df)):
        
#         # Assign the amount, name, etc. to display.
#         # Get the state abbreviation with the state mapping.
        
#         amount = df.amount.iloc[n]
        
#         date = str(df.date.iloc[n])
        
#         name = df.first_last.iloc[n]
        
#         city = df.city.iloc[n]
        
#         state = state_mapping[df.state.iloc[n]]
        
#         zip_code = str(df.zip.iloc[n])
        
#         link = '<a href=\"https://docquery.fec.gov/cgi-bin/fecimg/?' + str(df.image.iloc[n]) + '\" target=\"_blank\">Documentation</a>'
        
#         # Create a popup with the link to the reference document.
        
#         popup_link = folium.Popup(link)
                
#         # Plot the points.
        
#         folium.CircleMarker(
#             location=(jitter(df.center.iloc[n].y), jitter(df.center.iloc[n].x)),
#             tooltip=(amount + '<br/>' + date + '<br/>' + name + '<br/>' + city + ', ' + state + ' ' + zip_code),
#             popup=popup_link,
#             radius=4,
#             color='white',
#             fill=True,
#             fill_color='green',
#             fill_opacity=1
#         ).add_to(contribution_layer)

#     ##################
#     # PAC TRANSACTIONS
#     ##################

#     # Add a red dot for transactions sent by the PAC, not received.
#     # Identify transactions of interest based on recipient zip codes.
    
#     df_transfers = df_cc[df_cc.sender == pac][['city', 'state', 'zip', 'amount', 'date', 'recipient', 'image']]
    
#     # If there are transactions, proceed.
    
#     if not df_transfers.empty:

#         # Make another layer for transactions, not donations.
        
#         transfer_layer = folium.FeatureGroup(name='Transfers').add_to(m)

#         # Find zips where funds were transfered to.
        
#         pac_zip_transfers = zip_points[zip_points.zip.astype('int').isin(list(df_transfers.zip.values.astype('int')))]

#         # Add the center point to the information about the received transaction.
        
#         df_transfers = pd.merge(df_transfers, pac_zip_transfers[['zip', 'center']], how='left', on='zip').dropna(axis='rows')
        
#         # Format amounts with a $ and comma.
        
#         df_transfers = df_transfers.assign(amount='$' + df_transfers.apply(lambda x: "{:,}".format(x['amount']), axis=1))
        
#         # Drop any null values.
        
#         df_transfers = df_transfers.dropna(axis='rows')

#         # Plot all the sent transactions.
        
#         for n in range(len(df_transfers)):
            
#             # Assign the amount, name, etc. to display.
#             # Get the state abbreviation with the state mapping.
            
#             amount = df_transfers.amount.iloc[n]
            
#             date = str(df_transfers.date.iloc[n])
            
#             recipient = df_transfers.recipient.iloc[n]
            
#             city = df_transfers.city.iloc[n]
            
#             state = state_mapping[df_transfers.state.iloc[n]]
            
#             zip_code = str(df_transfers.zip.iloc[n])
                    
#             link = '<a href=\"https://docquery.fec.gov/cgi-bin/fecimg/?' + str(df_transfers.image.iloc[n]) + '\" target=\"_blank\">Documentation</a>'
            
#             # Create a popup with the link to the reference document.
            
#             popup_link = folium.Popup(link)
            
#             # Then add the marker.
            
#             folium.CircleMarker(
#                 location=(jitter(df_transfers.center.iloc[n].y), jitter(df_transfers.center.iloc[n].x)),
#                 tooltip=(recipient + '<br/>' + amount + '<br/>' + date + '<br/>' + city + ', ' + state + ' ' + zip_code),
#                 popup=popup_link,
#                 radius=4,
#                 color='red',
#                 fill=True,
#                 fill_color='red',
#                 fill_opacity=1
#             ).add_to(transfer_layer)

#     folium.LayerControl().add_to(m)

#     # Save the map output.
    
#     m.save('map.html')

#     return html.Iframe(srcDoc=open('map.html', 'r').read(), width='60%', height='600')

#############
# RUN THE APP
#############

if __name__ == '__main__':
    app.run_server(debug=True)

# Turn off hot-reloading.
# app.run_server(dev_tools_hot_reload=False)
