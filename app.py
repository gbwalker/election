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

######
# DATA
######

# Identify the data folder and relative paths to it.
# PATH = pathlib.Path(__file__).parent
# DATA_PATH = PATH.joinpath('data').resolve()

# Load the pickled data.
# zips = pickle.load(open(DATA_PATH.joinpath('zips'), 'rb'))

# zips = pd.read_pickle('C:/Users/Gabriel/Desktop/FEC/cleaned_data/zips')

df_candidate = pd.read_pickle('C:/Users/Gabriel/Desktop/FEC/cleaned_data/df_candidate')

markdown_text = '''
### Dash and Markdown!!

Dash apps can be written in Markdown.
Dash uses the [CommonMark](http://commonmark.org/)
specification of Markdown.
Check out their [60 Second Markdown Tutorial](http://commonmark.org/help/)
if this is your first introduction to Markdown!
'''

df = pd.read_csv(
    'https://gist.githubusercontent.com/chriddyp/'
    'c78bf172206ce24f77d6363a2d754b59/raw/'
    'c353e8ef842413cae56ae3920b8fd78468aa4cb2/'
    'usa-agricultural-exports-2011.csv')

#######
# STYLE
#######
# Use CSS from an external source. See details here about customization: https://dash.plot.ly/external-resources.
# See HTML components: https://dash.plot.ly/dash-html-components.

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

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

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(id='root',
    
    # Add in custom colors/styling.
    
    style={'backgroundColor': colors['background']},
    
    children=[
        
        # Title and introductory text divider.
        
        html.Div(
            id="header",
            children=[
                html.H1(
                    children='Hello Dash',
                    style={
                        'textAlign': 'left',
                        'color': colors['text']
                    }
                ),
                html.P(
                    id='intro-text',
                    children='Here is a paragraph of introductory text.'
                ),
                html.Div(
                    children='Dash: A web application framework for Python.', 
                    style={
                    'textAlign': 'left',
                    'color': colors['text']
                    }
                )
            ],
        ),
        
        # Main app container.
        
        html.Div(
            id="app-container",
            children=[
                
                # Input container.
            
                html.Div(
                    id="left-column",
                    children=[
                        html.Div(
                            id="slider-container",
                            children=[
                                html.P(
                                    id="slider-text",
                                    children="Drag the slider to change the year:",
                                )
                            ],
                        ),
                    ]
                ),
                
                # Map container.
                # Use an iframe to hold it: https://medium.com/@shachiakyaagba_41915/integrating-folium-with-dash-5338604e7c56.
                
                html.Div(
                    # id="heatmap-container",
                    # children=[
                    #     html.P(
                    #         "Heatmap of age adjusted mortality rates \
                    #             from poisonings in year {0}".format(min(YEARS)),
                    #         id="heatmap-title",
                    #     ),
                    #     dcc.Graph(
                    #         id="county-choropleth",
                    #         figure=dict(
                    #             data=[
                    #                 dict(
                    #                     lat=df_lat_lon["Latitude "],
                    #                     lon=df_lat_lon["Longitude"],
                    #                     text=df_lat_lon["Hover"],
                    #                     type="scattermapbox",
                    #                 )
                    #             ],
                    #             layout=dict(
                    #                 mapbox=dict(
                    #                     layers=[],
                    #                     accesstoken=mapbox_access_token,
                    #                     style=mapbox_style,
                    #                     center=dict(lat=38.72490, lon=-95.61446),
                    #                     pitch=0,
                    #                     zoom=3.5
                    #                 ),
                    #                 autosize=True,
                    #             ),
                    #         ),
                    #     )
                    # ],
                ),
                
                # dcc.Graph displays a plotly.js chart.

                dcc.Graph(
                        id='example-graph-2',
                        figure={
                            'data': [
                                {'x': [1, 2, 3], 'y': [4, 1, 2], 'type': 'bar', 'name': 'SF'},
                                {'x': [1, 2, 3], 'y': [2, 4, 5], 'type': 'bar', 'name': u'Montréal'},
                            ],
                            'layout': {
                                'plot_bgcolor': colors['background'],
                                'paper_bgcolor': colors['background'],
                                'font': {
                                    'color': colors['text']
                                }
                            }
                        }
                    ),
                
                html.Hr(),
                
                # An HTML table.
                
                html.H4(children='US Agriculture Exports (2011)'), 
                
                generate_table(df_candidate),
                
                html.Hr(),
                
                # Sample Markdown text.
                
                dcc.Markdown(children=markdown_text),
                
                html.Hr(),
                
                # A reactive text box.
                
                dcc.Input(id='my-id', value='initial value', type='text'),
                
                html.Div(id='my-div')
            ]
        ) 
    ])

###################
# REACTIVE ELEMENTS
###################

# A reactive text box. The functional component (i.e., function) that translates the input property into the output property is directly below.

@app.callback(
    Output(component_id='my-div', component_property='children'),
    [Input(component_id='my-id', component_property='value')]
)
def update_output_div(input_value):
    return 'You\'ve entered "{}" :)'.format(input_value)

#############
# RUN THE APP
#############

if __name__ == '__main__':
    app.run_server(debug=True)

# Turn off hot-reloading.
# app.run_server(dev_tools_hot_reload=False)