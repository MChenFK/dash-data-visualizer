import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
import os

# Constants
CSV_PATH = '../data/data.csv'
SENSOR_COLUMNS = [f'sensor{i+1}' for i in range(8)]
MAX_POINTS = 100  # Limit points to plot per sensor

# Dash setup
app = dash.Dash(__name__)
app.title = "Live CSV Sensor Dashboard"

app.layout = html.Div([
    html.H1("Live Sensor Dashboard (CSV)", style={'textAlign': 'center'}),

    dcc.Interval(id='interval-component', interval=1000, n_intervals=0),

    html.Div([
        html.Div([
            dcc.Graph(id=f'graph-{i}') for i in range(8)
        ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(4, 1fr)', 'gap': '15px'})
    ], style={'padding': '20px'})
])

# Callback to update all 8 graphs
@app.callback(
    [Output(f'graph-{i}', 'figure') for i in range(8)],
    Input('interval-component', 'n_intervals')
)
def update_graphs(n):
    if not os.path.exists(CSV_PATH):
        return [go.Figure().update_layout(title=f'Sensor {i+1}') for i in range(8)]

    df = pd.read_csv(CSV_PATH)

    # Use only the last MAX_POINTS entries for performance
    df = df.tail(MAX_POINTS)

    figures = []
    for i, col in enumerate(SENSOR_COLUMNS):
        if col in df.columns:
            trace = go.Scatter(
                x=df['timestamp'],
                y=df[col],
                mode='lines+markers',
                name=col
            )
            fig = go.Figure(data=[trace])
            fig.update_layout(title=f"{col.capitalize()}", margin=dict(l=30, r=10, t=40, b=30))
        else:
            fig = go.Figure().update_layout(title=f"{col} (Missing)")

        figures.append(fig)

    return figures

# Run the Dash app
if __name__ == '__main__':
    app.run_server(debug=False, host='0.0.0.0', port=8050)
