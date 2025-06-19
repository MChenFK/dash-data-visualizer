import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import pandas as pd
import os
import logging

# Logging setup
logging.basicConfig(
    filename=os.path.normpath(os.getcwd() + os.sep + os.pardir) + '/data/dash_debug.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
)

def log(msg):
    print(msg, flush=True)
    logging.info(msg)

# Constants
CSV_PATH = os.path.normpath(os.getcwd() + os.sep + os.pardir) + '/data/data.csv'
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

# Dash setup
app = dash.Dash(__name__)
app.title = "40 Inch Data"

app.layout = html.Div([
    html.H1("40 Inch Data", style={'textAlign': 'center'}),

    dcc.Interval(id='interval-component', interval=1000, n_intervals=0),

    html.Div([
        html.Div([
            dcc.Graph(id=f'graph-{i}', clear_on_unhover=True)
            for i in range(8)
        ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(4, 1fr)', 'gap': '15px'})
    ], style={'padding': '20px'})
])

# Callback to update all 8 graphs with zoom persistence
@app.callback(
    [Output(f'graph-{i}', 'figure') for i in range(8)],
    Input('interval-component', 'n_intervals'),
    [State(f'graph-{i}', 'relayoutData') for i in range(8)]
)
def update_graphs(n, *relayout_data_list):
    if not os.path.exists(CSV_PATH):
        log(f"CSV file not found: {CSV_PATH}")
        return [go.Figure().update_layout(title=SENSOR_COLUMNS[i]) for i in range(8)]

    df = pd.read_csv(CSV_PATH)
    df.columns = df.columns.str.strip()
    if 'timestamp' not in df.columns:
        log("CSV is missing 'timestamp' column.")
        return [go.Figure().update_layout(title=f"{col} (Missing timestamp)") for col in SENSOR_COLUMNS]

    df = df.tail(MAX_POINTS)

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

# Run the Dash app
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8050)
