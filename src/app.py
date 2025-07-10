import dash
from dash import dcc, html, Input, Output, State
import dash_table
import pandas as pd
import os
import plotly.graph_objs as go

# Constants and data
CSV_PATH = os.path.abspath(os.path.join(os.getcwd(), '..', 'data', 'data.csv'))
SENSOR_COLUMNS = [
    'deposition rate (A/sec)',
    'power (%)',
    'pressure (mTorr)',
    'temperature (C)',
    'crystal (kA)',
    'anode current (amp)',
    'neutralization current (amp)',
    'gas flow (sccm)',
]

MAX_POINTS = 100  # limit points to plot

def read_csv():
    if not os.path.exists(CSV_PATH):
        return None
    df = pd.read_csv(CSV_PATH)
    df.columns = df.columns.str.strip()
    if 'timestamp' not in df.columns:
        return None
    return df.tail(MAX_POINTS)

app = dash.Dash(__name__)
server = app.server
app.title = "40 Inch Data with Tabs"

app.layout = html.Div([
    # Banner
    html.Div([
        html.H1("40 Inch Manufacturing Data", style={'textAlign': 'center', 'padding': '10px'}),
    ], style={'backgroundColor': '#003366', 'color': 'white'}),

    # Tabs
    dcc.Tabs(id='tabs', value='tab-all', children=[
        dcc.Tab(label='All Graphs', value='tab-all'),
        dcc.Tab(label='Single Graph View', value='tab-single'),
        dcc.Tab(label='CSV Table', value='tab-table'),
    ]),

    # Store for current df (optional optimization)
    dcc.Store(id='data-store'),

    # Content container for tab content
    html.Div(id='tab-content'),

    # Interval for updating data
    dcc.Interval(id='interval-component', interval=5*1000, n_intervals=0)
])

# Callback to update data-store every interval
@app.callback(
    Output('data-store', 'data'),
    Input('interval-component', 'n_intervals')
)
def update_data(n):
    df = read_csv()
    if df is None:
        return {}
    return df.to_dict('records')

# Callback to render tab content
@app.callback(
    Output('tab-content', 'children'),
    Input('tabs', 'value'),
    State('data-store', 'data')
)
def render_tab(tab, data):
    if not data:
        df = read_csv()
        if df is None:
            return html.Div("No data available.")
        data = df.to_dict('records')
    
    df = pd.DataFrame(data)

    if tab == 'tab-all':
        # All graphs tab content
        return html.Div([
            html.Div([
                html.Label("Select Graphs to Show:"),
                dcc.Checklist(
                    id='graph-selector',
                    options=[{'label': col, 'value': col} for col in SENSOR_COLUMNS],
                    value=SENSOR_COLUMNS,  # default all selected
                    labelStyle={'display': 'inline-block', 'marginRight': '15px'}
                )
            ], style={'padding': '10px'}),
            html.Div(id='all-graphs-container', style={
                'display': 'grid',
                'gridTemplateColumns': 'repeat(auto-fill, minmax(300px, 1fr))',
                'gap': '15px',
                'padding': '10px'
            }),
        ])

    elif tab == 'tab-single':
        # Single graph view content
        return html.Div([
            dcc.Dropdown(
                id='single-graph-dropdown',
                options=[{'label': col, 'value': col} for col in SENSOR_COLUMNS],
                value=SENSOR_COLUMNS[0],
                clearable=False,
                style={'width': '300px', 'margin': '10px 0'}
            ),
            dcc.Graph(id='single-graph'),
            html.Div([
                html.Button("Previous", id='prev-graph', n_clicks=0),
                html.Button("Next", id='next-graph', n_clicks=0),
            ], style={'display': 'flex', 'gap': '10px', 'justifyContent': 'center', 'padding': '10px'})
        ])

    elif tab == 'tab-table':
        # CSV Table view
        return html.Div([
            dash_table.DataTable(
                id='csv-table',
                columns=[{"name": i, "id": i} for i in df.columns],
                data=df.to_dict('records'),
                page_size=15,
                style_table={'overflowX': 'auto'},
                style_header={'backgroundColor': '#003366', 'color': 'white', 'fontWeight': 'bold'},
                style_cell={'textAlign': 'left', 'padding': '5px'},
            )
        ])

@app.callback(
    [Output('all-graphs-container', 'children'),
     Output('all-graphs-container', 'style')],
    Input('graph-selector', 'value'),
    State('data-store', 'data')
)
def update_all_graphs(selected_graphs, data):
    if not data:
        return html.Div("No data to display."), {}
    if not selected_graphs:
        return html.Div("No graphs selected."), {}

    df = pd.DataFrame(data)
    ordered_selected = [col for col in SENSOR_COLUMNS if col in selected_graphs]

    graphs = []
    for col in ordered_selected:
        if col not in df.columns:
            continue
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df[col],
            mode='lines+markers',
            name=col
        ))
        fig.update_layout(title=col, margin=dict(l=30, r=10, t=40, b=30))

        graphs.append(
            dcc.Graph(
                id=f"graph-{col}",
                figure=fig,
                style={'height': '300px', 'width': '100%'}
            )
        )

    num_graphs = len(graphs) or 1

    container_style = {
        'display': 'grid',
        'gridTemplateColumns': f'repeat({num_graphs}, minmax(300px, 1fr))',
        'gap': '15px',
        'padding': '10px',
        'width': '100%',
    }

    return graphs, container_style


# Single graph callbacks (dropdown + next/prev buttons)
@app.callback(
    Output('single-graph-dropdown', 'value'),
    [Input('prev-graph', 'n_clicks'), Input('next-graph', 'n_clicks')],
    State('single-graph-dropdown', 'value')
)
def cycle_single_graph(prev_clicks, next_clicks, current):
    if current is None:
        return SENSOR_COLUMNS[0]

    ctx = dash.callback_context
    if not ctx.triggered:
        return current
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    current_index = SENSOR_COLUMNS.index(current)

    if button_id == 'prev-graph':
        new_index = (current_index - 1) % len(SENSOR_COLUMNS)
    elif button_id == 'next-graph':
        new_index = (current_index + 1) % len(SENSOR_COLUMNS)
    else:
        new_index = current_index

    return SENSOR_COLUMNS[new_index]

@app.callback(
    Output('single-graph', 'figure'),
    [Input('single-graph-dropdown', 'value'),
     Input('data-store', 'data')]
)
def update_single_graph(selected_col, data):
    if not data or selected_col is None:
        return go.Figure()
    df = pd.DataFrame(data)
    if selected_col not in df.columns:
        return go.Figure()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df[selected_col],
        mode='lines+markers',
        name=selected_col
    ))
    fig.update_layout(title=selected_col, margin=dict(l=30, r=10, t=40, b=30))

    return fig

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8050)
