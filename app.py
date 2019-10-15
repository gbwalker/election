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
zip_bounds = pd.read_pickle('C:/Users/Gabriel/Desktop/FEC/cleaned_data/zip_bounds')
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
                    searchable=False,
                    value='Hallmark Cards Pac'
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
    
    return html.Iframe(
        srcDoc=map_pac(input_value, df_individuals, zip_bounds, sf_states, state_abbreviations, df_cc), 
        width='60%', 
        height='600'
        )

#############
# RUN THE APP
#############

if __name__ == '__main__':
    app.run_server(debug=True)

# Turn off hot-reloading.
# app.run_server(dev_tools_hot_reload=False)
