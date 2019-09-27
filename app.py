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
import pandas as pd

######
# DATA
######

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

app.layout = html.Div(
    
    # Add in custom colors/styling.
    
    style={'backgroundColor': colors['background']},
    
    children=[
    
    # First component.

    html.H1(
        children='Hello Dash',
        style={
            'textAlign': 'center',
            'color': colors['text']
        }
    ),
    # Second component.

    html.Div(
        children='Dash: A web application framework for Python.', 
        style={
        'textAlign': 'center',
        'color': colors['text']
    }),

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
    
    generate_table(df),
    
    html.Hr(),
    
    # Sample Markdown text.
    
    dcc.Markdown(children=markdown_text),
    
    html.Hr(),
    
    # A reactive text box.
    
    dcc.Input(id='my-id', value='initial value', type='text'),
    
    html.Div(id='my-div')
    
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
    app.run_server(debug=True, dev_tools_hot_reload=True)

# Turn off hot-reloading.
# app.run_server(dev_tools_hot_reload=False)
