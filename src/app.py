import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_daq as daq
import plotly.graph_objs as go
import pandas as pd
import os
import logging
from functools import lru_cache

enable_logging = False

# Logging setup
if enable_logging:
    logging.basicConfig(
        filename=os.path.abspath(os.path.join(os.getcwd(), '..', 'data', 'dash_debug.log')),
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
    )

def log(msg):
    print(msg, flush=True)
    if enable_logging:
        logging.info(msg)

# Constants
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

MAX_POINTS = 100  # Limit points to plot per sensor

# Cache CSV reading to avoid multiple file reads in a short time
@lru_cache(maxsize=1)
def read_csv_cached():
    if not os.path.exists(CSV_PATH):
        log(f"CSV file not found: {CSV_PATH}")
        return None
    df = pd.read_csv(CSV_PATH)
    df.columns = df.columns.str.strip()
    if 'timestamp' not in df.columns:
        log("CSV is missing 'timestamp' column.")
        return None
    return df.tail(MAX_POINTS)

# Dash setup
app = dash.Dash(__name__)
app.title = "40 Inch Data"
server = app.server

# suffix_row = "_row"
# suffix_button_id = "_button"
# suffix_sparkline_graph = "_sparkline_graph"
# suffix_count = "_count"
# suffix_ooc_n = "_OOC_number"
# suffix_ooc_g = "_OOC_graph"
# suffix_indicator = "_indicator"

app.layout = html.Div([
    html.H1("40 Inch Data", style={'textAlign': 'center'}),

    dcc.Interval(id='interval-component', interval=5000, n_intervals=0),

    html.Div([
        html.Div([
            dcc.Graph(id=f'graph-{i}', clear_on_unhover=True)
            for i in range(8)
        ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(4, 1fr)', 'gap': '15px'})
    ], style={'padding': '20px'})
])

@app.callback(
    [Output(f'graph-{i}', 'figure') for i in range(8)],
    Input('interval-component', 'n_intervals'),
    [State(f'graph-{i}', 'relayoutData') for i in range(8)]
)
def update_graphs(n, *relayout_data_list):
    df = read_csv_cached()

    if df is None:
        # Return empty plots with titles indicating missing data
        return [go.Figure().update_layout(title=f"{col} (No data)") for col in SENSOR_COLUMNS]

    figures = []
    for i, col in enumerate(SENSOR_COLUMNS):
        relayout = relayout_data_list[i]
        fig = go.Figure()

        if col in df.columns:
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df[col],
                mode='lines+markers',
                name=col
            ))

            if relayout:
                layout_args = {}

                if 'xaxis.range[0]' in relayout and 'xaxis.range[1]' in relayout:
                    layout_args['xaxis'] = dict(
                        range=[
                            relayout['xaxis.range[0]'],
                            relayout['xaxis.range[1]']
                        ]
                    )

                if 'yaxis.range[0]' in relayout and 'yaxis.range[1]' in relayout:
                    layout_args['yaxis'] = dict(
                        range=[
                            relayout['yaxis.range[0]'],
                            relayout['yaxis.range[1]']
                        ]
                    )

                if layout_args:
                    fig.update_layout(**layout_args)

            fig.update_layout(title=col.capitalize(), margin=dict(l=30, r=10, t=40, b=30))
        else:
            fig.update_layout(title=f"{col} (Missing)")

        figures.append(fig)

    return figures


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8050)
